#!/usr/bin/env python3
"""
Unified Via Generation System - Via12 + Via23/Metal3 + Pin Generation with Power/Ground Tap Support
Generates complete routing automation in three stages:
1. Via12 generation from DEF file (creates internal database)
2. Via23/Metal3 generation with special handling for power/ground nets using tap positions
3. Pin generation for external nets (excludes nets starting with "net")

KEY FEATURES:
- Power nets (USE POWER): Via23 uses device Y + Ntap Y positions
- Ground nets (USE GROUND): Via23 uses device Y + Ptap Y positions
- Via23 positions matching NFET/PFET component Y coordinates are FILTERED OUT
- Metal3 extends to cover remaining Via23 positions after filtering
- Regular nets: Via23 placed at device Y positions as normal
- Pins created for external nets at M3 rectangle start points

DUMMY COMPONENT HANDLING:
- Gate (G) and Drain (D) vias are ALWAYS SKIPPED for Dummy components
- Source (S) vias are ALWAYS FORCED regardless of orientation (N, FN, FS, S)

FIXED: Added support for negative coordinates in DEF file
MODIFIED: Updated TCL syntax to use [gi::getActiveWindow] and [de::getActiveContext]
BUGFIX: FORCED Source via generation for ALL Dummy components regardless of orientation
"""

import re
from typing import Dict, List, Tuple, Set, Optional
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
class TapInfo:
    """Information about tap components"""
    name: str
    tap_type: str  # 'Ntap' or 'Ptap'
    x: float
    y: float


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
    
    # Tap Y position offset (applied ONLY to Ntap and Ptap positions for power/ground nets)
    # This offset is in the same units as component positions (microns/1000)
    NTAP_Y_OFFSET = 124  # Offset for Ntap Y positions (power nets)
    PTAP_Y_OFFSET = 124  # Offset for Ptap Y positions (ground nets)


# ==================== DEF PARSER ====================

