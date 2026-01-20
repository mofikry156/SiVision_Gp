import re

# ============ CONFIGURATION VARIABLES ============
METAL_WIDTH = 1.7  # Distance between start and end on x axis (in microns)
WINDOW_NUMBER = 2  # Window number for TCL commands
DESIGN_NAME = "hello_again"
CELL_NAME = "automationtesting"
METAL_LAYER = "M2"  # Metal layer to use
# =================================================

# ============ FILE PATHS CONFIGURATION ============
# Input DEF file path
INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"

# Output TCL file path
OUTPUT_PATH = r"C:\Users\TEBA\Desktop\automated automation\metal2.tcl"
# =================================================

def parse_def_file(def_content):
    """Parse DEF file and extract component information"""
    components = []
    
    # Extract components section
    comp_section = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', 
                            def_content, re.DOTALL)
    
    if not comp_section:
        return components
    
    # Parse each component line
    comp_lines = comp_section.group(1).strip().split('\n')
    
    for line in comp_lines:
        line = line.strip()
        if line.startswith('-'):
            # Parse component: - NAME TYPE + FIXED/PLACED ( X Y ) ORIENTATION
            match = re.search(r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:FIXED|PLACED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)', 
                            line)
            if match:
                name = match.group(1)
                comp_type = match.group(2)
                x = int(match.group(3))
                y = int(match.group(4))
                orientation = match.group(5)
                
                components.append({
                    'name': name,
                    'type': comp_type,
                    'x': x,
                    'y': y,
                    'orientation': orientation
                })
    
    return components

def filter_tap_components(components):
    """Filter out tap components"""
    filtered_components = []
    
    for comp in components:
        # Skip any tap components (Ntap, Ptap, Ntap_end, Ptap_end)
        if 'tap' in comp['type'].lower():
            continue
        
        filtered_components.append(comp)
    
    return filtered_components

def group_components_by_rows(components):
    """
    Group components by their Y coordinate (rows).
    Components with the same Y coordinate are in the same row.
    Returns a dictionary where keys are Y coordinates and values are lists of components.
    """
    rows = {}
    
    for comp in components:
        y = comp['y']
        if y not in rows:
            rows[y] = []
        rows[y].append(comp)
    
    # Sort rows by Y coordinate
    sorted_rows = dict(sorted(rows.items()))
    
    return sorted_rows

