import unittest
import sqlite3
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.carrier_tool.logic import find_match

DB_PATH = r"D:/شغل/CAC 6_October/Tools/Carrier_Selection_Tool/Carrier_HVAC_Data.db"

class TestEnrichedLogic(unittest.TestCase):
    def test_find_match_returns_enriched_data(self):
        # Request a known model
        result = find_match(DB_PATH, 10000, 0, 30, 'High')
        self.assertIsNotNone(result)
        
        # Check for new enriched fields
        # These will fail initially because find_match doesn't return them yet
        self.assertIn('gas_pipe', result)
        self.assertIn('liq_pipe', result)
        self.assertIn('mca', result)
        self.assertIn('rla', result)

if __name__ == "__main__":
    unittest.main()
