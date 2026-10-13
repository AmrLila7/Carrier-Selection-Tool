import sys
import os

# Absolute path to project root for absolute stability
PROJECT_ROOT = r"D:\شغل\CAC 6_October\Tools\Carrier_Selection_Tool"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


import sys
import os

# Project root is 3 levels up from this file: src/carrier_tool/main.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from src.carrier_tool.logic import find_match, fmt, MAX_AMBIENT_C
from src.carrier_tool.database import load_speeds, get_suggested_capacities, get_suggested_esp
from src.carrier_tool.exporter import DXFGenerator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "Carrier_HVAC_Data.db")

class ModernCarrierApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Carrier ClassiCOOL Engineering Suite')
        self.root.geometry('1250x900')
        
        self.palette = {
            'bg_main': '#F8FAFC',        
            'bg_sidebar': '#0F172A',    
            'bg_card': '#FFFFFF',       
            'text_main': '#1E293B',     
            'text_muted': '#64748B',    
            'text_on_dark': '#F1F5F9',  
            'primary': '#2563EB',       
            'primary_hover': '#1D4ED8', 
            'accent': '#3B82F6',        
            'success': '#10B981',       
            'error': '#EF4444',         
            'border': '#E2E8F0',        
        }
        
        self.root.configure(bg=self.palette['bg_main'])
        
        # Persistence State
        self.state = {
            'capacity': '',
            'esp': '',
            'ambient': '',
            'series': 'Any',
            'speed': '',
            'unit': 'Btu/hr'
        }
        
        self.current_match = None
        self.last_inputs = {}
        
        self.setup_styles()
        self.build_layout()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.palette['bg_main'])
        self.style.configure('Card.TFrame', background=self.palette['bg_card'], relief='flat')
        self.style.configure('Sidebar.TFrame', background=self.palette['bg_sidebar'])
        self.style.configure('TLabel', background=self.palette['bg_main'], foreground=self.palette['text_main'], font=('Segoe UI', 11))
        self.style.configure('Sidebar.TLabel', background=self.palette['bg_sidebar'], foreground=self.palette['text_on_dark'], font=('Segoe UI', 14, 'bold'))
        self.style.configure('Header.TLabel', background=self.palette['bg_main'], foreground=self.palette['text_main'], font=('Segoe UI', 26, 'bold'))
        self.style.configure('Result.TLabel', background=self.palette['bg_card'], foreground=self.palette['primary'], font=('Segoe UI', 18, 'bold'))
        self.style.configure('Value.TLabel', background=self.palette['bg_card'], foreground=self.palette['text_main'], font=('Segoe UI', 11))
        self.style.configure('Muted.TLabel', background=self.palette['bg_card'], foreground=self.palette['text_muted'], font=('Segoe UI', 10))
        self.style.configure('TEntry', fieldbackground=self.palette['bg_card'], bordercolor=self.palette['border'])
        self.style.configure('TCombobox', fieldbackground=self.palette['bg_card'], bordercolor=self.palette['border'])

    def build_layout(self):
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.sidebar = ttk.Frame(self.main_container, style='Sidebar.TFrame', width=260)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        brand_frame = tk.Frame(self.sidebar, bg=self.palette['bg_sidebar'])
        brand_frame.pack(pady=50, padx=20, fill=tk.X)
        ttk.Label(brand_frame, text='CARRIER', style='Sidebar.TLabel', justify=tk.CENTER).pack()
        ttk.Label(brand_frame, text='Engineering Suite', foreground=self.palette['text_muted'], background=self.palette['bg_sidebar'], font=('Segoe UI', 10)).pack()
        
        nav_container = tk.Frame(self.sidebar, bg=self.palette['bg_sidebar'])
        nav_container.pack(fill=tk.X, padx=15)

        nav_items = [
            ('Selection Tool', self.show_selection),
            ('Installation Guide', self.show_guide),
            ('Export Settings', self.show_settings),
        ]
        
        for text, cmd in nav_items:
            btn = tk.Button(nav_container, text=text, command=cmd, bg=self.palette['bg_sidebar'], fg=self.palette['text_on_dark'], 
                            font=('Segoe UI', 11), bd=0, padx=15, pady=12, anchor='w', 
                            activebackground=self.palette['primary'], activeforeground='white', cursor='hand2')
            btn.pack(fill=tk.X, pady=4)
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.palette['primary']))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=self.palette['bg_sidebar']))

        self.content_area = ttk.Frame(self.main_container)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.current_view = None
        self.show_selection()

    def clear_content(self):
        if self.current_view:
            self.current_view.destroy()

    def show_selection(self):
        self.clear_content()
        self.current_view = ttk.Frame(self.content_area, padding='40')
        self.current_view.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.current_view, text='Unit Selection Dashboard', style='Header.TLabel').pack(anchor=tk.W, pady=(0, 30))

        # --- TABS FOR SEARCH MODES ---
        self.tab_control = ttk.Notebook(self.current_view)
        self.tab_control.pack(fill=tk.BOTH, expand=True)

        self.tab_standard = ttk.Frame(self.tab_control)
        self.tab_advanced = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_standard, text=' Standard Selection ')
        self.tab_control.add(self.tab_advanced, text=' Advanced (Sensible Heat) ')

        self.build_standard_tab()
        self.build_advanced_tab()

    def build_standard_tab(self):
        # Input Card for Standard Tab
        input_card = ttk.Frame(self.tab_standard, style='Card.TFrame', padding='30')
        input_card.pack(fill=tk.X, pady=20)
        
        grid = ttk.Frame(input_card, style='Card.TFrame')
        grid.pack(fill=tk.X)

        # Capacity row
        cap_frame = ttk.Frame(grid, style='Card.TFrame')
        cap_frame.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=12)
        ttk.Label(cap_frame, text='Required Capacity:', style='Value.TLabel', background=self.palette['bg_card']).pack(side=tk.LEFT, padx=10)
        self.unit_var = tk.StringVar(value=self.state['unit'])
        unit_combo = ttk.Combobox(cap_frame, textvariable=self.unit_var, values=['Btu/hr', 'TR'], state='readonly', width=10)
        unit_combo.pack(side=tk.LEFT, padx=5)
        unit_combo.bind("<<ComboboxSelected>>", self.on_unit_change)
        self.ent_total_cap = ttk.Entry(cap_frame, font=('Segoe UI', 12))
        self.ent_total_cap.insert(0, self.state['capacity'])
        self.ent_total_cap.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.sug_var = tk.StringVar()
        self.sug_combo = ttk.Combobox(cap_frame, textvariable=self.sug_var, state='readonly', width=10)
        self.sug_combo.pack(side=tk.LEFT, padx=5)
        self.sug_combo.bind("<<ComboboxSelected>>", self.on_suggestion_select)
        ttk.Label(cap_frame, text="Suggestions", style='Muted.TLabel', background=self.palette['bg_card'], font=('Segoe UI', 8)).pack(side=tk.LEFT)
        self.update_capacity_suggestions()

        # ESP row
        esp_frame = ttk.Frame(grid, style='Card.TFrame')
        esp_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=12)
        ttk.Label(esp_frame, text='Required ESP (Pa):', style='Value.TLabel', background=self.palette['bg_card']).pack(side=tk.LEFT, padx=10)
        self.ent_esp = ttk.Entry(esp_frame, font=('Segoe UI', 12))
        self.ent_esp.insert(0, self.state['esp'])
        self.ent_esp.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.esp_sug_var = tk.StringVar()
        self.esp_sug_combo = ttk.Combobox(esp_frame, textvariable=self.esp_sug_var, state='readonly', width=10)
        self.esp_sug_combo.pack(side=tk.LEFT, padx=5)
        self.esp_sug_combo.bind("<<ComboboxSelected>>", self.on_esp_suggestion_select)
        ttk.Label(esp_frame, text="Suggestions", style='Muted.TLabel', background=self.palette['bg_card'], font=('Segoe UI', 8)).pack(side=tk.LEFT)
        self.update_esp_suggestions()

        # Ambient row
        ttk.Label(grid, text='Outdoor Ambient Temp (C):', style='Value.TLabel', background=self.palette['bg_card']).grid(row=2, column=0, sticky=tk.W, pady=12, padx=10)
        self.ent_ambient = ttk.Entry(grid, font=('Segoe UI', 12))
        self.ent_ambient.insert(0, self.state['ambient'])
        self.ent_ambient.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=12)

        # Series row
        ttk.Label(grid, text='Unit Series:', style='Value.TLabel', background=self.palette['bg_card']).grid(row=3, column=0, sticky=tk.W, pady=12, padx=10)
        self.series_var = tk.StringVar(value=self.state['series'])
        self.combo_series = ttk.Combobox(grid, textvariable=self.series_var, values=['Any', 'KDMT', 'QDMT'], state='readonly', font=('Segoe UI', 12))
        self.combo_series.grid(row=3, column=1, sticky=tk.EW, padx=10, pady=12)

        # Speed row
        ttk.Label(grid, text='Fan Speed:', style='Value.TLabel', background=self.palette['bg_card']).grid(row=4, column=0, sticky=tk.W, pady=12, padx=10)
        speeds = load_speeds(DB_PATH) or ['High', 'Med', 'Low']
        self.speed_var = tk.StringVar(value=self.state['speed'] if self.state['speed'] else speeds[0])
        self.combo_speed = ttk.Combobox(grid, textvariable=self.speed_var, values=speeds, state='readonly', font=('Segoe UI', 12))
        self.combo_speed.grid(row=4, column=1, sticky=tk.EW, padx=10, pady=12)
        
        grid.columnconfigure(1, weight=1)

        self.btn_calc = tk.Button(input_card, text='Find Matching Model', command=self.calculate_match, 
                                  bg=self.palette['primary'], fg='white', font=('Segoe UI', 12, 'bold'), 
                                  bd=0, padx=40, pady=15, cursor='hand2')
        self.btn_calc.pack(pady=25)
        self.btn_calc.bind('<Enter>', lambda e: self.btn_calc.configure(bg=self.palette['primary_hover']))
        self.btn_calc.bind('<Leave>', lambda e: self.btn_calc.configure(bg=self.palette['primary']))

        # Results for Standard Tab
        self.res_canvas = tk.Canvas(self.tab_standard, bg=self.palette['bg_main'], highlightthickness=0)
        self.res_scrollbar = ttk.Scrollbar(self.tab_standard, orient="vertical", command=self.res_canvas.yview)
        self.res_container = ttk.Frame(self.res_canvas, style='TFrame')
        self.res_container.bind("<Configure>", lambda e: self.res_canvas.configure(scrollregion=self.res_canvas.bbox("all")))
        self.res_canvas.create_window((0, 0), window=self.res_container, anchor="nw")
        self.res_canvas.configure(yscrollcommand=self.res_scrollbar.set)
        self.res_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.res_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.placeholder = ttk.Label(self.res_container, text='Ready for design inputs...', 
                                     font=('Segoe UI', 12), foreground=self.palette['text_muted'])
        self.placeholder.pack(pady=60)

    def build_advanced_tab(self):
        # Advanced Tab (Sensible Heat)
        input_card = ttk.Frame(self.tab_advanced, style='Card.TFrame', padding='30')
        input_card.pack(fill=tk.X, pady=20)
        
        grid = ttk.Frame(input_card, style='Card.TFrame')
        grid.pack(fill=tk.X)
        
        ttk.Label(grid, text='Sensible Capacity (Btu/hr):', style='Value.TLabel', background=self.palette['bg_card']).grid(row=0, column=0, sticky=tk.W, pady=12, padx=10)
        self.ent_sensible = ttk.Entry(grid, font=('Segoe UI', 12))
        self.ent_sensible.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=12)
        
        ttk.Label(grid, text='Required ESP (Pa):', style='Value.TLabel', background=self.palette['bg_card']).grid(row=1, column=0, sticky=tk.W, pady=12, padx=10)
        self.ent_esp_adv = ttk.Entry(grid, font=('Segoe UI', 12))
        self.ent_esp_adv.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=12)
        
        grid.columnconfigure(1, weight=1)
        
        # Advanced Search Button (Logic would be implemented similarly to calculate_match but using sensible_btu)
        self.btn_calc_adv = tk.Button(input_card, text='Find Sensible Match', command=lambda: messagebox.showinfo("Advanced Mode", "Sensible Heat search is in development."), 
                                      bg=self.palette['primary'], fg='white', font=('Segoe UI', 12, 'bold'), 
                                      bd=0, padx=40, pady=15, cursor='hand2')
        self.btn_calc_adv.pack(pady=25)

    def update_capacity_suggestions(self):
        suggs = get_suggested_capacities(DB_PATH)
        unit = self.unit_var.get()
        if unit == 'TR':
            values = suggs
        else:
            values = [f"{float(tr)*12000:.0f}" for tr in suggs]
        self.sug_combo['values'] = values

    def update_esp_suggestions(self):
        suggs = get_suggested_esp(DB_PATH)
        self.esp_sug_combo['values'] = suggs

    def on_unit_change(self, event):
        unit = self.unit_var.get()
        current_val = self.ent_total_cap.get()
        try:
            val = float(current_val)
            if unit == 'TR' and self.state['unit'] == 'Btu/hr':
                new_val = val / 12000
            elif unit == 'Btu/hr' and self.state['unit'] == 'TR':
                new_val = val * 12000
            else:
                new_val = val
            self.ent_total_cap.delete(0, tk.END)
            self.ent_total_cap.insert(0, f"{new_val:.2f}")
        except ValueError:
            pass
        self.state['unit'] = unit
        self.update_capacity_suggestions()

    def on_suggestion_select(self, event):
        val = self.sug_var.get()
        self.ent_total_cap.delete(0, tk.END)
        self.ent_total_cap.insert(0, val)

    def on_esp_suggestion_select(self, event):
        val = self.esp_sug_var.get()
        self.ent_esp.delete(0, tk.END)
        self.ent_esp.insert(0, val)

    def save_state(self):
        self.state['capacity'] = self.ent_total_cap.get()
        self.state['esp'] = self.ent_esp.get()
        self.state['ambient'] = self.ent_ambient.get()
        self.state['series'] = self.series_var.get()
        self.state['speed'] = self.speed_var.get()
        self.state['unit'] = self.unit_var.get()

    def show_guide(self):
        self.save_state()
        self.clear_content()
        self.current_view = ttk.Frame(self.content_area, padding='40')
        self.current_view.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.current_view, text='Installation Guide', style='Header.TLabel').pack(anchor=tk.W, pady=(0, 20))
        guide_text = "• Return Air: Can be converted from Back (Standard) to Bottom (Field).\\n" \
                     "• Fresh Air: Pre-punched intake available (Ø125mm or Ø160mm).\\n" \
                     "• Drainage: Use a minimum slope of 1/50 for condensate pipes.\\n" \
                     "• Installation: Avoid placing units in areas with high vibration or near heat sources.\\n" \
                     "• Clearance: Maintain minimum 40cm clearance from walls for airflow."
        lbl = ttk.Label(self.current_view, text=guide_text, font=('Segoe UI', 12), justify=tk.LEFT, wraplength=800)
        lbl.pack(anchor=tk.W, pady=20)

    def show_settings(self):
        self.save_state()
        self.clear_content()
        self.current_view = ttk.Frame(self.content_area, padding='40')
        self.current_view.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.current_view, text='CAD Export Settings', style='Header.TLabel').pack(anchor=tk.W, pady=(0, 20))
        settings_card = ttk.Frame(self.current_view, style='Card.TFrame', padding='30')
        settings_card.pack(fill=tk.X, pady=10)
        self.export_level = tk.StringVar(value='L2')
        ttk.Label(settings_card, text='Detail Level:', background=self.palette['bg_card']).grid(row=0, column=0, sticky=tk.W, padx=10, pady=12)
        ttk.Combobox(settings_card, textvariable=self.export_level, values=['L1', 'L2', 'L3'], state='readonly', width=10).grid(row=0, column=1, sticky=tk.W, padx=10)
        self.mirror_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_card, text='Mirror Piping Side', variable=self.mirror_var).grid(row=0, column=2, padx=30)
        self.ret_dir = tk.StringVar(value='back')
        ttk.Label(settings_card, text='Return Direction:', background=self.palette['bg_card']).grid(row=1, column=0, sticky=tk.W, padx=10, pady=12)
        ttk.Combobox(settings_card, textvariable=self.ret_dir, values=['back', 'bottom'], state='readonly', width=10).grid(row=1, column=1, sticky=tk.W, padx=10)
        self.units_var = tk.StringVar(value='mm')
        ttk.Label(settings_card, text='Drawing Units:', background=self.palette['bg_card']).grid(row=2, column=0, sticky=tk.W, padx=10, pady=12)
        ttk.Combobox(settings_card, textvariable=self.units_var, values=['mm', 'm'], state='readonly', width=10).grid(row=2, column=1, sticky=tk.W, padx=10, pady=12)

    def calculate_match(self):
        try:
            raw_cap = float(self.ent_total_cap.get())
            req_cap = raw_cap * 12000 if self.unit_var.get() == 'TR' else raw_cap
            req_esp = float(self.ent_esp.get())
            req_amb = float(self.ent_ambient.get())
        except ValueError:
            messagebox.showerror('Input Error', 'Please enter valid numbers.')
            return
        if req_amb > MAX_AMBIENT_C:
            messagebox.showwarning('Out of Range', f'Ambient above {MAX_AMBIENT_C}C is outside the catalog data.')
            return
        self.btn_calc.config(text="Searching...", state=tk.DISABLED)
        self.root.update_idletasks()
        speed = self.speed_var.get()
        series = self.series_var.get()
        try:
            match = find_match(DB_PATH, req_cap, req_esp, req_amb, speed, series_filter=series)
        except Exception as e:
            messagebox.showerror('DB Error', str(e))
            self.btn_calc.config(text="Find Matching Model", state=tk.NORMAL)
            return
        self._clear_results()
        if match:
            self.current_match = match
            self.last_inputs = {'esp': req_esp}
            self.create_result_card(match)
        else:
            self.current_match = None
            ttk.Label(self.res_container, text='No matching model found.', foreground=self.palette['error'], font=('Segoe UI', 14, 'bold')).pack(pady=60)
        self.btn_calc.config(text="Find Matching Model", state=tk.NORMAL)

    def _clear_results(self):
        for w in self.res_container.winfo_children():
            w.destroy()

    def create_result_card(self, data):
        card = ttk.Frame(self.res_container, style='Card.TFrame', padding='30')
        card.pack(fill=tk.X, pady=15, padx=10)
        header = ttk.Frame(card, style='Card.TFrame')
        header.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header, text='Selected System Model', background=self.palette['bg_card'], font=('Segoe UI', 11, 'bold'), foreground=self.palette['text_muted']).pack(anchor=tk.W)
        ttk.Label(header, text=data['sys_model'], style='Result.TLabel', background=self.palette['bg_card']).pack(anchor=tk.W)
        specs_f = ttk.Frame(card, style='Card.TFrame')
        specs_f.pack(fill=tk.X, pady=10)
        specs = [
            ('Unit Weight', fmt(data['weight'], 'Kg')),
            ('Nominal Capacity', fmt(data['tr'], 'TR')),
            ('Actual Capacity', fmt(data['cap'], 'Btu/hr')),
            ('Air Flow', fmt(data['cfm'], 'CFM')),
            ('Input Power', fmt(data['pwr'], 'W')),
            ('Power Supply', f"{data['volt']} / {data['ph']}"),
            ('Table ESP', fmt(data['table_esp'], 'Pa')),
            ('Table Ambient', fmt(data['table_amb'], 'C')),
            ('Fan Speed', data['speed']),
        ]
        for i, (label, value) in enumerate(specs):
            ttk.Label(specs_f, text=label + ':', style='Value.TLabel', background=self.palette['bg_card'], font=('Segoe UI', 10, 'bold')).grid(row=i // 2, column=(i % 2) * 2, sticky=tk.W, pady=8, padx=(0, 10))
            ttk.Label(specs_f, text=value, style='Value.TLabel', background=self.palette['bg_card']).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, pady=8)
        inst_f = ttk.Frame(card, style='Card.TFrame', padding='20')
        inst_f.pack(fill=tk.X, pady=15)
        sep = tk.Frame(inst_f, height=1, bg=self.palette['border'])
        sep.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(inst_f, text='Installation Data', background=self.palette['bg_card'], font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W)
        inst_grid = ttk.Frame(inst_f, style='Card.TFrame')
        inst_grid.pack(fill=tk.X, pady=10)
        inst_specs = [
            ('Gas Pipe', f"{data.get('gas_pipe', 'N/A')} in"),
            ('Liquid Pipe', f"{data.get('liq_pipe', 'N/A')} in"),
            ('MCA', f"{data.get('mca', 'N/A')} A"),
            ('RLA', f"{data.get('rla', 'N/A')} A"),
        ]
        for i, (label, value) in enumerate(inst_specs):
            ttk.Label(inst_grid, text=label + ':', style='Value.TLabel', background=self.palette['bg_card'], font=('Segoe UI', 10, 'bold')).grid(row=i // 2, column=(i % 2) * 2, sticky=tk.W, pady=5, padx=(0, 10))
            ttk.Label(inst_grid, text=value, style='Value.TLabel', background=self.palette['bg_card']).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, pady=5)
        self.btn_export = tk.Button(card, text='Export CAD Block (DXF)', command=self.export_cad, 
                                    bg=self.palette['primary'], fg='white', font=('Segoe UI', 11, 'bold'), 
                                    bd=0, padx=25, pady=12, cursor='hand2')
        self.btn_export.pack(pady=20, anchor=tk.E)
        self.btn_export.bind('<Enter>', lambda e: self.btn_export.configure(bg=self.palette['primary_hover']))
        self.btn_export.bind('<Leave>', lambda e: self.btn_export.configure(bg=self.palette['primary']))

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
            defaultenstion='.dxf', filetypes=[('DXF', '*.dxf')],
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
    app = ModernCarrierApp(root)
    root.mainloop()