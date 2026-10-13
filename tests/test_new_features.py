import unittest
import sqlite3
import os
from src.carrier_tool.logic import find_match
from src.carrier_tool.database import get_suggested_capacities

class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        self.db_path = "D:/شغل/CAC 6_October/Tools/Carrier_Selection_Tool/Carrier_HVAC_Data.db"

    def test_get_suggested_capacities(self):
        # Test that suggested capacities are returned and sorted
        suggestions = get_suggested_capacities(self.db_path)
        self.assertIsInstance(suggestions, list)
        self.assertTrue(len(suggestions) > 0)
        # Check if sorted descending
        self.assertEqual(suggestions, sorted(suggestions, reverse=True))

    def test_find_match_qdmt_filter(self):
        # Test that QDMT filter only returns QDMA/QDMT models
        # Using values that should match something in the DB
        result = find_match(self.db_path, 12000, 0, 35, "High", series_filter="QDMT")
        if result:
            self.assertTrue("QDMA" in result['sys_model'] or "QDMT" in result['sys_model'])
            self.assertFalse("KDMT" in result['sys_model'])
        else:
            self.fail("Should have found a QDMT match for 12000 Btu")

    def test_find_match_kdmt_filter(self):
        # Test that KDMT filter only returns KDMT models
        result = find_match(self.db_path, 12000, 0, 35, "High", series_filter="KDMT")
        if result:
            self.assertTrue("KDMT" in result['sys_model'])
            self.assertFalse("QDMA" in result['sys_model'])
        else:
            self.fail("Should have found a KDMT match for 12000 Btu")

    def test_find_match_any_filter(self):
        # Test that Any filter returns the best match (likely QDMA due to bonus)
        result = find_match(self.db_path, 12000, 0, 35, "High", series_filter="Any")
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()
