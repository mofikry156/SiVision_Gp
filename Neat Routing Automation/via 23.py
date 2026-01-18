import re
from collections import defaultdict

# ==================== GLOBAL VARIABLES ====================
WINDOW_NUMBER = 2
# X_AXIS_START and X_AXIS_STEP will be calculated dynamically from device positions
X_AXIS_START = None  # Will be calculated as min(pfet/nfet X positions) + 0.100 microns
X_AXIS_STEP = None   # Will be calculated as (X_END - X_START) / number_of_nets
X_OFFSET_MICRONS = 0.400  # 100nm offset from device boundaries
VIA_NAME = "VIA23"
RECT_OFFSET_X_MICRONS = 0.040 # Represents the "40" offset (40nm = 0.040um) for X-axis width
RECT_OFFSET_Y_SINGLE_MICRONS = 0.500 # Represents the "500" offset (500nm = 0.5um) for single via height

# ==================== FILE PATHS CONFIGURATION ====================
# Input DEF file path
INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"

# Output TCL file path
OUTPUT_PATH = r"C:\Users\TEBA\Desktop\Neat Routing Automation\4_via23 output.tcl"

# ==================== FUNCTIONS ====================

def parse_device_positions(def_content):
    """
    Parse DEF file and extract X positions of PFET and NFET devices.
    Returns (x_min, x_max) in microns, or (None, None) if no devices found.
    """
    x_positions = []
    
    # Find COMPONENTS section
    components_match = re.search(r'COMPONENTS.*?END COMPONENTS', def_content, re.DOTALL)
    
    if not components_match:
        return None, None
    
    components_section = components_match.group(0)
    
    # Pattern to match component lines with pfet or nfet (case-insensitive) and their positions
    # Example: - instance_name pfet + FIXED ( x y ) orientation
    # or: - instance_name nfet + FIXED ( x y ) orientation
    # Note: Using FIXED instead of PLACED as per the actual DEF format
    component_pattern = r'-\s+\S+\s+(pfet|nfet|PFET|NFET)\s+.*?\+\s+(FIXED|PLACED)\s+\(\s*(\d+)\s+\d+\s*\)'
    
    matches = re.finditer(component_pattern, components_section, re.IGNORECASE)
    
    for match in matches:
        x_coord = int(match.group(3))  # X coordinate in nanometers (now group 3 after adding FIXED|PLACED)
        x_positions.append(x_coord)
    
    if not x_positions:
        return None, None
    
    # Convert to microns
    x_min_microns = min(x_positions) / 1000.0
    x_max_microns = max(x_positions) / 1000.0
    
    return x_min_microns, x_max_microns


def calculate_x_parameters(x_min, x_max, num_nets):
    """
    Calculate X_AXIS_START and X_AXIS_STEP based on device positions.
    
    Args:
        x_min: Minimum X position of devices in microns
        x_max: Maximum X position of devices in microns
        num_nets: Number of different nets
    
    Returns:
        (x_start, x_step) tuple
    """
    if x_min is None or x_max is None or num_nets == 0:
        return None, None
    
    # X_START = min X + 100nm offset
    x_start = x_min + X_OFFSET_MICRONS
    
    # X_END = max X - 100nm offset
    x_end = x_max - X_OFFSET_MICRONS
    
    # X_STEP = (X_END - X_START) / number of nets
    # If only one net, step doesn't matter (can be any value or 0)
    if num_nets == 1:
        x_step = 0.0
    else:
        x_step = (x_end - x_start) / (num_nets - 1)
    
    return x_start, x_step