class DEFParser:
    """Parses DEF files to extract component, net, and tap information"""
    
    def __init__(self, def_content: str):
        self.def_content = def_content
        self.components: Dict[str, Component] = {}
        self.nets: Dict[str, List[NetConnection]] = {}
        self.power_nets: Set[str] = set()
        self.ground_nets: Set[str] = set()
        self.taps: List[TapInfo] = []
        
    def parse(self):
        """Parse the DEF file content"""
        self._parse_components()
        self._parse_nets()
        self._parse_power_ground_nets()
        self._parse_taps()
        
    def _parse_components(self):
        """Extract component information"""
        # FIXED: Added support for negative coordinates with -? in the pattern
        pattern = r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:FIXED|PLACED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)'
        
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
    
    def _parse_power_ground_nets(self):
        """Identify power and ground nets from USE POWER/GROUND declarations"""
        nets_match = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', self.def_content, re.DOTALL)
        if not nets_match:
            return
        
        nets_section = nets_match.group(1)
        
        # Split into individual net definitions (each starts with "- NetName")
        # Use \Z to match end of string for the last net
        net_pattern = r'-\s+(\S+)(.*?)(?=\n\s*-|\Z)'
        
        for net_match in re.finditer(net_pattern, nets_section, re.DOTALL):
            net_name = net_match.group(1)
            net_body = net_match.group(2)
            
            # Check if this net has USE POWER or USE GROUND
            if re.search(r'\+\s+USE\s+POWER', net_body):
                self.power_nets.add(net_name)
            elif re.search(r'\+\s+USE\s+GROUND', net_body):
                self.ground_nets.add(net_name)
    
    def _parse_taps(self):
        """Extract tap component information"""
        for name, comp in self.components.items():
            if 'ntap' in comp.cell_type.lower():
                self.taps.append(TapInfo(
                    name=name,
                    tap_type='Ntap',
                    x=comp.x,
                    y=comp.y
                ))
            elif 'ptap' in comp.cell_type.lower():
                self.taps.append(TapInfo(
                    name=name,
                    tap_type='Ptap',
                    x=comp.x,
                    y=comp.y
                ))
    
    def get_ntap_y_positions(self) -> List[float]:
        """Get all Ntap Y positions"""
        return sorted(list(set([tap.y for tap in self.taps if tap.tap_type == 'Ntap'])))
    
    def get_ptap_y_positions(self) -> List[float]:
        """Get all Ptap Y positions"""
        return sorted(list(set([tap.y for tap in self.taps if tap.tap_type == 'Ptap'])))
    
    def get_device_x_range(self) -> Tuple[float, float]:
        """Get X range of PFET/NFET devices"""
        x_positions = []
        
        for comp in self.components.values():
            if 'pfet' in comp.cell_type.lower() or 'nfet' in comp.cell_type.lower():
                x_positions.append(comp.x)
        
        if not x_positions:
            return (None, None)
        
        return (min(x_positions), max(x_positions))
    
    def is_power_net(self, net_name: str) -> bool:
        """Check if a net is a power net"""
        return net_name in self.power_nets
    
    def is_ground_net(self, net_name: str) -> bool:
        """Check if a net is a ground net"""
        return net_name in self.ground_nets
    
    def get_nfet_pfet_y_positions(self) -> List[float]:
        """Get all unique Y positions of NFET and PFET devices"""
        y_positions = []
        
        for comp in self.components.values():
            if 'nfet' in comp.cell_type.lower() or 'pfet' in comp.cell_type.lower():
                y_positions.append(comp.y)
        
        return sorted(list(set(y_positions)))


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
    
    def _should_skip_dummy_pin(self, comp: Component, pin_type: str) -> bool:
        """
        Determine if a pin should be skipped for a Dummy component.
        
        BUGFIX: For Dummy components:
        - ALWAYS skip Gate (G) and Drain (D) pins regardless of orientation
        - ALWAYS generate Source (S) pins regardless of orientation
        
        Returns True if the pin should be skipped, False otherwise.
        """
        if not self._is_dummy_component(comp.name):
            return False
        
        # For Dummy components: skip only G and D pins, keep S pins for ALL orientations
        if pin_type in ['G', 'D']:
            return True
        
        # Source pins should NEVER be skipped for Dummy components
        return False
    
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
        # First pass: process all normal connections
        for net_name, connections in self.nets.items():
            # Skip nets that violate row constraints
            if net_name in self.row_violations:
                continue
            
            for conn in connections:
                if conn.component not in self.components:
                    continue
                
                comp = self.components[conn.component]
                
                # BUGFIX: Use new method to check if pin should be skipped for Dummy components
                if self._should_skip_dummy_pin(comp, conn.pin):
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
        
        # Second pass: FORCE Source vias for ALL Dummy components regardless of net connections
        for comp_name, comp in self.components.items():
            if not self._is_dummy_component(comp.name):
                continue
            
            # Find which net this Dummy's Source is connected to
            source_net = None
            for net_name, connections in self.nets.items():
                for conn in connections:
                    if conn.component == comp_name and conn.pin == 'S':
                        source_net = net_name
                        break
                if source_net:
                    break
            
            # If no Source connection found in nets, skip this dummy
            if not source_net:
                continue
            
            # Skip if net has row violations
            if source_net in self.row_violations:
                continue
            
            # Calculate Source via position
            row = self._get_component_row(comp)
            offset_x, offset_y = self.get_offset(comp.orientation, 'S', source_net, row)
            
            via_x = comp.x + offset_x
            via_y = comp.y + offset_y
            
            # FORCE add Source via for Dummy component
            via = ViaInfo(
                component_name=comp.name,
                pin_type='S',
                x=via_x,
                y=via_y,
                net_name=source_net,
                row=row,
                option=1  # Source doesn't use options
            )
            self.via_database.add_via(via)
    
    def generate_via12_tcl(self) -> str:
        """Generate Via12 TCL script"""  
        script = "de::fit -fitView\n"
        script += f"db::setPrefValue leStopLevel -value 32 -scope [de::getActiveContext]\n"
        script += "ile::createVia\n"
        script += f"gi::setField {{viaAuto}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getActiveWindow]]\n\n"
        
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
                
                # BUGFIX: Use new method to check if pin should be skipped
                if self._should_skip_dummy_pin(comp, conn.pin):
                    continue
                
                row = self._get_component_row(comp)
                offset_x, offset_y = self.get_offset(comp.orientation, conn.pin, net_name, row)
                via_x = comp.x + offset_x
                via_y = comp.y + offset_y
                option = self.get_option(net_name, row, conn.pin)
                
                script += f"de::addPoint {{{via_x:.3f} {via_y:.3f}}} -context [de::getActiveContext]\n"
                script += "after 10\n"
                
                # Duplicate gate via
                if conn.pin == 'G' and Via12Parameters.DUPLICATE_GATE_VIAS:
                    x_dup = via_x + (Via12Parameters.GATE_DUPLICATE_OFFSET_X / Via12Parameters.MICRONS_TO_MM)
                    script += f"de::addPoint {{{x_dup:.3f} {via_y:.3f}}} -context [de::getActiveContext]\n"
                    script += "after 10\n"
            
            script += f"puts \"{net_name} complete!\"\n\n"
        
        # FORCE Source vias for ALL Dummy components
        script += "# ========== FORCED SOURCE VIAS FOR DUMMY COMPONENTS ==========\n"
        script += "puts \"Generating forced Source vias for Dummy components...\"\n\n"
        
        for comp_name, comp in self.components.items():
            if not self._is_dummy_component(comp.name):
                continue
            
            # Find which net this Dummy's Source is connected to
            source_net = None
            for net_name, connections in self.nets.items():
                for conn in connections:
                    if conn.component == comp_name and conn.pin == 'S':
                        source_net = net_name
                        break
                if source_net:
                    break
            
            # If no Source connection found in nets, skip this dummy
            if not source_net:
                continue
            
            # Skip if net has row violations
            if source_net in self.row_violations:
                continue
            
            # Calculate Source via position
            row = self._get_component_row(comp)
            offset_x, offset_y = self.get_offset(comp.orientation, 'S', source_net, row)
            
            via_x = comp.x + offset_x
            via_y = comp.y + offset_y
            
            script += f"# FORCED Source via for Dummy: {comp_name} (Net: {source_net}, Orient: {comp.orientation})\n"
            script += f"de::addPoint {{{via_x:.3f} {via_y:.3f}}} -context [de::getActiveContext]\n"
        
        script += "\nputs \"Dummy Source vias complete!\"\n\n"
        
        return script


