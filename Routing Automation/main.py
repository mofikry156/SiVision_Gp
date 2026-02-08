#!/usr/bin/env python3
"""
IC Routing Automation - SFTP GUI (WITH ENCRYPTED PERSISTENT SETTINGS)
Modern Tkinter interface for automated IC routing generation with remote SFTP execution
Features: All user settings are saved to encrypted local config file and restored on startup
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paramiko
import threading
import queue
import re
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import traceback
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import hashlib

# Import alignment module
try:
    import alignment
    ALIGNMENT_MODULE_LOADED = True
except ImportError as e:
    ALIGNMENT_MODULE_LOADED = False
    print(f"Warning: Could not import alignment module: {e}")

# ==================== ENCRYPTION MANAGER ====================
class EncryptionManager:
    """Handles encryption/decryption of configuration files"""
    
    def __init__(self):
        # Generate a machine-specific key based on hardware identifiers
        self.key = self._generate_machine_key()
        self.fernet = Fernet(self.key)
    
    def _generate_machine_key(self) -> bytes:
        """Generate encryption key based on machine-specific identifiers"""
        # Combine multiple machine identifiers for uniqueness
        machine_id = self._get_machine_id()
        
        # Use PBKDF2HMAC to derive a key from the machine ID
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ic_routing_automation_salt_v1',  # Static salt for consistency
            iterations=100000,
            backend=default_backend()
        )
        key_bytes = kdf.derive(machine_id.encode())
        
        # Encode as base64 for Fernet
        return base64.urlsafe_b64encode(key_bytes)
    
    def _get_machine_id(self) -> str:
        """Get a unique machine identifier"""
        try:
            # Try multiple methods to get machine ID
            if sys.platform == 'win32':
                # Windows: Use MAC address + username
                import uuid
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0,2*6,2)][::-1])
                username = os.environ.get('USERNAME', 'default')
                return f"{mac}_{username}"
            else:
                # Linux/Mac: Use machine-id or MAC address
                try:
                    with open('/etc/machine-id', 'r') as f:
                        return f.read().strip()
                except:
                    import uuid
                    return str(uuid.getnode())
        except:
            # Fallback: use a hash of the username and home directory
            import getpass
            username = getpass.getuser()
            home = os.path.expanduser('~')
            return hashlib.sha256(f"{username}_{home}".encode()).hexdigest()
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string data"""
        try:
            return self.fernet.encrypt(data.encode())
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt encrypted data"""
        try:
            return self.fernet.decrypt(encrypted_data).decode()
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")


# ==================== CONFIGURATION MANAGER ====================
class ConfigManager:
    """Manages encrypted persistent configuration storage"""
    
    def __init__(self, config_file='ic_routing_config.enc'):
        """Initialize config manager with encrypted config file path"""
        # Store config in user's home directory or app directory
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.config_path = os.path.join(app_dir, config_file)
        self.encryption_manager = EncryptionManager()
        self.default_config = self._get_default_config()
        
    def _get_default_config(self) -> dict:
        """Return default configuration"""
        return {
            'ssh': {
                'host': '10.20.50.5',
                'username': 'svgplayout2601yoatia',
                'password': ''
            },
            'paths': {
                'input_path': '/home/users/svgplayout2601yoatia/Full Automation scripts/DEF_file_Input',
                'output_path': '/home/users/svgplayout2601yoatia/Full Automation scripts/'
            },
            'stages': {
                '1_taps': {
                    'enabled': True,
                    'params': {
                        'rect_x_min_offset': 0,
                        'rect_x_max_offset': 147,
                        'rect_y_min_offset': 106,
                        'rect_y_max_offset': 140,
                        'via_x_start_offset': 110,
                        'via_x_end_offset': 45,
                        'via_y_offset': 123,
                        'via_spacing': 74,
                        'via_type': 'VIA12',
                        'metal_layer': 'M2'
                    }
                },
                '2_metal2': {
                    'enabled': True,
                    'params': {
                        'wire_width': 34,
                        'metal_width': 0.1,
                        'x_min_offset': 130,
                        'metal_layer': 'M2'
                    }
                },
                '3_via12': {
                    'enabled': True,
                    'params': {}
                },
                '4_metal3_via23': {
                    'enabled': True,
                    'params': {}
                },
                '5_pins': {
                    'enabled': True,
                    'params': {}
                },
                '6_pocut': {
                    'enabled': True,
                    'params': {
                        'metal_width': 1.7,
                        'pocut_layer': 'POCUT',
                        'y_offset': 15,
                        'pocut_thickness': 0.040
                    }
                },
                '7_dummies': {
                    'enabled': True,
                    'params': {}
                },
                '8_master': {
                    'enabled': True,
                    'params': {}
                }
            },
            'utilities': {
                'delete': {
                    'delete_m1': False,
                    'delete_m2': True,
                    'delete_m3': True,
                    'delete_vias': True
                },
                'row_alignment': {
                    'window_number': 2,
                    'delay': 0.1
                },
                'def_extraction': {
                    'output_dir': '/home/users/svgplayout2601yoatia/svgplayout2601yoatia_ws_14nm/Full Automation scripts/DEF_file_Input',
                    'filename': 'DEF_file_Input'
                }
            }
        }
    
    def load_config(self) -> dict:
        """Load encrypted configuration from file, create if doesn't exist"""
        try:
            if os.path.exists(self.config_path):
                # Read encrypted file
                with open(self.config_path, 'rb') as f:
                    encrypted_data = f.read()
                
                # Decrypt
                decrypted_json = self.encryption_manager.decrypt(encrypted_data)
                loaded_config = json.loads(decrypted_json)
                
                # Merge with defaults to handle new fields
                return self._merge_configs(self.default_config, loaded_config)
            else:
                # Create encrypted config file with defaults
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Creating new config file with defaults...")
            # If decryption fails, backup old file and create new one
            if os.path.exists(self.config_path):
                backup_path = self.config_path + '.backup'
                try:
                    os.rename(self.config_path, backup_path)
                    print(f"Backed up corrupted config to: {backup_path}")
                except:
                    pass
            return self.default_config.copy()
    
    def _merge_configs(self, default: dict, loaded: dict) -> dict:
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def save_config(self, config: dict):
        """Save configuration to encrypted file"""
        try:
            # Convert to JSON
            json_data = json.dumps(config, indent=4)
            
            # Encrypt
            encrypted_data = self.encryption_manager.encrypt(json_data)
            
            # Write to file
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Error saving config: {e}")
            raise
    
    def get_config_path(self) -> str:
        """Return the config file path"""
        return self.config_path


# ==================== VIA MODULE IMPORT FIX ====================
# Try multiple import strategies to load the via module

VIA_MODULE_LOADED = False
process_unified_via_generation = None

# Strategy 1: Try direct import from uploads
try:
    sys.path.insert(0, '/mnt/user-data/uploads')
    from via12_and_metal_3_and_via_23with_pins_automation import process_unified_via_generation
    VIA_MODULE_LOADED = True
    print("✓ Via module loaded successfully (Strategy 1)")
except ImportError as e:
    print(f"Strategy 1 failed: {e}")

# Strategy 2: Try loading from the file directly
if not VIA_MODULE_LOADED:
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "via_module",
            "/mnt/user-data/uploads/via12_and_metal_3_and_via_23with_pins_automation.py"
        )
        if spec and spec.loader:
            via_module = importlib.util.module_from_spec(spec)
            sys.modules['via_module'] = via_module
            spec.loader.exec_module(via_module)
            process_unified_via_generation = via_module.process_unified_via_generation
            VIA_MODULE_LOADED = True
            print("✓ Via module loaded successfully (Strategy 2)")
    except Exception as e:
        print(f"Strategy 2 failed: {e}")

