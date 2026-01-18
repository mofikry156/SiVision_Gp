#!/usr/bin/env python3
"""
Unified Routing Automation System - Complete Implementation
Executes in three stages:
1. Tap routing (Ntap/Ptap) - generates Metal2 rectangles and Via12
2. Via12 generation from DEF file - creates internal database
3. Via23/Metal3 generation - combines tap data + via12 database

All Metal2 data (taps + signal vias) is collected before Via23/Metal3 generation.
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
    source: str = "signal"  # "signal" or "tap"


@dataclass
class RowViaDatabase:
    """Database of via placements organized by row and net"""
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


# ==================== GLOBAL PARAMETERS ====================

class GlobalParameters:
    """All system parameters in one place"""
    
    # Via12 Parameters
    ROW_HEIGHT = 568
    DUPLICATE_GATE_VIAS = True
    GATE_DUPLICATE_OFFSET_X = 74
    MICRONS_TO_MM = 1000.0
    VIA12_WINDOW = 2
    
    # Via12 Orientation offsets - N orientation
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
    
    # Tap Parameters
    TAP_WINDOW = 6
    TAP_RECT_X_MIN_OFFSET = 0
    TAP_RECT_X_MAX_OFFSET = 147
    TAP_RECT_Y_MIN_OFFSET = 106
    TAP_RECT_Y_MAX_OFFSET = 140
    TAP_VIA_X_START_OFFSET = 110
    TAP_VIA_X_END_OFFSET = 45
    TAP_VIA_Y_OFFSET = 123
    TAP_VIA_SPACING = 74
    TAP_VIA_TYPE = "VIA12"
    TAP_METAL_LAYER = "M2"
    
    # Via23/Metal3 Parameters
    VIA23_WINDOW = 2
    VIA23_X_OFFSET_MICRONS = 0.400
    VIA23_NAME = "VIA23"
    VIA23_RECT_OFFSET_X_MICRONS = 0.040
    VIA23_RECT_OFFSET_Y_SINGLE_MICRONS = 0.500


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
                x=x / GlobalParameters.MICRONS_TO_MM,
                y=y / GlobalParameters.MICRONS_TO_MM,
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
    
    def find_power_ground_nets(self) -> Tuple[str, str]:
        """Find VDD/VCC and VSS/GND nets (case insensitive)"""
        power_net = None
        ground_net = None
        
        for net_name in self.nets.keys():
            net_upper = net_name.upper()
            if 'VDD' in net_upper or 'VCC' in net_upper:
                power_net = net_name
            elif 'VSS' in net_upper or 'GND' in net_upper:
                ground_net = net_name
        
        return (power_net or "VDD", ground_net or "VSS")


# ==================== TAP GENERATOR ====================

class TapGenerator:
    """Generates tap routing (Ntap/Ptap) - Stage 1"""
    
    def __init__(self, components: Dict[str, Component], power_net: str, ground_net: str, via_database: RowViaDatabase):
        self.components = components
        self.power_net = power_net
        self.ground_net = ground_net
        self.via_database = via_database
        
    def _group_taps_by_row(self):
        """Group tap devices by their Y position (row)"""
        ntaps = [c for c in self.components.values() if 'Ntap' in c.cell_type]
        ptaps = [c for c in self.components.values() if 'Ptap' in c.cell_type]
        
        def group_by_y(taps):
            rows = {}
            for tap in taps:
                y = int(tap.y * GlobalParameters.MICRONS_TO_MM)
                if y not in rows:
                    rows[y] = []
                rows[y].append(tap)
            return rows
        
        return group_by_y(ntaps), group_by_y(ptaps)
    
    def build_tap_database(self):
        """Build database with tap vias"""
        ntap_rows, ptap_rows = self._group_taps_by_row()
        
        # Process Ntap rows (power)
        for y_pos_nm, taps in ntap_rows.items():
            x_positions = [int(tap.x * GlobalParameters.MICRONS_TO_MM) for tap in taps]
            x_min = min(x_positions)
            x_max = max(x_positions)
            
            # Add vias to database
            x_start = x_min + GlobalParameters.TAP_VIA_X_START_OFFSET
            x_end = x_max + GlobalParameters.TAP_VIA_X_END_OFFSET
            y_via_nm = y_pos_nm + GlobalParameters.TAP_VIA_Y_OFFSET
            row_num = int(y_pos_nm / GlobalParameters.ROW_HEIGHT)
            
            current_x = x_start
            via_index = 0
            while current_x <= x_end:
                via = ViaInfo(
                    component_name=f"Ntap_Row_{y_pos_nm}_Via_{via_index}",
                    pin_type="TAP",
                    x=current_x / GlobalParameters.MICRONS_TO_MM,
                    y=y_via_nm / GlobalParameters.MICRONS_TO_MM,
                    net_name=self.power_net,
                    row=row_num,
                    option=1,
                    source="tap"
                )
                self.via_database.add_via(via)
                current_x += GlobalParameters.TAP_VIA_SPACING
                via_index += 1
        
        # Process Ptap rows (ground)
        for y_pos_nm, taps in ptap_rows.items():
            x_positions = [int(tap.x * GlobalParameters.MICRONS_TO_MM) for tap in taps]
            x_min = min(x_positions)
            x_max = max(x_positions)
            
            # Add vias to database
            x_start = x_min + GlobalParameters.TAP_VIA_X_START_OFFSET
            x_end = x_max + GlobalParameters.TAP_VIA_X_END_OFFSET
            y_via_nm = y_pos_nm + GlobalParameters.TAP_VIA_Y_OFFSET
            row_num = int(y_pos_nm / GlobalParameters.ROW_HEIGHT)
            
            current_x = x_start
            via_index = 0
            while current_x <= x_end:
                via = ViaInfo(
                    component_name=f"Ptap_Row_{y_pos_nm}_Via_{via_index}",
                    pin_type="TAP",
                    x=current_x / GlobalParameters.MICRONS_TO_MM,
                    y=y_via_nm / GlobalParameters.MICRONS_TO_MM,
                    net_name=self.ground_net,
                    row=row_num,
                    option=1,
                    source="tap"
                )
                self.via_database.add_via(via)
                current_x += GlobalParameters.TAP_VIA_SPACING
                via_index += 1
    
    def generate_tap_tcl(self) -> str:
        """Generate TCL script for tap routing"""
        ntap_rows, ptap_rows = self._group_taps_by_row()
        
        script = "# TCL Script - Stage 1: Tap Routing\n"
        script += f"# Power net: {self.power_net}\n"
        script += f"# Ground net: {self.ground_net}\n"
        script += f"# Window number: {GlobalParameters.TAP_WINDOW}\n\n"
        
        # Process Ntap rows
        script += "# ========== NTAP ROWS (Power) ==========\n"
        for y_pos_nm, taps in sorted(ntap_rows.items()):
            x_positions = [int(tap.x * GlobalParameters.MICRONS_TO_MM) for tap in taps]
            x_min = min(x_positions)
            x_max = max(x_positions)
            
            x1 = (x_min + GlobalParameters.TAP_RECT_X_MIN_OFFSET) / GlobalParameters.MICRONS_TO_MM
            x2 = (x_max + GlobalParameters.TAP_RECT_X_MAX_OFFSET) / GlobalParameters.MICRONS_TO_MM
            y1 = (y_pos_nm + GlobalParameters.TAP_RECT_Y_MIN_OFFSET) / GlobalParameters.MICRONS_TO_MM
            y2 = (y_pos_nm + GlobalParameters.TAP_RECT_Y_MAX_OFFSET) / GlobalParameters.MICRONS_TO_MM
            
            script += f"# Ntap Row at Y={y_pos_nm}\n"
            script += f"le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} "
            script += f"-design [ed] -lpp {{{GlobalParameters.TAP_METAL_LAYER} drawing}} -net {self.power_net}\n\n"
            
            # Generate vias
            x_start = (x_min + GlobalParameters.TAP_VIA_X_START_OFFSET) / GlobalParameters.MICRONS_TO_MM
            x_end = (x_max + GlobalParameters.TAP_VIA_X_END_OFFSET) / GlobalParameters.MICRONS_TO_MM
            y_via = (y_pos_nm + GlobalParameters.TAP_VIA_Y_OFFSET) / GlobalParameters.MICRONS_TO_MM
            via_spacing = GlobalParameters.TAP_VIA_SPACING / GlobalParameters.MICRONS_TO_MM
            
            current_x = x_start
            while current_x <= x_end:
                script += "ile::createVia\n"
                script += f"gi::setField {{viaAuto}} -value {{false}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.TAP_WINDOW}]]\n"
                script += f"gi::setField {{viaDefName}} -value {{{GlobalParameters.TAP_VIA_TYPE}}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.TAP_WINDOW}]]\n"
                script += f"de::addPoint {{{current_x:.3f} {y_via:.3f}}} -context [db::getNext [de::getContexts -window {GlobalParameters.TAP_WINDOW}]]\n\n"
                current_x += via_spacing
        
        # Process Ptap rows
        script += "# ========== PTAP ROWS (Ground) ==========\n"
        for y_pos_nm, taps in sorted(ptap_rows.items()):
            x_positions = [int(tap.x * GlobalParameters.MICRONS_TO_MM) for tap in taps]
            x_min = min(x_positions)
            x_max = max(x_positions)
            
            x1 = (x_min + GlobalParameters.TAP_RECT_X_MIN_OFFSET) / GlobalParameters.MICRONS_TO_MM
            x2 = (x_max + GlobalParameters.TAP_RECT_X_MAX_OFFSET) / GlobalParameters.MICRONS_TO_MM
            y1 = (y_pos_nm + GlobalParameters.TAP_RECT_Y_MIN_OFFSET) / GlobalParameters.MICRONS_TO_MM
            y2 = (y_pos_nm + GlobalParameters.TAP_RECT_Y_MAX_OFFSET) / GlobalParameters.MICRONS_TO_MM
            
            script += f"# Ptap Row at Y={y_pos_nm}\n"
            script += f"le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} "
            script += f"-design [ed] -lpp {{{GlobalParameters.TAP_METAL_LAYER} drawing}} -net {self.ground_net}\n\n"
            
            # Generate vias
            x_start = (x_min + GlobalParameters.TAP_VIA_X_START_OFFSET) / GlobalParameters.MICRONS_TO_MM
            x_end = (x_max + GlobalParameters.TAP_VIA_X_END_OFFSET) / GlobalParameters.MICRONS_TO_MM
            y_via = (y_pos_nm + GlobalParameters.TAP_VIA_Y_OFFSET) / GlobalParameters.MICRONS_TO_MM
            via_spacing = GlobalParameters.TAP_VIA_SPACING / GlobalParameters.MICRONS_TO_MM
            
            current_x = x_start
            while current_x <= x_end:
                script += "ile::createVia\n"
                script += f"gi::setField {{viaAuto}} -value {{false}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.TAP_WINDOW}]]\n"
                script += f"gi::setField {{viaDefName}} -value {{{GlobalParameters.TAP_VIA_TYPE}}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.TAP_WINDOW}]]\n"
                script += f"de::addPoint {{{current_x:.3f} {y_via:.3f}}} -context [db::getNext [de::getContexts -window {GlobalParameters.TAP_WINDOW}]]\n\n"
                current_x += via_spacing
        
        return script


# ==================== VIA12 GENERATOR ====================

class Via12Generator:
    """Generates Via12 TCL scripts and builds via database - Stage 2"""
    
    def __init__(self, components: Dict[str, Component], nets: Dict[str, List[NetConnection]], via_database: RowViaDatabase):
        self.components = components
        self.nets = nets
        self.via_database = via_database
        self.net_options = {}
        self.row_violations = {}
        self._check_row_constraints()
        self._assign_simple_options()
    
    def _is_dummy_component(self, component_name: str) -> bool:
        """Check if component name contains 'Dummy'"""
        return 'dummy' in component_name.lower()
    
    def _get_component_row(self, component: Component) -> int:
        """Determine which row a component belongs to"""
        return int(component.y / (GlobalParameters.ROW_HEIGHT / GlobalParameters.MICRONS_TO_MM))
    
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
        params = GlobalParameters
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
        """Build the via database for all signal nets"""
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
                    option=option,
                    source="signal"
                )
                self.via_database.add_via(via)
                
                # Add duplicate gate via if enabled
                if conn.pin == 'G' and GlobalParameters.DUPLICATE_GATE_VIAS:
                    x_duplicate = via_x + (GlobalParameters.GATE_DUPLICATE_OFFSET_X / GlobalParameters.MICRONS_TO_MM)
                    via_dup = ViaInfo(
                        component_name=comp.name + "_DUP",
                        pin_type=conn.pin,
                        x=x_duplicate,
                        y=via_y,
                        net_name=net_name,
                        row=row,
                        option=option,
                        source="signal"
                    )
                    self.via_database.add_via(via_dup)
    
    def generate_via12_tcl(self) -> str:
        """Generate Via12 TCL script"""
        script = "# TCL Via12 Generation Script - Stage 2\n"
        script += "# Auto-generated - Creates Via12 for signal nets\n\n"
        
        script += "# Initialization: Set viaAuto to true\n"
        script += "ile::createVia\n"
        script += f"gi::setField {{viaAuto}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.VIA12_WINDOW}]]\n\n"
        
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
                script += f"de::addPoint {{{via_x:.3f} {via_y:.3f}}} -context [db::getNext [de::getContexts -window {GlobalParameters.VIA12_WINDOW}]]\n"
                script += "after 1\n"
                
                # Duplicate gate via
                if conn.pin == 'G' and GlobalParameters.DUPLICATE_GATE_VIAS:
                    x_dup = via_x + (GlobalParameters.GATE_DUPLICATE_OFFSET_X / GlobalParameters.MICRONS_TO_MM)
                    script += f"# {comp.name} - {conn.pin} DUPLICATE\n"
                    script += "ile::createVia\n"
                    script += f"de::addPoint {{{x_dup:.3f} {via_y:.3f}}} -context [db::getNext [de::getContexts -window {GlobalParameters.VIA12_WINDOW}]]\n"
                    script += "after 1\n"
            
            script += f"puts \"{net_name} complete!\"\n\n"
        
        return script


# ==================== VIA23/METAL3 GENERATOR ====================

class Via23Metal3Generator:
    """Generates Via23 and Metal3 based on combined Via12 database - Stage 3"""
    
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
            self.x_start = device_x_min + GlobalParameters.VIA23_X_OFFSET_MICRONS
            x_end = device_x_max - GlobalParameters.VIA23_X_OFFSET_MICRONS
            
            if num_nets == 1:
                self.x_step = 0.0
            else:
                self.x_step = (x_end - self.x_start) / (num_nets - 1)
    
    def generate_via23_metal3_tcl(self) -> str:
        """Generate Via23 and Metal3 TCL script"""
        script = "# TCL Via23 and Metal3 Generation Script - Stage 3\n"
        script += "# Auto-generated from COMBINED Via12 database (Taps + Signals)\n"
        script += f"# Window Number: {GlobalParameters.VIA23_WINDOW}\n"
        script += f"# X Start: {self.x_start:.3f} microns\n"
        script += f"# X Step: {self.x_step:.3f} microns\n"
        script += f"# Via Name: {GlobalParameters.VIA23_NAME}\n"
        script += f"# Device Y positions filtered: {len(self.device_y_positions)}\n\n"
        
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
            
            # Generate Via23 for each filtered Y position
            for y_pos in filtered_y_positions:
                script += f"ile::createVia\n"
                script += f"gi::setField {{viaAuto}} -value {{false}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.VIA23_WINDOW}]]\n"
                script += f"gi::setField {{viaDefName}} -value {{{GlobalParameters.VIA23_NAME}}} "
                script += f"-in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalParameters.VIA23_WINDOW}]]\n"
                script += f"de::addPoint {{{x_pos:.3f} {y_pos:.3f}}} "
                script += f"-context [db::getNext [de::getContexts -window {GlobalParameters.VIA23_WINDOW}]]\n\n"
            
            # Generate Metal3 rectangle
            x_rect_min = x_pos - GlobalParameters.VIA23_RECT_OFFSET_X_MICRONS
            x_rect_max = x_pos + GlobalParameters.VIA23_RECT_OFFSET_X_MICRONS
            
            if len(filtered_y_positions) == 1:
                # Single via: extend 500nm upward
                y_rect_start = filtered_y_positions[0]
                y_rect_end = y_rect_start + GlobalParameters.VIA23_RECT_OFFSET_Y_SINGLE_MICRONS
            else:
                # Multiple vias: span from min to max
                y_rect_start = min(filtered_y_positions)
                y_rect_end = max(filtered_y_positions)
            
            script += f"# Metal3 Rectangle for {net_name}\n"
            script += f"le::createRectangle {{{{{x_rect_min:.3f} {y_rect_start:.3f}}} {{{x_rect_max:.3f} {y_rect_end:.3f}}}}} "
            script += f"-design [ed] -lpp {{M3 drawing}} -net {net_name}\n\n"
        
        script += f"# Total Via23 filtered (device Y match): {total_filtered}\n"
        
        return script


# ==================== MAIN UNIFIED SYSTEM ====================

def process_unified_routing(def_content: str) -> Tuple[str, str, str]:
    """
    Process DEF file and generate all three stage scripts
    
    Args:
        def_content: DEF file content
    
    Returns:
        Tuple of (tap_tcl, via12_tcl, via23_metal3_tcl)
    """
    print("="*70)
    print("UNIFIED ROUTING AUTOMATION SYSTEM")
    print("="*70)
    
    # Parse DEF file
    print("\n[PARSING] DEF file...")
    parser = DEFParser(def_content)
    parser.parse()
    
    print(f"  - Components: {len(parser.components)}")
    print(f"  - Nets: {len(parser.nets)}")
    
    # Get device information
    device_x_min, device_x_max = parser.get_device_x_range()
    if device_x_min is None:
        print("  ERROR: No PFET/NFET devices found")
        return ("", "", "")
    
    print(f"  - Device X range: {device_x_min:.3f} to {device_x_max:.3f} microns")
    
    device_y_positions = parser.get_device_y_positions()
    print(f"  - Device Y positions: {len(device_y_positions)}")
    
    # Find power/ground nets
    power_net, ground_net = parser.find_power_ground_nets()
    print(f"  - Power net: {power_net}")
    print(f"  - Ground net: {ground_net}")
    
    # Create shared via database
    via_database = RowViaDatabase()
    
    # STAGE 1: Tap routing
    print("\n[STAGE 1] Generating Tap Routing...")
    tap_gen = TapGenerator(parser.components, power_net, ground_net, via_database)
    tap_gen.build_tap_database()
    tap_tcl = tap_gen.generate_tap_tcl()
    
    tap_vias_count = 0
    for net in [power_net, ground_net]:
        if net in via_database.vias_by_net_and_row:
            for row in via_database.vias_by_net_and_row[net].values():
                tap_vias_count += len(row)
    
    print(f"  - Tap vias added to database: {tap_vias_count}")
    print(f"  - TCL script: {len(tap_tcl.splitlines())} lines")
    
    # STAGE 2: Signal Via12
    print("\n[STAGE 2] Generating Signal Via12...")
    via12_gen = Via12Generator(parser.components, parser.nets, via_database)
    via12_gen.build_via_database()
    via12_tcl = via12_gen.generate_via12_tcl()
    
    # Count dummy components
    dummy_count = sum(1 for comp in parser.components.values() 
                     if via12_gen._is_dummy_component(comp.name))
    if dummy_count > 0:
        print(f"  - Dummy components: {dummy_count} (G/D vias skipped)")
    
    # Report violations
    if via12_gen.row_violations:
        print(f"  - Row violations: {len(via12_gen.row_violations)} nets skipped")
    
    # Total database statistics
    all_nets = via_database.get_all_nets()
    print(f"  - Total nets in database: {len(all_nets)}")
    
    total_vias = 0
    for net in all_nets:
        rows = via_database.get_net_rows(net)
        for row in rows:
            vias = via_database.get_row_data(net, row)
            total_vias += len(vias)
    print(f"  - Total vias in database (taps + signals): {total_vias}")
    print(f"  - TCL script: {len(via12_tcl.splitlines())} lines")
    
    # STAGE 3: Via23/Metal3
    print("\n[STAGE 3] Generating Via23/Metal3 from combined database...")
    via23_gen = Via23Metal3Generator(via_database, device_x_min, device_x_max, device_y_positions)
    via23_metal3_tcl = via23_gen.generate_via23_metal3_tcl()
    print(f"  - TCL script: {len(via23_metal3_tcl.splitlines())} lines")
    print(f"  - X axis: start={via23_gen.x_start:.3f}, step={via23_gen.x_step:.3f}")
    
    print("\n" + "="*70)
    print("GENERATION COMPLETE")
    print("="*70)
    
    return (tap_tcl, via12_tcl, via23_metal3_tcl)


# ==================== MAIN ====================

if __name__ == "__main__":
    # Configuration
    INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"
    OUTPUT_TAPS_FILE = r"C:\Users\TEBA\Desktop\automated automation\stage1_taps.tcl"
    OUTPUT_VIA12_FILE = r"C:\Users\TEBA\Desktop\automated automation\stage2_via12.tcl"
    OUTPUT_VIA23_FILE = r"C:\Users\TEBA\Desktop\automated automation\stage3_via23_metal3.tcl"
    
    print("UNIFIED ROUTING AUTOMATION SYSTEM")
    print("="*70)
    print("Stage 1: Tap routing (Ntap/Ptap)")
    print("Stage 2: Signal Via12")
    print("Stage 3: Via23/Metal3 (using combined tap + signal data)")
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
    
    # Process and generate all three scripts
    tap_tcl, via12_tcl, via23_metal3_tcl = process_unified_routing(def_content)
    
    if not tap_tcl or not via12_tcl or not via23_metal3_tcl:
        print("\nERROR: Generation failed")
        exit(1)
    
    # Save Tap script
    try:
        with open(OUTPUT_TAPS_FILE, 'w') as f:
            f.write(tap_tcl)
        print(f"\n✓ Stage 1 (Taps) script saved: {OUTPUT_TAPS_FILE}")
    except Exception as e:
        print(f"\nERROR saving Tap script: {e}")
        exit(1)
    
    # Save Via12 script
    try:
        with open(OUTPUT_VIA12_FILE, 'w') as f:
            f.write(via12_tcl)
        print(f"✓ Stage 2 (Via12) script saved: {OUTPUT_VIA12_FILE}")
    except Exception as e:
        print(f"\nERROR saving Via12 script: {e}")
        exit(1)
    
    # Save Via23/Metal3 script
    try:
        with open(OUTPUT_VIA23_FILE, 'w') as f:
            f.write(via23_metal3_tcl)
        print(f"✓ Stage 3 (Via23/Metal3) script saved: {OUTPUT_VIA23_FILE}")
    except Exception as e:
        print(f"\nERROR saving Via23/Metal3 script: {e}")
        exit(1)
    
    print("\n" + "="*70)
    print("SUCCESS: All three scripts generated successfully!")
    print("="*70)
    print("\nExecution order:")
    print(f"  1. Run: {OUTPUT_TAPS_FILE}")
    print(f"  2. Run: {OUTPUT_VIA12_FILE}")
    print(f"  3. Run: {OUTPUT_VIA23_FILE}")
    print("\nThe Via23/Metal3 script now includes BOTH tap and signal data!")