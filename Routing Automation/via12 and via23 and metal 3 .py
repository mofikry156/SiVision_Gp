#!/usr/bin/env python3
"""
Unified Via Generation System - Via12 + Via23/Metal3
Generates complete routing automation in two stages:
1. Via12 generation from DEF file (creates internal database)
2. Via23/Metal3 generation from Via12 database (no DEF Metal2 reading needed)

The Via12 output becomes the direct input for Via23/Metal3 generation.
Via23 coordinates that match NFET/PFET device Y positions are filtered out.
"""

import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict


# ==================== DATA STRUCTURES ====================

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


@dataclass
class ViaInfo:
    """Information about a single via placement"""
    component_name: str
    pin_type: str
    x: float
    y: float
    net_name: str
    row: int
    option: int


@dataclass
class RowViaDatabase:
    """Database of via placements organized by row and net"""
    # Structure: {net_name: {row_number: [list of ViaInfo]}}
    vias_by_net_and_row: Dict[str, Dict[int, List[ViaInfo]]]
    
    def __init__(self):
        self.vias_by_net_and_row = defaultdict(lambda: defaultdict(list))
    
    def add_via(self, via: ViaInfo):
        """Add a via to the database"""
        self.vias_by_net_and_row[via.net_name][via.row].append(via)
    
    def get_row_data(self, net_name: str, row: int) -> List[ViaInfo]:
        """Get all vias for a specific net in a specific row"""
        return self.vias_by_net_and_row.get(net_name, {}).get(row, [])
    
    def get_all_nets(self) -> List[str]:
        """Get all net names in database"""
        return sorted(list(self.vias_by_net_and_row.keys()))
    
    def get_net_rows(self, net_name: str) -> List[int]:
        """Get all rows for a specific net"""
        if net_name not in self.vias_by_net_and_row:
            return []
        return sorted(list(self.vias_by_net_and_row[net_name].keys()))
    
    def get_row_y_range(self, net_name: str, row: int) -> Tuple[float, float]:
        """Get min and max Y positions for vias in a specific row"""
        vias = self.get_row_data(net_name, row)
        if not vias:
            return (0.0, 0.0)
        
        y_positions = [via.y for via in vias]
        return (min(y_positions), max(y_positions))


# ==================== VIA12 PARAMETERS ====================

class Via12Parameters:
    """Global parameters for Via12 generation"""
    
    # Row height constraint
    ROW_HEIGHT = 568
    
    # Gate via duplication
    DUPLICATE_GATE_VIAS = True
    GATE_DUPLICATE_OFFSET_X = 74
    
    # Orientation offset rules (N orientation)
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
    
    # FN orientation
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
    
    # FS orientation
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
    
    # S orientation
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
    
    # Conversion
    MICRONS_TO_MM = 1000.0
    CONTEXT_WINDOW = 2


# ==================== VIA23/METAL3 PARAMETERS ====================

class Via23Parameters:
    """Global parameters for Via23 and Metal3 generation"""
    
    WINDOW_NUMBER = 2
    X_OFFSET_MICRONS = 0.400  # 400nm offset from device boundaries
    VIA_NAME = "VIA23"
    RECT_OFFSET_X_MICRONS = 0.040  # 40nm width offset
    RECT_OFFSET_Y_SINGLE_MICRONS = 0.500  # 500nm height for single via


