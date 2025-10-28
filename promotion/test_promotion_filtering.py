"""
Test script for the corrected promotion filtering system
"""

import frappe

def test_season_and_vendor_code_reading():
    """Test the season and vendor code reading functionality"""
    
    # Test with a sample item code (replace with actual item from your system)
    test_item_code = "MRB93-GRY-29"  # Replace with actual item code from your system
    
    print(f"Testing item: {test_item_code}")
    
    try:
        # Get item details
        item_details = frappe.db.get_value("Item", test_item_code, 
            ["item_group", "brand", "custom_vendor_code"], as_dict=True)
        
        print(f"Item Details:")
        print(f"  Item Group: {item_details.get('item_group') if item_details else 'Not found'}")
        print(f"  Brand: {item_details.get('brand') if item_details else 'Not found'}")
        print(f"  Vendor Code: {item_details.get('custom_vendor_code') if item_details else 'Not found'}")
        
        # Test season reading
        promotion_doc = frappe.new_doc("Promotion")
        season = promotion_doc.get_item_season(test_item_code)
        print(f"  Season: {season}")
        
        # Test variant attributes directly
        variant_attributes = frappe.db.sql("""
            SELECT attribute, attribute_value 
            FROM `tabItem Variant Attribute` 
            WHERE parent = %s
        """, (test_item_code,), as_dict=True)
        
        print(f"  Variant Attributes:")
        for attr in variant_attributes:
            print(f"    {attr.attribute}: {attr.attribute_value}")
        
        return True
        
    except Exception as e:
        print(f"Error testing item {test_item_code}: {str(e)}")
        return False

def test_season_mapping():
    """Test the season mapping functionality"""
    
    promotion_doc = frappe.new_doc("Promotion")
    
    test_cases = [
        ("SS24", "Summer", True),
        ("Summer", "SS24", True),
        ("FW24", "Fall", True),
        ("Fall", "FW24", True),
        ("SP24", "Spring", True),
        ("Spring", "SP24", True),
        ("WI24", "Winter", True),
        ("Winter", "WI24", True),
        ("SS24", "FW24", False),
        ("Summer", "Winter", False),
    ]
    
    print("Testing season mapping:")
    for source, item, expected in test_cases:
        result = promotion_doc.seasons_match(source, item)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {source} vs {item}: {result} (expected {expected}) {status}")

def test_promotion_filtering():
    """Test the complete promotion filtering"""
    
    # Create a test promotion
    promotion = frappe.new_doc("Promotion")
    promotion.title = "Test Promotion - Summer Nike"
    promotion.based_on = "Item Group + Brand + Vendor Code + Season"
    promotion.company = "Your Company"
    promotion.min_qty = 1
    promotion.min_amount = 100
    
    # Add source item group
    source_group = promotion.append("source_item_groups", {})
    source_group.item_group = "Clothing"  # Adjust based on your item groups
    source_group.brand = "Meran"  # From your screenshot
    source_group.custom_vendor_code = "GD"  # From your screenshot
    source_group.season_attribute = "Summer"  # Will match SS24
    source_group.enabled = 1
    
    # Add action
    action = promotion.append("actions", {})
    action.reward_type = "Discount %"
    action.discount_percentage = 10
    action.reward_qty = 1
    
    try:
        promotion.insert()
        frappe.db.commit()
        print(f"✅ Test promotion created: {promotion.name}")
        
        # Test with mock item
        class MockItem:
            def __init__(self, item_code):
                self.item_code = item_code
                self.qty = 1
                self.amount = 100
        
        mock_item = MockItem("MRB93-GRY-29")  # Replace with actual item code
        matches = promotion.is_item_group_brand_vendor_season_match(mock_item)
        print(f"✅ Item matching test: {matches}")
        
        # Clean up
        promotion.delete()
        frappe.db.commit()
        print("✅ Test promotion cleaned up")
        
    except Exception as e:
        print(f"❌ Error in promotion filtering test: {str(e)}")

if __name__ == "__main__":
    print("=== Promotion Filtering Test ===")
    
    # Initialize Frappe
    frappe.init(site='your_site_name')  # Replace with your site name
    frappe.connect()
    
    print("\n1. Testing season and vendor code reading...")
    test_season_and_vendor_code_reading()
    
    print("\n2. Testing season mapping...")
    test_season_mapping()
    
    print("\n3. Testing complete promotion filtering...")
    test_promotion_filtering()
    
    print("\n=== Test Complete ===")
