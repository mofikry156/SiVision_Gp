#!/usr/bin/env python3
"""
DEF to TCL Via Generator - Simple Two-Device Per Row
Generates TCL via creation scripts using modern ile::createVia syntax
SIMPLE LOGIC: Each row has 2 devices. If they connect to different gate signals,
              one gets Option 1, the other gets Option 2. That's it.
Modified: 1 millisecond delay added after each via command
Modified: Skip G and D vias for components containing "Dummy" in name
Modified: Optional duplicate gate via with X+74 offset
Modified: Reads DEF input from external file
Modified: Added viaAuto initialization at start of script
"""

import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass


@dataclass
class Component:
    """Represents a component from DEF file"""
    name: str
    cell_type: str
    x: float
    y: float
    orientation: str


@dataclass
class NetConnection:
    """Represents a net connection"""
    net_name: str
    component: str
    pin: str


class GlobalParameters:
    """Global parameters for via generation - modify these as needed"""
    
    # Row height constraint - each signal must stay within one row
    ROW_HEIGHT = 568  # Y to Y+568
    
    # GATE VIA DUPLICATION - Set to True to create duplicate gate vias with X+74 offset
    DUPLICATE_GATE_VIAS = True  # <-- Toggle this to enable/disable gate duplication
    GATE_DUPLICATE_OFFSET_X = 74  # Offset in microns for duplicate gate via
    
    # Orientation offset rules
    # Case 1: N orientation
    N_DRAIN_OFFSET_X_OPT1 = 184
    N_DRAIN_OFFSET_Y_OPT1 = 319
    N_DRAIN_OFFSET_X_OPT2 = 184
    N_DRAIN_OFFSET_Y_OPT2 = 402
    N_SOURCE_OFFSET_X = 257
    N_SOURCE_OFFSET_Y = 502
    N_GATE_OFFSET_X_OPT1 = 147
    N_GATE_OFFSET_Y_OPT1 = 60
    N_GATE_OFFSET_X_OPT2 = 147
    N_GATE_OFFSET_Y_OPT2 = 146
    
    # Case 2: FN orientation
    FN_DRAIN_OFFSET_X_OPT1 = 184
    FN_DRAIN_OFFSET_Y_OPT1 = 319
    FN_DRAIN_OFFSET_X_OPT2 = 184
    FN_DRAIN_OFFSET_Y_OPT2 = 402
    FN_SOURCE_OFFSET_X = 110
    FN_SOURCE_OFFSET_Y = 502
    FN_GATE_OFFSET_X_OPT1 = 147
    FN_GATE_OFFSET_Y_OPT1 = 60
    FN_GATE_OFFSET_X_OPT2 = 147
    FN_GATE_OFFSET_Y_OPT2 = 146
    
    # Case 3: FS orientation
    FS_DRAIN_OFFSET_X_OPT1 = 184
    FS_DRAIN_OFFSET_Y_OPT1 = 249
    FS_DRAIN_OFFSET_X_OPT2 = 184
    FS_DRAIN_OFFSET_Y_OPT2 = 148
    FS_SOURCE_OFFSET_X = 110
    FS_SOURCE_OFFSET_Y = 64
    FS_GATE_OFFSET_X_OPT1 = 147
    FS_GATE_OFFSET_Y_OPT1 = 508
    FS_GATE_OFFSET_X_OPT2 = 147
    FS_GATE_OFFSET_Y_OPT2 = 422
    
    # Case 4: S orientation
    S_DRAIN_OFFSET_X_OPT1 = 184
    S_DRAIN_OFFSET_Y_OPT1 = 249
    S_DRAIN_OFFSET_X_OPT2 = 184
    S_DRAIN_OFFSET_Y_OPT2 = 148
    S_SOURCE_OFFSET_X = 257
    S_SOURCE_OFFSET_Y = 64
    S_GATE_OFFSET_X_OPT1 = 147
    S_GATE_OFFSET_Y_OPT1 = 508
    S_GATE_OFFSET_X_OPT2 = 147
    S_GATE_OFFSET_Y_OPT2 = 422
    
    # Microns to mm conversion factor
    MICRONS_TO_MM = 1000.0
    
    # Context window number
    CONTEXT_WINDOW = 2