# Strategy 3: Try exec() as last resort
if not VIA_MODULE_LOADED:
    try:
        via_module_path = "/mnt/user-data/uploads/via12_and_metal_3_and_via_23with_pins_automation.py"
        if os.path.exists(via_module_path):
            with open(via_module_path, 'r') as f:
                via_code = f.read()
            
            # Create namespace and execute
            via_namespace = {}
            exec(via_code, via_namespace)
            process_unified_via_generation = via_namespace.get('process_unified_via_generation')
            
            if process_unified_via_generation:
                VIA_MODULE_LOADED = True
                print("✓ Via module loaded successfully (Strategy 3)")
    except Exception as e:
        print(f"Strategy 3 failed: {e}")

if not VIA_MODULE_LOADED:
    print("⚠️ WARNING: Could not load via module - Via12/Metal3/Pins will not work")


# ==================== EMBEDDED MODULES ====================

# ==================== TAPS AUTOMATION MODULE ====================
class TapsAutomationGenerator:
    """Generates TCL script for tap routing"""
    
    def __init__(self, rect_x_min_offset=0, rect_x_max_offset=147,
                 rect_y_min_offset=106, rect_y_max_offset=140,
                 via_x_start_offset=110, via_x_end_offset=45,
                 via_y_offset=123, via_spacing=74,
                 via_type="VIA12", metal_layer="M2"):
        self.rect_x_min_offset = rect_x_min_offset
        self.rect_x_max_offset = rect_x_max_offset
        self.rect_y_min_offset = rect_y_min_offset
        self.rect_y_max_offset = rect_y_max_offset
        self.via_x_start_offset = via_x_start_offset
        self.via_x_end_offset = via_x_end_offset
        self.via_y_offset = via_y_offset
        self.via_spacing = via_spacing
        self.via_type = via_type
        self.metal_layer = metal_layer
    
    def parse_def_file(self, def_content):
        """Parse DEF file to extract components and nets"""
        components = []
        comp_pattern = r'- (\S+)\s+(\S+)\s+\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)'
        
        for match in re.finditer(comp_pattern, def_content):
            comp_name, comp_type, x, y, orientation = match.groups()
            components.append({
                'name': comp_name,
                'type': comp_type,
                'x': int(x),
                'y': int(y),
                'orientation': orientation
            })
        
        nets = []
        net_pattern = r'- (\S+)\s*\n'
        nets_section = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', def_content, re.DOTALL)
        if nets_section:
            for match in re.finditer(net_pattern, nets_section.group(1)):
                nets.append(match.group(1))
        
        return components, nets
    
    def find_power_ground_nets(self, nets):
        """Find VDD and VSS nets"""
        power_net = None
        ground_net = None
        
        for net in nets:
            net_upper = net.upper()
            if 'VDD' in net_upper or 'VCC' in net_upper:
                power_net = net
            elif 'VSS' in net_upper or 'GND' in net_upper:
                ground_net = net
        
        return power_net or "VDD", ground_net or "VSS"
    
    def group_taps_by_row(self, components):
        """Group tap devices by row"""
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
    
    def generate_vias_for_row(self, x_min, x_max, y_pos):
        """Generate via commands for a tap row"""
        via_commands = []
        
        x_start = (x_min + self.via_x_start_offset) / 1000.0
        x_end = (x_max + self.via_x_end_offset) / 1000.0
        y_via = (y_pos + self.via_y_offset) / 1000.0
        
        via_spacing = self.via_spacing / 1000.0
        
        current_x = x_start
        while current_x <= x_end:
            via_commands.append(f"de::addPoint {{{current_x:.3f} {y_via:.3f}}} -context [de::getActiveContext]")
            current_x += via_spacing
        
        return via_commands
    
    def generate_tcl(self, def_content):
        """Generate TCL script for taps routing"""
        components, nets = self.parse_def_file(def_content)
        power_net, ground_net = self.find_power_ground_nets(nets)
        ntap_rows, ptap_rows = self.group_taps_by_row(components)
        
        tcl_commands = []
        tcl_commands.append("# Generated TCL script for tap routing")
        tcl_commands.append(f"# Power net: {power_net}")
        tcl_commands.append(f"# Ground net: {ground_net}")
        tcl_commands.append("")
        
        tcl_commands.append("# ========== RECTANGLES ==========")
        tcl_commands.append("")
        
        tcl_commands.append("# NTAP ROWS (Power)")
        for y_pos, taps in sorted(ntap_rows.items()):
            x_positions = [tap['x'] for tap in taps]
            x_min = min(x_positions)
            x_max = max(x_positions)
            
            x1 = (x_min + self.rect_x_min_offset) / 1000.0
            x2 = (x_max + self.rect_x_max_offset) / 1000.0
            y1 = (y_pos + self.rect_y_min_offset) / 1000.0
            y2 = (y_pos + self.rect_y_max_offset) / 1000.0
            
            tcl_commands.append(f"# Ntap Row at Y={y_pos}")
            tcl_commands.append(f"le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{{self.metal_layer} drawing}} -net {power_net}")
            tcl_commands.append("")
        
        tcl_commands.append("# PTAP ROWS (Ground)")
        for y_pos, taps in sorted(ptap_rows.items()):
            x_positions = [tap['x'] for tap in taps]
            x_min = min(x_positions)
            x_max = max(x_positions)
            
            x1 = (x_min + self.rect_x_min_offset) / 1000.0
            x2 = (x_max + self.rect_x_max_offset) / 1000.0
            y1 = (y_pos + self.rect_y_min_offset) / 1000.0
            y2 = (y_pos + self.rect_y_max_offset) / 1000.0
            
            tcl_commands.append(f"# Ptap Row at Y={y_pos}")
            tcl_commands.append(f"le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{{self.metal_layer} drawing}} -net {ground_net}")
            tcl_commands.append("")
        
        tcl_commands.append("# ========== VIA SETUP ==========")
        tcl_commands.append("ile::createVia")
        tcl_commands.append("gi::setField {viaAuto} -value {false} -in [gi::getToolbars {deCommandOptions} -from [gi::getActiveWindow]]")
        tcl_commands.append(f"gi::setField {{viaDefName}} -value {{{self.via_type}}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getActiveWindow]]")
        tcl_commands.append("")
        
        tcl_commands.append("# ========== VIA PLACEMENTS ==========")
        tcl_commands.append("")
        
        tcl_commands.append("# NTAP ROW VIAS")
        for y_pos, taps in sorted(ntap_rows.items()):
            x_positions = [tap['x'] for tap in taps]
            x_min = min(x_positions)
            x_max = max(x_positions)
            
            tcl_commands.append(f"# Ntap Row at Y={y_pos}")
            via_cmds = self.generate_vias_for_row(x_min, x_max, y_pos)
            tcl_commands.extend(via_cmds)
            tcl_commands.append("")
        
        tcl_commands.append("# PTAP ROW VIAS")
        for y_pos, taps in sorted(ptap_rows.items()):
            x_positions = [tap['x'] for tap in taps]
            x_min = min(x_positions)
            x_max = max(x_positions)
            
            tcl_commands.append(f"# Ptap Row at Y={y_pos}")
            via_cmds = self.generate_vias_for_row(x_min, x_max, y_pos)
            tcl_commands.extend(via_cmds)
            tcl_commands.append("")
        
        return '\n'.join(tcl_commands)


