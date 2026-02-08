import re

# ============================================================
# GLOBAL CONFIGURATION VARIABLES
# ============================================================

# Rectangle offsets (in nanometers)
RECT_X_MIN_OFFSET = 0      # Offset from minimum X position
RECT_X_MAX_OFFSET = 147    # Offset from maximum X position
RECT_Y_MIN_OFFSET = 106    # Offset from Y position (bottom)
RECT_Y_MAX_OFFSET = 140    # Offset from Y position (top)

# Via offsets (in nanometers)
VIA_X_START_OFFSET = 110   # Starting X offset from minimum X
VIA_X_END_OFFSET = 45      # Ending X offset from maximum X
VIA_Y_OFFSET = 123         # Y offset from row Y position
VIA_SPACING = 74           # Spacing between vias

# Via type
VIA_TYPE = "VIA12"

# Metal layer
METAL_LAYER = "M2"

# ============================================================


def parse_def_file(def_path):
    """Parse DEF file to extract components and nets information."""
    with open(def_path, 'r') as f:
        content = f.read()
    
    # Extract components - FIXED: Added support for negative coordinates
    components = []
    comp_pattern = r'- (\S+)\s+(\S+)\s+\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)'
    for match in re.finditer(comp_pattern, content):
        comp_name, comp_type, x, y, orientation = match.groups()
        components.append({
            'name': comp_name,
            'type': comp_type,
            'x': int(x),
            'y': int(y),
            'orientation': orientation
        })
    
    # Extract net names
    nets = []
    net_pattern = r'- (\S+)\s*\n'
    nets_section = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', content, re.DOTALL)
    if nets_section:
        for match in re.finditer(net_pattern, nets_section.group(1)):
            nets.append(match.group(1))
    
    return components, nets

def find_power_ground_nets(nets):
    """Find VDD/VCC and VSS/GND nets (case insensitive)."""
    power_net = None
    ground_net = None
    
    for net in nets:
        net_upper = net.upper()
        if 'VDD' in net_upper or 'VCC' in net_upper:
            power_net = net
        elif 'VSS' in net_upper or 'GND' in net_upper:
            ground_net = net
    
    return power_net, ground_net

def group_taps_by_row(components):
    """Group tap devices by their Y position (row)."""
    ntaps = [c for c in components if 'Ntap' in c['type']]
    ptaps = [c for c in components if 'Ptap' in c['type']]
    
    # Group by Y coordinate
    def group_by_y(taps):
        rows = {}
        for tap in taps:
            y = tap['y']
            if y not in rows:
                rows[y] = []
            rows[y].append(tap)
        return rows
    
    ntap_rows = group_by_y(ntaps)
    ptap_rows = group_by_y(ptaps)
    
    return ntap_rows, ptap_rows

def generate_vias_for_row(x_min, x_max, y_pos):
    """Generate via commands for a tap row.
    
    Args:
        x_min: Minimum X position in nanometers (can be negative)
        x_max: Maximum X position in nanometers (can be negative)
        y_pos: Y position in nanometers
    
    Returns:
        List of TCL command strings
    """
    via_commands = []
    
    # Starting position
    x_start = (x_min + VIA_X_START_OFFSET) / 1000.0  # Convert to microns
    x_end = (x_max + VIA_X_END_OFFSET) / 1000.0      # End position
    y_via = (y_pos + VIA_Y_OFFSET) / 1000.0          # Y position in microns
    
    via_spacing = VIA_SPACING / 1000.0  # Convert spacing to microns
    
    # Generate vias - only de::addPoint commands, setup is done once at the beginning
    current_x = x_start
    while current_x <= x_end:
        via_commands.append("de::addPoint {{{:.3f} {:.3f}}} -context [de::getActiveContext]".format(current_x, y_via))
        current_x += via_spacing
    
    return via_commands

