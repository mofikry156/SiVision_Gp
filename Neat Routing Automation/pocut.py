import re

# ============ CONFIGURATION VARIABLES ============
METAL_WIDTH = 1.7  # Distance between start and end on x axis (in microns)
WINDOW_NUMBER = 6  # Window number for TCL commands
DESIGN_NAME = "hello_again"
CELL_NAME = "automationtesting"
METAL_LAYER = "M2"  # Metal layer to use
POCUT_LAYER = "POCUT"  # POCUT layer for rectangles
Y_OFFSET = 15  # Offset in microns for POCUT rectangles (±15)
POCUT_THICKNESS = 0.040  # Thickness/height of POCUT rectangle in microns
# =================================================

# ============ FILE PATHS CONFIGURATION ============
# Input DEF file path
INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"

# Output TCL file path
OUTPUT_PATH = r"C:\Users\TEBA\Desktop\Neat Routing Automation\1 polycut_output.tcl"
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

def generate_tcl_code(components, metal_width, window_num, design, cell, metal_layer, pocut_layer, y_offset, pocut_thickness):
    """Generate TCL code for POCUT rectangles only"""
    
    # Convert microns to design units (assuming microns)
    def to_design_units(microns):
        return microns / 1000.0
    
    tcl_code = []
    
    # Find the minimum and maximum x coordinates from all components
    if not components:
        return "# No components to process"
    
    # Group components by rows
    rows = group_components_by_rows(components)
    
    # Calculate overall x range for all shapes
    x_coords = [comp['x'] for comp in components]
    x_min = min(x_coords)
    x_max = max(x_coords)
    x_start = to_design_units(x_min)
    x_end = to_design_units(x_max + 294)  # Add 294 micron offset to the end
    
    # Add header comments
    tcl_code.append("# Auto-generated TCL code for POCUT rectangles")
    tcl_code.append(f"# Processing {len(rows)} unique rows")
    tcl_code.append(f"# Window Number: {window_num}")
    tcl_code.append(f"# Rectangle X range: {x_start:.6f} to {x_end:.6f} (from x={x_min} to x={x_max}+294 microns)")
    tcl_code.append("")
    
    # Setup commands
    tcl_code.append("# Setup layer visibility")
    tcl_code.append(f"db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window {window_num}]] -value false")
    tcl_code.append(f"gi::setField {{allSelectable}} -value {{false}} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows {window_num}]]]")
    tcl_code.append(f"db::setAttr visible -of [de::getLPPs -from [de::getContexts -window {window_num}]] -value false")
    tcl_code.append(f"gi::setField {{allVisible}} -value {{false}} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows {window_num}]]]")
    tcl_code.append("")
    
    # Set active layer to POCUT
    tcl_code.append("# Set active layer to POCUT")
    tcl_code.append(f"de::setActiveLPP [de::getLPPs {{{pocut_layer} drawing}} -from [oa::DesignFind {design} {cell} layout]]")
    tcl_code.append("")
    
    # Process each row - create POCUT rectangle at Y=0 of each row
    row_number = 1
    for y_coord, row_components in rows.items():
        tcl_code.append("# " + "="*70)
        tcl_code.append(f"# ROW {row_number}: Y = {y_coord} microns ({len(row_components)} components)")
        tcl_code.append("# " + "="*70)
        
        # Get the first component's orientation
        first_comp = row_components[0]
        orientation = first_comp['orientation']
        
        tcl_code.append(f"# Row orientation: {orientation}")
        
        # Convert y_coord to design units
        y_base = to_design_units(y_coord)
        
        # Create POCUT rectangle at Y=0 of this row
        tcl_code.append(f"# Creating POCUT rectangle at row Y position (offset 0)")
        tcl_code.append(f"# POCUT thickness: {pocut_thickness} microns")
        tcl_code.append("")
        
        # Rectangle height using the global thickness variable
        rect_height = pocut_thickness
        y_bottom = y_base - (rect_height / 2)
        y_top = y_base + (rect_height / 2)
        
        tcl_code.append(f"le::createRectangle {{{{{x_start:.3f} {y_bottom:.3f}}} {{{x_end:.3f} {y_top:.3f}}}}} -design [ed] -lpp {{{pocut_layer} drawing}}")
        tcl_code.append("")
        
        row_number += 1
    
    tcl_code.append("# " + "="*70)
    tcl_code.append(f"# Total POCUT rectangles created: {len(rows)}")
    tcl_code.append("# " + "="*70)
    
    return "\n".join(tcl_code)

def main():
    print("POCUT Rectangle Generator - File Input Version")
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
        METAL_LAYER,
        POCUT_LAYER,
        Y_OFFSET,
        POCUT_THICKNESS
    )
    
    # Write to output file
    try:
        with open(OUTPUT_PATH, 'w') as f:
            f.write(tcl_code)
        
        print("\nTCL code generated successfully!")
        print(f"Output written to: {OUTPUT_PATH}")
        print(f"Generated POCUT rectangles for {len(rows)} rows")
        
    except Exception as e:
        print(f"\nERROR writing to output file: {e}")
        print("\nGenerated TCL content:")
        print("-" * 80)
        print(tcl_code)

if __name__ == "__main__":
    main()