# ==================== METAL2 MODULE ====================
class Metal2Generator:
    """Generates TCL script for Metal2 layer"""
    
    def __init__(self, wire_width=34, metal_width=0.1, x_min_offset=130, metal_layer="M2"):
        self.wire_width = wire_width
        self.metal_width = metal_width
        self.x_min_offset = x_min_offset
        self.metal_layer = metal_layer
    
    def parse_def_file(self, def_content):
        """Parse DEF file and extract component information"""
        components = []
        
        comp_section = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', 
                                def_content, re.DOTALL)
        
        if not comp_section:
            return components
        
        comp_lines = comp_section.group(1).strip().split('\n')
        
        for line in comp_lines:
            line = line.strip()
            if line.startswith('-'):
                match = re.search(r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:FIXED|PLACED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)', 
                                line)
                if match:
                    name = match.group(1)
                    comp_type = match.group(2)
                    x = int(match.group(3))
                    y = int(match.group(4))
                    orientation = match.group(5)
                    
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
    
    def filter_tap_components(self, components):
        """Filter out tap components"""
        return [comp for comp in components if 'tap' not in comp['type'].lower()]
    
    def group_components_by_rows(self, components):
        """Group components by Y coordinate"""
        rows = {}
        
        for comp in components:
            y = comp['y']
            if y not in rows:
                rows[y] = []
            rows[y].append(comp)
        
        return dict(sorted(rows.items()))
    
    def calculate_x_range(self, components, include_dummy=True):
        """Calculate x range for components"""
        if include_dummy:
            filtered = components
        else:
            filtered = [comp for comp in components if not comp.get('is_dummy', False)]
        
        if not filtered:
            return None, None
        
        x_coords = [comp['x'] for comp in filtered]
        return min(x_coords), max(x_coords)
    
    def generate_tcl(self, def_content):
        """Generate TCL code for Metal2 layer"""
        def to_design_units(microns):
            return microns / 1000.0
        
        half_width = to_design_units(self.wire_width / 2)
        
        components = self.parse_def_file(def_content)
        filtered_components = self.filter_tap_components(components)
        rows = self.group_components_by_rows(filtered_components)
        
        tcl_code = []
        tcl_code.append("# Auto-generated TCL code for Metal2 horizontal rectangles")
        tcl_code.append(f"# Wire Width: {self.wire_width}")
        tcl_code.append(f"# Metal Layer: {self.metal_layer}")
        tcl_code.append("")
        
        created_rectangles = set()
        
        for row_number, (y_coord, row_components) in enumerate(rows.items(), 1):
            tcl_code.append(f"# ROW {row_number}: Y = {y_coord}")
            
            first_comp = row_components[0]
            orientation = first_comp['orientation']
            
            if orientation in ['N', 'FN']:
                y_offsets_essential = [146, 50, 308, 402]
                y_offsets_all = [496]
            elif orientation in ['S', 'FS']:
                y_offsets_essential = [158, 253, 508, 412]
                y_offsets_all = [63]
            else:
                continue
            
            y_base = to_design_units(y_coord)
            
            row_x_min_essential, row_x_max_essential = self.calculate_x_range(row_components, include_dummy=False)
            row_x_min_all, row_x_max_all = self.calculate_x_range(row_components, include_dummy=True)
            
            for offset in y_offsets_essential:
                y_center = y_base + to_design_units(offset)
                y_start = y_center + half_width
                y_end = y_center - half_width
                
                x_start = to_design_units(row_x_min_essential + self.x_min_offset)
                x_end = to_design_units(row_x_max_essential + 300)
                
                rect_key = (round(x_start, 6), round(y_start, 6), round(x_end, 6), round(y_end, 6))
                
                if rect_key in created_rectangles:
                    continue
                
                created_rectangles.add(rect_key)
                
                tcl_code.append(f"# Rectangle at offset {offset} (ESSENTIAL)")
                tcl_code.append(f"le::createRectangle {{{{{x_start:.3f} {y_start:.3f}}} {{{x_end:.3f} {y_end:.3f}}}}} -design [ed] -lpp {{{self.metal_layer} drawing}}")
            
            for offset in y_offsets_all:
                y_center = y_base + to_design_units(offset)
                y_start = y_center + half_width
                y_end = y_center - half_width
                
                x_start = to_design_units(row_x_min_all + self.x_min_offset)
                x_end = to_design_units(row_x_max_all + 300)
                
                rect_key = (round(x_start, 6), round(y_start, 6), round(x_end, 6), round(y_end, 6))
                
                if rect_key in created_rectangles:
                    continue
                
                created_rectangles.add(rect_key)
                
                tcl_code.append(f"# Rectangle at offset {offset} (ALL DEVICES)")
                tcl_code.append(f"le::createRectangle {{{{{x_start:.3f} {y_start:.3f}}} {{{x_end:.3f} {y_end:.3f}}}}} -design [ed] -lpp {{{self.metal_layer} drawing}}")
            
            tcl_code.append("")
        
        tcl_code.append(f"# Total rectangles created: {len(created_rectangles)}")
        
        return "\n".join(tcl_code)


# ==================== POCUT MODULE ====================
class PocutGenerator:
    """Generates TCL script for POCUT layer"""
    
    def __init__(self, metal_width=1.7, pocut_layer="POCUT", y_offset=15, pocut_thickness=0.040):
        self.metal_width = metal_width
        self.pocut_layer = pocut_layer
        self.y_offset = y_offset
        self.pocut_thickness = pocut_thickness
    
    def parse_def_file(self, def_content):
        """Parse DEF file"""
        components = []
        comp_section = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', 
                                def_content, re.DOTALL)
        
        if not comp_section:
            return components
        
        comp_lines = comp_section.group(1).strip().split('\n')
        
        for line in comp_lines:
            line = line.strip()
            if line.startswith('-'):
                match = re.search(r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:FIXED|PLACED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)', 
                                line)
                if match:
                    components.append({
                        'name': match.group(1),
                        'type': match.group(2),
                        'x': int(match.group(3)),
                        'y': int(match.group(4)),
                        'orientation': match.group(5)
                    })
        
        return components
    
    def filter_tap_components(self, components):
        """Filter out tap components"""
        return [comp for comp in components if 'tap' not in comp['type'].lower()]
    
    def group_components_by_rows(self, components):
        """Group components by Y coordinate"""
        rows = {}
        for comp in components:
            y = comp['y']
            if y not in rows:
                rows[y] = []
            rows[y].append(comp)
        return dict(sorted(rows.items()))
    
    def generate_tcl(self, def_content):
        """Generate TCL code for POCUT rectangles"""
        def to_design_units(microns):
            return microns / 1000.0
        
        components = self.parse_def_file(def_content)
        filtered_components = self.filter_tap_components(components)
        rows = self.group_components_by_rows(filtered_components)
        
        if not filtered_components:
            return "# No components to process"
        
        x_coords = [comp['x'] for comp in filtered_components]
        x_min = min(x_coords)
        x_max = max(x_coords)
        x_start = to_design_units(x_min)
        x_end = to_design_units(x_max + 294)
        
        tcl_code = []
        tcl_code.append("# Auto-generated TCL code for POCUT rectangles")
        tcl_code.append(f"# POCUT Layer: {self.pocut_layer}")
        tcl_code.append("")
        
        for row_number, (y_coord, row_components) in enumerate(rows.items(), 1):
            tcl_code.append(f"# ROW {row_number}: Y = {y_coord}")
            
            y_base = to_design_units(y_coord)
            rect_height = self.pocut_thickness
            y_bottom = y_base - (rect_height / 2)
            y_top = y_base + (rect_height / 2)
            
            tcl_code.append(f"le::createRectangle {{{{{x_start:.3f} {y_bottom:.3f}}} {{{x_end:.3f} {y_top:.3f}}}}} -design [ed] -lpp {{{self.pocut_layer} drawing}}")
            tcl_code.append("")
        
        tcl_code.append(f"# Total POCUT rectangles created: {len(rows)}")
        
        return "\n".join(tcl_code)