# ==================== VIA23/METAL3 GENERATOR ====================

class Via23Metal3Generator:
    """Generates Via23 and Metal3 with special handling for power/ground nets"""
    
    def __init__(self, via_database: RowViaDatabase, device_x_min: float, device_x_max: float,
                 parser: DEFParser):
        self.via_database = via_database
        self.device_x_min = device_x_min
        self.device_x_max = device_x_max
        self.parser = parser
        
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
        """Generate Via23 and Metal3 TCL script with power/ground tap support and NFET/PFET filtering"""
        script = "# TCL Via23 and Metal3 Generation Script\n"
        script += "# Auto-generated from Via12 database\n"
        script += f"# Window Number: {Via23Parameters.WINDOW_NUMBER}\n"
        script += f"# X Start: {self.x_start:.3f} microns\n"
        script += f"# X Step: {self.x_step:.3f} microns\n"
        script += f"# Via Name: {Via23Parameters.VIA_NAME}\n"
        script += f"# Ntap Y Offset: {Via23Parameters.NTAP_Y_OFFSET} (applied to Ntap positions for power nets)\n"
        script += f"# Ptap Y Offset: {Via23Parameters.PTAP_Y_OFFSET} (applied to Ptap positions for ground nets)\n"
        script += "# SPECIAL: Power/Ground nets use BOTH device Y positions AND tap Y positions\n"
        script += "# FILTER: Via23 positions matching NFET/PFET Y coordinates are excluded\n\n"
        
        # Get NFET/PFET Y positions for filtering
        nfet_pfet_y_positions = set(self.parser.get_nfet_pfet_y_positions())
        script += f"# NFET/PFET Y positions (will be filtered from Via23): {sorted(nfet_pfet_y_positions)}\n\n"
        
        # ONE-TIME Via23 configuration setup
        script += "# Via23 Configuration (one-time setup)\n"
        script += "ile::createVia\n"
        script += f"gi::setField {{viaAuto}} -value {{false}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getActiveWindow]]\n"
        script += f"gi::setField {{viaDefName}} -value {{{Via23Parameters.VIA_NAME}}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getActiveWindow]]\n\n"
        
        nets = self.via_database.get_all_nets()
        
        # Convert tap offsets from same units to microns
        ntap_offset_microns = Via23Parameters.NTAP_Y_OFFSET / Via12Parameters.MICRONS_TO_MM
        ptap_offset_microns = Via23Parameters.PTAP_Y_OFFSET / Via12Parameters.MICRONS_TO_MM
        
        for net_index, net_name in enumerate(nets):
            x_pos = self.x_start + (net_index * self.x_step)
            
            is_power = self.parser.is_power_net(net_name)
            is_ground = self.parser.is_ground_net(net_name)
            
            if is_power:
                script += f"# ========== POWER NET: {net_name} (X={x_pos:.3f}) ==========\n"
            elif is_ground:
                script += f"# ========== GROUND NET: {net_name} (X={x_pos:.3f}) ==========\n"
            else:
                script += f"# ========== Net: {net_name} (X={x_pos:.3f}) ==========\n"
            
            # Get all Y positions from Via12 database
            all_device_y_positions = []
            rows = self.via_database.get_net_rows(net_name)
            for row in rows:
                vias = self.via_database.get_row_data(net_name, row)
                for via in vias:
                    all_device_y_positions.append(via.y)
            
            if not all_device_y_positions:
                script += f"# No device vias found for {net_name}\n\n"
                continue
            
            # Remove duplicates and sort
            unique_device_y = sorted(set(all_device_y_positions))
            
            # Determine Via23 Y positions based on net type (BEFORE filtering)
            if is_power:
                # Use BOTH device Y positions AND Ntap Y positions + NTAP offset for power nets
                tap_y_positions_raw = self.parser.get_ntap_y_positions()
                tap_y_positions = [y + ntap_offset_microns for y in tap_y_positions_raw]
                script += f"# Power net - Using device Y positions + Ntap Y positions\n"
                script += f"# Device Y positions: {unique_device_y}\n"
                script += f"# Ntap Y positions (raw): {tap_y_positions_raw}\n"
                script += f"# Applying Ntap offset ({Via23Parameters.NTAP_Y_OFFSET}): Final tap Y = {tap_y_positions}\n"
                # Combine device positions and tap positions
                via23_y_positions_unfiltered = sorted(set(unique_device_y + tap_y_positions))
            elif is_ground:
                # Use BOTH device Y positions AND Ptap Y positions + PTAP offset for ground nets
                tap_y_positions_raw = self.parser.get_ptap_y_positions()
                tap_y_positions = [y + ptap_offset_microns for y in tap_y_positions_raw]
                script += f"# Ground net - Using device Y positions + Ptap Y positions\n"
                script += f"# Device Y positions: {unique_device_y}\n"
                script += f"# Ptap Y positions (raw): {tap_y_positions_raw}\n"
                script += f"# Applying Ptap offset ({Via23Parameters.PTAP_Y_OFFSET}): Final tap Y = {tap_y_positions}\n"
                # Combine device positions and tap positions
                via23_y_positions_unfiltered = sorted(set(unique_device_y + tap_y_positions))
            else:
                # Regular nets use device Y positions (NO OFFSET)
                via23_y_positions_unfiltered = unique_device_y
            
            # FILTER OUT positions that match NFET/PFET Y positions
            via23_y_positions = [y for y in via23_y_positions_unfiltered if y not in nfet_pfet_y_positions]
            
            filtered_count = len(via23_y_positions_unfiltered) - len(via23_y_positions)
            if filtered_count > 0:
                script += f"# Filtered out {filtered_count} Via23(s) matching NFET/PFET Y positions\n"
            
            # Generate Via23 placements
            if len(via23_y_positions) == 0:
                script += f"# No Via23 positions remaining after filtering\n\n"
                continue
                
            script += f"# Placing {len(via23_y_positions)} Via23(s)\n"
            for y_pos in via23_y_positions:
                script += f"de::addPoint {{{x_pos:.3f} {y_pos:.3f}}} -context [de::getActiveContext]\n"
            
            script += "\n"
            
            # Generate Metal3 rectangle
            x_rect_min = x_pos - Via23Parameters.RECT_OFFSET_X_MICRONS
            x_rect_max = x_pos + Via23Parameters.RECT_OFFSET_X_MICRONS
            
            # Metal3 uses the filtered Via23 Y positions
            all_y_for_metal3 = via23_y_positions
            
            if len(all_y_for_metal3) == 0:
                script += f"# No Via23 positions for Metal3 (all filtered)\n\n"
                continue
            elif len(all_y_for_metal3) == 1:
                # Single position: extend 500nm upward
                y_rect_start = all_y_for_metal3[0]
                y_rect_end = y_rect_start + Via23Parameters.RECT_OFFSET_Y_SINGLE_MICRONS
            else:
                # Multiple positions: span from min to max
                y_rect_start = min(all_y_for_metal3)
                y_rect_end = max(all_y_for_metal3)
            
            script += f"# Metal3 Rectangle for {net_name}\n"
            script += f"le::createRectangle {{{{{x_rect_min:.3f} {y_rect_start:.3f}}} {{{x_rect_max:.3f} {y_rect_end:.3f}}}}} "
            script += f"-design [ed] -lpp {{M3 drawing}} -net {net_name}\n\n"
        
        return script