def generate_tcl_script(components, nets, output_path):
    """Generate TCL script for tap routing."""
    
    # Find power and ground nets
    power_net, ground_net = find_power_ground_nets(nets)
    
    if not power_net:
        power_net = "VDD"  # Default
    if not ground_net:
        ground_net = "VSS"  # Default
    
    # Group taps by row
    ntap_rows, ptap_rows = group_taps_by_row(components)
    
    tcl_commands = []
    tcl_commands.append("# Generated TCL script for tap routing")
    tcl_commands.append("# Uses getActiveWindow and getActiveContext")
    tcl_commands.append("# Power net: {}".format(power_net))
    tcl_commands.append("# Ground net: {}".format(ground_net))
    tcl_commands.append("#")
    tcl_commands.append("# Configuration:")
    tcl_commands.append("#   Rectangle X offsets: {} to {}".format(RECT_X_MIN_OFFSET, RECT_X_MAX_OFFSET))
    tcl_commands.append("#   Rectangle Y offsets: {} to {}".format(RECT_Y_MIN_OFFSET, RECT_Y_MAX_OFFSET))
    tcl_commands.append("#   Via X offsets: {} to {}".format(VIA_X_START_OFFSET, VIA_X_END_OFFSET))
    tcl_commands.append("#   Via Y offset: {}".format(VIA_Y_OFFSET))
    tcl_commands.append("#   Via spacing: {}".format(VIA_SPACING))
    tcl_commands.append("#   Via type: {}".format(VIA_TYPE))
    tcl_commands.append("#   Metal layer: {}".format(METAL_LAYER))
    tcl_commands.append("")
    
    # ========== PART 1: ALL RECTANGLES ==========
    tcl_commands.append("# ========== RECTANGLES ==========")
    tcl_commands.append("")
    
    # Process Ntap rows (connected to power) - rectangles only
    tcl_commands.append("# NTAP ROWS (Power)")
    for y_pos, taps in sorted(ntap_rows.items()):
        # Find min and max X positions
        x_positions = [tap['x'] for tap in taps]
        x_min = min(x_positions)
        x_max = max(x_positions)
        
        tcl_commands.append("# Ntap Row at Y={}".format(y_pos))
        tcl_commands.append("# X range: {} to {}".format(x_min, x_max))
        
        # Calculate coordinates (convert from nanometers to microns)
        x1 = (x_min + RECT_X_MIN_OFFSET) / 1000.0
        x2 = (x_max + RECT_X_MAX_OFFSET) / 1000.0
        y1 = (y_pos + RECT_Y_MIN_OFFSET) / 1000.0
        y2 = (y_pos + RECT_Y_MAX_OFFSET) / 1000.0
        
        # Generate rectangle command
        tcl_cmd = "le::createRectangle {{{{{:.3f} {:.3f}}} {{{:.3f} {:.3f}}}}} -design [ed] -lpp {{{} drawing}} -net {}".format(
            x1, y1, x2, y2, METAL_LAYER, power_net
        )
        tcl_commands.append(tcl_cmd)
        tcl_commands.append("")
    
    # Process Ptap rows (connected to ground) - rectangles only
    tcl_commands.append("# PTAP ROWS (Ground)")
    for y_pos, taps in sorted(ptap_rows.items()):
        # Find min and max X positions
        x_positions = [tap['x'] for tap in taps]
        x_min = min(x_positions)
        x_max = max(x_positions)
        
        tcl_commands.append("# Ptap Row at Y={}".format(y_pos))
        tcl_commands.append("# X range: {} to {}".format(x_min, x_max))
        
        # Calculate coordinates (convert from nanometers to microns)
        x1 = (x_min + RECT_X_MIN_OFFSET) / 1000.0
        x2 = (x_max + RECT_X_MAX_OFFSET) / 1000.0
        y1 = (y_pos + RECT_Y_MIN_OFFSET) / 1000.0
        y2 = (y_pos + RECT_Y_MAX_OFFSET) / 1000.0
        
        # Generate rectangle command
        tcl_cmd = "le::createRectangle {{{{{:.3f} {:.3f}}} {{{:.3f} {:.3f}}}}} -design [ed] -lpp {{{} drawing}} -net {}".format(
            x1, y1, x2, y2, METAL_LAYER, ground_net
        )
        tcl_commands.append(tcl_cmd)
        tcl_commands.append("")
    
    # ========== PART 2: VIA SETUP ==========
    tcl_commands.append("# ========== VIA SETUP ==========")
    tcl_commands.append("ile::createVia")
    tcl_commands.append("gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getActiveWindow]]")
    tcl_commands.append("gi::setField {viaDefName} -value {" + VIA_TYPE + "} -in [gi::getToolbars {deCommandOptions} -from [gi::getActiveWindow]]")
    tcl_commands.append("")
    
    # ========== PART 3: ALL VIA PLACEMENTS ==========
    tcl_commands.append("# ========== VIA PLACEMENTS ==========")
    tcl_commands.append("")
    
    # Generate vias for Ntap rows
    tcl_commands.append("# NTAP ROW VIAS")
    for y_pos, taps in sorted(ntap_rows.items()):
        x_positions = [tap['x'] for tap in taps]
        x_min = min(x_positions)
        x_max = max(x_positions)
        
        tcl_commands.append("# Ntap Row at Y={}".format(y_pos))
        via_cmds = generate_vias_for_row(x_min, x_max, y_pos)
        tcl_commands.extend(via_cmds)
        tcl_commands.append("")
    
    # Generate vias for Ptap rows
    tcl_commands.append("# PTAP ROW VIAS")
    for y_pos, taps in sorted(ptap_rows.items()):
        x_positions = [tap['x'] for tap in taps]
        x_min = min(x_positions)
        x_max = max(x_positions)
        
        tcl_commands.append("# Ptap Row at Y={}".format(y_pos))
        via_cmds = generate_vias_for_row(x_min, x_max, y_pos)
        tcl_commands.extend(via_cmds)
        tcl_commands.append("")
    
    # Write to output file
    with open(output_path, 'w') as f:
        f.write('\n'.join(tcl_commands))
    
    # Calculate statistics
    total_ntap_vias = 0
    for y_pos, taps in ntap_rows.items():
        x_positions = [tap['x'] for tap in taps]
        x_min = min(x_positions)
        x_max = max(x_positions)
        x_start = x_min + VIA_X_START_OFFSET
        x_end = x_max + VIA_X_END_OFFSET
        num_vias = int((x_end - x_start) / VIA_SPACING) + 1
        total_ntap_vias += num_vias
    
    total_ptap_vias = 0
    for y_pos, taps in ptap_rows.items():
        x_positions = [tap['x'] for tap in taps]
        x_min = min(x_positions)
        x_max = max(x_positions)
        x_start = x_min + VIA_X_START_OFFSET
        x_end = x_max + VIA_X_END_OFFSET
        num_vias = int((x_end - x_start) / VIA_SPACING) + 1
        total_ptap_vias += num_vias
    
    print(f"TCL script generated successfully at: {output_path}")
    print(f"Total Ntap rows: {len(ntap_rows)}")
    print(f"Total Ptap rows: {len(ptap_rows)}")
    print(f"Total Ntap vias: {total_ntap_vias}")
    print(f"Total Ptap vias: {total_ptap_vias}")
    print(f"Power net used: {power_net}")
    print(f"Ground net used: {ground_net}")
    
    # Print detailed coordinate info for debugging
    print("\nDetailed tap information:")
    print("Ntap rows:")
    for y_pos, taps in sorted(ntap_rows.items()):
        x_positions = [tap['x'] for tap in taps]
        print(f"  Y={y_pos}: X from {min(x_positions)} to {max(x_positions)} ({len(taps)} taps)")
    print("Ptap rows:")
    for y_pos, taps in sorted(ptap_rows.items()):
        x_positions = [tap['x'] for tap in taps]
        print(f"  Y={y_pos}: X from {min(x_positions)} to {max(x_positions)} ({len(taps)} taps)")

# Main execution
if __name__ == "__main__":
    # Use uploaded file location
    input_path = "c:/Users/TEBA/Desktop/Neat Routing Automation/DEF_file_Input.txt"
    output_path = "c:/Users/TEBA/Desktop/routing automation final product/taps_routing.tcl"
    
    try:
        # Parse DEF file
        print("Parsing DEF file...")
        components, nets = parse_def_file(input_path)
        print(f"Found {len(components)} components and {len(nets)} nets")
        
        # Count tap components
        ntaps = [c for c in components if 'Ntap' in c['type']]
        ptaps = [c for c in components if 'Ptap' in c['type']]
        print(f"Found {len(ntaps)} Ntap components and {len(ptaps)} Ptap components")
        
        # Generate TCL script
        print("\nGenerating TCL script...")
        generate_tcl_script(components, nets, output_path)
        
    except FileNotFoundError:
        print(f"Error: Could not find input file at {input_path}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()