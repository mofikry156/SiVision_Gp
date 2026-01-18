import re
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set

# ==============================================================================
#                               CONFIGURATION
# ==============================================================================
BASE_DIR = r"C:\Users\TEBA\Desktop\Neat Routing Automation"
INPUT_DEF_FILE = os.path.join(BASE_DIR, "DEF_file_Input.txt")
OUTPUT_DIR = BASE_DIR

FILENAMES = {
    "metal2": "1 metal2 output .tcl",
    "via12": "2 via 12 .tcl",
    "dummy": "3 dummies connections output.tcl",
    "via23": "4_via23 output.tcl",
    "master": "0_master_run_all.tcl"
}

WINDOW_NUMBER = 2

# ==============================================================================
#                          MODULE 1: METAL 2 PLACEMENT
# ==============================================================================
class Metal2PlacementGenerator:
    def __init__(self, design_name="hello_again", cell_name="automationtesting"):
        self.metal_width = 1.7
        self.window_number = WINDOW_NUMBER
        self.design_name = design_name
        self.cell_name = cell_name
        self.metal_layer = "M2"

    def parse_components(self, def_content):
        components = []
        comp_section = re.search(r'COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS', def_content, re.DOTALL)
        if not comp_section: return components
        
        for line in comp_section.group(1).strip().split('\n'):
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

    def generate(self, def_content):
        components = self.parse_components(def_content)
        filtered_comps = [c for c in components if 'tap' not in c['type'].lower()]
        
        rows = {}
        for comp in filtered_comps:
            if comp['y'] not in rows: rows[comp['y']] = []
            rows[comp['y']].append(comp)
        sorted_rows = dict(sorted(rows.items()))

        if not filtered_comps: return "# No components for Metal2"
        x_coords = [c['x'] for c in filtered_comps]
        x_start = min(x_coords) / 1000.0
        x_end = (max(x_coords) + 300) / 1000.0

        tcl = []
        tcl.append("# MODULE 1: METAL 2 PLACEMENT")
        tcl.append(f"db::setAttr selectable -of [de::getLPPs -from [de::getContexts -window {self.window_number}]] -value false")
        tcl.append(f"de::setActiveLPP [de::getLPPs {{{self.metal_layer} drawing}} -from [oa::DesignFind {self.design_name} {self.cell_name} layout]]")
        
        created_wires = set()
        for y_coord, row_comps in sorted_rows.items():
            orientation = row_comps[0]['orientation']
            if orientation in ['N', 'FN']:
                offsets = [146, 50, 308, 402, 496]
            elif orientation in ['S', 'FS']:
                offsets = [158, 253, 508, 412, 63]
            else: continue

            y_base = y_coord / 1000.0
            for offset in offsets:
                y_wire = y_base + (offset / 1000.0)
                wire_key = (round(x_start, 6), round(y_wire, 6), round(x_end, 6))
                if wire_key in created_wires: continue
                created_wires.add(wire_key)
                tcl.append("ile::createInterconnect")
                tcl.append(f"de::addPoint [list {x_start:.6f} {y_wire:.6f}] -context [db::getNext [de::getContexts -window {self.window_number}]]")
                tcl.append(f"de::completeShape [list {x_end:.6f} {y_wire:.6f}] -context [db::getNext [de::getContexts -window {self.window_number}]]")
        
        return "\n".join(tcl)

# ==============================================================================
#                          MODULE 2: VIA 12 GENERATION
# ==============================================================================
@dataclass
class V12Component:
    name: str; cell_type: str; x: float; y: float; orientation: str

@dataclass
class V12NetConnection:
    net_name: str; component: str; pin: str