def parse_metal2_routes(def_content):
    """
    Parse DEF file and extract Metal2 routing information grouped by net name.
    Returns a dictionary: {net_name: [list of y_coordinates]}
    """
    metal2_routes = defaultdict(set)  # Use set to avoid duplicate Y positions
    
    # Find SPECIALNETS and NETS sections
    specialnets_match = re.search(r'SPECIALNETS.*?END SPECIALNETS', def_content, re.DOTALL)
    nets_match = re.search(r'NETS.*?END NETS', def_content, re.DOTALL)
    
    sections = []
    if specialnets_match:
        sections.append(('SPECIALNETS', specialnets_match.group(0)))
    if nets_match:
        sections.append(('NETS', nets_match.group(0)))
    
    for section_name, section_content in sections:
        # Split into individual nets
        net_blocks = re.split(r'\n-\s+', section_content)
        
        for block in net_blocks:
            if not block.strip():
                continue
                
            # Extract net name (first line)
            lines = block.split('\n')
            first_line = lines[0].strip()
            
            # Net name is the first word after the dash (or at the beginning)
            net_name_match = re.match(r'(\S+)', first_line)
            if not net_name_match:
                continue
            net_name = net_name_match.group(1)
            
            # Skip if it's a section header
            if net_name in ['SPECIALNETS', 'NETS', 'END']:
                continue
            
            # Find all M2 (Metal2) routes with coordinates
            # Pattern: M2 width ( x1 y1 ) ( x2 y2 ) or M2 width ( x y )
            m2_patterns = [
                r'M2\s+\d+\s+\(\s*(\d+)\s+(\d+)\s*\)\s+\(\s*\d+\s+\d+\s*\)',  # M2 with two points
                r'M2\s+\d+\s+\(\s*(\d+)\s+(\d+)\s*\)',  # M2 with one point
            ]
            
            for pattern in m2_patterns:
                matches = re.finditer(pattern, block)
                for match in matches:
                    y_coord = int(match.group(2))
                    metal2_routes[net_name].add(y_coord)
    
    # Convert sets to sorted lists
    result = {}
    for net_name, y_coords in metal2_routes.items():
        if len(y_coords) > 0:  # Only include nets with Metal2 routes
            result[net_name] = sorted(list(y_coords))
    
    return result


def generate_tcl_commands(metal2_routes, x_axis_start, x_axis_step):
    """
    Generate TCL commands to create vias for each net at different X positions.
    Each new signal (net) gets its own X position, stepped by X_AXIS_STEP.
    Also generates a rectangle covering the extent of vias in that column.
    """
    tcl_commands = []
    tcl_commands.append("# Auto-generated VIA23 creation commands")
    tcl_commands.append(f"# Window Number: {WINDOW_NUMBER}")
    tcl_commands.append(f"# Starting X Position: {x_axis_start:.3f} microns (calculated from device positions)")
    tcl_commands.append(f"# X Step: {x_axis_step:.3f} microns (calculated from device span and net count)")
    tcl_commands.append(f"# Via Name: {VIA_NAME}\n")
    
    # Sort nets by name for consistent output
    sorted_nets = sorted(metal2_routes.items())
    
    for net_index, (net_name, y_positions) in enumerate(sorted_nets):
        # Calculate X position for this net
        x_pos = x_axis_start + (net_index * x_axis_step)
        
        tcl_commands.append(f"# Net: {net_name} (X Position: {x_pos:.3f})")
        tcl_commands.append(f"# Found {len(y_positions)} Metal2 route(s) at Y positions: {y_positions}")
        
        # 1. Generate via command for each Y position
        for y_pos in y_positions:
            # Convert from nanometers to microns
            y_microns = y_pos / 1000.0
            
            tcl_command = (
                f"ile::createVia\n"
                f"gi::setField {{viaDefName}} -value {{{VIA_NAME}}} "
                f"-in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {WINDOW_NUMBER}]]\n"
                f"de::addPoint {{{x_pos:.3f} {y_microns:.3f}}} "
                f"-context [db::getNext [de::getContexts -window {WINDOW_NUMBER}]]\n"
            )
            tcl_commands.append(tcl_command)

        # 2. Generate Rectangle command for the column
        if y_positions:
            # Calculate X bounds (X +/- 40nm)
            x_rect_min = x_pos - RECT_OFFSET_X_MICRONS
            x_rect_max = x_pos + RECT_OFFSET_X_MICRONS
            
            y_rect_start = 0.0
            y_rect_end = 0.0

            # Logic check: Single via vs Multiple vias
            if len(y_positions) == 1:
                # Case: Single Via
                # Start at the via Y, end at via Y + 500nm
                via_y_nm = y_positions[0]
                y_rect_start = via_y_nm / 1000.0
                y_rect_end = y_rect_start + RECT_OFFSET_Y_SINGLE_MICRONS
            else:
                # Case: Multiple Vias
                # Start at min Y via, end at max Y via
                y_min_nm = min(y_positions)
                y_max_nm = max(y_positions)
                y_rect_start = y_min_nm / 1000.0
                y_rect_end = y_max_nm / 1000.0
            
            rect_command = (
                f"le::createRectangle {{{{{x_rect_min:.3f} {y_rect_start:.3f}}} {{{x_rect_max:.3f} {y_rect_end:.3f}}}}} "
                f"-design [ed] -lpp {{M3 drawing}} -net {net_name}"
            )
            tcl_commands.append(rect_command)
        
        tcl_commands.append("")  # Empty line between nets
    
    return "\n".join(tcl_commands)


