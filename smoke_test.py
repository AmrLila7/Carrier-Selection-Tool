
import sys
import os

# Simulate the PYTHONPATH setup done in the .bat
project_root = r"D:\شغل\CAC 6_October\Tools\Carrier_Selection_Tool"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.carrier_tool.database import load_speeds, get_suggested_capacities
    from src.carrier_tool.logic import find_match
    from src.carrier_tool.exporter import DXFGenerator
    print("SUCCESS: All core modules imported correctly.")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"UNEXPECTED ERROR: {e}")
    sys.exit(1)

# Test a simple logic call to ensure no crashes
try:
    db_path = os.path.join(project_root, "Carrier_HVAC_Data.db")
    res = find_match(db_path, 12000, 0, 35, "High", series_filter="Any")
    print(f"LOGIC TEST: Successfully retrieved match: {res['sys_model'] if res else 'None'}")
except Exception as e:
    print(f"LOGIC ERROR: {e}")
    sys.exit(1)