# ==================== DEF PARSER ====================

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
                x=x / Via12Parameters.MICRONS_TO_MM,
                y=y / Via12Parameters.MICRONS_TO_MM,
                orientation=orientation
            )
    
    def _parse_nets(self):
        """Extract net connections"""
        nets_match = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', self.def_content, re.DOTALL)
        if not nets_match:
            return
        
        nets_section = nets_match.group(1)
        net_pattern = r'-\s+(\S+)(.*?)(?=\n\s*-|\Z)'
        pin_pattern = r'\(\s*(\S+)\s+(\S+)\s*\)'
        
        for net_match in re.finditer(net_pattern, nets_section, re.DOTALL):
            net_name = net_match.group(1)
            net_body = net_match.group(2)
            
            connections = []
            for pin_match in re.finditer(pin_pattern, net_body):
                component = pin_match.group(1)
                pin = pin_match.group(2)
                
                if component == 'PIN':
                    continue
                    
                connections.append(NetConnection(
                    net_name=net_name,
                    component=component,
                    pin=pin
                ))
            
            if connections:
                self.nets[net_name] = connections
    
    def get_device_x_range(self) -> Tuple[float, float]:
        """Get X range of PFET/NFET devices"""
        x_positions = []
        
        for comp in self.components.values():
            if 'pfet' in comp.cell_type.lower() or 'nfet' in comp.cell_type.lower():
                x_positions.append(comp.x)
        
        if not x_positions:
            return (None, None)
        
        return (min(x_positions), max(x_positions))
    
    def get_device_y_positions(self) -> Set[float]:
        """Get all Y positions of PFET/NFET devices"""
        y_positions = set()
        
        for comp in self.components.values():
            if 'pfet' in comp.cell_type.lower() or 'nfet' in comp.cell_type.lower():
                y_positions.add(comp.y)
        
        return y_positions


# ==================== VIA12 GENERATOR ====================

class Via12Generator:
    """Generates Via12 TCL scripts and builds via database"""
    
    def __init__(self, components: Dict[str, Component], nets: Dict[str, List[NetConnection]]):
        self.components = components
        self.nets = nets
        self.net_options = {}
        self.row_violations = {}
        self.via_database = RowViaDatabase()
        self._check_row_constraints()
        self._assign_simple_options()
    
    def _is_dummy_component(self, component_name: str) -> bool:
        """Check if component name contains 'Dummy'"""
        return 'dummy' in component_name.lower()
    
    def _get_component_row(self, component: Component) -> int:
        """Determine which row a component belongs to"""
        return int(component.y / Via12Parameters.ROW_HEIGHT)
    
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
        """Assign options for gate and drain signals per row"""
        all_rows = set()
        for comp in self.components.values():
            row = self._get_component_row(comp)
            all_rows.add(row)
        
        for row in sorted(all_rows):
            # Gate signals
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
            for idx, net_name in enumerate(gate_nets):
                option = 1 if idx == 0 else 2
                self.net_options[(net_name, row, 'G')] = option
            
            # Drain signals
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
            for idx, net_name in enumerate(drain_nets):
                option = 1 if idx == 0 else 2
                self.net_options[(net_name, row, 'D')] = option
    
    def get_option(self, net_name: str, row: int, pin_type: str) -> int:
        """Get the assigned option for a net in a specific row"""
        return self.net_options.get((net_name, row, pin_type), 1)
        
    def get_offset(self, orientation: str, pin_type: str, net_name: str, row: int) -> Tuple[float, float]:
        """Get X,Y offset based on orientation and pin type"""
        params = Via12Parameters
        micron_to_mm = 1.0 / params.MICRONS_TO_MM
        
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
    
    def build_via_database(self):
        """Build the via database for all nets"""
        for net_name, connections in self.nets.items():
            # Skip nets that violate row constraints
            if net_name in self.row_violations:
                continue
            
            for conn in connections:
                if conn.component not in self.components:
                    continue
                
                comp = self.components[conn.component]
                
                # Skip G and D pins for Dummy components
                if self._is_dummy_component(comp.name) and conn.pin in ['G', 'D']:
                    continue
                
                row = self._get_component_row(comp)
                offset_x, offset_y = self.get_offset(comp.orientation, conn.pin, net_name, row)
                
                via_x = comp.x + offset_x
                via_y = comp.y + offset_y
                option = self.get_option(net_name, row, conn.pin)
                
                # Add primary via
                via = ViaInfo(
                    component_name=comp.name,
                    pin_type=conn.pin,
                    x=via_x,
                    y=via_y,
                    net_name=net_name,
                    row=row,
                    option=option
                )
                self.via_database.add_via(via)
                
                # Add duplicate gate via if enabled
                if conn.pin == 'G' and Via12Parameters.DUPLICATE_GATE_VIAS:
                    x_duplicate = via_x + (Via12Parameters.GATE_DUPLICATE_OFFSET_X / Via12Parameters.MICRONS_TO_MM)
                    via_dup = ViaInfo(
                        component_name=comp.name + "_DUP",
                        pin_type=conn.pin,
                        x=x_duplicate,
                        y=via_y,
                        net_name=net_name,
                        row=row,
                        option=option
                    )
                    self.via_database.add_via(via_dup)
    
    def generate_via12_tcl(self) -> str:
        """Generate Via12 TCL script"""
        script = "# TCL Via12 Generation Script\n"
        script += "# Auto-generated - Creates Via12 and builds internal database\n\n"
        
        script += "# Initialization: Set viaAuto to true\n"
        script += "ile::createVia\n"
        script += f"gi::setField {{viaAuto}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {Via12Parameters.CONTEXT_WINDOW}]]\n\n"
        
        for net_name in sorted(self.nets.keys()):
            if net_name in self.row_violations:
                script += f"# SKIPPED: {net_name} (row violation)\n\n"
                continue
            
            script += f"# Net: {net_name}\n"
            script += f"puts \"Generating Via12 for {net_name}...\"\n"
            
            connections = self.nets[net_name]
            for conn in connections:
                if conn.component not in self.components:
                    continue
                
                comp = self.components[conn.component]
                
                if self._is_dummy_component(comp.name) and conn.pin in ['G', 'D']:
                    continue
                
                row = self._get_component_row(comp)
                offset_x, offset_y = self.get_offset(comp.orientation, conn.pin, net_name, row)
                via_x = comp.x + offset_x
                via_y = comp.y + offset_y
                option = self.get_option(net_name, row, conn.pin)
                
                script += f"# {comp.name} - {conn.pin} (Row {row}, Option {option})\n"
                script += "ile::createVia\n"
                script += f"de::addPoint {{{via_x:.3f} {via_y:.3f}}} -context [db::getNext [de::getContexts -window {Via12Parameters.CONTEXT_WINDOW}]]\n"
                script += "after 1\n"
                
                # Duplicate gate via
                if conn.pin == 'G' and Via12Parameters.DUPLICATE_GATE_VIAS:
                    x_dup = via_x + (Via12Parameters.GATE_DUPLICATE_OFFSET_X / Via12Parameters.MICRONS_TO_MM)
                    script += f"# {comp.name} - {conn.pin} DUPLICATE\n"
                    script += "ile::createVia\n"
                    script += f"de::addPoint {{{x_dup:.3f} {via_y:.3f}}} -context [db::getNext [de::getContexts -window {Via12Parameters.CONTEXT_WINDOW}]]\n"
                    script += "after 1\n"
            
            script += f"puts \"{net_name} complete!\"\n\n"
        
        return script


