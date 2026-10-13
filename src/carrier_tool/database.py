import sqlite3

def load_speeds(db_path):
    try:
        conn = sqlite3.connect(db_path)
        try:
            # Get unique speeds
            speeds = [r[0] for r in conn.execute("SELECT DISTINCT speed FROM performance")]
            
            # Define the logical engineering order: High -> Med -> Low
            order = {'High': 0, 'Med': 1, 'Medium': 1, 'Low': 2}
            
            # Sort based on the order map, fallback to alphabetical if speed not in map
            return sorted(speeds, key=lambda x: order.get(x, 99))
        finally:
            conn.close()
    except Exception:
        return ['High', 'Med', 'Low']

def get_suggested_capacities(db_path):
    try:
        conn = sqlite3.connect(db_path)
        try:
            return sorted([r[0] for r in conn.execute("SELECT DISTINCT tr FROM models WHERE tr IS NOT NULL")], reverse=True)
        finally:
            conn.close()
    except Exception:
        return []

def get_suggested_esp(db_path):
    try:
        conn = sqlite3.connect(db_path)
        try:
            return sorted([r[0] for r in conn.execute("SELECT DISTINCT esp FROM performance WHERE esp IS NOT NULL")], reverse=False)
        finally:
            conn.close()
    except Exception:
        return []