class Via12Generator:
    def __init__(self):
        self.ROW_HEIGHT = 568
        self.DUPLICATE_GATE_VIAS = True
        self.GATE_OFFSET_X = 74
        self.OFFSET_MAP = {
            'N': {'D': {1: (184, 319), 2: (184, 402)}, 'S': (257, 502), 'G': {1: (147, 60), 2: (147, 146)}},
            'FN': {'D': {1: (184, 319), 2: (184, 402)}, 'S': (110, 502), 'G': {1: (147, 60), 2: (147, 146)}},
            'FS': {'D': {1: (184, 249), 2: (184, 148)}, 'S': (110, 64), 'G': {1: (147, 508), 2: (147, 422)}},
            'S': {'D': {1: (184, 249), 2: (184, 148)}, 'S': (257, 64), 'G': {1: (147, 508), 2: (147, 422)}}
        }

    def parse(self, def_content):
        components = {}
        nets = {}
        for match in re.finditer(r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:FIXED|PLACED)\s+\(\s*(\d+)\s+(\d+)\s*\)\s+(\S+)', def_content):
            name, ctype, x, y, ori = match.groups()
            components[name] = V12Component(name, ctype, int(x)/1000.0, int(y)/1000.0, ori)

        nets_match = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', def_content, re.DOTALL)
        if nets_match:
            for net_match in re.finditer(r'-\s+(\S+)(.*?)(?=\n\s*-|\Z)', nets_match.group(1), re.DOTALL):
                net_name, net_body = net_match.groups()
                conns = []
                for pin_match in re.finditer(r'\(\s*(\S+)\s+(\S+)\s*\)', net_body):
                    if pin_match.group(1) != 'PIN':
                        conns.append(V12NetConnection(net_name, pin_match.group(1), pin_match.group(2)))
                if conns: nets[net_name] = conns
        return components, nets

    def generate(self, def_content):
        comps, nets = self.parse(def_content)
        tcl = []
        tcl.append("ile::createVia")
        tcl.append(f"gi::setField {{viaAuto}} -value {{true}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {WINDOW_NUMBER}]]")
        tcl.append("# MODULE 2: VIA 12 GENERATION")

        net_options = {}
        # Fixed KeyError: 'S'/'B' using nested defaultdict
        rows = defaultdict(lambda: defaultdict(set))
        
        for c in comps.values():
            row = int(c.y * 1000 / self.ROW_HEIGHT)
            for net_name, conns in nets.items():
                for conn in conns:
                    if conn.component == c.name:
                        if conn.pin == 'B': continue # Skipping 'B' pins
                        if 'dummy' not in c.name.lower():
                            rows[row][conn.pin].add(net_name)

        for row, pin_dict in rows.items():
            for pin_type, pin_nets in pin_dict.items():
                sorted_nets = sorted(list(pin_nets))
                for idx, net in enumerate(sorted_nets):
                    net_options[(net, row, pin_type)] = 1 if idx == 0 else 2

        for net_name, conns in sorted(nets.items()):
            tcl.append(f"\n# Net: {net_name}")
            for conn in conns:
                if conn.component not in comps: continue
                comp = comps[conn.component]
                if conn.pin == 'B' or ('dummy' in comp.name.lower() and conn.pin in ['G', 'D']):
                    continue

                row = int(comp.y * 1000 / self.ROW_HEIGHT)
                opt = net_options.get((net_name, row, conn.pin), 1)
                
                offsets_data = self.OFFSET_MAP.get(comp.orientation, {}).get(conn.pin)
                if not offsets_data: continue

                if isinstance(offsets_data, dict):
                    off_x, off_y = offsets_data.get(opt, offsets_data[1])
                else:
                    off_x, off_y = offsets_data
                
                final_x, final_y = comp.x + (off_x / 1000.0), comp.y + (off_y / 1000.0)
                tcl.append(f"ile::createVia\nde::addPoint {{{final_x:.3f} {final_y:.3f}}} -context [db::getNext [de::getContexts -window {WINDOW_NUMBER}]]\nafter 1")
                
                if conn.pin == 'G' and self.DUPLICATE_GATE_VIAS:
                    dup_x = final_x + (self.GATE_OFFSET_X / 1000.0)
                    tcl.append(f"ile::createVia\nde::addPoint {{{dup_x:.3f} {final_y:.3f}}} -context [db::getNext [de::getContexts -window {WINDOW_NUMBER}]]\nafter 1")

        return "\n".join(tcl)

# ==============================================================================
#                          MODULE 3: DUMMY CONNECTIONS
# ==============================================================================
class DummyConnectionGenerator:
    def generate(self, def_content):
        net_map = {} 
        nets_match = re.search(r'NETS\s+\d+\s*;(.*?)END NETS', def_content, re.DOTALL)
        if nets_match:
            for n_match in re.finditer(r'-\s+(\S+)(.*?)(?=\n\s*-|\Z)', nets_match.group(1), re.DOTALL):
                net, body = n_match.groups()
                for p_match in re.finditer(r'\(\s*(\S+)\s+(\S+)\s*\)', body):
                    cname, pin = p_match.groups()
                    if cname not in net_map: net_map[cname] = {}
                    net_map[cname][pin] = net

        tcl = ["# MODULE 3: DUMMY CONNECTIONS"]
        comp_pattern = r'-\s+(\S+)\s+(\S+)\s+\+\s+(?:PLACED|FIXED)\s+\(\s*(\d+)\s+(\d+)\s*\)\s+(\w+)'
        for match in re.finditer(comp_pattern, def_content):
            name, _, x_str, y_str, ori = match.groups()
            if 'dummy' in name.lower():
                x, y = int(x_str) / 1000.0, int(y_str) / 1000.0
                net = net_map.get(name, {}).get('S', 'VSS')
                rects = []
                if ori in ['N', 'FN']:
                    rects = [(0.093, 0.543, 0.275, 0.509), (0.130, 0.198, 0.239, 0.163), (0.168, 0.543, 0.201, 0.180)]
                elif ori in ['S', 'FS']:
                    rects = [(0.093, 0.025, 0.275, 0.059), (0.130, 0.370, 0.239, 0.405), (0.168, 0.025, 0.201, 0.388)]
                
                for r in rects:
                    x1, y1, x2, y2 = x+r[0], y+r[1], x+r[2], y+r[3]
                    tcl.append(f'le::createRectangle {{{{{x1:.3f} {y1:.3f}}} {{{x2:.3f} {y2:.3f}}}}} -design [ed] -lpp {{M1 drawing}} -net {net}')
        return "\n".join(tcl)

