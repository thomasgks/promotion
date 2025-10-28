"""
Example implementation for Promotion Filtering with Custom Vendor Code and Season

This example demonstrates how to use the enhanced promotion filtering system
that supports filtering based on:
- Item Group
- Brand  
- Custom Vendor Code
- Season (from variant attributes)

Usage Examples:
"""

import frappe
from frappe import _

def create_sample_promotion_with_comprehensive_filtering():
    """
    Example: Create a promotion that filters based on Item Group + Brand + Vendor Code + Season
    
    This promotion will apply to:
    - Item Group: "Clothing"
    - Brand: "Nike" 
    - Custom Vendor Code: "VENDOR001"
    - Season: "Summer"
    """
    
    # Create the promotion
    promotion = frappe.new_doc("Promotion")
    promotion.title = "Summer Nike Clothing Vendor Promotion"
    promotion.based_on = "Item Group + Brand + Vendor Code + Season"
    promotion.company = "Your Company"
    promotion.valid_from = "2024-06-01"
    promotion.valid_upto = "2024-08-31"
    promotion.min_qty = 2
    promotion.min_amount = 100
    
    # Add source item group with comprehensive filtering
    source_group = promotion.append("source_item_groups", {})
    source_group.item_group = "Clothing"
    source_group.brand = "Nike"
    source_group.custom_vendor_code = "VENDOR001"
    source_group.season_attribute = "Summer"
    source_group.enabled = 1
    
    # Add promotion action (20% discount)
    action = promotion.append("actions", {})
    action.reward_type = "Discount %"
    action.discount_percentage = 20
    action.reward_qty = 1
    action.target_brand = "Nike"
    
    # Save the promotion
    promotion.insert()
    frappe.db.commit()
    
    return promotion.name

def create_flexible_promotion_example():
    """
    Example: Create a promotion with flexible filtering
    
    This promotion will apply to any items in "Electronics" item group
    from vendor "TECH001" during "Winter" season, regardless of brand
    """
    
    promotion = frappe.new_doc("Promotion")
    promotion.title = "Winter Electronics Tech Vendor Promotion"
    promotion.based_on = "Item Group + Brand + Vendor Code + Season"
    promotion.company = "Your Company"
    promotion.valid_from = "2024-12-01"
    promotion.valid_upto = "2024-02-28"
    promotion.min_qty = 1
    promotion.min_amount = 200
    
    # Add source item group with flexible filtering
    source_group = promotion.append("source_item_groups", {})
    source_group.item_group = "Electronics"
    # Leave brand empty to match any brand
    source_group.custom_vendor_code = "TECH001"
    source_group.season_attribute = "Winter"
    source_group.enabled = 1
    
    # Add promotion action (15% discount)
    action = promotion.append("actions", {})
    action.reward_type = "Discount %"
    action.discount_percentage = 15
    action.reward_qty = 1
    
    promotion.insert()
    frappe.db.commit()
    
    return promotion.name

def create_all_seasons_promotion():
    """
    Example: Create a promotion that works for all seasons
    
    This promotion applies to "Sports" items from "SPORT001" vendor
    regardless of season or brand
    """
    
    promotion = frappe.new_doc("Promotion")
    promotion.title = "Year-Round Sports Vendor Promotion"
    promotion.based_on = "Item Group + Brand + Vendor Code + Season"
    promotion.company = "Your Company"
    promotion.valid_from = "2024-01-01"
    promotion.valid_upto = "2024-12-31"
    promotion.min_qty = 3
    promotion.min_amount = 150
    
    # Add source item group with all seasons
    source_group = promotion.append("source_item_groups", {})
    source_group.item_group = "Sports"
    source_group.custom_vendor_code = "SPORT001"
    source_group.season_attribute = "All Seasons"  # Works for any season
    source_group.enabled = 1
    
    # Add promotion action (Buy 3 Get 1 Free)
    action = promotion.append("actions", {})
    action.reward_type = "Discount %"
    action.discount_percentage = 100
    action.reward_qty = 1
    
    promotion.insert()
    frappe.db.commit()
    
    return promotion.name

