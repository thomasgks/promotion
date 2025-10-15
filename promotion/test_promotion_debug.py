#!/usr/bin/env python3

# Test to debug promotion logic
import sys
sys.path.append('/home/erpnext/frappe-bench/apps/frappe')

def test_promotion_debug():
    print("=== PROMOTION DEBUG TEST ===")
    
    # Test the quantity calculation
    total_applicable_qty = 5
    min_qty = 1
    reward_qty = 1
    
    # Old logic
    complete_sets_old = int(total_applicable_qty / min_qty)
    total_free_items_old = complete_sets_old * reward_qty
    
    # New logic
    items_per_set = min_qty + reward_qty
    complete_sets_new = int(total_applicable_qty / items_per_set)
    total_free_items_new = complete_sets_new * reward_qty
    
    print(f"Total applicable qty: {total_applicable_qty}")
    print(f"Min qty: {min_qty}, Reward qty: {reward_qty}")
    print(f"Items per set: {items_per_set}")
    print(f"Complete sets (new): {complete_sets_new}")
    print(f"Total free items (new): {total_free_items_new}")
    
    # Test individual item logic
    print("\n=== INDIVIDUAL ITEM LOGIC TEST ===")
    
    # Simulate items with different rates
    items = [
        {'item_code': '882747', 'qty': 1, 'rate': 176.00},
        {'item_code': '838954', 'qty': 3, 'rate': 35.00},
        {'item_code': '882747', 'qty': 1, 'rate': 176.00}
    ]
    
    # Create individual units
    individual_items = []
    for item in items:
        for i in range(item['qty']):
            individual_items.append({
                'item_code': item['item_code'],
                'rate': item['rate'],
                'unit_index': i + 1
            })
    
    # Sort by rate
    individual_items.sort(key=lambda x: x['rate'])
    
    print("Individual items sorted by rate:")
    for i, item in enumerate(individual_items):
        print(f"  {i+1}. {item['item_code']} Unit {item['unit_index']} - Rate: {item['rate']}")
    
    # Select cheapest items for free
    free_items_needed = total_free_items_new
    selected_items = {}
    
    for item in individual_items:
        if free_items_needed <= 0:
            break
        
        item_code = item['item_code']
        if item_code not in selected_items:
            selected_items[item_code] = 0
        
        selected_items[item_code] += 1
        free_items_needed -= 1
    
    print(f"\nSelected items for free (need {total_free_items_new}):")
    for item_code, count in selected_items.items():
        print(f"  {item_code}: {count} units free")
    
    # Expected result
    print(f"\nExpected result:")
    print(f"  - 2 cheapest items should be free (35.00 SAR items)")
    print(f"  - 3 remaining items should be paid (176.00 SAR items)")
    print(f"  - Total: 3 × 176.00 = 528.00 SAR")

if __name__ == "__main__":
    test_promotion_debug()





