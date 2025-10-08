#!/usr/bin/env python3
"""
Test script to verify season matching logic
"""

import sys
import os

# Add the promotion app to the path
sys.path.insert(0, '/home/erpnext/frappe-bench/apps/promotion')

def test_season_matching():
    """Test the season matching logic"""
    
    # Import the Promotion class
    from promotion.promotion.doctype.promotion.promotion import Promotion
    
    # Create a promotion instance to test the method
    promotion = Promotion()
    
    # Test cases
    test_cases = [
        # (source_season, item_season, expected_result, description)
        ("SS25", "SS25", True, "Exact match SS25"),
        ("SS25", "SS24", True, "Pattern match SS25 vs SS24"),
        ("SS25", "SS23", True, "Pattern match SS25 vs SS23"),
        ("SS25", "FW25", False, "Different season codes"),
        ("SS25", "Summer", True, "SS25 vs Summer (mapped)"),
        ("Summer", "SS25", True, "Summer vs SS25 (mapped)"),
        ("", "SS25", True, "Empty source matches all"),
        ("SS25", "", False, "Empty item season"),
    ]
    
    print("Testing Season Matching Logic")
    print("=" * 50)
    
    for source_season, item_season, expected, description in test_cases:
        result = promotion.seasons_match(source_season, item_season)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | {description}")
        print(f"      Source: '{source_season}' | Item: '{item_season}' | Expected: {expected} | Got: {result}")
        print()

if __name__ == "__main__":
    test_season_matching()

