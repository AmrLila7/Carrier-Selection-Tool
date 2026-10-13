import unittest
import sqlite3
import os
import sys

# Add src to path so we can import carrier_tool
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.carrier_tool.logic import find_match

DB_PATH = r"D:/شغل/CAC 6_October/Tools/Carrier_Selection_Tool\Carrier_HVAC_Data.db"

class TestCarrierLogic(unittest.TestCase):
    def test_find_match_success(self):
        # Model '53KDMT12N-718' has perf (esp=0.0, amb=35.0, total_btu=12865.0, speed='High')
        result = find_match(DB_PATH, 10000, 0, 30, 'High')
        self.assertIsNotNone(result)
        self.assertEqual(result['sys_model'], '53KDMT12N-718')
        self.assertGreaterEqual(result['cap'], 10000)

    def test_find_match_no_result(self):
        # Request impossible capacity
        result = find_match(DB_PATH, 1000000, 0, 30, 'High')
        self.assertIsNone(result)

    def test_find_match_invalid_speed(self):
        # Request speed that doesn't exist
        result = find_match(DB_PATH, 10000, 0, 30, 'Ultra-Fast')
        self.assertIsNone(result)

    def test_find_match_esp_too_high(self):
        # Request ESP higher than available
        result = find_match(DB_PATH, 10000, 500, 30, 'High')
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
