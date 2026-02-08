import re
from collections import defaultdict

# Global variables
WINDOW_NUMBER = 2
DELAY = 10  # Delay in milliseconds after each TCL command

def parse_def_file(file_content):
    """Parse DEF file content (string) and extract component information"""
    components = []
    
    # Extract components section
    comp_section = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', file_content, re.DOTALL)
    if not comp_section:
        return components
    
    # Parse each component line
    comp_lines = comp_section.group(1).strip().split('\n')
    for line in comp_lines:
        line = line.strip()
        if line.startswith('-'):
            # Parse component: - name type + FIXED/PLACED ( x y ) orientation
            # Updated to handle negative coordinates
            match = re.match(r'-\s+(\S+)\s+(\S+).*?\(\s*(-?\d+)\s+(-?\d+)\s*\)', line)
            if match:
                name = match.group(1)
                device_type = match.group(2)
                x = int(match.group(3))
                y = int(match.group(4))
                components.append({
                    'name': name,
                    'type': device_type,
                    'x': x,
                    'y': y
                })
    
    return components

def group_components_by_row(components):
    """Group components by their Y-coordinate (row)"""
    rows = defaultdict(list)
    for comp in components:
        rows[comp['y']].append(comp)
    
    # Sort components within each row by X-coordinate
    for y in rows:
        rows[y].sort(key=lambda c: c['x'])
    
    # Return sorted rows (by Y-coordinate, ascending from bottom to top)
    sorted_rows = sorted(rows.items(), key=lambda x: x[0])
    return sorted_rows

def get_mighty_offset(device_type):
    """Determine the mighty offset based on device type"""
    device_lower = device_type.lower()
    if 'ntap' in device_lower or 'ptap' in device_lower:
        return 200
    else:
        return 568

def calculate_target_positions(rows):
    """Calculate the final correct Y position for each row"""
    target_positions = []
    
    # First row stays at its original position
    current_y = rows[0][0]
    target_positions.append(current_y)
    
    # Calculate positions for subsequent rows
    for i in range(len(rows) - 1):
        # Get the device type of current row to determine offset
        current_row_components = rows[i][1]
        first_device = current_row_components[0]
        offset = get_mighty_offset(first_device['type'])
        
        # Next row position = current row position + offset
        current_y = current_y + offset
        target_positions.append(current_y)
    
    return target_positions

def generate_tcl_script(rows, target_positions, window_num=WINDOW_NUMBER, delay=DELAY):
    """Generate TCL script for row alignment"""
    tcl_lines = []
    
    # Add header commands
    tcl_lines.append(f"db::setPrefValue leStopLevel -value 0 ;")
    tcl_lines.append(f"after {delay}")
    tcl_lines.append(f"db::setPrefValue leStartLevel -value 0 ;")
    tcl_lines.append(f"after {delay}")
    tcl_lines.append(f"de::redraw")
    tcl_lines.append(f"after {delay}")
    tcl_lines.append("")
    
    # Process each row starting from row 2 (index 1)
    for i in range(1, len(rows)):
        y_pos, row_components = rows[i]
        
        # Get first and last device in the row
        first_device = row_components[0]
        last_device = row_components[-1]
        
        # Calculate selection region
        # Start point: (X of first device - 50, Y of device - 50)
        start_x = (first_device['x'] - 50) / 1000.0
        start_y = (first_device['y'] - 50) / 1000.0
        
        # End point: (X of last device + 50, Y of device + 600)
        end_x = (last_device['x'] + 5000) / 1000.0
        end_y = (first_device['y'] + 600) / 1000.0
        
        # Select the row
        tcl_lines.append(f"# Row {i+1}: Selecting devices at Y={y_pos}")
        tcl_lines.append(f"db::setPrefValue deSelectMode -value Replace;")
        tcl_lines.append(f"after {delay}")
        tcl_lines.append(f"ide::selectByRegion -region rectangle -point {{{start_x:.3f} {start_y:.3f}}}")
        tcl_lines.append(f"after {delay}")
        tcl_lines.append(f"de::endDrag {{{end_x:.3f} {end_y:.3f}}} ")
        tcl_lines.append(f"after {delay}")
        tcl_lines.append("")
        
        # Move the row using stretch
        # First point: any point in the current row (use first device position)
        stretch_x1 = first_device['x'] / 1000.0
        stretch_y1 = first_device['y'] / 1000.0
        
        # Second point: same X, but at target Y position
        stretch_x2 = first_device['x'] / 1000.0
        target_y = target_positions[i]
        stretch_y2 = target_y / 1000.0
        
        tcl_lines.append(f"# Moving to Y={target_y}")
        tcl_lines.append(f"ile::stretch -point {{{stretch_x1:.3f} {stretch_y1:.3f}}}")
        tcl_lines.append(f"after {delay}")
        tcl_lines.append(f"de::endDrag {{{stretch_x2:.3f} {stretch_y2:.3f}}}")
        tcl_lines.append(f"after {delay}")
        tcl_lines.append("")
    
    return "\n".join(tcl_lines)

def generate_alignment_tcl(def_content, window_num=WINDOW_NUMBER, delay=DELAY):
    """
    Main function to generate alignment TCL script from DEF content
    
    Args:
        def_content (str): The content of the DEF file as a string
        window_num (int): Window number for the TCL script
        delay (int): Delay in milliseconds after each TCL command
    
    Returns:
        str: Generated TCL script for row alignment
    
    Raises:
        Exception: If parsing fails or insufficient rows found
    """
    # Parse DEF file content
    components = parse_def_file(def_content)
    
    if not components:
        raise Exception("No components found in DEF file. Check if DEF file format is correct.")
    
    # Group by rows
    rows = group_components_by_row(components)
    
    if len(rows) < 2:
        raise Exception("Less than 2 rows found. Need at least 2 rows for alignment.")
    
    # Calculate target positions for each row
    target_positions = calculate_target_positions(rows)
    
    # Generate TCL script
    tcl_script = generate_tcl_script(rows, target_positions, window_num, delay)
    
    return tcl_script


# For standalone execution (optional - can be used for testing)
def main():
    """Standalone execution for testing purposes"""
    import sys
    
    # Input and output paths for standalone use
    DEF_INPUT_PATH = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"
    TCL_OUTPUT_PATH = r"C:\Users\TEBA\Desktop\automated automation\align.tcl"
    
    try:
        # Parse DEF file
        print(f"Reading DEF file from: {DEF_INPUT_PATH}")
        with open(DEF_INPUT_PATH, 'r') as f:
            def_content = f.read()
        
        # Generate TCL script
        tcl_script = generate_alignment_tcl(def_content)
        
        # Write to output file
        with open(TCL_OUTPUT_PATH, 'w') as f:
            f.write(tcl_script)
        
        print(f"\nTCL script written to: {TCL_OUTPUT_PATH}")
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()