# ==================== VIA23/METAL3 GENERATOR ====================

class Via23Metal3Generator:
    """Generates Via23 and Metal3 based on Via12 database"""
    
    def __init__(self, via_database: RowViaDatabase, device_x_min: float, device_x_max: float, device_y_positions: Set[float]):
        self.via_database = via_database
        self.device_x_min = device_x_min
        self.device_x_max = device_x_max
        self.device_y_positions = device_y_positions
        
        # Calculate X parameters
        nets = via_database.get_all_nets()
        num_nets = len(nets)
        
        if num_nets == 0:
            self.x_start = 0.0
            self.x_step = 0.0
        else:
            self.x_start = device_x_min + Via23Parameters.X_OFFSET_MICRONS
            x_end = device_x_max - Via23Parameters.X_OFFSET_MICRONS
            
            if num_nets == 1:
                self.x_step = 0.0
            else:
                self.x_step = (x_end - self.x_start) / (num_nets - 1)
    
    def generate_via23_metal3_tcl(self) -> str:
        """Generate Via23 and Metal3 TCL script"""
        script = "# TCL Via23 and Metal3 Generation Script\n"
        script += "# Auto-generated from Via12 database\n"
        script += f"# Window Number: {Via23Parameters.WINDOW_NUMBER}\n"
        script += f"# X Start: {self.x_start:.3f} microns\n"
        script += f"# X Step: {self.x_step:.3f} microns\n"
        script += f"# Via Name: {Via23Parameters.VIA_NAME}\n"
        script += f"# Device Y positions filtered: {len(self.device_y_positions)}\n\n"
        
        # ONE-TIME Via23 configuration setup
        script += "# Via23 Configuration (one-time setup)\n"
        script += "ile::createVia\n"
        script += f"gi::setField {{viaAuto}} -value {{false}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {Via23Parameters.WINDOW_NUMBER}]]\n"
        script += f"gi::setField {{viaDefName}} -value {{{Via23Parameters.VIA_NAME}}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {Via23Parameters.WINDOW_NUMBER}]]\n\n"
        
        nets = self.via_database.get_all_nets()
        total_filtered = 0
        
        for net_index, net_name in enumerate(nets):
            x_pos = self.x_start + (net_index * self.x_step)
            
            script += f"# ========== Net: {net_name} (X={x_pos:.3f}) ==========\n"
            
            # Get all rows for this net
            rows = self.via_database.get_net_rows(net_name)
            
            # Collect all Y positions across all rows for this net
            all_y_positions = []
            for row in rows:
                vias = self.via_database.get_row_data(net_name, row)
                for via in vias:
                    all_y_positions.append(via.y)
            
            if not all_y_positions:
                script += f"# No vias found for {net_name}\n\n"
                continue
            
            # Remove duplicates and sort
            unique_y_positions = sorted(set(all_y_positions))
            
            # Filter out Y positions that match device Y positions
            filtered_y_positions = [y for y in unique_y_positions if y not in self.device_y_positions]
            filtered_count = len(unique_y_positions) - len(filtered_y_positions)
            total_filtered += filtered_count
            
            script += f"# Found {len(unique_y_positions)} unique Y position(s)"
            if filtered_count > 0:
                script += f", filtered {filtered_count} (device Y match)"
            script += "\n"
            
            if not filtered_y_positions:
                script += f"# All Y positions filtered for {net_name} (match device positions)\n\n"
                continue
            
            # Generate Via23 for each filtered Y position (NO repeated configuration)
            for y_pos in filtered_y_positions:
                script += f"de::addPoint {{{x_pos:.3f} {y_pos:.3f}}} -context [db::getNext [de::getContexts -window {Via23Parameters.WINDOW_NUMBER}]]\n"
            
            script += "\n"
            
            # Generate Metal3 rectangle
            x_rect_min = x_pos - Via23Parameters.RECT_OFFSET_X_MICRONS
            x_rect_max = x_pos + Via23Parameters.RECT_OFFSET_X_MICRONS
            
            if len(filtered_y_positions) == 1:
                # Single via: extend 500nm upward
                y_rect_start = filtered_y_positions[0]
                y_rect_end = y_rect_start + Via23Parameters.RECT_OFFSET_Y_SINGLE_MICRONS
            else:
                # Multiple vias: span from min to max
                y_rect_start = min(filtered_y_positions)
                y_rect_end = max(filtered_y_positions)
            
            script += f"# Metal3 Rectangle for {net_name}\n"
            script += f"le::createRectangle {{{{{x_rect_min:.3f} {y_rect_start:.3f}}} {{{x_rect_max:.3f} {y_rect_end:.3f}}}}} "
            script += f"-design [ed] -lpp {{M3 drawing}} -net {net_name}\n\n"
        
        script += f"# Total Via23 filtered (device Y match): {total_filtered}\n"
        
        return script