class DEFParser:
    """Parses DEF files to extract component and net information"""
    
    def __init__(self, def_content: str):
        self.def_content = def_content
        self.components: Dict[str, Component] = {}
        self.nets: Dict[str, List[NetConnection]] = {}
        
    def parse(self):
        """Parse the DEF file content"""
        self._parse_components()
        self._parse_nets()
        
    def _parse_components(self):
        """Extract component information"""
        # Pattern: - component_name cell_type + FIXED ( x y ) orientation
        pattern = r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:FIXED|PLACED)\s+\(\s*(\d+)\s+(\d+)\s*\)\s+(\S+)'
        
        for match in re.finditer(pattern, self.def_content):
            name = match.group(1)
            cell_type = match.group(2)
            x = int(match.group(3))
            y = int(match.group(4))
            orientation = match.group(5)
            
            self.components[name] = Component(
                name=name,
                cell_type=cell_type,
                x=x / GlobalParameters.MICRONS_TO_MM,
                y=y / GlobalParameters.MICRONS_TO_MM,
                orientation=orientation
            )
    
    def _parse_nets(self):
        """Extract net connections"""
        # Find NETS section
        nets_match = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', self.def_content, re.DOTALL)
        if not nets_match:
            return
        
        nets_section = nets_match.group(1)
        
        # Pattern: - net_name ... ( component pin ) ...
        net_pattern = r'-\s+(\S+)(.*?)(?=\n\s*-|\Z)'
        pin_pattern = r'\(\s*(\S+)\s+(\S+)\s*\)'
        
        for net_match in re.finditer(net_pattern, nets_section, re.DOTALL):
            net_name = net_match.group(1)
            net_body = net_match.group(2)
            
            connections = []
            for pin_match in re.finditer(pin_pattern, net_body):
                component = pin_match.group(1)
                pin = pin_match.group(2)
                
                # Skip PIN entries (these are ports, not component pins)
                if component == 'PIN':
                    continue
                    
                connections.append(NetConnection(
                    net_name=net_name,
                    component=component,
                    pin=pin
                ))
            
            if connections:
                self.nets[net_name] = connections


