import sqlite3
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_AMBIENT_C = 52

def fmt(value, unit=""):
    if value is None or value == "": return "N/A"
    return f"{value} {unit}".strip()

def interpolate(x, x0, y0, x1, y1):
    if x1 == x0: return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

def find_match(db_path, req_cap, req_esp, req_amb, speed, series_filter="Any"):
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT m.id, m.evaporator_model, m.tr, m.phase, m.voltage, m.gas_pipe, m.liq_pipe, m.weight, "
                "p.total_btu, p.input_w, p.cfm, p.esp, p.ambient "
                "FROM models m JOIN performance p ON m.id = p.model_id "
                "WHERE p.speed = ?", 
                (speed,),
            )
            rows = cur.fetchall()
            
            model_ids = [r[0] for r in rows]
            elec_data = {}
            if model_ids:
                placeholders = ','.join(['?'] * len(model_ids))
                cur.execute(f"SELECT model_id, mca, rla, lra, fla FROM electrical WHERE model_id IN ({placeholders})", model_ids)
                for r in cur.fetchall():
                    elec_data[r[0]] = {'mca': r[1], 'rla': r[2], 'lra': r[3], 'fla': r[4]}
    except sqlite3.Error as e:
        logging.error(f"Database error during match search: {e}")
        raise RuntimeError(f"Database access failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in find_match: {e}")
        raise

    model_performance = {}
    for r in rows:
        m_id = r[0]
        if m_id not in model_performance:
            model_performance[m_id] = []
        model_performance[m_id].append(r)

    candidates = []
    for m_id, records in model_performance.items():
        if series_filter == "KDMT" and "QDMA" in m_id:
            continue
        if series_filter == "QDMT" and "QDMA" not in m_id:
            continue

        sorted_recs = sorted(records, key=lambda x: x[12])
        low_point = None
        high_point = None
        for r in sorted_recs:
            if r[12] <= req_amb:
                low_point = r
            if r[12] >= req_amb:
                high_point = r
                break
        
        if low_point and high_point:
            interp_cap = interpolate(req_amb, low_point[12], low_point[8], high_point[12], high_point[8])
            interp_esp = interpolate(req_amb, low_point[12], low_point[11], high_point[12], high_point[11])
            interp_cfm = interpolate(req_amb, low_point[12], low_point[10], high_point[12], high_point[10])
            best_point_data = {'cap': interp_cap, 'esp': interp_esp, 'cfm': interp_cfm, 'ambient': req_amb, 'record': high_point}
        elif low_point:
            best_point_data = {'cap': low_point[8], 'esp': low_point[11], 'cfm': low_point[10], 'ambient': low_point[12], 'record': low_point}
        elif high_point:
            best_point_data = {'cap': high_point[8], 'esp': high_point[11], 'cfm': high_point[10], 'ambient': high_point[12], 'record': high_point}
        else:
            continue

        if best_point_data['cap'] < req_cap:
            continue 
        
        cap_diff = best_point_data['cap'] - req_cap
        esp_diff = max(0, req_esp - best_point_data['esp'])
        series_bonus = -50 if ("QDMA" in m_id or "QDMT" in m_id) else 0
        
        score = cap_diff + (esp_diff * 20) + series_bonus
        candidates.append((score, best_point_data, best_point_data['record']))

    if not candidates: 
        return None

    candidates.sort(key=lambda x: x[0])
    score, data, record = candidates[0]
    sys_id = record[0]
    elec = elec_data.get(sys_id, {})
    
    return {
        'sys_model': record[0], 'evap_model': record[1], 'tr': record[2], 'ph': record[3], 'volt': record[4],
        'gas_pipe': record[5], 'liq_pipe': record[6], 'weight': record[7], 
        'cap': data['cap'], 'pwr': record[9], 'cfm': data['cfm'],
        'table_esp': data['esp'], 'table_amb': data['ambient'], 'speed': speed,
        'mca': elec.get('mca'), 'rla': elec.get('rla'), 'lra': elec.get('lra'), 'fla': elec.get('fla'),
    }