# ==================== DUMMIES MODULE ====================
class DummiesGenerator:
    """Generates TCL script for dummy device connections"""
    
    def parse_def_file(self, def_content):
        """Parse DEF file and extract dummy device information"""
        dummy_devices = []
        
        components_match = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', def_content, re.DOTALL)
        if not components_match:
            return dummy_devices
        
        components_section = components_match.group(1)
        
        component_pattern = r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\w+)'
        components = re.findall(component_pattern, components_section)
        
        nets_match = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', def_content, re.DOTALL)
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
                x_coord = int(x)
                y_coord = int(y)
                
                source_net = "VSS"
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
    
    def generate_tcl(self, def_content):
        """Generate TCL commands for dummy device connections"""
        dummy_devices = self.parse_def_file(def_content)
        
        tcl_commands = []
        tcl_commands.append("# TCL commands for dummy device connections")
        tcl_commands.append("")
        
        for device in dummy_devices:
            name = device['name']
            x = device['x']
            y = device['y']
            orientation = device['orientation']
            net = device['source_net']
            
            tcl_commands.append(f"# Device: {name} at ({x}, {y}) orientation: {orientation}")
            tcl_commands.append(f"# Source net: {net}")
            
            x_mm = x / 1000.0
            y_mm = y / 1000.0
            
            if orientation in ['N', 'FN']:
                x1 = x_mm + 0.093
                y1 = y_mm + 0.543
                x2 = x_mm + 0.275
                y2 = y_mm + 0.509
                tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}}')
                
                x1 = x_mm + 0.130
                y1 = y_mm + 0.198
                x2 = x_mm + 0.239
                y2 = y_mm + 0.163
                tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}}')
                
                x1 = x_mm + 0.168
                y1 = y_mm + 0.543
                x2 = x_mm + 0.201
                y2 = y_mm + 0.180
                tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}}')
                
            elif orientation in ['S', 'FS']:
                x1 = x_mm + 0.093
                y1 = y_mm + 0.025
                x2 = x_mm + 0.275
                y2 = y_mm + 0.059
                tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}}')
                
                x1 = x_mm + 0.130
                y1 = y_mm + 0.370
                x2 = x_mm + 0.239
                y2 = y_mm + 0.405
                tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}}')
                
                x1 = x_mm + 0.168
                y1 = y_mm + 0.025
                x2 = x_mm + 0.201
                y2 = y_mm + 0.388
                tcl_commands.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}}')
            
            tcl_commands.append("")
        
        return '\n'.join(tcl_commands)