def test_promotion_filtering():
    """
    Test the promotion filtering with sample items
    """
    
    # Test items with different attributes
    test_items = [
        {
            "item_code": "Nike-Summer-Shirt-001",
            "item_group": "Clothing",
            "brand": "Nike", 
            "custom_vendor_code": "VENDOR001",
            "season": "Summer"
        },
        {
            "item_code": "Adidas-Summer-Shoes-002", 
            "item_group": "Clothing",
            "brand": "Adidas",
            "custom_vendor_code": "VENDOR002", 
            "season": "Summer"
        },
        {
            "item_code": "Nike-Winter-Jacket-003",
            "item_group": "Clothing", 
            "brand": "Nike",
            "custom_vendor_code": "VENDOR001",
            "season": "Winter"
        }
    ]
    
    # Get the promotion
    promotion_name = create_sample_promotion_with_comprehensive_filtering()
    promotion = frappe.get_doc("Promotion", promotion_name)
    
    print(f"Testing promotion: {promotion.title}")
    print(f"Based on: {promotion.based_on}")
    
    # Test each item
    for item_data in test_items:
        # Create a mock quotation item
        class MockItem:
            def __init__(self, item_code):
                self.item_code = item_code
                self.qty = 1
                self.amount = 100
        
        mock_item = MockItem(item_data["item_code"])
        
        # Check if item matches the promotion criteria
        matches = promotion.is_item_group_brand_vendor_season_match(mock_item)
        
        print(f"\nItem: {item_data['item_code']}")
        print(f"  Item Group: {item_data['item_group']}")
        print(f"  Brand: {item_data['brand']}")
        print(f"  Vendor Code: {item_data['custom_vendor_code']}")
        print(f"  Season: {item_data['season']}")
        print(f"  Matches Promotion: {'YES' if matches else 'NO'}")
        
        if matches:
            print(f"  ✅ This item would qualify for the promotion!")
        else:
            print(f"  ❌ This item does not qualify for the promotion")

def setup_item_custom_fields():
    """
    Helper function to set up custom fields on Item doctype if needed
    """
    
    # Check if custom_vendor_code field exists on Item
    if not frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "custom_vendor_code"}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Item"
        custom_field.fieldname = "custom_vendor_code"
        custom_field.label = "Custom Vendor Code"
        custom_field.fieldtype = "Data"
        custom_field.insert()
        frappe.db.commit()
    
    # Check if season_attribute field exists on Item (as fallback)
    if not frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "season_attribute"}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Item"
        custom_field.fieldname = "season_attribute"
        custom_field.label = "Season"
        custom_field.fieldtype = "Data"
        custom_field.description = "Leave empty for all seasons"
        custom_field.insert()
        frappe.db.commit()

def create_sample_items():
    """
    Create sample items with the required attributes for testing
    """
    
    # Setup custom fields first
    setup_item_custom_fields()
    
    items_to_create = [
        {
            "item_code": "Nike-Summer-Shirt-001",
            "item_name": "Nike Summer T-Shirt",
            "item_group": "Clothing",
            "brand": "Nike",
            "custom_vendor_code": "VENDOR001",
            "season_attribute": "Summer"
        },
        {
            "item_code": "Adidas-Summer-Shoes-002",
            "item_name": "Adidas Summer Shoes", 
            "item_group": "Clothing",
            "brand": "Adidas",
            "custom_vendor_code": "VENDOR002",
            "season_attribute": "Summer"
        },
        {
            "item_code": "Nike-Winter-Jacket-003",
            "item_name": "Nike Winter Jacket",
            "item_group": "Clothing",
            "brand": "Nike", 
            "custom_vendor_code": "VENDOR001",
            "season_attribute": "Winter"
        }
    ]
    
    created_items = []
    
    for item_data in items_to_create:
        if not frappe.db.exists("Item", item_data["item_code"]):
            item = frappe.new_doc("Item")
            item.item_code = item_data["item_code"]
            item.item_name = item_data["item_name"]
            item.item_group = item_data["item_group"]
            item.brand = item_data["brand"]
            item.custom_vendor_code = item_data["custom_vendor_code"]
            item.season_attribute = item_data["season_attribute"]
            item.is_stock_item = 1
            item.insert()
            created_items.append(item.item_code)
    
    if created_items:
        frappe.db.commit()
        print(f"Created sample items: {', '.join(created_items)}")
    
    return created_items

if __name__ == "__main__":
    """
    Run this script to test the promotion filtering system
    """
    print("=== Promotion Filtering System Test ===\n")
    
    # Create sample items
    print("1. Creating sample items...")
    create_sample_items()
    
    # Test promotion filtering
    print("\n2. Testing promotion filtering...")
    test_promotion_filtering()
    
    print("\n=== Test Complete ===")
