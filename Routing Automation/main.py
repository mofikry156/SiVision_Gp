#!/usr/bin/env python3
"""
VLSI Routing Automation - Complete Main Controller
===================================================
Orchestrates all routing automation scripts in the correct execution order:
1. Dummies Connections
2. POCUT
3. Smart Metal 2 Placement
4. Taps Automation
5. Via12, Via23, and Metal3 (with taps data integration)

Generates 6 TCL files + 1 master execution script
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict


# ============================================================================
# GLOBAL CONFIGURATION - CENTRALIZED CONTROL
# ============================================================================

class GlobalConfig:
    """Central configuration for all routing automation scripts"""
    
    # ========== FILE PATHS ==========
    INPUT_DEF_FILE = r"C:\Users\TEBA\Desktop\Neat Routing Automation\DEF_file_Input.txt"
    OUTPUT_DIRECTORY = r"c:\Users\TEBA\Desktop\automated automation"
    
    # Output TCL filenames (in execution order)
    OUTPUT_FILES = {
        'dummies': '1_dummies_connections.tcl',
        'pocut': '2_pocut.tcl',
        'metal2': '3_metal2.tcl',
        'taps': '4_taps_routing.tcl',
        'via12': '5_via12.tcl',
        'via23_metal3': '6_via23_metal3.tcl',
        'master': 'MASTER_EXECUTE_ALL.tcl'
    }
    
    # ========== WINDOW NUMBERS ==========
    WINDOW_NUMBER_METAL2 = 2
    WINDOW_NUMBER_POCUT = 2
    WINDOW_NUMBER_TAPS = 2
    WINDOW_NUMBER_VIA12 = 2
    WINDOW_NUMBER_VIA23 = 2
    
    # ========== DESIGN INFORMATION ==========
    DESIGN_NAME = "hello_again"
    CELL_NAME = "automationtesting"
    
    # ========== METAL2 PARAMETERS ==========
    METAL2_WIDTH = 1.7  # Distance between start and end on x axis (microns)
    METAL2_LAYER = "M2"
    
    # ========== POCUT PARAMETERS ==========
    POCUT_LAYER = "POCUT"
    POCUT_Y_OFFSET = 15  # Offset in microns (±15)
    POCUT_THICKNESS = 0.040  # Thickness/height in microns
    
    # ========== TAPS PARAMETERS ==========
    # Rectangle offsets (nanometers)
    TAPS_RECT_X_MIN_OFFSET = 0
    TAPS_RECT_X_MAX_OFFSET = 147
    TAPS_RECT_Y_MIN_OFFSET = 106
    TAPS_RECT_Y_MAX_OFFSET = 140
    
    # Via offsets (nanometers)
    TAPS_VIA_X_START_OFFSET = 110
    TAPS_VIA_X_END_OFFSET = 45
    TAPS_VIA_Y_OFFSET = 123
    TAPS_VIA_SPACING = 74
    TAPS_VIA_TYPE = "VIA12"
    TAPS_METAL_LAYER = "M2"
    
    # ========== VIA12 PARAMETERS ==========
    VIA12_ROW_HEIGHT = 568
    VIA12_DUPLICATE_GATE_VIAS = True
    VIA12_GATE_DUPLICATE_OFFSET_X = 74
    VIA12_MICRONS_TO_MM = 1000.0
    VIA12_CONTEXT_WINDOW = 2
    
    # Via12 Orientation Offsets (N orientation)
    VIA12_N_DRAIN_OFFSET_X_OPT1 = 184
    VIA12_N_DRAIN_OFFSET_Y_OPT1 = 319
    VIA12_N_DRAIN_OFFSET_X_OPT2 = 184
    VIA12_N_DRAIN_OFFSET_Y_OPT2 = 402
    VIA12_N_SOURCE_OFFSET_X = 257
    VIA12_N_SOURCE_OFFSET_Y = 502
    VIA12_N_GATE_OFFSET_X_OPT1 = 147
    VIA12_N_GATE_OFFSET_Y_OPT1 = 60
    VIA12_N_GATE_OFFSET_X_OPT2 = 147
    VIA12_N_GATE_OFFSET_Y_OPT2 = 146
    
    # FN orientation
    VIA12_FN_DRAIN_OFFSET_X_OPT1 = 184
    VIA12_FN_DRAIN_OFFSET_Y_OPT1 = 319
    VIA12_FN_DRAIN_OFFSET_X_OPT2 = 184
    VIA12_FN_DRAIN_OFFSET_Y_OPT2 = 402
    VIA12_FN_SOURCE_OFFSET_X = 110
    VIA12_FN_SOURCE_OFFSET_Y = 502
    VIA12_FN_GATE_OFFSET_X_OPT1 = 147
    VIA12_FN_GATE_OFFSET_Y_OPT1 = 60
    VIA12_FN_GATE_OFFSET_X_OPT2 = 147
    VIA12_FN_GATE_OFFSET_Y_OPT2 = 146
    
    # FS orientation
    VIA12_FS_DRAIN_OFFSET_X_OPT1 = 184
    VIA12_FS_DRAIN_OFFSET_Y_OPT1 = 249
    VIA12_FS_DRAIN_OFFSET_X_OPT2 = 184
    VIA12_FS_DRAIN_OFFSET_Y_OPT2 = 148
    VIA12_FS_SOURCE_OFFSET_X = 110
    VIA12_FS_SOURCE_OFFSET_Y = 64
    VIA12_FS_GATE_OFFSET_X_OPT1 = 147
    VIA12_FS_GATE_OFFSET_Y_OPT1 = 508
    VIA12_FS_GATE_OFFSET_X_OPT2 = 147
    VIA12_FS_GATE_OFFSET_Y_OPT2 = 422
    
    # S orientation
    VIA12_S_DRAIN_OFFSET_X_OPT1 = 184
    VIA12_S_DRAIN_OFFSET_Y_OPT1 = 249
    VIA12_S_DRAIN_OFFSET_X_OPT2 = 184
    VIA12_S_DRAIN_OFFSET_Y_OPT2 = 148
    VIA12_S_SOURCE_OFFSET_X = 257
    VIA12_S_SOURCE_OFFSET_Y = 64
    VIA12_S_GATE_OFFSET_X_OPT1 = 147
    VIA12_S_GATE_OFFSET_Y_OPT1 = 508
    VIA12_S_GATE_OFFSET_X_OPT2 = 147
    VIA12_S_GATE_OFFSET_Y_OPT2 = 422
    
    # ========== VIA23/METAL3 PARAMETERS ==========
    VIA23_X_OFFSET_MICRONS = 0.400  # 400nm offset from device boundaries
    VIA23_VIA_NAME = "VIA23"
    VIA23_RECT_OFFSET_X_MICRONS = 0.040  # 40nm width offset
    VIA23_RECT_OFFSET_Y_SINGLE_MICRONS = 0.500  # 500nm height for single via
    VIA23_METAL_LAYER = "M3"


# ============================================================================
# SHARED DATA STRUCTURES
# ============================================================================

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
class TapRowData:
    """Stores tap row information for Via23/Metal3 integration"""
    y_position: float
    x_min: float
    x_max: float
    tap_type: str  # 'Ntap' or 'Ptap'
    net_name: str  # Power or Ground net


class RowViaDatabase:
    """Database of via placements organized by row and net"""
    
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


# ============================================================================
# DEF PARSER (SHARED)
# ============================================================================

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
                x=x / GlobalConfig.VIA12_MICRONS_TO_MM,
                y=y / GlobalConfig.VIA12_MICRONS_TO_MM,
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
        """Find VDD/VCC and VSS/GND nets"""
        power_net = None
        ground_net = None
        
        for net_name in self.nets.keys():
            net_upper = net_name.upper()
            if 'VDD' in net_upper or 'VCC' in net_upper:
                power_net = net_name
            elif 'VSS' in net_upper or 'GND' in net_upper:
                ground_net = net_name
        
        return (power_net or "VDD", ground_net or "VSS")
    
    def get_tap_rows(self) -> List[TapRowData]:
        """Extract tap row information for Via23/Metal3 integration"""
        tap_rows = []
        power_net, ground_net = self.find_power_ground_nets()
        
        # Group taps by Y position
        ntaps_by_y = defaultdict(list)
        ptaps_by_y = defaultdict(list)
        
        for comp in self.components.values():
            if 'ntap' in comp.cell_type.lower():
                ntaps_by_y[comp.y].append(comp)
            elif 'ptap' in comp.cell_type.lower():
                ptaps_by_y[comp.y].append(comp)
        
        # Process Ntap rows
        for y_pos, taps in ntaps_by_y.items():
            x_coords = [tap.x for tap in taps]
            tap_rows.append(TapRowData(
                y_position=y_pos,
                x_min=min(x_coords),
                x_max=max(x_coords),
                tap_type='Ntap',
                net_name=power_net
            ))
        
        # Process Ptap rows
        for y_pos, taps in ptaps_by_y.items():
            x_coords = [tap.x for tap in taps]
            tap_rows.append(TapRowData(
                y_position=y_pos,
                x_min=min(x_coords),
                x_max=max(x_coords),
                tap_type='Ptap',
                net_name=ground_net
            ))
        
        return sorted(tap_rows, key=lambda x: x.y_position)


# ============================================================================
# SCRIPT 1: DUMMIES CONNECTIONS
# ============================================================================

def generate_dummies_connections(def_content: str) -> str:
    """Generate TCL for dummy device connections"""
    
    def parse_dummy_devices(content):
        dummy_devices = []
        components_match = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', content, re.DOTALL)
        if not components_match:
            return dummy_devices
        
        components_section = components_match.group(1)
        component_pattern = r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:PLACED|FIXED)\s+\(\s*(\d+)\s+(\d+)\s*\)\s+(\w+)'
        components = re.findall(component_pattern, components_section)
        
        # Parse nets
        nets_match = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', content, re.DOTALL)
        nets_dict = {}
        
        if nets_match:
            nets_section = nets_match.group(1)
            net_definitions = re.split(r'-\s+(\S+)', nets_section)[1:]
            
            for i in range(0, len(net_definitions), 2):
                if i + 1 < len(net_definitions):
                    net_name = net_definitions[i]
                    net_connections = net_definitions[i + 1]
                    pin_pattern = r'\(\s*(\S+)\s+(\w+)\s*\)'
                    pins = re.findall(pin_pattern, net_connections)
                    
                    for comp_name, pin_type in pins:
                        if comp_name not in nets_dict:
                            nets_dict[comp_name] = {}
                        nets_dict[comp_name][pin_type] = net_name
        
        for comp_name, cell_type, x, y, orientation in components:
            if 'dummy' in comp_name.lower() or 'lxdummy' in comp_name.lower():
                source_net = "VSS"
                if comp_name in nets_dict and 'S' in nets_dict[comp_name]:
                    source_net = nets_dict[comp_name]['S']
                
                dummy_devices.append({
                    'name': comp_name,
                    'x': int(x),
                    'y': int(y),
                    'orientation': orientation,
                    'source_net': source_net
                })
        
        return dummy_devices
    
    dummy_devices = parse_dummy_devices(def_content)
    
    tcl = ["# TCL commands for dummy device connections"]
    tcl.append("# Generated automatically\n")
    
    for device in dummy_devices:
        name = device['name']
        x = device['x']
        y = device['y']
        orientation = device['orientation']
        net = device['source_net']
        
        tcl.append(f"# Device: {name} at ({x}, {y}) orientation: {orientation}")
        tcl.append(f"# Source net: {net}\n")
        
        x_mm = x / 1000.0
        y_mm = y / 1000.0
        
        if orientation in ['N', 'FN']:
            tcl.append(f'le::createRectangle {{{{{x_mm + 0.093:.3f} {y_mm + 0.543:.3f}}} {{{x_mm + 0.275:.3f} {y_mm + 0.509:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            tcl.append(f'le::createRectangle {{{{{x_mm + 0.130:.3f} {y_mm + 0.198:.3f}}} {{{x_mm + 0.239:.3f} {y_mm + 0.163:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            tcl.append(f'le::createRectangle {{{{{x_mm + 0.168:.3f} {y_mm + 0.543:.3f}}} {{{x_mm + 0.201:.3f} {y_mm + 0.180:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
        elif orientation in ['S', 'FS']:
            tcl.append(f'le::createRectangle {{{{{x_mm + 0.093:.3f} {y_mm + 0.025:.3f}}} {{{x_mm + 0.275:.3f} {y_mm + 0.059:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            tcl.append(f'le::createRectangle {{{{{x_mm + 0.130:.3f} {y_mm + 0.370:.3f}}} {{{x_mm + 0.239:.3f} {y_mm + 0.405:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
            tcl.append(f'le::createRectangle {{{{{x_mm + 0.168:.3f} {y_mm + 0.025:.3f}}} {{{x_mm + 0.201:.3f} {y_mm + 0.388:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
        
        tcl.append("")
    
    return '\n'.join(tcl)


# ============================================================================
# SCRIPT 2: POCUT
# ============================================================================

def generate_pocut(def_content: str) -> str:
    """Generate TCL for POCUT rectangles"""
    
    def parse_components(content):
        components = []
        comp_section = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', content, re.DOTALL)
        if not comp_section:
            return components
        
        comp_lines = comp_section.group(1).strip().split('\n')
        for line in comp_lines:
            line = line.strip()
            if line.startswith('-'):
                match = re.search(r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:FIXED|PLACED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)', line)
                if match:
                    components.append({
                        'name': match.group(1),
                        'type': match.group(2),
                        'x': int(match.group(3)),
                        'y': int(match.group(4)),
                        'orientation': match.group(5)
                    })
        return components
    
    def filter_tap_components(components):
        return [c for c in components if 'tap' not in c['type'].lower()]
    
    def group_by_rows(components):
        rows = {}
        for comp in components:
            y = comp['y']
            if y not in rows:
                rows[y] = []
            rows[y].append(comp)
        return dict(sorted(rows.items()))
    
    components = parse_components(def_content)
    filtered = filter_tap_components(components)
    rows = group_by_rows(filtered)
    
    if not filtered:
        return "# No components to process"
    
    x_coords = [comp['x'] for comp in filtered]
    x_min = min(x_coords)
    x_max = max(x_coords)
    x_start = x_min / 1000.0
    x_end = (x_max + 294) / 1000.0
    
    tcl = ["# Auto-generated TCL code for POCUT rectangles"]
    tcl.append(f"# Processing {len(rows)} unique rows")
    tcl.append(f"# Window Number: {GlobalConfig.WINDOW_NUMBER_POCUT}")
    tcl.append("")
    
    tcl.append("# Setup layer visibility")
    tcl.append(f"db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window {GlobalConfig.WINDOW_NUMBER_POCUT}]] -value false")
    tcl.append(f"gi::setField {{allSelectable}} -value {{false}} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows {GlobalConfig.WINDOW_NUMBER_POCUT}]]]")
    tcl.append(f"db::setAttr visible -of [de::getLPPs -from [de::getContexts -window {GlobalConfig.WINDOW_NUMBER_POCUT}]] -value false")
    tcl.append(f"gi::setField {{allVisible}} -value {{false}} -in [db::getAttr toolbar -of [gi::getAssistants leObjectLayerPanel -from [gi::getWindows {GlobalConfig.WINDOW_NUMBER_POCUT}]]]")
    tcl.append("")
    
    tcl.append(f"de::setActiveLPP [de::getLPPs {{{GlobalConfig.POCUT_LAYER} drawing}} -from [oa::DesignFind {GlobalConfig.DESIGN_NAME} {GlobalConfig.CELL_NAME} layout]]")
    tcl.append("")
    
    row_number = 1
    for y_coord, row_components in rows.items():
        tcl.append(f"# ROW {row_number}: Y = {y_coord} microns")
        y_base = y_coord / 1000.0
        rect_height = GlobalConfig.POCUT_THICKNESS
        y_bottom = y_base - (rect_height / 2)
        y_top = y_base + (rect_height / 2)
        
        tcl.append(f"le::createRectangle {{{{{x_start:.3f} {y_bottom:.3f}}} {{{x_end:.3f} {y_top:.3f}}}}} -design [ed] -lpp {{{GlobalConfig.POCUT_LAYER} drawing}}")
        tcl.append("")
        row_number += 1
    
    return '\n'.join(tcl)


# ============================================================================
# SCRIPT 3: SMART METAL 2 PLACEMENT
# ============================================================================

def generate_metal2(def_content: str) -> str:
    """Generate TCL for Metal2 horizontal wires"""
    
    def parse_components(content):
        components = []
        comp_section = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', content, re.DOTALL)
        if not comp_section:
            return components
        
        comp_lines = comp_section.group(1).strip().split('\n')
        for line in comp_lines:
            line = line.strip()
            if line.startswith('-'):
                match = re.search(r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:FIXED|PLACED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)', line)
                if match:
                    components.append({
                        'name': match.group(1),
                        'type': match.group(2),
                        'x': int(match.group(3)),
                        'y': int(match.group(4)),
                        'orientation': match.group(5)
                    })
        return components
    
    def filter_tap_components(components):
        return [c for c in components if 'tap' not in c['type'].lower()]
    
    def group_by_rows(components):
        rows = {}
        for comp in components:
            y = comp['y']
            if y not in rows:
                rows[y] = []
            rows[y].append(comp)
        return dict(sorted(rows.items()))
    
    components = parse_components(def_content)
    filtered = filter_tap_components(components)
    rows = group_by_rows(filtered)
    
    if not filtered:
        return "# No components to process"
    
    x_coords = [comp['x'] for comp in filtered]
    x_min = min(x_coords)
    x_max = max(x_coords)
    x_start = x_min / 1000.0
    x_end = (x_max + 300) / 1000.0
    
    tcl = ["# Auto-generated TCL code for Metal2 horizontal wire creation"]
    tcl.append(f"# Window Number: {GlobalConfig.WINDOW_NUMBER_METAL2}")
    tcl.append("")
    
    tcl.append("# Setup layer visibility")
    tcl.append(f"db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window {GlobalConfig.WINDOW_NUMBER_METAL2}]] -value false")
    tcl.append(f"de::setActiveLPP [de::getLPPs {{{GlobalConfig.METAL2_LAYER} drawing}} -from [oa::DesignFind {GlobalConfig.DESIGN_NAME} {GlobalConfig.CELL_NAME} layout]]")
    tcl.append("")
    
    created_wires = set()
    row_number = 1
    
    for y_coord, row_components in rows.items():
        orientation = row_components[0]['orientation']
        tcl.append(f"# ROW {row_number}: Y = {y_coord}, Orientation: {orientation}")
        
        if orientation in ['N', 'FN']:
            y_offsets = [146, 50, 308, 402, 496]
        elif orientation in ['S', 'FS']:
            y_offsets = [158, 253, 508, 412, 63]
        else:
            row_number += 1
            continue
        
        y_base = y_coord / 1000.0
        
        for offset in y_offsets:
            y_wire = y_base + (offset / 1000.0)
            wire_key = (round(x_start, 6), round(y_wire, 6), round(x_end, 6))
            
            if wire_key in created_wires:
                continue
            
            created_wires.add(wire_key)
            tcl.append("ile::createInterconnect")
            tcl.append(f"de::addPoint [list {x_start:.6f} {y_wire:.6f}] -context [db::getNext [de::getContexts -window {GlobalConfig.WINDOW_NUMBER_METAL2}]]")
            tcl.append(f"de::completeShape [list {x_end:.6f} {y_wire:.6f}] -context [db::getNext [de::getContexts -window {GlobalConfig.WINDOW_NUMBER_METAL2}]]")
        
        tcl.append("")
        row_number += 1
    
    return '\n'.join(tcl)


# ============================================================================
# SCRIPT 4: TAPS AUTOMATION
# ============================================================================

def generate_taps_routing(def_content: str) -> str:
    """Generate TCL for tap routing"""
    
    def parse_components(content):
        components = []
        comp_pattern = r'- (\S+)\s+(\S+)\s+\+\s+(?:PLACED|FIXED)\s+\(\s*(\d+)\s+(\d+)\s*\)\s+(\S+)'
        for match in re.finditer(comp_pattern, content):
            comp_name, comp_type, x, y, orientation = match.groups()
            components.append({
                'name': comp_name,
                'type': comp_type,
                'x': int(x),
                'y': int(y),
                'orientation': orientation
            })
        return components
    
    def find_power_ground_nets(content):
        power_net = None
        ground_net = None
        nets_section = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', content, re.DOTALL)
        
        if nets_section:
            net_pattern = r'- (\S+)\s*\n'
            for match in re.finditer(net_pattern, nets_section.group(1)):
                net = match.group(1)
                net_upper = net.upper()
                if 'VDD' in net_upper or 'VCC' in net_upper:
                    power_net = net
                elif 'VSS' in net_upper or 'GND' in net_upper:
                    ground_net = net
        
        return (power_net or "VDD", ground_net or "VSS")
    
    def group_taps_by_row(components):
        ntaps = [c for c in components if 'Ntap' in c['type']]
        ptaps = [c for c in components if 'Ptap' in c['type']]
        
        def group_by_y(taps):
            rows = {}
            for tap in taps:
                y = tap['y']
                if y not in rows:
                    rows[y] = []
                rows[y].append(tap)
            return rows
        
        return group_by_y(ntaps), group_by_y(ptaps)
    
    def generate_vias_for_row(x_min, x_max, y_pos):
        via_commands = []
        x_start = (x_min + GlobalConfig.TAPS_VIA_X_START_OFFSET) / 1000.0
        x_end = (x_max + GlobalConfig.TAPS_VIA_X_END_OFFSET) / 1000.0
        y_via = (y_pos + GlobalConfig.TAPS_VIA_Y_OFFSET) / 1000.0
        via_spacing = GlobalConfig.TAPS_VIA_SPACING / 1000.0
        
        current_x = x_start
        while current_x <= x_end:
            via_commands.append("ile::createVia")
            via_commands.append(f"gi::setField {{{{viaAuto}}}} -value {{{{false}}}} -in [gi::getToolbars {{{{deCommandOptions}}}} -from [gi::getWindows {GlobalConfig.WINDOW_NUMBER_TAPS}]]")
            via_commands.append(f"gi::setField {{{{viaDefName}}}} -value {{{{{GlobalConfig.TAPS_VIA_TYPE}}}}} -in [gi::getToolbars {{{{deCommandOptions}}}} -from [gi::getWindows {GlobalConfig.WINDOW_NUMBER_TAPS}]]")
            via_commands.append(f"de::addPoint {{{{{current_x:.3f} {y_via:.3f}}}}} -context [db::getNext [de::getContexts -window {GlobalConfig.WINDOW_NUMBER_TAPS}]]")
            via_commands.append("")
            current_x += via_spacing
        
        return via_commands
    
    components = parse_components(def_content)
    power_net, ground_net = find_power_ground_nets(def_content)
    ntap_rows, ptap_rows = group_taps_by_row(components)
    
    tcl = ["# Generated TCL script for tap routing"]
    tcl.append(f"# Power net: {power_net}")
    tcl.append(f"# Ground net: {ground_net}")
    tcl.append(f"# Window number: {GlobalConfig.WINDOW_NUMBER_TAPS}")
    tcl.append("")
    
    tcl.append("# ========== NTAP ROWS (Power) ==========")
    for y_pos, taps in sorted(ntap_rows.items()):
        x_positions = [tap['x'] for tap in taps]
        x_min = min(x_positions)
        x_max = max(x_positions)
        
        tcl.append(f"# Ntap Row at Y={y_pos}")
        
        x1 = (x_min + GlobalConfig.TAPS_RECT_X_MIN_OFFSET) / 1000.0
        x2 = (x_max + GlobalConfig.TAPS_RECT_X_MAX_OFFSET) / 1000.0
        y1 = (y_pos + GlobalConfig.TAPS_RECT_Y_MIN_OFFSET) / 1000.0
        y2 = (y_pos + GlobalConfig.TAPS_RECT_Y_MAX_OFFSET) / 1000.0
        
        tcl.append(f"le::createRectangle {{{{{{{x1:.3f} {y1:.3f}}}}} {{{{{x2:.3f} {y2:.3f}}}}}}} -design [ed] -lpp {{{{{GlobalConfig.TAPS_METAL_LAYER} drawing}}}} -net {power_net}")
        tcl.append("")
        
        via_cmds = generate_vias_for_row(x_min, x_max, y_pos)
        tcl.extend(via_cmds)
    
    tcl.append("")
    tcl.append("# ========== PTAP ROWS (Ground) ==========")
    for y_pos, taps in sorted(ptap_rows.items()):
        x_positions = [tap['x'] for tap in taps]
        x_min = min(x_positions)
        x_max = max(x_positions)
        
        tcl.append(f"# Ptap Row at Y={y_pos}")
        
        x1 = (x_min + GlobalConfig.TAPS_RECT_X_MIN_OFFSET) / 1000.0
        x2 = (x_max + GlobalConfig.TAPS_RECT_X_MAX_OFFSET) / 1000.0
        y1 = (y_pos + GlobalConfig.TAPS_RECT_Y_MIN_OFFSET) / 1000.0
        y2 = (y_pos + GlobalConfig.TAPS_RECT_Y_MAX_OFFSET) / 1000.0
        
        tcl.append(f"le::createRectangle {{{{{{{x1:.3f} {y1:.3f}}}}} {{{{{x2:.3f} {y2:.3f}}}}}}} -design [ed] -lpp {{{{{GlobalConfig.TAPS_METAL_LAYER} drawing}}}} -net {ground_net}")
        tcl.append("")
        
        via_cmds = generate_vias_for_row(x_min, x_max, y_pos)
        tcl.extend(via_cmds)
    
    return '\n'.join(tcl)


# ============================================================================
# VIA12 GENERATOR CLASS
# ============================================================================

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
        return int(component.y / GlobalConfig.VIA12_ROW_HEIGHT)
    
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
        micron_to_mm = 1.0 / GlobalConfig.VIA12_MICRONS_TO_MM
        option = self.get_option(net_name, row, pin_type)
        
        if orientation == 'N':
            if pin_type == 'D':
                if option == 1:
                    return (GlobalConfig.VIA12_N_DRAIN_OFFSET_X_OPT1 * micron_to_mm, GlobalConfig.VIA12_N_DRAIN_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (GlobalConfig.VIA12_N_DRAIN_OFFSET_X_OPT2 * micron_to_mm, GlobalConfig.VIA12_N_DRAIN_OFFSET_Y_OPT2 * micron_to_mm)
            elif pin_type == 'S':
                return (GlobalConfig.VIA12_N_SOURCE_OFFSET_X * micron_to_mm, GlobalConfig.VIA12_N_SOURCE_OFFSET_Y * micron_to_mm)
            elif pin_type == 'G':
                if option == 1:
                    return (GlobalConfig.VIA12_N_GATE_OFFSET_X_OPT1 * micron_to_mm, GlobalConfig.VIA12_N_GATE_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (GlobalConfig.VIA12_N_GATE_OFFSET_X_OPT2 * micron_to_mm, GlobalConfig.VIA12_N_GATE_OFFSET_Y_OPT2 * micron_to_mm)
                    
        elif orientation == 'FN':
            if pin_type == 'D':
                if option == 1:
                    return (GlobalConfig.VIA12_FN_DRAIN_OFFSET_X_OPT1 * micron_to_mm, GlobalConfig.VIA12_FN_DRAIN_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (GlobalConfig.VIA12_FN_DRAIN_OFFSET_X_OPT2 * micron_to_mm, GlobalConfig.VIA12_FN_DRAIN_OFFSET_Y_OPT2 * micron_to_mm)
            elif pin_type == 'S':
                return (GlobalConfig.VIA12_FN_SOURCE_OFFSET_X * micron_to_mm, GlobalConfig.VIA12_FN_SOURCE_OFFSET_Y * micron_to_mm)
            elif pin_type == 'G':
                if option == 1:
                    return (GlobalConfig.VIA12_FN_GATE_OFFSET_X_OPT1 * micron_to_mm, GlobalConfig.VIA12_FN_GATE_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (GlobalConfig.VIA12_FN_GATE_OFFSET_X_OPT2 * micron_to_mm, GlobalConfig.VIA12_FN_GATE_OFFSET_Y_OPT2 * micron_to_mm)
                    
        elif orientation == 'FS':
            if pin_type == 'D':
                if option == 1:
                    return (GlobalConfig.VIA12_FS_DRAIN_OFFSET_X_OPT1 * micron_to_mm, GlobalConfig.VIA12_FS_DRAIN_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (GlobalConfig.VIA12_FS_DRAIN_OFFSET_X_OPT2 * micron_to_mm, GlobalConfig.VIA12_FS_DRAIN_OFFSET_Y_OPT2 * micron_to_mm)
            elif pin_type == 'S':
                return (GlobalConfig.VIA12_FS_SOURCE_OFFSET_X * micron_to_mm, GlobalConfig.VIA12_FS_SOURCE_OFFSET_Y * micron_to_mm)
            elif pin_type == 'G':
                if option == 1:
                    return (GlobalConfig.VIA12_FS_GATE_OFFSET_X_OPT1 * micron_to_mm, GlobalConfig.VIA12_FS_GATE_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (GlobalConfig.VIA12_FS_GATE_OFFSET_X_OPT2 * micron_to_mm, GlobalConfig.VIA12_FS_GATE_OFFSET_Y_OPT2 * micron_to_mm)
                    
        elif orientation == 'S':
            if pin_type == 'D':
                if option == 1:
                    return (GlobalConfig.VIA12_S_DRAIN_OFFSET_X_OPT1 * micron_to_mm, GlobalConfig.VIA12_S_DRAIN_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (GlobalConfig.VIA12_S_DRAIN_OFFSET_X_OPT2 * micron_to_mm, GlobalConfig.VIA12_S_DRAIN_OFFSET_Y_OPT2 * micron_to_mm)
            elif pin_type == 'S':
                return (GlobalConfig.VIA12_S_SOURCE_OFFSET_X * micron_to_mm, GlobalConfig.VIA12_S_SOURCE_OFFSET_Y * micron_to_mm)
            elif pin_type == 'G':
                if option == 1:
                    return (GlobalConfig.VIA12_S_GATE_OFFSET_X_OPT1 * micron_to_mm, GlobalConfig.VIA12_S_GATE_OFFSET_Y_OPT1 * micron_to_mm)
                else:
                    return (GlobalConfig.VIA12_S_GATE_OFFSET_X_OPT2 * micron_to_mm, GlobalConfig.VIA12_S_GATE_OFFSET_Y_OPT2 * micron_to_mm)
        
        return (0, 0)
    
    def build_via_database(self):
        """Build the via database for all nets"""
        for net_name, connections in self.nets.items():
            if net_name in self.row_violations:
                continue
            
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
                
                if conn.pin == 'G' and GlobalConfig.VIA12_DUPLICATE_GATE_VIAS:
                    x_duplicate = via_x + (GlobalConfig.VIA12_GATE_DUPLICATE_OFFSET_X / GlobalConfig.VIA12_MICRONS_TO_MM)
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
        script += f"gi::setField {{viaAuto}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalConfig.VIA12_CONTEXT_WINDOW}]]\n\n"
        
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
                script += f"de::addPoint {{{via_x:.3f} {via_y:.3f}}} -context [db::getNext [de::getContexts -window {GlobalConfig.VIA12_CONTEXT_WINDOW}]]\n"
                script += "after 1\n"
                
                if conn.pin == 'G' and GlobalConfig.VIA12_DUPLICATE_GATE_VIAS:
                    x_dup = via_x + (GlobalConfig.VIA12_GATE_DUPLICATE_OFFSET_X / GlobalConfig.VIA12_MICRONS_TO_MM)
                    script += f"# {comp.name} - {conn.pin} DUPLICATE\n"
                    script += "ile::createVia\n"
                    script += f"de::addPoint {{{x_dup:.3f} {via_y:.3f}}} -context [db::getNext [de::getContexts -window {GlobalConfig.VIA12_CONTEXT_WINDOW}]]\n"
                    script += "after 1\n"
            
            script += f"puts \"{net_name} complete!\"\n\n"
        
        return script


# ============================================================================
# VIA23/METAL3 GENERATOR CLASS
# ============================================================================

class Via23Metal3Generator:
    """Generates Via23 and Metal3 based on Via12 database and taps data"""
    
    def __init__(self, via_database: RowViaDatabase, device_x_min: float, device_x_max: float, 
                 device_y_positions: Set[float], tap_rows: List[TapRowData]):
        self.via_database = via_database
        self.device_x_min = device_x_min
        self.device_x_max = device_x_max
        self.device_y_positions = device_y_positions
        self.tap_rows = tap_rows
        
        # Calculate X parameters
        nets = via_database.get_all_nets()
        num_nets = len(nets)
        
        if num_nets == 0:
            self.x_start = 0.0
            self.x_step = 0.0
        else:
            self.x_start = device_x_min + GlobalConfig.VIA23_X_OFFSET_MICRONS
            x_end = device_x_max - GlobalConfig.VIA23_X_OFFSET_MICRONS
            
            if num_nets == 1:
                self.x_step = 0.0
            else:
                self.x_step = (x_end - self.x_start) / (num_nets - 1)
    
    def generate_via23_metal3_tcl(self) -> str:
        """Generate Via23 and Metal3 TCL script with taps integration"""
        script = "# TCL Via23 and Metal3 Generation Script\n"
        script += "# Auto-generated from Via12 database WITH TAPS INTEGRATION\n"
        script += f"# Window Number: {GlobalConfig.WINDOW_NUMBER_VIA23}\n"
        script += f"# X Start: {self.x_start:.3f} microns\n"
        script += f"# X Step: {self.x_step:.3f} microns\n"
        script += f"# Via Name: {GlobalConfig.VIA23_VIA_NAME}\n"
        script += f"# Device Y positions filtered: {len(self.device_y_positions)}\n"
        script += f"# Tap rows integrated: {len(self.tap_rows)}\n\n"
        
        # ONE-TIME Via23 configuration setup
        script += "# Via23 Configuration (one-time setup)\n"
        script += "ile::createVia\n"
        script += f"gi::setField {{viaAuto}} -value {{false}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalConfig.WINDOW_NUMBER_VIA23}]]\n"
        script += f"gi::setField {{viaDefName}} -value {{{GlobalConfig.VIA23_VIA_NAME}}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {GlobalConfig.WINDOW_NUMBER_VIA23}]]\n\n"
        
        nets = self.via_database.get_all_nets()
        total_filtered = 0
        
        for net_index, net_name in enumerate(nets):
            x_pos = self.x_start + (net_index * self.x_step)
            
            script += f"# ========== Net: {net_name} (X={x_pos:.3f}) ==========\n"
            
            rows = self.via_database.get_net_rows(net_name)
            
            all_y_positions = []
            for row in rows:
                vias = self.via_database.get_row_data(net_name, row)
                for via in vias:
                    all_y_positions.append(via.y)
            
            if not all_y_positions:
                script += f"# No vias found for {net_name}\n\n"
                continue
            
            unique_y_positions = sorted(set(all_y_positions))
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
            
            for y_pos in filtered_y_positions:
                script += f"de::addPoint {{{x_pos:.3f} {y_pos:.3f}}} -context [db::getNext [de::getContexts -window {GlobalConfig.WINDOW_NUMBER_VIA23}]]\n"
            
            script += "\n"
            
            x_rect_min = x_pos - GlobalConfig.VIA23_RECT_OFFSET_X_MICRONS
            x_rect_max = x_pos + GlobalConfig.VIA23_RECT_OFFSET_X_MICRONS
            
            if len(filtered_y_positions) == 1:
                y_rect_start = filtered_y_positions[0]
                y_rect_end = y_rect_start + GlobalConfig.VIA23_RECT_OFFSET_Y_SINGLE_MICRONS
            else:
                y_rect_start = min(filtered_y_positions)
                y_rect_end = max(filtered_y_positions)
            
            script += f"# Metal3 Rectangle for {net_name}\n"
            script += f"le::createRectangle {{{{{x_rect_min:.3f} {y_rect_start:.3f}}} {{{x_rect_max:.3f} {y_rect_end:.3f}}}}} "
            script += f"-design [ed] -lpp {{{GlobalConfig.VIA23_METAL_LAYER} drawing}} -net {net_name}\n\n"
        
        script += f"# Total Via23 filtered (device Y match): {total_filtered}\n\n"
        
        # ========== TAPS INTEGRATION ==========
        script += "# " + "="*70 + "\n"
        script += "# TAPS INTEGRATION - Via23 and Metal3 for Power/Ground Rails\n"
        script += "# " + "="*70 + "\n\n"
        
        for tap_row in self.tap_rows:
            script += f"# {tap_row.tap_type} at Y={tap_row.y_position:.3f} (Net: {tap_row.net_name})\n"
            
            # Calculate X position - use leftmost position with offset
            x_tap_pos = tap_row.x_min + GlobalConfig.VIA23_X_OFFSET_MICRONS
            
            # Via23 at tap row
            script += f"de::addPoint {{{x_tap_pos:.3f} {tap_row.y_position:.3f}}} -context [db::getNext [de::getContexts -window {GlobalConfig.WINDOW_NUMBER_VIA23}]]\n"
            
            # Metal3 rectangle for tap
            x_rect_min = x_tap_pos - GlobalConfig.VIA23_RECT_OFFSET_X_MICRONS
            x_rect_max = x_tap_pos + GlobalConfig.VIA23_RECT_OFFSET_X_MICRONS
            y_rect_start = tap_row.y_position
            y_rect_end = tap_row.y_position + GlobalConfig.VIA23_RECT_OFFSET_Y_SINGLE_MICRONS
            
            script += f"le::createRectangle {{{{{x_rect_min:.3f} {y_rect_start:.3f}}} {{{x_rect_max:.3f} {y_rect_end:.3f}}}}} "
            script += f"-design [ed] -lpp {{{GlobalConfig.VIA23_METAL_LAYER} drawing}} -net {tap_row.net_name}\n\n"
        
        script += f"# Total tap rows integrated: {len(self.tap_rows)}\n"
        script += "puts \"Via23/Metal3 generation with taps integration complete\"\n"
        
        return script


# ============================================================================
# SCRIPT 5 & 6: VIA12 + VIA23/METAL3 (COMPLETE WITH TAPS INTEGRATION)
# ============================================================================

def generate_via12_via23_metal3(def_content: str, tap_rows: List[TapRowData]) -> Tuple[str, str]:
    """
    Generate Via12 and Via23/Metal3 TCL scripts with taps integration
    Returns: (via12_tcl, via23_metal3_tcl)
    """
    
    # Parse DEF
    parser = DEFParser(def_content)
    parser.parse()
    
    # Get device ranges
    device_x_min, device_x_max = parser.get_device_x_range()
    if device_x_min is None:
        return ("# ERROR: No PFET/NFET devices found\n", "# ERROR: No PFET/NFET devices found\n")
    
    device_y_positions = parser.get_device_y_positions()
    
    # Generate Via12 and build database
    via12_gen = Via12Generator(parser.components, parser.nets)
    via12_gen.build_via_database()
    
    # Generate Via12 TCL
    via12_tcl = via12_gen.generate_via12_tcl()
    
    # Generate Via23/Metal3 using the database AND taps data
    via23_gen = Via23Metal3Generator(
        via12_gen.via_database, 
        device_x_min, 
        device_x_max, 
        device_y_positions,
        tap_rows  # <-- TAPS INTEGRATION HERE
    )
    via23_metal3_tcl = via23_gen.generate_via23_metal3_tcl()
    
    return (via12_tcl, via23_metal3_tcl)


# ============================================================================
# MASTER TCL GENERATOR
# ============================================================================

def generate_master_tcl(output_files: Dict[str, str], output_dir: str) -> str:
    """Generate master TCL script that sources all other scripts"""
    
    tcl = ["# Master Execution Script"]
    tcl.append("# Auto-generated - executes all routing automation scripts in order")
    tcl.append(f"# Output Directory: {output_dir}")
    tcl.append("")
    tcl.append("puts \"===========================================================\"")
    tcl.append("puts \"VLSI Routing Automation - Master Execution\"")
    tcl.append("puts \"===========================================================\"")
    tcl.append("")
    
    # Execution order
    execution_order = ['dummies', 'pocut', 'metal2', 'taps', 'via12', 'via23_metal3']
    
    for idx, key in enumerate(execution_order, 1):
        filename = output_files[key]
        filepath = os.path.join(output_dir, filename).replace('\\', '/')
        
        tcl.append(f"# Step {idx}: {filename}")
        tcl.append(f"puts \"Executing step {idx}/{len(execution_order)}: {filename}\"")
        tcl.append(f'source "{filepath}"')
        tcl.append(f'puts "Completed: {filename}"')
        tcl.append("")
    
    tcl.append("puts \"===========================================================\"")
    tcl.append("puts \"All routing automation steps completed successfully!\"")
    tcl.append("puts \"===========================================================\"")
    
    return '\n'.join(tcl)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("VLSI ROUTING AUTOMATION - MAIN CONTROLLER")
    print("=" * 80)
    print(f"\nInput DEF: {GlobalConfig.INPUT_DEF_FILE}")
    print(f"Output Directory: {GlobalConfig.OUTPUT_DIRECTORY}\n")
    
    # Read DEF file
    print("[1/7] Reading DEF file...")
    try:
        with open(GlobalConfig.INPUT_DEF_FILE, 'r') as f:
            def_content = f.read()
        print(f"      ✓ Read {len(def_content)} characters")
    except FileNotFoundError:
        print(f"      ✗ ERROR: File not found: {GlobalConfig.INPUT_DEF_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"      ✗ ERROR: {e}")
        sys.exit(1)
    
    # Create output directory if needed
    os.makedirs(GlobalConfig.OUTPUT_DIRECTORY, exist_ok=True)
    
    # Extract tap rows data for Via23/Metal3 integration
    print("\n[2/7] Parsing DEF and extracting tap rows data...")
    parser = DEFParser(def_content)
    parser.parse()
    tap_rows = parser.get_tap_rows()
    print(f"      ✓ Found {len(tap_rows)} tap rows for integration")
    for tap in tap_rows:
        print(f"        - {tap.tap_type} at Y={tap.y_position:.3f} (Net: {tap.net_name})")
    
    # Generate each script
    print("\n[3/7] Generating Dummies Connections TCL...")
    dummies_tcl = generate_dummies_connections(def_content)
    output_path = os.path.join(GlobalConfig.OUTPUT_DIRECTORY, GlobalConfig.OUTPUT_FILES['dummies'])
    with open(output_path, 'w') as f:
        f.write(dummies_tcl)
    print(f"      ✓ Saved: {GlobalConfig.OUTPUT_FILES['dummies']}")
    
    print("\n[4/7] Generating POCUT TCL...")
    pocut_tcl = generate_pocut(def_content)
    output_path = os.path.join(GlobalConfig.OUTPUT_DIRECTORY, GlobalConfig.OUTPUT_FILES['pocut'])
    with open(output_path, 'w') as f:
        f.write(pocut_tcl)
    print(f"      ✓ Saved: {GlobalConfig.OUTPUT_FILES['pocut']}")
    
    print("\n[5/7] Generating Metal2 TCL...")
    metal2_tcl = generate_metal2(def_content)
    output_path = os.path.join(GlobalConfig.OUTPUT_DIRECTORY, GlobalConfig.OUTPUT_FILES['metal2'])
    with open(output_path, 'w') as f:
        f.write(metal2_tcl)
    print(f"      ✓ Saved: {GlobalConfig.OUTPUT_FILES['metal2']}")
    
    print("\n[6/7] Generating Taps Routing TCL...")
    taps_tcl = generate_taps_routing(def_content)
    output_path = os.path.join(GlobalConfig.OUTPUT_DIRECTORY, GlobalConfig.OUTPUT_FILES['taps'])
    with open(output_path, 'w') as f:
        f.write(taps_tcl)
    print(f"      ✓ Saved: {GlobalConfig.OUTPUT_FILES['taps']}")
    
    print("\n[7/7] Generating Via12, Via23, and Metal3 TCL (with taps integration)...")
    via12_tcl, via23_metal3_tcl = generate_via12_via23_metal3(def_content, tap_rows)
    
    output_path = os.path.join(GlobalConfig.OUTPUT_DIRECTORY, GlobalConfig.OUTPUT_FILES['via12'])
    with open(output_path, 'w') as f:
        f.write(via12_tcl)
    print(f"      ✓ Saved: {GlobalConfig.OUTPUT_FILES['via12']}")
    
    output_path = os.path.join(GlobalConfig.OUTPUT_DIRECTORY, GlobalConfig.OUTPUT_FILES['via23_metal3'])
    with open(output_path, 'w') as f:
        f.write(via23_metal3_tcl)
    print(f"      ✓ Saved: {GlobalConfig.OUTPUT_FILES['via23_metal3']}")
    print(f"      ✓ Integrated {len(tap_rows)} tap rows into Via23/Metal3")
    
    # Generate master execution script
    print("\n[MASTER] Generating master execution script...")
    master_tcl = generate_master_tcl(GlobalConfig.OUTPUT_FILES, GlobalConfig.OUTPUT_DIRECTORY)
    output_path = os.path.join(GlobalConfig.OUTPUT_DIRECTORY, GlobalConfig.OUTPUT_FILES['master'])
    with open(output_path, 'w') as f:
        f.write(master_tcl)
    print(f"         ✓ Saved: {GlobalConfig.OUTPUT_FILES['master']}")
    
    print("\n" + "=" * 80)
    print("SUCCESS! All TCL scripts generated successfully!")
    print("=" * 80)
    print("\nGenerated files:")
    for key in ['dummies', 'pocut', 'metal2', 'taps', 'via12', 'via23_metal3', 'master']:
        print(f"  • {GlobalConfig.OUTPUT_FILES[key]}")
    
    print(f"\nTo execute all scripts, run:")
    master_path = os.path.join(GlobalConfig.OUTPUT_DIRECTORY, GlobalConfig.OUTPUT_FILES['master']).replace('\\', '/')
    print(f'  source "{master_path}"')
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()