# ==============================================================================
#                          MODULE 4: VIA 23 GENERATION
# ==============================================================================
class Via23Generator:
    def __init__(self):
        self.VIA_NAME = "VIA23"
        self.X_OFFSET_MICRONS = 0.100  # 100nm offset from device boundaries
        self.RECT_OFFSET_X_MICRONS = 0.040  # 40nm offset for rectangle width
        self.RECT_OFFSET_Y_SINGLE_MICRONS = 0.500  # 500nm offset for single via height

    def parse_device_positions(self, def_content):
        """
        Parse DEF file and extract X positions of pfet and nfet devices.
        Returns (x_min, x_max) in microns, or (None, None) if no devices found.
        """
        x_positions = []
        
        # Find COMPONENTS section
        components_match = re.search(r'COMPONENTS.*?END COMPONENTS', def_content, re.DOTALL)
        
        if not components_match:
            return None, None
        
        components_section = components_match.group(0)
        
        # Pattern to match component lines with pfet or nfet (case-insensitive) and their positions
        # Example: - instance_name pfet + FIXED ( x y ) orientation
        component_pattern = r'-\s+\S+\s+(pfet|nfet|PFET|NFET)\s+.*?\+\s+(FIXED|PLACED)\s+\(\s*(\d+)\s+\d+\s*\)'
        
        matches = re.finditer(component_pattern, components_section, re.IGNORECASE)
        
        for match in matches:
            x_coord = int(match.group(3))  # X coordinate in nanometers
            x_positions.append(x_coord)
        
        if not x_positions:
            return None, None
        
        # Convert to microns
        x_min_microns = min(x_positions) / 1000.0
        x_max_microns = max(x_positions) / 1000.0
        
        return x_min_microns, x_max_microns

    def calculate_x_parameters(self, x_min, x_max, num_nets):
        """
        Calculate X_START and X_STEP based on device positions.
        
        Args:
            x_min: Minimum X position of devices in microns
            x_max: Maximum X position of devices in microns
            num_nets: Number of different nets
        
        Returns:
            (x_start, x_step) tuple
        """
        if x_min is None or x_max is None or num_nets == 0:
            return None, None
        
        # X_START = min X + 100nm offset
        x_start = x_min + self.X_OFFSET_MICRONS
        
        # X_END = max X - 100nm offset
        x_end = x_max - self.X_OFFSET_MICRONS
        
        # X_STEP = (X_END - X_START) / (number of nets - 1)
        # If only one net, step doesn't matter (can be 0)
        if num_nets == 1:
            x_step = 0.0
        else:
            x_step = (x_end - x_start) / (num_nets - 1)
        
        return x_start, x_step

    def generate(self, def_content):
        tcl = ["# MODULE 4: VIA 23 GENERATION"]
        
        # Parse device positions to calculate X parameters
        x_min, x_max = self.parse_device_positions(def_content)
        
        if x_min is None or x_max is None:
            print("   [WARNING] No pfet/nfet devices found. Using default X parameters.")
            x_start, x_step = 3.900, 0.350  # Fallback to defaults
        else:
            # Parse routes first to get net count
            routes = defaultdict(set)
            for section in re.findall(r'(?:SPECIALNETS|NETS).*?END (?:SPECIALNETS|NETS)', def_content, re.DOTALL):
                blocks = re.split(r'\n-\s+', section)
                for block in blocks:
                    if not block.strip(): continue
                    net_match = re.match(r'(\S+)', block.strip())
                    if net_match:
                        net_name = net_match.group(1)
                        for m2 in re.finditer(r'M2\s+\d+\s+\(\s*(\d+)\s+(\d+)\s*\)', block):
                            routes[net_name].add(int(m2.group(2)))
            
            num_nets = len([k for k, v in routes.items() if v])
            x_start, x_step = self.calculate_x_parameters(x_min, x_max, num_nets)
            
            if x_start is None or x_step is None:
                print("   [WARNING] Could not calculate X parameters. Using defaults.")
                x_start, x_step = 3.900, 0.350
            else:
                x_end = x_max - self.X_OFFSET_MICRONS
                print(f"   [INFO] Calculated X_START={x_start:.3f}, X_END={x_end:.3f}, X_STEP={x_step:.3f}")
        
        tcl.append(f"# X_START: {x_start:.3f} microns, X_STEP: {x_step:.3f} microns")
        tcl.append("ile::createVia")
        tcl.append(f"gi::setField {{viaAuto}} -value {{false}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {WINDOW_NUMBER}]]")
        tcl.append(f"gi::setField {{viaDefName}} -value {{{self.VIA_NAME}}} -in [gi::getToolbars {{deCommandOptions}} -from [gi::getWindows {WINDOW_NUMBER}]]")
        
        routes = defaultdict(set)
        for section in re.findall(r'(?:SPECIALNETS|NETS).*?END (?:SPECIALNETS|NETS)', def_content, re.DOTALL):
            blocks = re.split(r'\n-\s+', section)
            for block in blocks:
                if not block.strip(): continue
                net_match = re.match(r'(\S+)', block.strip())
                if net_match:
                    net_name = net_match.group(1)
                    for m2 in re.finditer(r'M2\s+\d+\s+\(\s*(\d+)\s+(\d+)\s*\)', block):
                        routes[net_name].add(int(m2.group(2)))

        sorted_nets = sorted([(k, sorted(list(v))) for k, v in routes.items() if v])
        for idx, (net_name, y_coords) in enumerate(sorted_nets):
            x_pos = x_start + (idx * x_step)
            for y_nm in y_coords:
                tcl.append(f"ile::createVia\nde::addPoint {{{x_pos:.3f} {y_nm/1000.0:.3f}}} -context [db::getNext [de::getContexts -window {WINDOW_NUMBER}]]")
            if y_coords:
                y_min, y_max = min(y_coords)/1000.0, max(y_coords)/1000.0
                if len(y_coords) == 1: y_max = y_min + self.RECT_OFFSET_Y_SINGLE_MICRONS
                x_rect_min = x_pos - self.RECT_OFFSET_X_MICRONS
                x_rect_max = x_pos + self.RECT_OFFSET_X_MICRONS
                tcl.append(f"le::createRectangle {{{{{x_rect_min:.3f} {y_min:.3f}}} {{{x_rect_max:.3f} {y_max:.3f}}}}} -design [ed] -lpp {{M3 drawing}} -net {net_name}")
        return "\n".join(tcl)