# ==================== PIN GENERATOR ====================

class PinGenerator:
    """Generates pin creation TCL script for non-internal nets"""
    
    def __init__(self, via23_gen: Via23Metal3Generator, parser: DEFParser):
        self.via23_gen = via23_gen
        self.parser = parser
        self.via_database = via23_gen.via_database
    
    def should_create_pin(self, net_name: str) -> bool:
        """Determine if a pin should be created for this net"""
        # Exclude nets whose names start with "net" (case-insensitive)
        if net_name.lower().startswith('net'):
            return False
        return True
    
    def generate_pin_tcl(self) -> str:
        """Generate pin creation TCL script"""
        script = "# TCL Pin Generation Script\n"
        script += "# Auto-generated from Via23/Metal3 generation\n"
        script += f"# Window Number: {Via23Parameters.WINDOW_NUMBER}\n"
        script += "# Creates pins at M3 rectangle start points for external nets\n"
        script += "# Excludes internal nets (names starting with 'net')\n\n"
        
        # ONE-TIME Pin configuration setup
        script += "# Pin Creation Configuration (one-time setup)\n"
        script += "ile::createPin\n"
        script += f"gi::setField {{inputMode}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getActiveWindow]]\n"
        script += f"gi::setField {{align}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getActiveWindow]]\n"
        script += f"gi::setField {{pinLabel}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getActiveWindow]]\n\n"
        
        nets = self.via_database.get_all_nets()
        
        # Get NFET/PFET Y positions for filtering (same as Via23)
        nfet_pfet_y_positions = set(self.parser.get_nfet_pfet_y_positions())
        
        # Convert tap offsets
        ntap_offset_microns = Via23Parameters.NTAP_Y_OFFSET / Via12Parameters.MICRONS_TO_MM
        ptap_offset_microns = Via23Parameters.PTAP_Y_OFFSET / Via12Parameters.MICRONS_TO_MM
        
        pins_created = 0
        pins_skipped = 0
        
        for net_index, net_name in enumerate(nets):
            # Check if pin should be created
            if not self.should_create_pin(net_name):
                script += f"# SKIPPED: {net_name} (internal net - name starts with 'net')\n"
                pins_skipped += 1
                continue
            
            # Calculate X position (same as Via23)
            x_pos = self.via23_gen.x_start + (net_index * self.via23_gen.x_step)
            
            # Get all Y positions (same logic as Via23)
            is_power = self.parser.is_power_net(net_name)
            is_ground = self.parser.is_ground_net(net_name)
            
            all_device_y_positions = []
            rows = self.via_database.get_net_rows(net_name)
            for row in rows:
                vias = self.via_database.get_row_data(net_name, row)
                for via in vias:
                    all_device_y_positions.append(via.y)
            
            if not all_device_y_positions:
                script += f"# SKIPPED: {net_name} (no device vias found)\n"
                pins_skipped += 1
                continue
            
            unique_device_y = sorted(set(all_device_y_positions))
            
            # Determine Y positions (same as Via23)
            if is_power:
                tap_y_positions_raw = self.parser.get_ntap_y_positions()
                tap_y_positions = [y + ntap_offset_microns for y in tap_y_positions_raw]
                via23_y_positions_unfiltered = sorted(set(unique_device_y + tap_y_positions))
            elif is_ground:
                tap_y_positions_raw = self.parser.get_ptap_y_positions()
                tap_y_positions = [y + ptap_offset_microns for y in tap_y_positions_raw]
                via23_y_positions_unfiltered = sorted(set(unique_device_y + tap_y_positions))
            else:
                via23_y_positions_unfiltered = unique_device_y
            
            # Apply NFET/PFET filtering (same as Via23)
            via23_y_positions = [y for y in via23_y_positions_unfiltered if y not in nfet_pfet_y_positions]
            
            if len(via23_y_positions) == 0:
                script += f"# SKIPPED: {net_name} (no Via23 positions after filtering)\n"
                pins_skipped += 1
                continue
            
            # Pin position = M3 rectangle start point
            x_pin = x_pos
            
            # Y position = minimum Y of Via23 positions (same as M3 rectangle start)
            if len(via23_y_positions) == 1:
                y_pin = via23_y_positions[0]
            else:
                y_pin = min(via23_y_positions)
            
            # Generate pin creation command
            script += f"# Pin for net: {net_name}\n"
            script += f"de::addPoint {{{x_pin:.3f} {y_pin:.3f}}} -context [de::getActiveContext]\n\n"
            pins_created += 1
        
        script += f"# Pin Generation Summary:\n"
        script += f"#   Pins created: {pins_created}\n"
        script += f"#   Pins skipped: {pins_skipped}\n"
        
        return script