# ==================== MAIN PROCESSING ====================

def process_unified_via_generation(def_content: str) -> Tuple[str, str]:
    """
    Process DEF file and generate both Via12 and Via23/Metal3 scripts
    
    Args:
        def_content: DEF file content
    
    Returns:
        Tuple of (via12_tcl_script, via23_metal3_tcl_script)
    """
    print("="*70)
    print("UNIFIED VIA GENERATION SYSTEM")
    print("="*70)
    
    # Parse DEF file
    print("\n[1/4] Parsing DEF file...")
    parser = DEFParser(def_content)
    parser.parse()
    
    print(f"  - Found {len(parser.components)} components")
    print(f"  - Found {len(parser.nets)} nets")
    
    # Get device X range
    device_x_min, device_x_max = parser.get_device_x_range()
    if device_x_min is None:
        print("  ERROR: No PFET/NFET devices found")
        return ("", "")
    
    print(f"  - Device X range: {device_x_min:.3f} to {device_x_max:.3f} microns")
    
    # Get device Y positions for filtering
    device_y_positions = parser.get_device_y_positions()
    print(f"  - Device Y positions to filter: {len(device_y_positions)}")
    
    # Generate Via12 and build database
    print("\n[2/4] Generating Via12 and building database...")
    via12_gen = Via12Generator(parser.components, parser.nets)
    via12_gen.build_via_database()
    
    # Count dummy components
    dummy_count = sum(1 for comp in parser.components.values() 
                     if via12_gen._is_dummy_component(comp.name))
    if dummy_count > 0:
        print(f"  - Dummy components: {dummy_count} (G/D vias skipped)")
    
    # Report violations
    if via12_gen.row_violations:
        print(f"  - Row violations: {len(via12_gen.row_violations)} nets skipped")
    
    # Database statistics
    all_nets = via12_gen.via_database.get_all_nets()
    print(f"  - Database contains {len(all_nets)} nets")
    
    total_vias = 0
    for net in all_nets:
        rows = via12_gen.via_database.get_net_rows(net)
        for row in rows:
            vias = via12_gen.via_database.get_row_data(net, row)
            total_vias += len(vias)
    print(f"  - Total vias in database: {total_vias}")
    
    # Generate Via12 TCL
    print("\n[3/4] Generating Via12 TCL script...")
    via12_tcl = via12_gen.generate_via12_tcl()
    print(f"  - Via12 script: {len(via12_tcl.splitlines())} lines")
    
    # Generate Via23/Metal3 using the database
    print("\n[4/4] Generating Via23/Metal3 TCL script from database...")
    via23_gen = Via23Metal3Generator(via12_gen.via_database, device_x_min, device_x_max, device_y_positions)
    via23_metal3_tcl = via23_gen.generate_via23_metal3_tcl()
    print(f"  - Via23/Metal3 script: {len(via23_metal3_tcl.splitlines())} lines")
    print(f"  - X axis: start={via23_gen.x_start:.3f}, step={via23_gen.x_step:.3f}")
    
    print("\n" + "="*70)
    print("GENERATION COMPLETE")
    print("="*70)
    
    return (via12_tcl, via23_metal3_tcl)