def main():
    """Main function to parse DEF and generate TCL output."""
    
    print("Metal2 VIA23 Generator - Dynamic X-Axis Calculation")
    print("=" * 60)
    
    # Read DEF file
    print(f"\nReading DEF file from: {INPUT_DEF_FILE}")
    try:
        with open(INPUT_DEF_FILE, 'r') as f:
            DEF_CONTENT = f.read()
        print(f"Successfully read {len(DEF_CONTENT)} characters from input file")
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {INPUT_DEF_FILE}")
        print("Please check the file path and try again.")
        return
    except Exception as e:
        print(f"ERROR reading input file: {e}")
        return
    
    if not DEF_CONTENT.strip():
        print("ERROR: DEF file is empty.")
        return
    
    # Parse device positions to calculate X parameters
    print("\nParsing PFET/NFET device positions...")
    x_min, x_max = parse_device_positions(DEF_CONTENT)
    
    if x_min is None or x_max is None:
        print("ERROR: No PFET/NFET devices found in DEF file.")
        print("Cannot calculate X-axis parameters.")
        return
    
    print(f"Device X range: {x_min:.3f} to {x_max:.3f} microns")
    
    # Parse Metal2 routes
    print("\nParsing DEF file for Metal2 routes...")
    metal2_routes = parse_metal2_routes(DEF_CONTENT)
    
    if not metal2_routes:
        print("No Metal2 routes found in the DEF file.")
        return
    
    print(f"\nFound {len(metal2_routes)} nets with Metal2 routes:")
    for net_name, y_positions in sorted(metal2_routes.items()):
        print(f"  - {net_name}: {len(y_positions)} Y position(s)")
    
    # Calculate X parameters
    x_axis_start, x_axis_step = calculate_x_parameters(x_min, x_max, len(metal2_routes))
    
    if x_axis_start is None or x_axis_step is None:
        print("ERROR: Could not calculate X-axis parameters.")
        return
    
    x_end = x_max - X_OFFSET_MICRONS
    print(f"\nCalculated X-axis parameters:")
    print(f"  X_START = {x_axis_start:.3f} microns (min device X + {X_OFFSET_MICRONS:.3f})")
    print(f"  X_END = {x_end:.3f} microns (max device X - {X_OFFSET_MICRONS:.3f})")
    print(f"  X_STEP = {x_axis_step:.3f} microns ((X_END - X_START) / {len(metal2_routes) - 1 if len(metal2_routes) > 1 else 1})")
    
    print("\nGenerating TCL commands...")
    tcl_output = generate_tcl_commands(metal2_routes, x_axis_start, x_axis_step)
    
    # Write to output file
    try:
        with open(OUTPUT_PATH, 'w') as f:
            f.write(tcl_output)
        print(f"\nTCL commands successfully written to: {OUTPUT_PATH}")
        print(f"Total nets processed: {len(metal2_routes)}")
        
        # Calculate total vias
        total_vias = sum(len(y_pos) for y_pos in metal2_routes.values())
        print(f"Total vias to be created: {total_vias}")
        
    except Exception as e:
        print(f"\nERROR writing to file: {e}")
        print("\nGenerated TCL content:")
        print("-" * 80)
        print(tcl_output)


if __name__ == "__main__":
    main()