# ==================== SSH/SFTP CONNECTION ====================
class SSHConnection:
    """Manages SSH/SFTP connections to remote server"""
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.ssh_client = None
        self.sftp_client = None
    
    def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                self.host,
                username=self.username,
                password=self.password,
                timeout=10
            )
            self.sftp_client = self.ssh_client.open_sftp()
            return True
        except Exception as e:
            raise Exception(f"Connection failed: {str(e)}")
    
    def read_file(self, remote_path: str) -> str:
        """Read file from remote server"""
        try:
            with self.sftp_client.file(remote_path, 'r') as f:
                content = f.read().decode('utf-8')
            return content
        except Exception as e:
            raise Exception(f"Failed to read {remote_path}: {str(e)}")
    
    def write_file(self, remote_path: str, content: str):
        """Write file to remote server"""
        try:
            import os
            self._create_remote_directory(os.path.dirname(remote_path))
            
            with self.sftp_client.file(remote_path, 'w') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to write {remote_path}: {str(e)}")
    
    def _create_remote_directory(self, path: str):
        """Recursively create remote directory"""
        if not path or path == '/':
            return
        
        try:
            self.sftp_client.stat(path)
        except IOError:
            import os
            parent = os.path.dirname(path)
            if parent:
                self._create_remote_directory(parent)
            self.sftp_client.mkdir(path)
    
    def close(self):
        """Close connections"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()


# ==================== MAIN GUI ====================
class ModernRoutingGUI:
    """Modern Tkinter GUI for IC Routing Automation with Encrypted Persistent Settings"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ IC Routing Automation - SFTP (Encrypted)")
        self.root.geometry("1400x900")
        
        self.colors = {
            'bg': '#f0f0f0',
            'primary': '#2ecc71',
            'secondary': '#27ae60',
            'accent': '#3498db',
            'dark': '#2c3e50',
            'light': '#ecf0f1',
            'white': '#ffffff',
            'error': '#e74c3c',
            'success': '#27ae60',
            'text': '#2c3e50'
        }
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        
        # Load saved configuration
        self.saved_config = self.config_manager.load_config()
        
        self.init_variables()
        self.log_queue = queue.Queue()
        self.setup_ui()
        self.process_log_queue()
        
        # Log config file location
        self.log(f"🔒 Encrypted config: {self.config_manager.get_config_path()}", 'info')
        self.log("Settings encrypted and auto-saved", 'success')
        
        # Register save on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def init_variables(self):
        """Initialize all configuration variables with saved values"""
        # SSH Configuration
        ssh_config = self.saved_config.get('ssh', {})
        self.var_host = tk.StringVar(value=ssh_config.get('host', '10.20.50.5'))
        self.var_username = tk.StringVar(value=ssh_config.get('username', 'svgplayout2601yoatia'))
        self.var_password = tk.StringVar(value=ssh_config.get('password', ''))
        
        # Paths Configuration
        paths_config = self.saved_config.get('paths', {})
        self.var_input_path = tk.StringVar(
            value=paths_config.get('input_path', '/home/users/svgplayout2601yoatia/Full Automation scripts/DEF_file_Input')
        )
        self.var_output_path = tk.StringVar(
            value=paths_config.get('output_path', '/home/users/svgplayout2601yoatia/Full Automation scripts/')
        )
        
        # Routing Stages Configuration
        stages_config = self.saved_config.get('stages', {})
        
        self.routing_stages = {
            '1_taps': {
                'enabled': tk.BooleanVar(value=stages_config.get('1_taps', {}).get('enabled', True)),
                'name': '1. Taps Automation',
                'output_file': '1_taps_routing.tcl',
                'expanded': tk.BooleanVar(value=False),
                'params': self._load_stage_params('1_taps', {
                    'rect_x_min_offset': (tk.IntVar, 0),
                    'rect_x_max_offset': (tk.IntVar, 147),
                    'rect_y_min_offset': (tk.IntVar, 106),
                    'rect_y_max_offset': (tk.IntVar, 140),
                    'via_x_start_offset': (tk.IntVar, 110),
                    'via_x_end_offset': (tk.IntVar, 45),
                    'via_y_offset': (tk.IntVar, 123),
                    'via_spacing': (tk.IntVar, 74),
                    'via_type': (tk.StringVar, 'VIA12'),
                    'metal_layer': (tk.StringVar, 'M2')
                })
            },
            '2_metal2': {
                'enabled': tk.BooleanVar(value=stages_config.get('2_metal2', {}).get('enabled', True)),
                'name': '2. Metal2 Smart',
                'output_file': '2_metal2.tcl',
                'expanded': tk.BooleanVar(value=False),
                'params': self._load_stage_params('2_metal2', {
                    'wire_width': (tk.IntVar, 34),
                    'metal_width': (tk.DoubleVar, 0.1),
                    'x_min_offset': (tk.IntVar, 130),
                    'metal_layer': (tk.StringVar, 'M2')
                })
            },
            '3_via12': {
                'enabled': tk.BooleanVar(value=stages_config.get('3_via12', {}).get('enabled', True)),
                'name': '3. Via12 (Original Module)',
                'output_file': '3_via12.tcl',
                'expanded': tk.BooleanVar(value=False),
                'params': {}
            },
            '4_metal3_via23': {
                'enabled': tk.BooleanVar(value=stages_config.get('4_metal3_via23', {}).get('enabled', True)),
                'name': '4. Metal3 + Via23 (Original Module)',
                'output_file': '4_metal3_via23.tcl',
                'expanded': tk.BooleanVar(value=False),
                'params': {}
            },
            '5_pins': {
                'enabled': tk.BooleanVar(value=stages_config.get('5_pins', {}).get('enabled', True)),
                'name': '5. Pins (Original Module)',
                'output_file': '5_pins.tcl',
                'expanded': tk.BooleanVar(value=False),
                'params': {}
            },
            '6_pocut': {
                'enabled': tk.BooleanVar(value=stages_config.get('6_pocut', {}).get('enabled', True)),
                'name': '6. POCUT',
                'output_file': '6_pocut.tcl',
                'expanded': tk.BooleanVar(value=False),
                'params': self._load_stage_params('6_pocut', {
                    'metal_width': (tk.DoubleVar, 1.7),
                    'pocut_layer': (tk.StringVar, 'POCUT'),
                    'y_offset': (tk.IntVar, 15),
                    'pocut_thickness': (tk.DoubleVar, 0.040)
                })
            },
            '7_dummies': {
                'enabled': tk.BooleanVar(value=stages_config.get('7_dummies', {}).get('enabled', True)),
                'name': '7. Dummies Connections',
                'output_file': '7_dummies_connections.tcl',
                'expanded': tk.BooleanVar(value=False),
                'params': {}
            },
            '8_master': {
                'enabled': tk.BooleanVar(value=stages_config.get('8_master', {}).get('enabled', True)),
                'name': '8. Master Script',
                'output_file': '0_master_routing.tcl',
                'expanded': tk.BooleanVar(value=False),
                'params': {}
            }
        }
        
        # Utilities Configuration
        utils_config = self.saved_config.get('utilities', {})
        delete_config = utils_config.get('delete', {})
        
        self.var_delete_m1 = tk.BooleanVar(value=delete_config.get('delete_m1', False))
        self.var_delete_m2 = tk.BooleanVar(value=delete_config.get('delete_m2', True))
        self.var_delete_m3 = tk.BooleanVar(value=delete_config.get('delete_m3', True))
        self.var_delete_vias = tk.BooleanVar(value=delete_config.get('delete_vias', True))
        
        row_align_config = utils_config.get('row_alignment', {})
        self.var_window_number = tk.IntVar(value=row_align_config.get('window_number', 2))
        self.var_delay = tk.DoubleVar(value=row_align_config.get('delay', 0.1))
        
        def_extract_config = utils_config.get('def_extraction', {})
        self.var_def_output_dir = tk.StringVar(
            value=def_extract_config.get('output_dir', '/home/users/svgplayout2601yoatia/svgplayout2601yoatia_ws_14nm/Full Automation scripts/DEF_file_Input')
        )
        self.var_def_filename = tk.StringVar(value=def_extract_config.get('filename', 'DEF_file_Input'))
    
    def _load_stage_params(self, stage_id: str, param_spec: dict) -> dict:
        """Load stage parameters from saved config"""
        saved_params = self.saved_config.get('stages', {}).get(stage_id, {}).get('params', {})
        params = {}
        
        for param_name, (var_type, default_value) in param_spec.items():
            saved_value = saved_params.get(param_name, default_value)
            params[param_name] = var_type(value=saved_value)
        
        return params
    
    def save_current_config(self):
        """Save current configuration to encrypted file"""
        config = {
            'ssh': {
                'host': self.var_host.get(),
                'username': self.var_username.get(),
                'password': self.var_password.get()
            },
            'paths': {
                'input_path': self.var_input_path.get(),
                'output_path': self.var_output_path.get()
            },
            'stages': {},
            'utilities': {
                'delete': {
                    'delete_m1': self.var_delete_m1.get(),
                    'delete_m2': self.var_delete_m2.get(),
                    'delete_m3': self.var_delete_m3.get(),
                    'delete_vias': self.var_delete_vias.get()
                },
                'row_alignment': {
                    'window_number': self.var_window_number.get(),
                    'delay': self.var_delay.get()
                },
                'def_extraction': {
                    'output_dir': self.var_def_output_dir.get(),
                    'filename': self.var_def_filename.get()
                }
            }
        }
        
        # Save stage configurations
        for stage_id, stage_info in self.routing_stages.items():
            stage_config = {
                'enabled': stage_info['enabled'].get(),
                'params': {}
            }
            
            for param_name, param_var in stage_info['params'].items():
                stage_config['params'][param_name] = param_var.get()
            
            config['stages'][stage_id] = stage_config
        
        self.config_manager.save_config(config)
    
    def on_closing(self):
        """Handle window closing event"""
        self.save_current_config()
        self.root.destroy()
    
    def setup_ui(self):
        """Setup the complete UI"""
        self.root.configure(bg=self.colors['bg'])
        
        self.create_top_bar()
        
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_panel = self.create_left_panel(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_panel = self.create_right_panel(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.notification_frame = tk.Frame(self.root, bg=self.colors['success'], height=40)
        self.notification_label = tk.Label(
            self.notification_frame,
            text="",
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 10, 'bold')
        )
        self.notification_label.pack(expand=True)
    
    def create_top_bar(self):
        """Create top bar with title and generate button"""
        top_bar = tk.Frame(self.root, bg=self.colors['primary'], height=70)
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 0))
        top_bar.pack_propagate(False)
        
        title = tk.Label(
            top_bar,
            text="⚡ IC Routing Automation - SFTP 🔒",
            bg=self.colors['primary'],
            fg='white',
            font=('Segoe UI', 20, 'bold')
        )
        title.pack(side=tk.LEFT, padx=20)
        
        status_text = "✅ ORIGINAL VIA MODULE LOADED" if VIA_MODULE_LOADED else "⚠️ VIA MODULE NOT LOADED"
        status_color = 'white' if VIA_MODULE_LOADED else '#ffeb3b'
        
        status_label = tk.Label(
            top_bar,
            text=status_text,
            bg=self.colors['primary'],
            fg=status_color,
            font=('Segoe UI', 10, 'bold')
        )
        status_label.pack(side=tk.LEFT, padx=20)
        
        # Add save button
        save_btn = tk.Button(
            top_bar,
            text="🔒 Save Settings",
            bg=self.colors['white'],
            fg=self.colors['accent'],
            font=('Segoe UI', 12, 'bold'),
            cursor='hand2',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self.manual_save
        )
        save_btn.pack(side=tk.RIGHT, padx=10)
        
        generate_btn = tk.Button(
            top_bar,
            text="🚀 Generate Routing",
            bg=self.colors['white'],
            fg=self.colors['primary'],
            font=('Segoe UI', 14, 'bold'),
            cursor='hand2',
            relief=tk.FLAT,
            padx=30,
            pady=10,
            command=self.generate_all
        )
        generate_btn.pack(side=tk.RIGHT, padx=10)
    
    def manual_save(self):
        """Manually save configuration"""
        try:
            self.save_current_config()
            self.log("🔒 Settings encrypted and saved!", 'success')
            self.show_notification("🔒 Settings saved!")
        except Exception as e:
            self.log(f"✗ Failed to save settings: {str(e)}", 'error')
            self.show_notification(f"✗ {str(e)}", True)
    
    def create_left_panel(self, parent):
        """Create left configuration panel"""
        panel = tk.Frame(parent, bg=self.colors['white'], relief=tk.RAISED, bd=1)
        
        canvas = tk.Canvas(panel, bg=self.colors['white'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['white'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        # Bind mouse wheel events
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/Mac
        canvas.bind_all("<Button-4>", _on_mousewheel_linux)  # Linux scroll up
        canvas.bind_all("<Button-5>", _on_mousewheel_linux)  # Linux scroll down
        
        self.create_card(scrollable_frame, "SSH/SFTP Connection", [
            ("Host:", self.var_host),
            ("Username:", self.var_username),
            ("Password:", self.var_password, True)
        ], test_button=True)
        
        self.create_card(scrollable_frame, "Remote File Paths", [
            ("Input DEF File:", self.var_input_path),
            ("Output Directory:", self.var_output_path)
        ])
        
        stages_frame = tk.LabelFrame(
            scrollable_frame,
            text="Routing Stages",
            bg=self.colors['white'],
            fg=self.colors['text'],
            font=('Segoe UI', 11, 'bold'),
            padx=10,
            pady=10
        )
        stages_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for stage_id, stage_info in self.routing_stages.items():
            self.create_stage_card(stages_frame, stage_id, stage_info)
        
        self.create_utilities_card(scrollable_frame)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return panel
    
    def create_card(self, parent, title, fields, test_button=False):
        """Create a configuration card"""
        card = tk.LabelFrame(
            parent,
            text=title,
            bg=self.colors['white'],
            fg=self.colors['text'],
            font=('Segoe UI', 11, 'bold'),
            padx=10,
            pady=10
        )
        card.pack(fill=tk.X, padx=10, pady=10)
        
        for i, field_info in enumerate(fields):
            label_text = field_info[0]
            var = field_info[1]
            is_password = field_info[2] if len(field_info) > 2 else False
            
            label = tk.Label(
                card,
                text=label_text,
                bg=self.colors['white'],
                fg=self.colors['text'],
                font=('Segoe UI', 9)
            )
            label.grid(row=i, column=0, sticky='w', pady=5)
            
            entry = tk.Entry(
                card,
                textvariable=var,
                font=('Segoe UI', 9),
                show='*' if is_password else ''
            )
            entry.grid(row=i, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        card.columnconfigure(1, weight=1)
        
        if test_button:
            test_btn = tk.Button(
                card,
                text="Test Connection",
                bg=self.colors['accent'],
                fg='white',
                font=('Segoe UI', 9, 'bold'),
                cursor='hand2',
                command=self.test_connection
            )
            test_btn.grid(row=len(fields), column=0, columnspan=2, pady=(10, 0))
    
    def create_stage_card(self, parent, stage_id, stage_info):
        """Create collapsible stage card"""
        container = tk.Frame(parent, bg=self.colors['white'])
        container.pack(fill=tk.X, pady=5)
        
        header = tk.Frame(container, bg=self.colors['light'], cursor='hand2')
        header.pack(fill=tk.X)
        
        cb = tk.Checkbutton(
            header,
            variable=stage_info['enabled'],
            bg=self.colors['light'],
            font=('Segoe UI', 10, 'bold')
        )
        cb.pack(side=tk.LEFT, padx=5)
        
        title = tk.Label(
            header,
            text=stage_info['name'],
            bg=self.colors['light'],
            fg=self.colors['text'],
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2'
        )
        title.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=10)
        
        arrow = tk.Label(
            header,
            text="▼" if stage_info['expanded'].get() else "▶",
            bg=self.colors['light'],
            fg=self.colors['text'],
            font=('Segoe UI', 10),
            cursor='hand2'
        )
        arrow.pack(side=tk.RIGHT, padx=10)
        
        def toggle():
            stage_info['expanded'].set(not stage_info['expanded'].get())
            if stage_info['expanded'].get():
                params_frame.pack(fill=tk.X, padx=20, pady=5)
                arrow.config(text="▼")
            else:
                params_frame.pack_forget()
                arrow.config(text="▶")
        
        header.bind("<Button-1>", lambda e: toggle())
        title.bind("<Button-1>", lambda e: toggle())
        arrow.bind("<Button-1>", lambda e: toggle())
        
        params_frame = tk.Frame(container, bg=self.colors['white'])
        
        if stage_info['params']:
            row = 0
            for param_name, param_var in stage_info['params'].items():
                label_text = param_name.replace('_', ' ').title() + ":"
                
                label = tk.Label(
                    params_frame,
                    text=label_text,
                    bg=self.colors['white'],
                    fg=self.colors['text'],
                    font=('Segoe UI', 8)
                )
                label.grid(row=row, column=0, sticky='w', pady=2)
                
                if isinstance(param_var, tk.BooleanVar):
                    cb = tk.Checkbutton(
                        params_frame,
                        variable=param_var,
                        bg=self.colors['white']
                    )
                    cb.grid(row=row, column=1, sticky='w', pady=2)
                else:
                    entry = tk.Entry(
                        params_frame,
                        textvariable=param_var,
                        font=('Segoe UI', 8),
                        width=20
                    )
                    entry.grid(row=row, column=1, sticky='ew', pady=2)
                
                row += 1
            
            params_frame.columnconfigure(1, weight=1)
        
        stage_info['copy_frame'] = tk.Frame(container, bg=self.colors['white'])
    
    def create_utilities_card(self, parent):
        """Create utilities card"""
        card = tk.LabelFrame(
            parent,
            text="Utilities",
            bg=self.colors['white'],
            fg=self.colors['text'],
            font=('Segoe UI', 11, 'bold'),
            padx=10,
            pady=10
        )
        card.pack(fill=tk.X, padx=10, pady=10)
        
        delete_frame = tk.LabelFrame(
            card,
            text="Delete Routing",
            bg=self.colors['white'],
            font=('Segoe UI', 9, 'bold')
        )
        delete_frame.pack(fill=tk.X, pady=5)
        
        tk.Checkbutton(delete_frame, text="M1", variable=self.var_delete_m1, 
                      bg=self.colors['white']).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(delete_frame, text="M2", variable=self.var_delete_m2,
                      bg=self.colors['white']).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(delete_frame, text="M3", variable=self.var_delete_m3,
                      bg=self.colors['white']).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(delete_frame, text="Vias", variable=self.var_delete_vias,
                      bg=self.colors['white']).pack(side=tk.LEFT, padx=5)
        
        copy_delete_btn = tk.Button(
            delete_frame,
            text="📋 Copy Delete Code",
            bg=self.colors['accent'],
            fg='white',
            font=('Segoe UI', 9),
            cursor='hand2',
            command=self.copy_delete_code
        )
        copy_delete_btn.pack(side=tk.RIGHT, padx=5)
        
        row_frame = tk.LabelFrame(
            card,
            text="Row Alignment Generation",
            bg=self.colors['white'],
            font=('Segoe UI', 9, 'bold')
        )
        row_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(row_frame, text="Window Number:", bg=self.colors['white']).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        tk.Entry(row_frame, textvariable=self.var_window_number, width=10).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        tk.Label(row_frame, text="Delay (s):", bg=self.colors['white']).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        tk.Entry(row_frame, textvariable=self.var_delay, width=10).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        gen_align_btn = tk.Button(
            row_frame,
            text="Generate Alignment",
            bg=self.colors['accent'],
            fg='white',
            font=('Segoe UI', 9),
            cursor='hand2',
            command=self.generate_row_alignment
        )
        gen_align_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        def_frame = tk.LabelFrame(
            card,
            text="DEF Extraction",
            bg=self.colors['white'],
            font=('Segoe UI', 9, 'bold')
        )
        def_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(def_frame, text="Output Dir:", bg=self.colors['white']).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        tk.Entry(def_frame, textvariable=self.var_def_output_dir, width=40).grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        
        tk.Label(def_frame, text="Filename:", bg=self.colors['white']).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        tk.Entry(def_frame, textvariable=self.var_def_filename, width=40).grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        copy_def_btn = tk.Button(
            def_frame,
            text="📋 Copy DEF Extraction Code",
            bg=self.colors['accent'],
            fg='white',
            font=('Segoe UI', 9),
            cursor='hand2',
            command=self.copy_def_extraction
        )
        copy_def_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        def_frame.columnconfigure(1, weight=1)
    
    def create_right_panel(self, parent):
        """Create right panel with log console"""
        panel = tk.Frame(parent, bg=self.colors['dark'], relief=tk.RAISED, bd=1)
        
        header = tk.Frame(panel, bg=self.colors['dark'])
        header.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            header,
            text="📋 Execution Logs",
            bg=self.colors['dark'],
            fg='white',
            font=('Segoe UI', 12, 'bold')
        ).pack(side=tk.LEFT)
        
        clear_btn = tk.Button(
            header,
            text="Clear",
            bg=self.colors['light'],
            fg=self.colors['text'],
            font=('Segoe UI', 9),
            cursor='hand2',
            command=lambda: self.log_text.delete(1.0, tk.END)
        )
        clear_btn.pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(
            panel,
            wrap=tk.WORD,
            bg='#1e1e1e',
            fg='#d4d4d4',
            font=('Consolas', 9),
            insertbackground='white'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.log_text.tag_config('timestamp', foreground='#808080')
        self.log_text.tag_config('info', foreground='#4ec9b0')
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        
        return panel
    
    def log(self, message, level='info'):
        """Add log message to queue (thread-safe)"""
        self.log_queue.put((message, level))
    
    def process_log_queue(self):
        """Process log messages from queue"""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
                self.log_text.insert(tk.END, f"{message}\n", level)
                self.log_text.see(tk.END)
                self.log_text.update()
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_log_queue)
    
    def show_notification(self, message, is_error=False):
        """Show notification bar"""
        bg_color = self.colors['error'] if is_error else self.colors['success']
        self.notification_frame.config(bg=bg_color)
        self.notification_label.config(bg=bg_color, text=message)
        self.notification_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.root.after(3000, lambda: self.notification_frame.pack_forget())
    
    def test_connection(self):
        """Test SSH/SFTP connection"""
        def test_thread():
            try:
                self.log("Testing connection...", 'info')
                conn = SSHConnection(
                    self.var_host.get(),
                    self.var_username.get(),
                    self.var_password.get()
                )
                conn.connect()
                self.log("✓ Connection successful!", 'success')
                self.show_notification("✓ Connected")
                conn.close()
            except Exception as e:
                self.log(f"✗ Connection failed: {str(e)}", 'error')
                self.show_notification(f"✗ {str(e)}", True)
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def copy_delete_code(self):
        """Copy delete routing code to clipboard"""
        code_lines = []
        
        if self.var_delete_m3.get():
            code_lines.append("db::destroy [db::getShapes -lpp {M3 drawing} -of [ed]]")
        if self.var_delete_m2.get():
            code_lines.append("db::destroy [db::getShapes -lpp {M2 drawing} -of [ed]]")
        if self.var_delete_m1.get():
            code_lines.append("db::destroy [db::getShapes -lpp {M1 drawing} -of [ed]]")
        if self.var_delete_vias.get():
            code_lines.append("db::destroy [db::getVias -of [ed]]")
        
        if code_lines:
            code = "\n".join(code_lines)
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.log("📋 Delete code copied to clipboard", 'success')
            self.show_notification("📋 Code copied!")
        else:
            self.log("⚠ No layers selected for deletion", 'warning')
    
    def copy_def_extraction(self):
        """Copy DEF extraction code to clipboard"""
        code = f"""# Open Export DEF dialog
db::showExportDef
set dlg [gi::getDialogs dbExportDef]
gi::setActiveDialog $dlg
db::setAttr geometry -of $dlg -value 445x402+536+191
gi::setField viewName -value layout -in $dlg
gi::setField runDirectory -value "{self.var_def_output_dir.get()}" -in $dlg
gi::setField fileName -value "{self.var_def_filename.get()}" -in $dlg
gi::pressButton ok -in $dlg"""
        
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.log("📋 DEF extraction code copied to clipboard", 'success')
        self.show_notification("📋 Code copied!")
    
    def generate_row_alignment(self):
        """Generate row alignment script using alignment module"""
        def gen_thread():
            try:
                self.log("="*60, 'info')
                self.log("Generating Row Alignment script...", 'info')
                
                if not ALIGNMENT_MODULE_LOADED:
                    self.log("✗ ERROR: Alignment module not loaded", 'error')
                    self.log("Please ensure alignment.py is in the same directory as this script", 'error')
                    self.show_notification("✗ Alignment module not found!", True)
                    return
                
                conn = SSHConnection(
                    self.var_host.get(),
                    self.var_username.get(),
                    self.var_password.get()
                )
                conn.connect()
                self.log("✓ Connected to server", 'success')
                
                self.log(f"Reading DEF file from: {self.var_input_path.get()}", 'info')
                def_content = conn.read_file(self.var_input_path.get())
                self.log(f"✓ Read {len(def_content)} characters", 'success')
                
                # Use alignment module to generate TCL
                self.log("Generating alignment TCL using alignment module...", 'info')
                tcl_script = alignment.generate_alignment_tcl(
                    def_content,
                    window_num=self.var_window_number.get(),
                    delay=int(self.var_delay.get() * 1000)  # Convert seconds to milliseconds
                )
                self.log(f"✓ Generated {len(tcl_script)} characters of TCL", 'success')
                
                output_path = self.var_output_path.get() + "/row_alignment.tcl"
                conn.write_file(output_path, tcl_script)
                self.log(f"✓ Saved to: {output_path}", 'success')
                
                conn.close()
                
                # Auto-save configuration
                self.save_current_config()
                
                self.log("✓ Row Alignment generation complete!", 'success')
                self.show_notification("✓ Row Alignment generated!")
                
                # Add copy buttons in the UI thread
                self.root.after(0, lambda: self.add_alignment_copy_buttons(output_path))
                
            except Exception as e:
                self.log(f"✗ Error: {str(e)}", 'error')
                self.log(traceback.format_exc(), 'error')
                self.show_notification(f"✗ {str(e)}", True)
        
        threading.Thread(target=gen_thread, daemon=True).start()
    
    def add_alignment_copy_buttons(self, output_path):
        """Add copy source and copy content buttons for alignment in utilities section"""
        # Find the row alignment frame
        for child in self.root.winfo_children():
            self._find_and_add_buttons(child, output_path)
    
    def _find_and_add_buttons(self, widget, output_path):
        """Recursively find the row alignment frame and add buttons"""
        try:
            # Check if this widget has the right text (Row Alignment Generation)
            if hasattr(widget, 'cget'):
                try:
                    text = widget.cget('text')
                    if text == "Row Alignment Generation":
                        # Found the right frame, now add buttons if not already there
                        # Clear any existing buttons first
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Frame) and child.winfo_class() == 'Frame':
                                # Check if it's our copy button frame
                                has_copy_btn = False
                                for btn in child.winfo_children():
                                    if isinstance(btn, tk.Button):
                                        btn_text = btn.cget('text')
                                        if '📋 Copy Source' in btn_text or '📄 Copy Content' in btn_text:
                                            has_copy_btn = True
                                            break
                                if has_copy_btn:
                                    child.destroy()
                        
                        # Create new copy buttons frame
                        copy_frame = tk.Frame(widget, bg=self.colors['white'])
                        
                        def copy_source():
                            try:
                                self.root.clipboard_clear()
                                self.root.clipboard_append(output_path)
                                self.log(f"📋 Copied source path: {output_path}", 'success')
                            except Exception as e:
                                self.log(f"✗ Failed to copy source: {str(e)}", 'error')
                        
                        source_btn = tk.Button(
                            copy_frame,
                            text="📋 Copy Source",
                            bg=self.colors['secondary'],
                            fg='white',
                            font=('Segoe UI', 8),
                            cursor='hand2',
                            command=copy_source
                        )
                        source_btn.pack(side=tk.LEFT, padx=5, pady=5)
                        
                        def copy_content():
                            try:
                                conn = SSHConnection(
                                    self.var_host.get(),
                                    self.var_username.get(),
                                    self.var_password.get()
                                )
                                conn.connect()
                                content = conn.read_file(output_path)
                                conn.close()
                                
                                self.root.clipboard_clear()
                                self.root.clipboard_append(content)
                                self.log(f"📄 Copied file content from: {output_path}", 'success')
                            except Exception as e:
                                self.log(f"✗ Failed to copy content: {str(e)}", 'error')
                        
                        content_btn = tk.Button(
                            copy_frame,
                            text="📄 Copy Content",
                            bg=self.colors['secondary'],
                            fg='white',
                            font=('Segoe UI', 8),
                            cursor='hand2',
                            command=copy_content
                        )
                        content_btn.pack(side=tk.LEFT, padx=5, pady=5)
                        
                        copy_frame.grid(row=3, column=0, columnspan=2, pady=5)
                        return
                except:
                    pass
            
            # Recursively check children
            for child in widget.winfo_children():
                self._find_and_add_buttons(child, output_path)
        except:
            pass
    
    def add_copy_buttons(self, stage_id, output_path):
        """Add copy buttons for a generated stage"""
        stage_info = self.routing_stages[stage_id]
        copy_frame = stage_info['copy_frame']
        
        for widget in copy_frame.winfo_children():
            widget.destroy()
        
        def copy_source():
            source_cmd = f'source "{output_path}"'
            self.root.clipboard_clear()
            self.root.clipboard_append(source_cmd)
            self.log(f"📋 Copied source command: {source_cmd}", 'success')
        
        source_btn = tk.Button(
            copy_frame,
            text="📋 Copy Source",
            bg=self.colors['accent'],
            fg='white',
            font=('Segoe UI', 8),
            cursor='hand2',
            command=copy_source
        )
        source_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        def copy_content():
            try:
                conn = SSHConnection(
                    self.var_host.get(),
                    self.var_username.get(),
                    self.var_password.get()
                )
                conn.connect()
                content = conn.read_file(output_path)
                conn.close()
                
                self.root.clipboard_clear()
                self.root.clipboard_append(content)
                self.log(f"📄 Copied file content from: {output_path}", 'success')
            except Exception as e:
                self.log(f"✗ Failed to copy content: {str(e)}", 'error')
        
        content_btn = tk.Button(
            copy_frame,
            text="📄 Copy Content",
            bg=self.colors['secondary'],
            fg='white',
            font=('Segoe UI', 8),
            cursor='hand2',
            command=copy_content
        )
        content_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        copy_frame.pack(fill=tk.X, padx=20, pady=5)
    
    def generate_all(self):
        """Main generation function - runs all enabled stages"""
        def gen_thread():
            try:
                self.log("="*60, 'info')
                self.log("🚀 Starting IC Routing Automation", 'info')
                self.log("="*60, 'info')
                
                if not VIA_MODULE_LOADED:
                    self.log("⚠️ WARNING: Original Via module not loaded - Via12/Metal3/Pins will use fallback", 'warning')
                
                if not ALIGNMENT_MODULE_LOADED:
                    self.log("⚠️ WARNING: Alignment module not loaded - Row Alignment will not be available", 'warning')
                
                self.log("Connecting to server...", 'info')
                conn = SSHConnection(
                    self.var_host.get(),
                    self.var_username.get(),
                    self.var_password.get()
                )
                conn.connect()
                self.log(f"✓ Connected to {self.var_host.get()}", 'success')
                
                self.log(f"Reading DEF file: {self.var_input_path.get()}", 'info')
                def_content = conn.read_file(self.var_input_path.get())
                self.log(f"✓ Read {len(def_content)} characters", 'success')
                
                enabled_stages = [(k, v) for k, v in self.routing_stages.items() if v['enabled'].get()]
                self.log(f"\nEnabled stages: {len(enabled_stages)}", 'info')
                
                for i, (stage_id, stage_info) in enumerate(enabled_stages, 1):
                    self.log(f"\n[{i}/{len(enabled_stages)}] Processing: {stage_info['name']}", 'info')
                    
                    tcl_script = self.generate_stage_script(stage_id, def_content)
                    
                    output_path = self.var_output_path.get() + "/" + stage_info['output_file']
                    conn.write_file(output_path, tcl_script)
                    self.log(f"  ✓ Saved: {output_path}", 'success')
                    
                    self.root.after(0, lambda sid=stage_id, op=output_path: self.add_copy_buttons(sid, op))
                
                conn.close()
                
                # Auto-save configuration after successful generation
                self.save_current_config()
                
                self.log("\n" + "="*60, 'info')
                self.log("✅ GENERATION COMPLETE!", 'success')
                self.log("="*60, 'info')
                self.show_notification("✅ All scripts generated!")
                
            except Exception as e:
                self.log(f"\n✗ ERROR: {str(e)}", 'error')
                self.log(traceback.format_exc(), 'error')
                self.show_notification(f"✗ {str(e)}", True)
        
        threading.Thread(target=gen_thread, daemon=True).start()
    
    def generate_stage_script(self, stage_id: str, def_content: str) -> str:
        """Generate TCL script for a specific stage"""
        stage_info = self.routing_stages[stage_id]
        
        if stage_id == '1_taps':
            params = stage_info['params']
            generator = TapsAutomationGenerator(
                rect_x_min_offset=params['rect_x_min_offset'].get(),
                rect_x_max_offset=params['rect_x_max_offset'].get(),
                rect_y_min_offset=params['rect_y_min_offset'].get(),
                rect_y_max_offset=params['rect_y_max_offset'].get(),
                via_x_start_offset=params['via_x_start_offset'].get(),
                via_x_end_offset=params['via_x_end_offset'].get(),
                via_y_offset=params['via_y_offset'].get(),
                via_spacing=params['via_spacing'].get(),
                via_type=params['via_type'].get(),
                metal_layer=params['metal_layer'].get()
            )
            return generator.generate_tcl(def_content)
            
        elif stage_id == '2_metal2':
            params = stage_info['params']
            generator = Metal2Generator(
                wire_width=params['wire_width'].get(),
                metal_width=params['metal_width'].get(),
                x_min_offset=params['x_min_offset'].get(),
                metal_layer=params['metal_layer'].get()
            )
            return generator.generate_tcl(def_content)
            
        elif stage_id == '3_via12':
            # Use ORIGINAL via module
            if VIA_MODULE_LOADED and process_unified_via_generation:
                via12_tcl, _, _ = process_unified_via_generation(def_content)
                return via12_tcl
            else:
                return "# ERROR: Original via module not loaded\n# Please check the via module file"
            
        elif stage_id == '4_metal3_via23':
            # Use ORIGINAL via module
            if VIA_MODULE_LOADED and process_unified_via_generation:
                _, via23_metal3_tcl, _ = process_unified_via_generation(def_content)
                return via23_metal3_tcl
            else:
                return "# ERROR: Original via module not loaded\n# Please check the via module file"
            
        elif stage_id == '5_pins':
            # Use ORIGINAL via module
            if VIA_MODULE_LOADED and process_unified_via_generation:
                _, _, pin_tcl = process_unified_via_generation(def_content)
                return pin_tcl
            else:
                return "# ERROR: Original via module not loaded\n# Please check the via module file"
            
        elif stage_id == '6_pocut':
            params = stage_info['params']
            generator = PocutGenerator(
                metal_width=params['metal_width'].get(),
                pocut_layer=params['pocut_layer'].get(),
                y_offset=params['y_offset'].get(),
                pocut_thickness=params['pocut_thickness'].get()
            )
            return generator.generate_tcl(def_content)
            
        elif stage_id == '7_dummies':
            generator = DummiesGenerator()
            return generator.generate_tcl(def_content)
            
        elif stage_id == '8_master':
            return self.generate_master_script()
        
        return "# Unknown stage"
    
    def generate_master_script(self) -> str:
        """Generate master script that sources all enabled stages in order"""
        lines = [
            "# Master Routing Script",
            "# Auto-generated - sources all enabled routing stages in order",
            ""
        ]
        
        enabled_stages = [(k, v) for k, v in self.routing_stages.items() 
                         if v['enabled'].get() and k != '8_master']
        
        for stage_id, stage_info in enabled_stages:
            output_path = self.var_output_path.get() + "/" + stage_info['output_file']
            lines.append(f"# {stage_info['name']}")
            lines.append(f'puts "Executing: {stage_info['name']}"')
            lines.append(f'source "{output_path}"')
            lines.append(f'puts "✓ Completed: {stage_info['name']}"')
            lines.append("")
        
        lines.append('puts "✅ All routing stages completed!"')
        
        return "\n".join(lines)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ModernRoutingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()