# ==================== MAIN ====================

if __name__ == "__main__":
    # Configuration
    INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"
    OUTPUT_VIA12_FILE = r"C:\Users\TEBA\Desktop\automated automation\unified_via12 .tcl"
    OUTPUT_VIA23_FILE = r"C:\Users\TEBA\Desktop\automated automation\unified_via23_metal3 .tcl"
    
    print("UNIFIED VIA GENERATION SYSTEM")
    print("Combines Via12 generation with Via23/Metal3 routing")
    print("No Metal2 reading from DEF - uses internal Via12 database")
    print("Filters Via23 at device Y positions")
    print("="*70)
    
    # Read DEF file
    print(f"\nReading DEF file: {INPUT_DEF_FILE}")
    try:
        with open(INPUT_DEF_FILE, 'r') as f:
            def_content = f.read()
        print(f"Successfully read {len(def_content)} characters")
    except FileNotFoundError:
        print(f"ERROR: File not found: {INPUT_DEF_FILE}")
        exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)
    
    # Process and generate both scripts
    via12_tcl, via23_metal3_tcl = process_unified_via_generation(def_content)
    
    if not via12_tcl or not via23_metal3_tcl:
        print("\nERROR: Generation failed")
        exit(1)
    
    # Save Via12 script
    try:
        with open(OUTPUT_VIA12_FILE, 'w') as f:
            f.write(via12_tcl)
        print(f"\n✓ Via12 script saved: {OUTPUT_VIA12_FILE}")
    except Exception as e:
        print(f"\nERROR saving Via12 script: {e}")
        exit(1)
    
    # Save Via23/Metal3 script
    try:
        with open(OUTPUT_VIA23_FILE, 'w') as f:
            f.write(via23_metal3_tcl)
        print(f"✓ Via23/Metal3 script saved: {OUTPUT_VIA23_FILE}")
    except Exception as e:
        print(f"\nERROR saving Via23/Metal3 script: {e}")
        exit(1)
    
    print("\n" + "="*70)
    print("SUCCESS: Both scripts generated successfully!")
    print("="*70)
    print("\nExecution order:")
    print(f"  1. Run: {OUTPUT_VIA12_FILE}")
    print(f"  2. Run: {OUTPUT_VIA23_FILE}")