import re
from collections import defaultdict

# Global variables
WINDOW_NUMBER = 2
DELAY = 10  # Delay in milliseconds after each TCL command

# Input and output paths
DEF_INPUT_PATH = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"
TCL_OUTPUT_PATH = r"C:\Users\TEBA\Desktop\Neat Routing Automation\Align.txt"

def parse_def_file(file_path):
    """Parse DEF file and extract component information"""
    components = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract components section
    comp_section = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', content, re.DOTALL)
    if not comp_section:
        return components
    
    # Parse each component line
    comp_lines = comp_section.group(1).strip().split('\n')
    for line in comp_lines:
        line = line.strip()
        if line.startswith('-'):
            # Parse component: - name type + FIXED/PLACED ( x y ) orientation
            match = re.match(r'-\s+(\S+)\s+(\S+).*?\(\s*(\d+)\s+(\d+)\s*\)', line)
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

def generate_tcl_script(rows, target_positions, window_num, delay):
    """Generate TCL script for row alignment"""
    tcl_lines = []
    
    # Add header commands
    tcl_lines.append(f"db::setPrefValue leStopLevel -value 0 -scope [db::getNext [de::getContexts -window {window_num}]];")
    tcl_lines.append(f"after {delay}")
    tcl_lines.append(f"db::setPrefValue leStartLevel -value 0 -scope [db::getNext [de::getContexts -window {window_num}]];")
    tcl_lines.append(f"after {delay}")
    tcl_lines.append(f"de::redraw -window {window_num}")
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
        tcl_lines.append(f"db::setPrefValue deSelectMode -value Replace -scope [db::getScopes [db::getNext [de::getContexts -window {window_num}]]];")
        tcl_lines.append(f"after {delay}")
        tcl_lines.append(f"ide::selectByRegion -region rectangle -point {{{start_x:.3f} {start_y:.3f}}}")
        tcl_lines.append(f"after {delay}")
        tcl_lines.append(f"de::endDrag {{{end_x:.3f} {end_y:.3f}}} -context [db::getNext [de::getContexts -window {window_num}]]")
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
        tcl_lines.append(f"de::endDrag {{{stretch_x2:.3f} {stretch_y2:.3f}}} -context [db::getNext [de::getContexts -window {window_num}]]")
        tcl_lines.append(f"after {delay}")
        tcl_lines.append("")
    
    return "\n".join(tcl_lines)

def main():
    try:
        # Parse DEF file
        print(f"Reading DEF file from: {DEF_INPUT_PATH}")
        components = parse_def_file(DEF_INPUT_PATH)
        print(f"Found {len(components)} components")
        
        # Group by rows
        rows = group_components_by_row(components)
        print(f"Found {len(rows)} rows")
        
        # Calculate target positions for each row
        target_positions = calculate_target_positions(rows)
        print("Target positions calculated:")
        for i, (y_pos, _) in enumerate(rows):
            print(f"  Row {i+1}: Current Y={y_pos}, Target Y={target_positions[i]}")
        
        # Generate TCL script
        tcl_script = generate_tcl_script(rows, target_positions, WINDOW_NUMBER, DELAY)
        
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