class TCLGenerator:
    """Generates TCL via creation scripts - Simple 2 device per row logic"""
    
    def __init__(self, components: Dict[str, Component], nets: Dict[str, List[NetConnection]]):
        self.components = components
        self.nets = nets
        # Simple: Map net_name -> option (1 or 2) for each row
        # Key: (net_name, row, pin_type) -> option
        self.net_options = {}
        self.row_violations = {}
        self._check_row_constraints()
        self._assign_simple_options()
    
    def _is_dummy_component(self, component_name: str) -> bool:
        """Check if component name contains 'Dummy' (case-insensitive)"""
        return 'dummy' in component_name.lower()
    
    def _get_component_row(self, component: Component) -> int:
        """Determine which row a component belongs to based on its Y coordinate"""
        return int(component.y / GlobalParameters.ROW_HEIGHT)
    
    def _check_row_constraints(self):
        """Check which nets violate the single-row constraint"""
        for net_name, connections in self.nets.items():
            rows_used = set()
            
            for conn in connections:
                if conn.component in self.components:
                    comp = self.components[conn.component]
                    row = self._get_component_row(comp)
                    rows_used.add(row)
            
            if len(rows_used) > 1:
                self.row_violations[net_name] = sorted(list(rows_used))
    
    def _assign_simple_options(self):
        """SIMPLE LOGIC: For each row, find unique gate/drain signals and alternate options"""
        print(f"\n>> Simple Option Assignment: 2 devices per row")
        
        # Get all rows
        all_rows = set()
        for comp in self.components.values():
            row = self._get_component_row(comp)
            all_rows.add(row)
        
        # For each row, process gate and drain signals INDEPENDENTLY
        for row in sorted(all_rows):
            print(f"\n  Row {row}:")
            
            # GATE signals in this row (INDEPENDENT LOGIC)
            gate_nets_in_row = set()
            for net_name, connections in self.nets.items():
                for conn in connections:
                    if conn.pin == 'G' and conn.component in self.components:
                        comp = self.components[conn.component]
                        if self._is_dummy_component(comp.name):
                            continue
                        if self._get_component_row(comp) == row:
                            gate_nets_in_row.add(net_name)
            
            gate_nets = sorted(list(gate_nets_in_row))
            
            if gate_nets:
                print(f"    Gate signals: {gate_nets}")
                # Assign gate options INDEPENDENTLY: first net = Option 1, second net = Option 2
                for idx, net_name in enumerate(gate_nets):
                    option = 1 if idx == 0 else 2
                    self.net_options[(net_name, row, 'G')] = option
                    print(f"      {net_name} = Gate Option {option}")
            
            # DRAIN signals in this row (INDEPENDENT LOGIC - separate from gates!)
            drain_nets_in_row = set()
            for net_name, connections in self.nets.items():
                for conn in connections:
                    if conn.pin == 'D' and conn.component in self.components:
                        comp = self.components[conn.component]
                        if self._is_dummy_component(comp.name):
                            continue
                        if self._get_component_row(comp) == row:
                            drain_nets_in_row.add(net_name)
            
            drain_nets = sorted(list(drain_nets_in_row))
            
            if drain_nets:
                print(f"    Drain signals: {drain_nets}")
                # Assign drain options INDEPENDENTLY: first net = Option 1, second net = Option 2
                for idx, net_name in enumerate(drain_nets):
                    option = 1 if idx == 0 else 2
                    self.net_options[(net_name, row, 'D')] = option
                    print(f"      {net_name} = Drain Option {option}")
    
    def get_option(self, net_name: str, row: int, pin_type: str) -> int:
        """Get the assigned option for a net in a specific row"""
        return self.net_options.get((net_name, row, pin_type), 1)
        
    def get_offset(self, orientation: str, pin_type: str, net_name: str, row: int) -> Tuple[float, float]:
        """Get X,Y offset based on orientation and pin type"""
        params = GlobalParameters
        micron_to_mm = 1.0 / params.MICRONS_TO_MM
        
        # Get option for this net
        option = self.get_option(net_name, row, pin_type)
        
        if orientation == 'N':
            if pin_type == 'D':
                if option == 1:
                    return (params.N_DRAIN_OFFSET_X_OPT1 * micron_to_mm, params.N_DRAIN_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (params.N_DRAIN_OFFSET_X_OPT2 * micron_to_mm, params.N_DRAIN_OFFSET_Y_OPT2 * micron_to_mm)
            elif pin_type == 'S':
                return (params.N_SOURCE_OFFSET_X * micron_to_mm, params.N_SOURCE_OFFSET_Y * micron_to_mm)
            elif pin_type == 'G':
                if option == 1:
                    return (params.N_GATE_OFFSET_X_OPT1 * micron_to_mm, params.N_GATE_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (params.N_GATE_OFFSET_X_OPT2 * micron_to_mm, params.N_GATE_OFFSET_Y_OPT2 * micron_to_mm)
                    
        elif orientation == 'FN':
            if pin_type == 'D':
                if option == 1:
                    return (params.FN_DRAIN_OFFSET_X_OPT1 * micron_to_mm, params.FN_DRAIN_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (params.FN_DRAIN_OFFSET_X_OPT2 * micron_to_mm, params.FN_DRAIN_OFFSET_Y_OPT2 * micron_to_mm)
            elif pin_type == 'S':
                return (params.FN_SOURCE_OFFSET_X * micron_to_mm, params.FN_SOURCE_OFFSET_Y * micron_to_mm)
            elif pin_type == 'G':
                if option == 1:
                    return (params.FN_GATE_OFFSET_X_OPT1 * micron_to_mm, params.FN_GATE_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (params.FN_GATE_OFFSET_X_OPT2 * micron_to_mm, params.FN_GATE_OFFSET_Y_OPT2 * micron_to_mm)
                    
        elif orientation == 'FS':
            if pin_type == 'D':
                if option == 1:
                    return (params.FS_DRAIN_OFFSET_X_OPT1 * micron_to_mm, params.FS_DRAIN_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (params.FS_DRAIN_OFFSET_X_OPT2 * micron_to_mm, params.FS_DRAIN_OFFSET_Y_OPT2 * micron_to_mm)
            elif pin_type == 'S':
                return (params.FS_SOURCE_OFFSET_X * micron_to_mm, params.FS_SOURCE_OFFSET_Y * micron_to_mm)
            elif pin_type == 'G':
                if option == 1:
                    return (params.FS_GATE_OFFSET_X_OPT1 * micron_to_mm, params.FS_GATE_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (params.FS_GATE_OFFSET_X_OPT2 * micron_to_mm, params.FS_GATE_OFFSET_Y_OPT2 * micron_to_mm)
                    
        elif orientation == 'S':
            if pin_type == 'D':
                if option == 1:
                    return (params.S_DRAIN_OFFSET_X_OPT1 * micron_to_mm, params.S_DRAIN_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (params.S_DRAIN_OFFSET_X_OPT2 * micron_to_mm, params.S_DRAIN_OFFSET_Y_OPT2 * micron_to_mm)
            elif pin_type == 'S':
                return (params.S_SOURCE_OFFSET_X * micron_to_mm, params.S_SOURCE_OFFSET_Y * micron_to_mm)
            elif pin_type == 'G':
                if option == 1:
                    return (params.S_GATE_OFFSET_X_OPT1 * micron_to_mm, params.S_GATE_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (params.S_GATE_OFFSET_X_OPT2 * micron_to_mm, params.S_GATE_OFFSET_Y_OPT2 * micron_to_mm)
        
        return (0, 0)
    
    def generate_via_command(self, x: float, y: float, component_name: str, pin_type: str, net_name: str, row: int) -> str:
        """Generate a single via creation command using modern syntax with 1ms delay"""
        opt = self.get_option(net_name, row, pin_type)
        opt_note = f" (Row {row}, Option {opt})"
        
        script = f"""# {component_name} - {pin_type}{opt_note}
ile::createVia
de::addPoint {{{x:.3f} {y:.3f}}} -context [db::getNext [de::getContexts -window {GlobalParameters.CONTEXT_WINDOW}]]
after 1
"""
        
        # If this is a gate via and duplication is enabled, add the duplicate
        if pin_type == 'G' and GlobalParameters.DUPLICATE_GATE_VIAS:
            x_duplicate = x + (GlobalParameters.GATE_DUPLICATE_OFFSET_X / GlobalParameters.MICRONS_TO_MM)
            script += f"""# {component_name} - {pin_type}{opt_note} [DUPLICATE +{GlobalParameters.GATE_DUPLICATE_OFFSET_X}]
ile::createVia
de::addPoint {{{x_duplicate:.3f} {y:.3f}}} -context [db::getNext [de::getContexts -window {GlobalParameters.CONTEXT_WINDOW}]]
after 1
"""
        
        return script
    
    def generate_net_script(self, net_name: str) -> str:
        """Generate TCL script for a specific net"""
        if net_name not in self.nets:
            return f"# Net {net_name} not found\n"
        
        connections = self.nets[net_name]
        script = f"# Via Generation Script for Net: {net_name}\n"
        script += f"# Total connections: {len(connections)}\n"
        
        # Check for row constraint violation
        if net_name in self.row_violations:
            script += f"# WARNING: This net spans multiple rows: {self.row_violations[net_name]}\n"
            script += f"# CONSTRAINT VIOLATION: Each signal must stay within one row (height={GlobalParameters.ROW_HEIGHT})\n"
            script += f"# This net will be SKIPPED to prevent routing errors.\n\n"
            return script
        
        script += "\n"
        script += f"puts \"Generating vias for {net_name}...\"\n\n"
        
        via_count = 0
        skipped_count = 0
        
        for conn in connections:
            if conn.component not in self.components:
                script += f"# Warning: Component {conn.component} not found\n"
                continue
            
            comp = self.components[conn.component]
            
            # Skip G and D pins for Dummy components
            if self._is_dummy_component(comp.name) and conn.pin in ['G', 'D']:
                script += f"# SKIPPED: {comp.name} - {conn.pin} (Dummy component, G/D vias disabled)\n"
                skipped_count += 1
                continue
            
            row = self._get_component_row(comp)
            
            # Get offset for this pin type and orientation
            offset_x, offset_y = self.get_offset(comp.orientation, conn.pin, net_name, row)
            
            via_x = comp.x + offset_x
            via_y = comp.y + offset_y
            
            script += self.generate_via_command(via_x, via_y, comp.name, conn.pin, net_name, row)
            via_count += 1
            
            # Count duplicate if it's a gate via
            if conn.pin == 'G' and GlobalParameters.DUPLICATE_GATE_VIAS:
                via_count += 1
        
        script += f"\nputs \"{net_name} via generation complete!\"\n"
        script += f"puts \"Total vias created: {via_count}\"\n"
        if skipped_count > 0:
            script += f"puts \"Vias skipped (Dummy G/D): {skipped_count}\"\n"
        
        return script
    
    def generate_all_nets_script(self) -> str:
        """Generate TCL script for all nets"""
        script = "# TCL Via Generation Script for All Nets\n"
        script += "# Auto-generated from DEF file\n"
        script += "# Uses modern ile::createVia syntax\n"
        script += "# SIMPLE LOGIC: 2 devices per row - Different gate signals get different options\n"
        script += "# First unique gate signal = Option 1, Second = Option 2\n"
        script += "# Each via command includes 1ms delay (after 1)\n"
        script += "# NOTE: G and D vias SKIPPED for components containing 'Dummy' in name\n"
        
        if GlobalParameters.DUPLICATE_GATE_VIAS:
            script += f"# GATE DUPLICATION: ENABLED - Each gate via duplicated at X+{GlobalParameters.GATE_DUPLICATE_OFFSET_X}\n"
        else:
            script += "# GATE DUPLICATION: DISABLED\n"
        
        script += "\n"
        
        # --- NEW INITIALIZATION COMMANDS ---
        script += "# Initialization: Set viaAuto to true\n"
        script += "ile::createVia\n"
        script += f"gi::setField {{viaAuto}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.CONTEXT_WINDOW}]]\n"
        script += "\n"
        # ------------------------------------
        
        # Report option assignments
        if self.net_options:
            script += "# ==================== OPTION ASSIGNMENTS PER ROW ====================\n"
            
            # Group by row
            options_by_row = {}
            for (net_name, row, pin_type), opt in self.net_options.items():
                if row not in options_by_row:
                    options_by_row[row] = {'G': {}, 'D': {}}
                options_by_row[row][pin_type][net_name] = opt
            
            for row in sorted(options_by_row.keys()):
                script += f"#   Row {row}:\n"
                if options_by_row[row]['G']:
                    script += f"#     Gates:\n"
                    for net_name, opt in sorted(options_by_row[row]['G'].items()):
                        script += f"#       {net_name} = Option {opt}\n"
                if options_by_row[row]['D']:
                    script += f"#     Drains:\n"
                    for net_name, opt in sorted(options_by_row[row]['D'].items()):
                        script += f"#       {net_name} = Option {opt}\n"
            script += "# ====================================================================\n\n"
        
        # Report row violations
        if self.row_violations:
            script += "# ==================== WARNING ====================\n"
            script += f"# {len(self.row_violations)} net(s) violate single-row constraint!\n"
            script += "# These nets will be SKIPPED:\n"
            for net_name, rows in self.row_violations.items():
                script += f"#   - {net_name} (spans rows: {rows})\n"
            script += "# ==================================================\n\n"
        
        # Generate scripts for each net
        for net_name in sorted(self.nets.keys()):
            script += "\n# " + "="*60 + "\n"
            script += self.generate_net_script(net_name)
            script += "\n"
        
        return script
    
    def list_available_nets(self) -> List[str]:
        """Return list of all available nets"""
        return sorted(self.nets.keys())


def process_def_content(def_content: str, net_filter: List[str] = None) -> str:
    """
    Process DEF content and generate TCL via script
    
    Args:
        def_content: String containing DEF file content
        net_filter: Optional list of net names to generate (None = all nets)
    
    Returns:
        TCL script as string
    """
    # Parse DEF file
    parser = DEFParser(def_content)
    parser.parse()
    
    print(f"Found {len(parser.components)} components")
    print(f"Found {len(parser.nets)} nets")
    
    # Generate TCL script
    generator = TCLGenerator(parser.components, parser.nets)
    
    # Count Dummy components
    dummy_count = sum(1 for comp in parser.components.values() if generator._is_dummy_component(comp.name))
    if dummy_count > 0:
        print(f"! Found {dummy_count} Dummy components - G and D vias will be SKIPPED for these")
    
    # Report gate duplication status
    if GlobalParameters.DUPLICATE_GATE_VIAS:
        print(f"! Gate via duplication: ENABLED (offset X+{GlobalParameters.GATE_DUPLICATE_OFFSET_X})")
    else:
        print(f"! Gate via duplication: DISABLED")
    
    # Report row violations
    if generator.row_violations:
        print(f"\n! WARNING: {len(generator.row_violations)} net(s) violate single-row constraint!")
        print("These nets span multiple rows and will be SKIPPED:")
        for net_name, rows in generator.row_violations.items():
            print(f"  - {net_name} (rows: {rows})")
    
    if net_filter:
        # Generate only specific nets
        script = "# TCL Via Generation Script for Selected Nets\n"
        script += "# Uses modern ile::createVia syntax\n"
        script += "# SIMPLE: First gate signal = Option 1, Second = Option 2\n"
        script += "# Each via command includes 1ms delay (after 1)\n"
        script += "# NOTE: G and D vias SKIPPED for components containing 'Dummy' in name\n"
        if GlobalParameters.DUPLICATE_GATE_VIAS:
            script += f"# GATE DUPLICATION: ENABLED - Each gate via duplicated at X+{GlobalParameters.GATE_DUPLICATE_OFFSET_X}\n"
        
        # --- NEW INITIALIZATION COMMANDS ---
        script += "\n# Initialization: Set viaAuto to true\n"
        script += "ile::createVia\n"
        script += f"gi::setField {{viaAuto}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.CONTEXT_WINDOW}]]\n"
        # ------------------------------------
        
        script += "\n"
        for net_name in net_filter:
            if net_name in parser.nets:
                script += generator.generate_net_script(net_name)
                script += "\n# " + "="*60 + "\n\n"
            else:
                print(f"Warning: Net '{net_name}' not found")
    else:
        # Generate all nets
        script = generator.generate_all_nets_script()
    
    return script


def list_nets_in_def(def_content: str) -> List[str]:
    """
    List all nets found in DEF content
    
    Args:
        def_content: String containing DEF file content
    
    Returns:
        List of net names
    """
    parser = DEFParser(def_content)
    parser.parse()
    generator = TCLGenerator(parser.components, parser.nets)
    return generator.list_available_nets()


if __name__ == "__main__":
    # ============================================
    # FILE PATHS CONFIGURATION
    # ============================================
    
    # Input DEF file path
    INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"
    
    # Output TCL file path
    OUTPUT_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\2 via 12 .tcl"
    
    # Option 1: Generate all nets
    GENERATE_ALL_NETS = True
    
    # Option 2: Generate only specific nets (set GENERATE_ALL_NETS = False)
    SPECIFIC_NETS = ['VSS']
    
    print("DEF to TCL Via Generator (Simple 2-Device Per Row)")
    print("LOGIC: First unique gate signal = Option 1, Second = Option 2")
    print("Via Delay: 1 millisecond between each via creation")
    print("Dummy Components: G and D vias SKIPPED (S vias still generated)")
    if GlobalParameters.DUPLICATE_GATE_VIAS:
        print(f"Gate Duplication: ENABLED (X+{GlobalParameters.GATE_DUPLICATE_OFFSET_X})")
    else:
        print("Gate Duplication: DISABLED")
    print("# " + "="*60)
    
    # Read DEF file
    print(f"\nReading DEF file from: {INPUT_DEF_FILE}")
    try:
        with open(INPUT_DEF_FILE, 'r') as f:
            DEF_CONTENT = f.read()
        print(f"Successfully read {len(DEF_CONTENT)} characters from input file")
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {INPUT_DEF_FILE}")
        print("Please check the file path and try again.")
        exit(1)
    except Exception as e:
        print(f"ERROR reading input file: {e}")
        exit(1)
    
    # List available nets
    print("\nListing available nets...")
    available_nets = list_nets_in_def(DEF_CONTENT)
    print(f"Found {len(available_nets)} nets:")
    for net in available_nets:
        print(f"  - {net}")
    
    # Generate TCL script
    print("\nGenerating TCL script...")
    if GENERATE_ALL_NETS:
        tcl_script = process_def_content(DEF_CONTENT)
    else:
        tcl_script = process_def_content(DEF_CONTENT, net_filter=SPECIFIC_NETS)
    
    # Save output
    try:
        with open(OUTPUT_FILE, 'w') as f:
            f.write(tcl_script)
        print(f"\n>> TCL script generated: {OUTPUT_FILE}")
        print(f">> Total lines: {len(tcl_script.splitlines())}")
    except Exception as e:
        print(f"ERROR writing output file: {e}")
        exit(1)
    
    print("\nTo modify via positions:")
    print("  1. Edit GlobalParameters class values")
    print("  2. Run the script again")
    print("\nTo enable/disable gate duplication:")
    print("  1. Set GlobalParameters.DUPLICATE_GATE_VIAS = True/False")
    print(f"  2. Adjust GlobalParameters.GATE_DUPLICATE_OFFSET_X (currently {GlobalParameters.GATE_DUPLICATE_OFFSET_X})")