def generate_tcl_code(components, metal_width, window_num, design, cell, layer):
    """Generate TCL code for creating horizontal wires"""
    
    # Convert microns to design units (assuming microns)
    def to_design_units(microns):
        return microns / 1000.0
    
    tcl_code = []
    
    # Track created wires to avoid duplicates
    created_wires = set()
    
    # Find the minimum and maximum x coordinates from all components
    if not components:
        return "# No components to process"
    
    # Group components by rows
    rows = group_components_by_rows(components)
    
    # Calculate overall x range for all wires
    x_coords = [comp['x'] for comp in components]
    x_min = min(x_coords)
    x_max = max(x_coords)
    x_start = to_design_units(x_min)
    x_end = to_design_units(x_max + 300)  # Add 300 micron offset to the end
    
    # Add header comments
    tcl_code.append("# Auto-generated TCL code for horizontal wire creation")
    tcl_code.append(f"# Processing {len(rows)} unique rows")
    tcl_code.append(f"# Metal Width: {metal_width}")
    tcl_code.append(f"# Window Number: {window_num}")
    tcl_code.append(f"# Wire X range: {x_start:.6f} to {x_end:.6f} (from x={x_min} to x={x_max}+300 microns)")
    tcl_code.append("")
    
    # Setup commands
    tcl_code.append("# Setup layer visibility")
    tcl_code.append(f"db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window {window_num}]] -value false")
    tcl_code.append(f"gi::setField {{allSelectable}} -value {{false}} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows {window_num}]]]")
    tcl_code.append(f"db::setAttr visible -of [de::getLPPs -from [de::getContexts -window {window_num}]] -value false")
    tcl_code.append(f"gi::setField {{allVisible}} -value {{false}} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows {window_num}]]]")
    tcl_code.append("")
    
    # Set active layer
    tcl_code.append("# Set active layer")
    tcl_code.append(f"de::setActiveLPP [de::getLPPs {{{layer} drawing}} -from [oa::DesignFind {design} {cell} layout]]")
    tcl_code.append("")
    
    # Process each row
    row_number = 1
    for y_coord, row_components in rows.items():
        tcl_code.append("# " + "="*70)
        tcl_code.append(f"# ROW {row_number}: Y = {y_coord} microns ({len(row_components)} components)")
        tcl_code.append("# " + "="*70)
        
        # Get the first component's orientation (assuming all in same row have same orientation)
        first_comp = row_components[0]
        orientation = first_comp['orientation']
        
        tcl_code.append(f"# Row orientation: {orientation}")
        
        # Determine y offsets based on orientation
        if orientation in ['N', 'FN']:
            # Case 1: N or FN orientation
            y_offsets = [146, 50, 308, 402, 496]
            tcl_code.append(f"# Using N/FN offsets: {y_offsets}")
        elif orientation in ['S', 'FS']:
            # Case 2: S or FS orientation
            y_offsets = [158, 253, 508, 412, 63]
            tcl_code.append(f"# Using S/FS offsets: {y_offsets}")
        else:
            tcl_code.append(f"# Warning: Unknown orientation '{orientation}', skipping this row")
            tcl_code.append("")
            row_number += 1
            continue
        
        # Convert y_coord to design units
        y_base = to_design_units(y_coord)
        
        # Generate wire for each offset
        for offset in y_offsets:
            y_wire = y_base + to_design_units(offset)
            
            # Create a unique identifier for this wire (round to avoid floating point issues)
            wire_key = (round(x_start, 6), round(y_wire, 6), round(x_end, 6))
            
            # Skip if this wire was already created
            if wire_key in created_wires:
                tcl_code.append(f"# Skipping duplicate wire at y={y_wire:.6f}")
                continue
            
            # Mark this wire as created
            created_wires.add(wire_key)
            
            tcl_code.append("")
            tcl_code.append(f"# Wire at offset {offset} microns from row base")
            tcl_code.append("ile::createInterconnect")
            tcl_code.append(f"de::addPoint \\")
            tcl_code.append(f"    [list {x_start:.6f} {y_wire:.6f}] \\")
            tcl_code.append(f"    -context [db::getNext [de::getContexts -window {window_num}]]")
            tcl_code.append(f"de::completeShape \\")
            tcl_code.append(f"    [list {x_end:.6f} {y_wire:.6f}] \\")
            tcl_code.append(f"    -context [db::getNext [de::getContexts -window {window_num}]]")
        
        tcl_code.append("")
        row_number += 1
    
    tcl_code.append("# " + "="*70)
    tcl_code.append(f"# Total wires created: {len(created_wires)}")
    tcl_code.append("# " + "="*70)
    tcl_code.append("")
    
    # Add cleanup commands at the end
    tcl_code.append("# Restore layer visibility")
    tcl_code.append(f"db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window {window_num}]] -value true")
    tcl_code.append(f"gi::setField {{allSelectable}} -value {{true}} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows {window_num}]]]")
    tcl_code.append(f"db::setAttr visible -of [de::getLPPs -from [de::getContexts -window {window_num}]] -value true")
    tcl_code.append(f"gi::setField {{allVisible}} -value {{true}} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows {window_num}]]]")
    tcl_code.append("# Set active layer")
    tcl_code.append(f"de::setActiveLPP [de::getLPPs {{{layer} drawing}} -from [oa::DesignFind {design} {cell} layout]]")
    
    return "\n".join(tcl_code)

def main():
    print("Metal2 Horizontal Wire Generator - File Input Version")
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
     
    # Parse components
    print("\nParsing DEF file...")
    components = parse_def_file(def_content)
    print(f"Found {len(components)} components")
    
    # Filter out tap components
    filtered_components = filter_tap_components(components)
    print(f"After filtering tap components: {len(filtered_components)} components")
    
    # Group by rows for analysis
    rows = group_components_by_rows(filtered_components)
    print(f"Components are organized in {len(rows)} unique rows:")
    for y_coord, row_comps in rows.items():
        print(f"  Row at Y={y_coord}: {len(row_comps)} components (orientation: {row_comps[0]['orientation']})")
    
    # Generate TCL code
    print("\nGenerating TCL code...")
    tcl_code = generate_tcl_code(
        filtered_components, 
        METAL_WIDTH, 
        WINDOW_NUMBER,
        DESIGN_NAME,
        CELL_NAME,
        METAL_LAYER
    )
    
    # Write to output file
    try:
        with open(OUTPUT_PATH, 'w') as f:
            f.write(tcl_code)
        
        print("\nTCL code generated successfully!")
        print(f"Output written to: {OUTPUT_PATH}")
        print(f"Generated wires for {len(rows)} rows")
        
    except Exception as e:
        print(f"\nERROR writing to output file: {e}")
        print("\nGenerated TCL content:")
        print("-" * 80)
        print(tcl_code)

if __name__ == "__main__":
    main()