# ==================== MAIN PROCESSING ====================

def process_unified_via_generation(def_content: str) -> Tuple[str, str, str]:
    """
    Process DEF file and generate Via12, Via23/Metal3, and Pin scripts
    
    Args:
        def_content: DEF file content
    
    Returns:
        Tuple of (via12_tcl_script, via23_metal3_tcl_script, pin_tcl_script)
    """
    print("="*70)
    print("UNIFIED VIA GENERATION SYSTEM WITH POWER/GROUND TAP SUPPORT + PIN GENERATION")
    print("="*70)
    
    # Parse DEF file
    print("\n[1/6] Parsing DEF file...")
    parser = DEFParser(def_content)
    parser.parse()
    
    print(f"  - Found {len(parser.components)} components")
    print(f"  - Found {len(parser.nets)} nets")
    print(f"  - Power nets: {len(parser.power_nets)} {list(parser.power_nets)}")
    print(f"  - Ground nets: {len(parser.ground_nets)} {list(parser.ground_nets)}")
    print(f"  - Taps found: {len(parser.taps)}")
    
    # Report tap positions
    ntap_y = parser.get_ntap_y_positions()
    ptap_y = parser.get_ptap_y_positions()
    print(f"  - Ntap Y positions: {ntap_y}")
    print(f"  - Ptap Y positions: {ptap_y}")
    
    # Get device X range
    device_x_min, device_x_max = parser.get_device_x_range()
    if device_x_min is None:
        print("  ERROR: No PFET/NFET devices found")
        return ("", "", "")
    
    print(f"  - Device X range: {device_x_min:.3f} to {device_x_max:.3f} microns")
    
    # Generate Via12 and build database
    print("\n[2/6] Generating Via12 and building database...")
    via12_gen = Via12Generator(parser.components, parser.nets)
    via12_gen.build_via_database()
    
    # Count dummy components
    dummy_count = sum(1 for comp in parser.components.values() 
                     if via12_gen._is_dummy_component(comp.name))
    if dummy_count > 0:
        print(f"  - Dummy components: {dummy_count} (G/D vias skipped, S vias generated)")
    
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
    print("\n[3/6] Generating Via12 TCL script...")
    via12_tcl = via12_gen.generate_via12_tcl()
    print(f"  - Via12 script: {len(via12_tcl.splitlines())} lines")
    
    # Generate Via23/Metal3 with tap support
    print("\n[4/6] Generating Via23/Metal3 TCL script with tap support...")
    via23_gen = Via23Metal3Generator(via12_gen.via_database, device_x_min, device_x_max, parser)
    via23_metal3_tcl = via23_gen.generate_via23_metal3_tcl()
    print(f"  - Via23/Metal3 script: {len(via23_metal3_tcl.splitlines())} lines")
    print(f"  - X axis: start={via23_gen.x_start:.3f}, step={via23_gen.x_step:.3f}")
    
    # Generate Pin script
    print("\n[5/6] Generating Pin TCL script...")
    pin_gen = PinGenerator(via23_gen, parser)
    pin_tcl = pin_gen.generate_pin_tcl()
    print(f"  - Pin script: {len(pin_tcl.splitlines())} lines")
    
    # Count pins
    pin_count = sum(1 for net in all_nets if pin_gen.should_create_pin(net))
    print(f"  - External nets (pins to create): {pin_count}")
    print(f"  - Internal nets (skipped): {len(all_nets) - pin_count}")
    
    print("\n[6/6] Summary...")
    for net in all_nets:
        if parser.is_power_net(net):
            print(f"  - {net}: POWER (Via23 at device Y + Ntap Y positions)")
        elif parser.is_ground_net(net):
            print(f"  - {net}: GROUND (Via23 at device Y + Ptap Y positions)")
    
    print("\n" + "="*70)
    print("GENERATION COMPLETE")
    print("="*70)
    
    return (via12_tcl, via23_metal3_tcl, pin_tcl)


