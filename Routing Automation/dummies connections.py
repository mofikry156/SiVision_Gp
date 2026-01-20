import re
import os

# ============ FILE PATHS CONFIGURATION ============
# Input DEF file path
INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"

# Output TCL file path
OUTPUT_PATH = r"C:\Users\TEBA\Desktop\Neat Routing Automation\3 dummies connections output.tcl"
# =================================================

def parse_def_file(def_content):
    """Parse DEF file and extract dummy device information"""
    dummy_devices = []
    
    # Parse COMPONENTS section
    components_match = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', def_content, re.DOTALL)
    if not components_match:
        return dummy_devices
    
    components_section = components_match.group(1)
    
    # Find all component lines
    component_pattern = r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:PLACED|FIXED)\s+\(\s*(\d+)\s+(\d+)\s*\)\s+(\w+)'
    components = re.findall(component_pattern, components_section)
    
    # Parse NETS section to find source connections
    nets_match = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', def_content, re.DOTALL)
    nets_dict = {}
    
    if nets_match:
        nets_section = nets_match.group(1)
        # Split by net definition
        net_definitions = re.split(r'-\s+(\S+)', nets_section)[1:]  # Skip first empty element
        
        for i in range(0, len(net_definitions), 2):
            if i + 1 < len(net_definitions):
                net_name = net_definitions[i]
                net_connections = net_definitions[i + 1]
                
                # Find all component pin connections
                pin_pattern = r'\(\s*(\S+)\s+(\w+)\s*\)'
                pins = re.findall(pin_pattern, net_connections)
                
                for comp_name, pin_type in pins:
                    if comp_name not in nets_dict:
                        nets_dict[comp_name] = {}
                    nets_dict[comp_name][pin_type] = net_name
    
    # Filter dummy devices and extract info
    for comp_name, cell_type, x, y, orientation in components:
        if 'dummy' in comp_name.lower() or 'lxdummy' in comp_name.lower():
            x_coord = int(x)
            y_coord = int(y)
            
            # Get source net name
            source_net = "VSS"  # Default
            if comp_name in nets_dict and 'S' in nets_dict[comp_name]:
                source_net = nets_dict[comp_name]['S']
            
            dummy_devices.append({
                'name': comp_name,
                'x': x_coord,
                'y': y_coord,
                'orientation': orientation,
                'source_net': source_net
            })
    
    return dummy_devices

def generate_tcl_commands(dummy_devices):
    """Generate TCL commands for creating rectangles"""
    tcl_commands = []
    
    tcl_commands.append("# TCL commands for dummy device connections")
    tcl_commands.append("# Generated automatically from DEF file\n")
    
    for device in dummy_devices:
        name = device['name']
        x = device['x']
        y = device['y']
        orientation = device['orientation']
        net = device['source_net']
        
        tcl_commands.append(f"# Device: {name} at ({x}, {y}) orientation: {orientation}")
        tcl_commands.append(f"# Source net: {net}\n")
        
        # Convert microns to mm (divide by 1000)
        x_mm = x / 1000.0
        y_mm = y / 1000.0
        
        if orientation in ['N', 'FN']:
            # Case 1: N or FN orientation
            # First rectangle
            x1 = x_mm + 0.093
            y1 = y_mm + 0.543
            x2 = x_mm + 0.275
            y2 = y_mm + 0.509
            tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            
            # Second rectangle
            x1 = x_mm + 0.130
            y1 = y_mm + 0.198
            x2 = x_mm + 0.239
            y2 = y_mm + 0.163
            tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            
            # Third rectangle
            x1 = x_mm + 0.168
            y1 = y_mm + 0.543
            x2 = x_mm + 0.201
            y2 = y_mm + 0.180
            tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            
        elif orientation in ['S', 'FS']:
            # Case 2: S or FS orientation
            # First rectangle
            x1 = x_mm + 0.093
            y1 = y_mm + 0.025
            x2 = x_mm + 0.275
            y2 = y_mm + 0.059
            tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            
            # Second rectangle
            x1 = x_mm + 0.130
            y1 = y_mm + 0.370
            x2 = x_mm + 0.239
            y2 = y_mm + 0.405
            tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            
            # Third rectangle
            x1 = x_mm + 0.168
            y1 = y_mm + 0.025
            x2 = x_mm + 0.201
            y2 = y_mm + 0.388
            tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
        
        tcl_commands.append("")  # Empty line between devices
    
    return tcl_commands

def main():
    print("Dummy Device Connection Generator - File Input Version")
    print("=" * 60)
    
    # Read DEF file
    print(f"\nReading DEF file from: {INPUT_DEF_FILE}")
    try:
        with open(INPUT_DEF_FILE, 'r') as f:
            def_content = f.read()
        print(f"Successfully read {len(def_content)} characters from input file")
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {INPUT_DEF_FILE}")
        print("Please check the file path and try again.")
        return
    except Exception as e:
        print(f"ERROR reading input file: {e}")
        return
    
    if not def_content.strip():
        print("ERROR: DEF file is empty.")
        return
    
    # Parse the DEF file
    print("\nParsing DEF file for dummy devices...")
    dummy_devices = parse_def_file(def_content)
    
    if not dummy_devices:
        print("No dummy devices found in the DEF file.")
        return
    
    print(f"\nFound {len(dummy_devices)} dummy devices:")
    for device in dummy_devices:
        print(f"  - {device['name']}: ({device['x']}, {device['y']}) {device['orientation']} -> Net: {device['source_net']}")
    
    # Generate TCL commands
    print("\nGenerating TCL commands...")
    tcl_commands = generate_tcl_commands(dummy_devices)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Write to file
    try:
        with open(OUTPUT_PATH, 'w') as f:
            f.write('\n'.join(tcl_commands))
        
        print(f"\nTCL commands generated successfully!")
        print(f"Output saved to: {OUTPUT_PATH}")
        
        rectangle_count = len([cmd for cmd in tcl_commands if cmd.startswith('le::createRectangle')])
        print(f"\nTotal rectangles to be created: {rectangle_count}")
        print(f"Rectangles per device: 3")
        
    except Exception as e:
        print(f"\nERROR writing to output file: {e}")
        print("\nGenerated TCL content:")
        print("-" * 80)
        print('\n'.join(tcl_commands))

if __name__ == "__main__":
    main()