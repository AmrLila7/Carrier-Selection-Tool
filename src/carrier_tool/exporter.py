import os
try:
    import ezdxf
except ImportError:
    ezdxf = None

LAYERS = {
    "OUTLINE":    ("HVAC-AHU-OUTLINE", 1, "CONTINUOUS"),
    "OPENINGS":   ("HVAC-AHU-OPENINGS", 3, "CONTINUOUS"),
    "SERVICE":    ("HVAC-AHU-SERVICE", 8, "CONTINUOUS"),
    "PIPES":      ("HVAC-AHU-PIPES", 4, "CONTINUOUS"),
    "HANGERS":    ("HVAC-AHU-HANGERS", 6, "CONTINUOUS"),
    "TEXT":       ("HVAC-AHU-TEXT", 7, "CONTINUOUS"),
    "UNVERIFIED": ("HVAC-UNVERIFIED", 2, "CONTINUOUS"),
}

GEOMETRY_MAP = {
    '53KDMT12N-718':  {'W': 920,  'H': 210, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53QDMA6T12N-728': {'W': 920,  'H': 210, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDMT18N-718':  {'W': 920,  'H': 270, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53QDMA6T18N-728': {'W': 920,  'H': 270, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDMT24N-718':  {'W': 920,  'H': 270, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53QDMA6T24N-728': {'W': 920,  'H': 270, 'D': 635, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDMT30N-718':  {'W': 1200, 'H': 300, 'D': 865, 'return': 'back/bottom', 'pipe_side': 1},
    '53QDMA6T30N-728': {'W': 1200, 'H': 300, 'D': 865, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDMT36N-718T': {'W': 1200, 'H': 300, 'D': 865, 'return': 'back/bottom', 'pipe_side': 1},
    '53QDMA6T36N-728': {'W': 1200, 'H': 300, 'D': 865, 'return': 'back/bottom', 'pipe_side': 1},
    '53KDHT42N-518T': {'W': 1200, 'H': 380, 'D': 625, 'return': 'back',        'pipe_side': 1},
    '53QDMA6T48N-528': {'W': 1200, 'H': 380, 'D': 625, 'return': 'back',        'pipe_side': 1},
    '53KDHT48N-518T': {'W': 1200, 'H': 380, 'D': 625, 'return': 'back',        'pipe_side': 1},
    '53KDHT60N-518T': {'W': 1200, 'H': 380, 'D': 625, 'return': 'back',        'pipe_side': 1},
    '53QDMA6T60N-528': {'W': 1200, 'H': 380, 'D': 625, 'return': 'back',        'pipe_side': 1},
    '53KDHT72N-518T': {'W': 1470, 'H': 510, 'D': 795, 'return': 'back',        'pipe_side': -1},
}

class DXFGenerator:
    @staticmethod
    def generate(model_id, data, options, save_path):
        if ezdxf is None:
            raise RuntimeError("مكتبة ezdxf غير مثبتة. نفذ: pip install ezdxf")

        try:
            doc = ezdxf.new('R2010')
            doc.header['$INSUNITS'] = 4 
            scale = options.get('scale', 1.0)
            layers = {k: v[0] for k, v in LAYERS.items()}
            for name, color, ltype in LAYERS.values():
                doc.layers.add(name=name, color=color, linetype=ltype)

            block_name = f"BLOCK_{model_id}"
            block = doc.blocks.new(name=block_name)
            geo = GEOMETRY_MAP.get(model_id, {"W": 1000, "H": 300, "D": 600})
            w, h, d = geo["W"] * scale, geo["H"] * scale, geo["D"] * scale
            pipe_side = geo.get('pipe_side', 1) * (-1 if options.get('mirror') else 1)

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
            
            doc.saveas(save_path)
            return save_path
        except IOError as e:
            raise RuntimeError(f"Could not save DXF file to {save_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while generating DXF: {e}")