# ==================== MAIN ====================

if __name__ == "__main__":
    # Read DEF file from uploaded location
    INPUT_DEF_FILE = "C:/Users/TEBA/Desktop/Neat Routing Automation/DEF_file_Input.txt"
    OUTPUT_VIA12_FILE = "C:/Users/TEBA/Desktop/routing automation final product/unified_via12_FIXED.tcl"
    OUTPUT_VIA23_FILE = "C:/Users/TEBA/Desktop/routing automation final product/unified_via23_metal3_FIXED.tcl"
    OUTPUT_PIN_FILE = "C:/Users/TEBA/Desktop/routing automation final product/unified_pins_FIXED.tcl"
    
    print("UNIFIED VIA GENERATION SYSTEM - BUGFIX VERSION")
    print("="*70)
    print("Features:")
    print("  - Power nets (USE POWER): Via23 uses device Y + Ntap Y positions")
    print("  - Ground nets (USE GROUND): Via23 uses device Y + Ptap Y positions")
    print("  - Via23 at NFET/PFET Y coordinates are FILTERED OUT")
    print("  - Metal3 extends to cover remaining Via23 positions")
    print("  - Pins created for external nets (excluding 'net*' names)")
    print("  - FIXED: Handles negative coordinates correctly")
    print("  - MODIFIED: Updated TCL syntax")
    print("  - BUGFIX: Source vias now correctly generated for Dummy components in ALL orientations")
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
    via12_tcl, via23_metal3_tcl, pin_tcl = process_unified_via_generation(def_content)
    
    if not via12_tcl or not via23_metal3_tcl or not pin_tcl:
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
    
    # Save Pin script
    try:
        with open(OUTPUT_PIN_FILE, 'w') as f:
            f.write(pin_tcl)
        print(f"✓ Pin script saved: {OUTPUT_PIN_FILE}")
    except Exception as e:
        print(f"\nERROR saving Pin script: {e}")
        exit(1)
    
    print("\n" + "="*70)
    print("SUCCESS: All three scripts generated successfully with BUGFIX!")
    print("="*70)
    print("\nExecution order:")
    print(f"  1. Run: {OUTPUT_VIA12_FILE}")
    print(f"  2. Run: {OUTPUT_VIA23_FILE}")
    print(f"  3. Run: {OUTPUT_PIN_FILE}")