# ==============================================================================
#                               MAIN EXECUTION
# ==============================================================================
def main():
    print("="*60)
    print("      VLSI LAYOUT AUTOMATION - CENTRALIZED GENERATOR")
    print("="*60)
    try:
        with open(INPUT_DEF_FILE, 'r') as f: def_content = f.read()
        print(f"[OK] Read DEF file ({len(def_content)} bytes)")
    except Exception as e:
        print(f"[ERROR] {e}"); return

    generators = [
        ("Metal 2 Placement", Metal2PlacementGenerator(), FILENAMES["metal2"]),
        ("Via 12 Logic",      Via12Generator(),           FILENAMES["via12"]),
        ("Dummy Connects",    DummyConnectionGenerator(), FILENAMES["dummy"]),
        ("Via 23 Logic",      Via23Generator(),           FILENAMES["via23"]),
    ]

    generated_files = []
    for label, gen, fname in generators:
        print(f"\n>> Running: {label}...")
        try:
            tcl_content = gen.generate(def_content)
            out_path = os.path.join(OUTPUT_DIR, fname)
            with open(out_path, 'w') as f: f.write(tcl_content)
            print(f"   [Success] Written to: {fname}")
            generated_files.append(out_path)
        except Exception as e:
            print(f"   [FAILED] {label}: {e}")
            import traceback; traceback.print_exc()

    if generated_files:
        master_path = os.path.join(OUTPUT_DIR, FILENAMES["master"])
        with open(master_path, 'w') as f:
            f.write("# Master Execution Script\n")
            for path in generated_files:
                clean_path = path.replace('\\', '/')
                f.write(f"source \"{clean_path}\"\n")
                f.write("puts \"Completed: " + os.path.basename(path) + "\"\n")
        
        print(f"\n[DONE] Master script created: {FILENAMES['master']}")

if __name__ == "__main__":
    main()