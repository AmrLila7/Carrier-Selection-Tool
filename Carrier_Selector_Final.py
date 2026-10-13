import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import ezdxf
except ImportError:
    ezdxf = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'Carrier_HVAC_Data.db')
MAX_AMBIENT_C = 52
NOTE_TEXT = "FOR COORDINATION ONLY - VERIFY AGAINST APPROVED SUBMITTAL BEFORE SHOP DRAWINGS"

GEOMETRY_MAP = {
    '53KDMT12N-718':  {'W': 920,  'H': 210, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDMT18N-718':  {'W': 920,  'H': 270, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDMT24N-718':  {'W': 920,  'H': 270, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDMT30N-718':  {'W': 1200, 'H': 300, 'D': 865, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDMT36N-718T': {'W': 1200, 'H': 300, 'D': 865, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDHT42N-518T': {'W': 1200, 'H': 380, 'D': 625, 'return': 'back',        'pipe_side': 1},
    '53KDHT48N-518T': {'W': 1200, 'H': 380, 'D': 625, 'return': 'back',        'pipe_side': 1},
    '53KDHT60N-518T': {'W': 1200, 'H': 380, 'D': 625, 'return': 'back',        'pipe_side': 1},
    '53KDHT72N-518T': {'W': 1470, 'H': 510, 'D': 795, 'return': 'back',        'pipe_side': -1},
}

LAYERS = {
    "OUTLINE":    ("HVAC-AHU-OUTLINE", 1, "CONTINUOUS"),
    "OPENINGS":   ("HVAC-AHU-OPENINGS", 3, "CONTINUOUS"),
    "SERVICE":    ("HVAC-AHU-SERVICE", 8, "CONTINUOUS"),
    "PIPES":      ("HVAC-AHU-PIPES", 4, "CONTINUOUS"),
    "HANGERS":    ("HVAC-AHU-HANGERS", 6, "CONTINUOUS"),
    "TEXT":       ("HVAC-AHU-TEXT", 7, "CONTINUOUS"),
    "UNVERIFIED": ("HVAC-UNVERIFIED", 2, "CONTINUOUS"),
}

def fmt(value, unit=""):
    if value is None or value == "": return "N/A"
    return f"{value} {unit}".strip()

def find_match(db_path, req_cap, req_esp, req_amb, speed):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT m.id, m.evaporator_model, m.tr, m.phase, m.voltage, m.gas_pipe, m.liq_pipe, "
            "p.total_btu, p.input_w, p.cfm, p.esp, p.ambient "
            "FROM models m JOIN performance p ON m.id = p.model_id "
            "WHERE p.esp >= ? AND p.ambient >= ? AND p.speed = ?", 
            (req_esp, req_amb, speed),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    best = {}
    for r in rows:
        key = (r[11], r[10]) 
        cur_best = best.get(r[0])
        if cur_best is None or key < (cur_best[11], cur_best[10]):
            best[r[0]] = r

    candidates = sorted((r for r in best.values() if r[7] >= req_cap), key=lambda r: r[7])
    if not candidates: return None
    r = candidates[0]
    return {
        'sys_model': r[0], 'evap_model': r[1], 'tr': r[2], 'ph': r[3], 'volt': r[4],
        'gas': r[5], 'liq': r[6], 'cap': r[7], 'pwr': r[8], 'cfm': r[9],
        'table_esp': r[10], 'table_amb': r[11], 'speed': speed,
    }

def load_speeds(db_path):
    try:
        conn = sqlite3.connect(db_path)
        try:
            return [r[0] for r in conn.execute("SELECT DISTINCT speed FROM performance ORDER BY speed")]
        finally:
            conn.close()
    except Exception:
        return []

class DXFGenerator:
    @staticmethod
    def generate(model_id, data, options, save_path):
        if ezdxf is None:
            raise RuntimeError("مكتبة ezdxf غير مثبتة. نفذ: pip install ezdxf")

        doc = ezdxf.new('R2010')
        doc.header['$INSUNITS'] = 4 
        
        scale = options.get('scale', 1.0)
        
        layers = {k: v[0] for k, v in LAYERS.items()}
        for name, color, ltype in LAYERS.values():
            doc.layers.add(name=name, color=color, linetype=ltype)

        # --- Create a formal Block Definition ---
        block_name = f"BLOCK_{model_id}"
        block = doc.blocks.new(name=block_name)
        
        geo = GEOMETRY_MAP.get(model_id, {"W": 1000, "H": 300, "D": 600})
        w, h, d = geo["W"] * scale, geo["H"] * scale, geo["D"] * scale
        pipe_side = geo.get('pipe_side', 1) * (-1 if options.get('mirror') else 1)

        # 1. Detailed Geometry inside Block
        block.add_lwpolyline([(-w/2, -d/2), (w/2, -d/2), (w/2, d/2), (-w/2, d/2), (-w/2, -d/2)], 
                             dxfattribs={'layer': layers["OUTLINE"], 'color': 1})
        block.add_lwpolyline([(-w/2 + 5*scale, -d/2 + 5*scale), (w/2 - 5*scale, -d/2 + 5*scale), 
                              (w/2 - 5*scale, d/2 - 5*scale), (-w/2 + 5*scale, d/2 - 5*scale), 
                              (-w/2 + 5*scale, -d/2 + 5*scale)], 
                             dxfattribs={'layer': layers["OUTLINE"], 'color': 1})
        
        split_x = w * 0.3 
        block.add_line((split_x, -d/2), (split_x, d/2), dxfattribs={'layer': layers["OUTLINE"], 'color': 1})
        
        m_w, m_d = w * 0.2, d * 0.3
        m_x, m_y = -w*0.3, 0
        block.add_lwpolyline([(m_x-m_w/2, m_y-m_d/2), (m_x+m_w/2, m_y-m_d/2), 
                              (m_x+m_w/2, m_y+m_d/2), (m_x-m_w/2, m_y+m_d/2), (m_x-m_w/2, m_y-m_d/2)], 
                            dxfattribs={'layer': layers["OUTLINE"], 'color': 1})
        block.add_line((m_x-m_w/4, m_y-m_d/2), (m_x-m_w/4, m_y+m_d/2), dxfattribs={'layer': layers["OUTLINE"], 'color': 1})
        block.add_line((m_x+m_w/4, m_y-m_d/2), (m_x+m_w/4, m_y+m_d/2), dxfattribs={'layer': layers["OUTLINE"], 'color': 1})

        block.add_lwpolyline([(m_x-m_w/2, m_y), (-w/2, m_y), (-w/2, m_y+20*scale)], dxfattribs={'layer': layers["PIPES"]})
        
        lug_r = 3 * scale
        for lx, ly in [(-w/2+10*scale, -d/2+10*scale), (w/2-10*scale, -d/2+10*scale), 
                      (w/2-10*scale, d/2-10*scale), (-w/2+10*scale, d/2-10*scale)]:
            block.add_circle(center=(lx, ly), radius=lug_r, dxfattribs={'layer': layers["OUTLINE"], 'color': 1})

        # --- ADD ATTRIBUTES (ATTDEF) ---
        attrs_data = [
            ("MODEL", "Model", model_id, (0, d/2 + 20*scale)),
            ("CAP_TR", "Capacity TR", f"{data.get('tr', 'N/A')} TR", (0, d/2 + 40*scale)),
            ("CAP_BTU", "Capacity BTU", f"{data.get('cap', 'N/A')} BTU", (0, d/2 + 60*scale)),
            ("CFM", "Airflow CFM", f"{data.get('cfm', 'N/A')} CFM", (0, d/2 + 80*scale)),
            ("ESP", "ESP Pa", f"{options.get('esp', 'N/A')} Pa", (0, d/2 + 100*scale)),
            ("ELEC", "Electrical", f"{data.get('volt', 'N/A')}V/{data.get('ph', 'N/A')}Ph", (0, d/2 + 120*scale)),
        ]
        
        for tag, prompt, val, pos in attrs_data:
            block.add_attdef(tag, prompt, val, pos, dxfattribs={'layer': layers["TEXT"], 'height': 20*scale})

        msp = doc.modelspace()
        ref = msp.add_block_insert(block_name, (0, 0))
        for tag, prompt, val, pos in attrs_data:
            ref.add_attrib(tag, val)

        filename = f"{model_id}_block.dxf"
        save_path = os.path.join(BASE_DIR, filename)
        doc.saveas(save_path)
        return save_path

class CarrierSelectorApp:
    def __init__(self, root):
        self.root = root
        self.current_match = None
        self.last_inputs = {}
        self.root.title('Carrier ClassiCOOL R410A Selector - Pro Version')
        self.root.geometry('750x1000')
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Segoe UI', 11))
        self.style.configure('Result.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#2563eb')
        self.style.configure('Value.TLabel', font=('Segoe UI', 12))

        main_frame = ttk.Frame(root, padding='30')
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text='Carrier HVAC Selection Tool', font=('Segoe UI', 20, 'bold')).pack(pady=(0, 20))

        input_frame = ttk.LabelFrame(main_frame, text=' Design Inputs ', padding='20')
        input_frame.pack(fill=tk.X, pady=10)
        grid = ttk.Frame(input_frame)
        grid.pack(fill=tk.X)

        ttk.Label(grid, text='Required Total Capacity (Btu/hr):').grid(row=0, column=0, sticky=tk.W, pady=8, padx=5)
        self.ent_total_cap = ttk.Entry(grid)
        self.ent_total_cap.grid(row=0, column=1, sticky=tk.EW, padx=5)

        ttk.Label(grid, text='Required ESP (Pa):').grid(row=1, column=0, sticky=tk.W, pady=8, padx=5)
        self.ent_esp = ttk.Entry(grid)
        self.ent_esp.grid(row=1, column=1, sticky=tk.EW, padx=5)

        ttk.Label(grid, text='Outdoor Ambient Temp (C):').grid(row=2, column=0, sticky=tk.W, pady=8, padx=5)
        self.ent_ambient = ttk.Entry(grid)
        self.ent_ambient.grid(row=2, column=1, sticky=tk.EW, padx=5)

        ttk.Label(grid, text='Preferred Fan Speed:').grid(row=3, column=0, sticky=tk.W, pady=8, padx=5)
        speeds = load_speeds(DB_PATH) or ['High', 'Medium', 'Low']
        self.speed_var = tk.StringVar(value=speeds[0])
        ttk.Combobox(grid, textvariable=self.speed_var, values=speeds, state='readonly') \
            .grid(row=3, column=1, sticky=tk.EW, padx=5)
        grid.columnconfigure(1, weight=1)

        ttk.Button(main_frame, text='Find Matching Model', command=self.calculate_match).pack(pady=25)

        cad = ttk.LabelFrame(main_frame, text=' CAD Export Options ', padding='20')
        cad.pack(fill=tk.X, pady=10)

        self.export_level = tk.StringVar(value='L2')
        ttk.Label(cad, text='Detail Level:').grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Combobox(cad, textvariable=self.export_level, values=['L1', 'L2', 'L3'],
                     state='readonly', width=10).grid(row=0, column=1, sticky=tk.W, padx=5)

        self.mirror_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(cad, text='Mirror Piping Side', variable=self.mirror_var).grid(row=0, column=2, padx=20)

        self.ret_dir = tk.StringVar(value='back')
        ttk.Label(cad, text='Return Direction:').grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        ttk.Combobox(cad, textvariable=self.ret_dir, values=['back', 'bottom'],
                     state='readonly', width=10).grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(cad, text='(bottom: 1-3 TR only)', font=('Segoe UI', 9, 'italic')) \
            .grid(row=1, column=2, sticky=tk.W, padx=5)

        self.units_var = tk.StringVar(value='mm')
        ttk.Label(cad, text='Drawing Units:').grid(row=2, column=0, sticky=tk.W, padx=5, pady=10)
        ttk.Combobox(cad, textvariable=self.units_var, values=['mm', 'm'],
                     state='readonly', width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=10)

        self.btn_export = ttk.Button(main_frame, text='Export CAD Block (DXF)',
                                     command=self.export_cad, state='disabled')
        self.btn_export.pack(pady=10)

        self.res_container = ttk.Frame(main_frame)
        self.res_container.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.res_container, text='Enter design values and click calculate...',
                  font=('Segoe UI', 11), foreground='#64748b', justify=tk.CENTER).pack(pady=50)

    def _clear_results(self):
        for w in self.res_container.winfo_children():
            w.destroy()

    def calculate_match(self):
        try:
            req_cap = float(self.ent_total_cap.get())
            req_esp = float(self.ent_esp.get())
            req_amb = float(self.ent_ambient.get())
        except ValueError:
            messagebox.showerror('Input Error', 'Please enter valid numbers.')
            return
        if req_cap <= 0 or req_esp < 0:
            messagebox.showerror('Input Error', 'Capacity must be > 0 and ESP must be >= 0.')
            return
        if req_amb > MAX_AMBIENT_C:
            messagebox.showwarning('Out of range',
                                   f'Ambient above {MAX_AMBIENT_C} C is outside the catalog data.')
            return
        if not os.path.exists(DB_PATH):
            messagebox.showerror('DB Error', f'Database not found at {DB_PATH}')
            return

        speed = self.speed_var.get()
        try:
            match = find_match(DB_PATH, req_cap, req_esp, req_amb, speed)
        except Exception as e:
            messagebox.showerror('DB Error', str(e))
            return

        self._clear_results()
        if match:
            self.current_match = match
            self.last_inputs = {'esp': req_esp}
            self.create_result_card(match)
            self.btn_export.config(state='normal')
        else:
            self.current_match = None
            self.btn_export.config(state='disabled')
            ttk.Label(self.res_container, text='No matching model found.',
                      foreground='#dc2626', justify=tk.CENTER).pack(pady=50)

    def create_result_card(self, data):
        card = ttk.LabelFrame(self.res_container, text=' Selection Result ', padding='20')
        card.pack(fill=tk.X, pady=10)
        header = ttk.Frame(card)
        header.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header, text='Matched System Model:').pack(anchor=tk.W)
        ttk.Label(header, text=data['sys_model'], style='Result.TLabel', font=('Segoe UI', 18, 'bold')).pack(anchor=tk.W)
        ttk.Label(header, text='Matched Evaporator Model:').pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(header, text=data['evap_model'], style='Result.TLabel', font=('Segoe UI', 14, 'bold')).pack(anchor=tk.W)

        specs_f = ttk.Frame(card)
        specs_f.pack(fill=tk.X, pady=10)
        specs = [
            ('Nominal Capacity', fmt(data['tr'], 'TR')),
            ('Actual Capacity', fmt(data['cap'], 'Btu/hr')),
            ('Air Flow', fmt(data['cfm'], 'CFM')),
            ('Input Power', fmt(data['pwr'], 'W')),
            ('Power Supply', f"{data['volt']} / {data['ph']}"),
            ('Gas Pipe', f"{data['gas']} in"),
            ('Liquid Pipe', f"{data['liq']} in"),
            ('Fan Speed', data['speed']),
            ('Table ESP used', fmt(data['table_esp'], 'Pa')),
            ('Table Ambient used', fmt(data['table_amb'], 'C')),
        ]
        for i, (label, value) in enumerate(specs):
            ttk.Label(specs_f, text=label + ':', font=('Segoe UI', 10, 'bold')) \
                .grid(row=i // 2, column=(i % 2) * 2, sticky=tk.W, pady=5, padx=(0, 10))
            ttk.Label(specs_f, text=value, style='Value.TLabel') \
                .grid(row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, pady=5)
        specs_f.columnconfigure(1, weight=1)
        specs_f.columnconfigure(3, weight=1)
        ttk.Label(card, text='Values are taken from the nearest catalog row at or above the design point '
                             '(tolerance +-5%).',
                  foreground='#16a34a', font=('Segoe UI', 10, 'italic'), wraplength=620) \
            .pack(pady=(20, 0), anchor=tk.W)

    def export_cad(self):
        if not self.current_match:
            return
        options = {
            'level': self.export_level.get(),
            'mirror': self.mirror_var.get(),
            'return_dir': self.ret_dir.get(),
            'units': self.units_var.get(),
            'esp': self.last_inputs.get('esp'),
            'scale': 0.001 if self.units_var.get() == 'm' else 1.0
        }
        model_id = self.current_match['sys_model']
        path = filedialog.asksaveasfilename(
            defaultextension='.dxf', filetypes=[('DXF', '*.dxf')],
            initialdir=BASE_DIR, initialfile=f'{model_id}_block.dxf')
        if not path:
            return
        try:
            DXFGenerator.generate(model_id, self.current_match, options, path)
            messagebox.showinfo('Export Success', f'CAD Block saved to:\\n{path}')
        except Exception as e:
            import traceback
            messagebox.showerror('Export Error', f'{e}\\n\\n{traceback.format_exc()}')

if __name__ == '__main__':
    root = tk.Tk()
    CarrierSelectorApp(root)
    root.mainloop()
