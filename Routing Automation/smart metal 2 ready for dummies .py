import re

# ============ CONFIGURATION VARIABLES ============
WIRE_WIDTH = 34  # Wire width in design units (half-width is 17, so total is 34)
METAL_WIDTH = 0.1 #istance between start and end on x axis (in microns)
WINDOW_NUMBER = 2  # Window number for TCL commands
DESIGN_NAME = "hello_again"
CELL_NAME = "automationtesting"
METAL_LAYER = "M2"  # Metal layer to use
X_MIN_OFFSET = 130  # Offset to add to all x_min positions (in microns)
# =================================================

# ============ FILE PATHS CONFIGURATION ============
# Input DEF file path
INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"

# Output TCL file path
OUTPUT_PATH = r"C:\Users\TEBA\Desktop\routing automation final product\metal 2 .txt"
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
                
                # Check if this is a dummy device (has lxDummy prefix)
                is_dummy = name.startswith('lxDummy')
                
                components.append({
                    'name': name,
                    'type': comp_type,
                    'x': x,
                    'y': y,
                    'orientation': orientation,
                    'is_dummy': is_dummy
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

def calculate_x_range(components, include_dummy=True):
    """
    Calculate x range for components, optionally excluding dummy devices.
    
    Args:
        components: List of components
        include_dummy: If False, only consider essential (non-dummy) devices
    
    Returns:
        tuple: (x_min, x_max) in design units (microns)
    """
    if include_dummy:
        filtered = components
    else:
        # Filter out dummy devices
        filtered = [comp for comp in components if not comp.get('is_dummy', False)]
    
    if not filtered:
        return None, None
    
    x_coords = [comp['x'] for comp in filtered]
    return min(x_coords), max(x_coords)

def generate_tcl_code(components, metal_width, window_num, design, cell, layer, x_min_offset):
    """Generate TCL code for creating horizontal rectangles"""
    
    # Convert microns to design units (assuming microns)
    def to_design_units(microns):
        return microns / 1000.0
    
    # Calculate half-width in design units
    half_width = to_design_units(WIRE_WIDTH / 2)
    
    tcl_code = []
    
    # Track created rectangles to avoid duplicates
    created_rectangles = set()
    
    # Find the minimum and maximum x coordinates from all components
    if not components:
        return "# No components to process"
    
    # Group components by rows
    rows = group_components_by_rows(components)
    
    # Calculate x ranges
    # For essential devices only (exclude dummy)
    x_min_essential, x_max_essential = calculate_x_range(components, include_dummy=False)
    # For all devices (include dummy)
    x_min_all, x_max_all = calculate_x_range(components, include_dummy=True)
    
    # Add header comments
    tcl_code.append("# Auto-generated TCL code for horizontal rectangle creation")
    tcl_code.append(f"# Processing {len(rows)} unique rows")
    tcl_code.append(f"# Wire Width: {WIRE_WIDTH} (half-width: {WIRE_WIDTH/2})")
    tcl_code.append(f"# Metal Width: {metal_width}")
    tcl_code.append(f"# Window Number: {window_num}")
    tcl_code.append(f"# X Min Offset: {x_min_offset} microns")
    tcl_code.append(f"# X range (essential devices only): {x_min_essential} to {x_max_essential} microns")
    tcl_code.append(f"# X range (all devices): {x_min_all} to {x_max_all} microns")
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
            # [146, 50, 308, 402] = essential devices only
            # [496] = all devices (including dummy)
            y_offsets_essential = [146, 50, 308, 402]
            y_offsets_all = [496]
            tcl_code.append(f"# Using N/FN offsets (essential): {y_offsets_essential}")
            tcl_code.append(f"# Using N/FN offsets (all devices): {y_offsets_all}")
        elif orientation in ['S', 'FS']:
            # Case 2: S or FS orientation
            # [158, 253, 508, 412] = essential devices only
            # [63] = all devices (including dummy)
            y_offsets_essential = [158, 253, 508, 412]
            y_offsets_all = [63]
            tcl_code.append(f"# Using S/FS offsets (essential): {y_offsets_essential}")
            tcl_code.append(f"# Using S/FS offsets (all devices): {y_offsets_all}")
        else:
            tcl_code.append(f"# Warning: Unknown orientation '{orientation}', skipping this row")
            tcl_code.append("")
            row_number += 1
            continue
        
        # Convert y_coord to design units
        y_base = to_design_units(y_coord)
        
        # Calculate x ranges for this specific row
        row_x_min_essential, row_x_max_essential = calculate_x_range(row_components, include_dummy=False)
        row_x_min_all, row_x_max_all = calculate_x_range(row_components, include_dummy=True)
        
        # Generate rectangles for essential device offsets
        for offset in y_offsets_essential:
            y_center = y_base + to_design_units(offset)
            
            # Calculate y coordinates for rectangle (center +/- half_width)
            y_start = y_center + half_width  # y + 17
            y_end = y_center - half_width    # y - 17
            
            # Use essential devices x range with offset
            x_start = to_design_units(row_x_min_essential + x_min_offset)
            x_end = to_design_units(row_x_max_essential + 300)  # Add 300 micron offset to the end
            
            # Create a unique identifier for this rectangle (round to avoid floating point issues)
            rect_key = (round(x_start, 6), round(y_start, 6), round(x_end, 6), round(y_end, 6))
            
            # Skip if this rectangle was already created
            if rect_key in created_rectangles:
                tcl_code.append(f"# Skipping duplicate rectangle at y={y_center:.6f}")
                continue
            
            # Mark this rectangle as created
            created_rectangles.add(rect_key)
            
            tcl_code.append("")
            tcl_code.append(f"# Rectangle at offset {offset} microns (ESSENTIAL DEVICES ONLY)")
            tcl_code.append(f"# X range: {row_x_min_essential}+{x_min_offset} to {row_x_max_essential}+300 microns")
            tcl_code.append(f"# Y center: {y_center:.3f}, Y range: {y_start:.3f} to {y_end:.3f}")
            tcl_code.append(f"le::createRectangle {{{{{x_start:.3f} {y_start:.3f}}} {{{x_end:.3f} {y_end:.3f}}}}} -design [ed] -lpp {{{layer} drawing}}")
        
        # Generate rectangles for all device offsets (including dummy)
        for offset in y_offsets_all:
            y_center = y_base + to_design_units(offset)
            
            # Calculate y coordinates for rectangle (center +/- half_width)
            y_start = y_center + half_width  # y + 17
            y_end = y_center - half_width    # y - 17
            
            # Use all devices x range (including dummy) with offset
            x_start = to_design_units(row_x_min_all + x_min_offset)
            x_end = to_design_units(row_x_max_all + 300)  # Add 300 micron offset to the end
            
            # Create a unique identifier for this rectangle (round to avoid floating point issues)
            rect_key = (round(x_start, 6), round(y_start, 6), round(x_end, 6), round(y_end, 6))
            
            # Skip if this rectangle was already created
            if rect_key in created_rectangles:
                tcl_code.append(f"# Skipping duplicate rectangle at y={y_center:.6f}")
                continue
            
            # Mark this rectangle as created
            created_rectangles.add(rect_key)
            
            tcl_code.append("")
            tcl_code.append(f"# Rectangle at offset {offset} microns (ALL DEVICES INCLUDING DUMMY)")
            tcl_code.append(f"# X range: {row_x_min_all}+{x_min_offset} to {row_x_max_all}+300 microns")
            tcl_code.append(f"# Y center: {y_center:.3f}, Y range: {y_start:.3f} to {y_end:.3f}")
            tcl_code.append(f"le::createRectangle {{{{{x_start:.3f} {y_start:.3f}}} {{{x_end:.3f} {y_end:.3f}}}}} -design [ed] -lpp {{{layer} drawing}}")
        
        tcl_code.append("")
        row_number += 1
    
    tcl_code.append("# " + "="*70)
    tcl_code.append(f"# Total rectangles created: {len(created_rectangles)}")
    tcl_code.append("# " + "="*70)
    
    return "\n".join(tcl_code)

def main():
    print("Metal2 Horizontal Rectangle Generator - Modified Version")
    print("=" * 60)
    print("Features:")
    print(f"  - Wire width: {WIRE_WIDTH} (half-width: {WIRE_WIDTH/2})")
    print("  - Essential device rectangles (offsets 146,50,308,402 for N/FN or 158,253,508,412 for S/FS)")
    print("  - All device rectangles including dummy (offset 496 for N/FN or 63 for S/FS)")
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
    
    # Count dummy devices
    dummy_count = sum(1 for comp in components if comp.get('is_dummy', False))
    essential_count = len(components) - dummy_count
    print(f"  - Essential devices: {essential_count}")
    print(f"  - Dummy devices: {dummy_count}")
    
    # Filter out tap components
    filtered_components = filter_tap_components(components)
    print(f"After filtering tap components: {len(filtered_components)} components")
    
    # Count dummy devices after filtering
    dummy_count = sum(1 for comp in filtered_components if comp.get('is_dummy', False))
    essential_count = len(filtered_components) - dummy_count
    print(f"  - Essential devices: {essential_count}")
    print(f"  - Dummy devices: {dummy_count}")
    
    # Group by rows for analysis
    rows = group_components_by_rows(filtered_components)
    print(f"\nComponents are organized in {len(rows)} unique rows:")
    for y_coord, row_comps in rows.items():
        essential_in_row = sum(1 for comp in row_comps if not comp.get('is_dummy', False))
        dummy_in_row = len(row_comps) - essential_in_row
        print(f"  Row at Y={y_coord}: {len(row_comps)} components " +
              f"(orientation: {row_comps[0]['orientation']}, " +
              f"essential: {essential_in_row}, dummy: {dummy_in_row})")
    
    # Generate TCL code
    print("\nGenerating TCL code...")
    tcl_code = generate_tcl_code(
        filtered_components, 
        METAL_WIDTH, 
        WINDOW_NUMBER,
        DESIGN_NAME,
        CELL_NAME,
        METAL_LAYER,
        X_MIN_OFFSET
    )
    
    # Write to output file
    try:
        with open(OUTPUT_PATH, 'w') as f:
            f.write(tcl_code)
        
        print("\nTCL code generated successfully!")
        print(f"Output written to: {OUTPUT_PATH}")
        print(f"Generated rectangles for {len(rows)} rows")
        print("\nRectangle types:")
        print("  - Essential device rectangles: Exclude dummy devices in x-axis calculation")
        print("  - All device rectangles: Include dummy devices in x-axis calculation")
        
    except Exception as e:
        print(f"\nERROR writing to output file: {e}")
        print("\nGenerated TCL content:")
        print("-" * 80)
        print(tcl_code)

if __name__ == "__main__":
    main()