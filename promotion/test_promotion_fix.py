#!/usr/bin/env python3

import frappe
from frappe import _

def test_promotion_fix():
    """Test the promotion fix to ensure multiple items are made free"""
    
    try:
        # Get the first available promotion
        promotions = frappe.get_all("Promotion", filters={"disabled": 0}, limit=1)
        if not promotions:
            print("No promotions found")
            return False
        
        promotion_name = promotions[0].name
        promotion_doc = frappe.get_doc("Promotion", promotion_name)
        
        print(f"Testing promotion: {promotion_name}")
        print(f"Min Qty: {promotion_doc.min_qty}")
        print(f"Reward Qty: {promotion_doc.reward_qty}")
        
        # Get the first available quotation
        quotations = frappe.get_all("Quotation", limit=1)
        if not quotations:
            print("No quotations found")
            return False
        
        quotation_name = quotations[0].name
        quotation_doc = frappe.get_doc("Quotation", quotation_name)
        
        print(f"Testing quotation: {quotation_name}")
        print(f"Total items: {len(quotation_doc.items)}")
        
        # Show all items
        for i, item in enumerate(quotation_doc.items):
            print(f"  {i+1}. {item.item_code} - Rate: {item.rate}, Qty: {item.qty}")
        
        # Test the promotion logic
        applicable_items = promotion_doc.get_applicable_items(quotation_doc.items)
        print(f"\nApplicable items: {len(applicable_items)}")
        
        if applicable_items:
            total_applicable_qty = sum(flt(item.qty) for item in applicable_items)
            min_qty = flt(promotion_doc.min_qty)
            reward_qty = flt(promotion_doc.reward_qty)
            
            complete_sets = int(total_applicable_qty / min_qty)
            total_free_items = complete_sets * reward_qty
            
            print(f"Total applicable qty: {total_applicable_qty}")
            print(f"Complete sets: {complete_sets}")
            print(f"Total free items: {total_free_items}")
            
            # Test the find_cheapest_items_for_promotion method
            all_target_items = promotion_doc.get_all_target_items()
            free_items = promotion_doc.find_cheapest_items_for_promotion(quotation_doc, all_target_items, total_free_items)
            
            print(f"\nFree items selected: {len(free_items)}")
            for i, item in enumerate(free_items):
                print(f"  {i+1}. {item.item_code} - Rate: {item.rate}")
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    frappe.init(site="sodas")
    frappe.connect()
    test_promotion_fix()



