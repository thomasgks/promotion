"""
IMPLEMENTATION EXAMPLE - Bundle & Coupon Cap Extensions
========================================================

ADD THESE METHODS TO THE END OF THE Promotion CLASS in promotion.py

This file shows exactly what to add without modifying existing code.
"""

# ==========================================
# STEP 1: Add these imports at the top if not present
# ==========================================
# (Already present in your file)
# import frappe
# from frappe.utils import flt


# ==========================================
# STEP 2: Add these methods to Promotion class
# ==========================================

class PromotionExtensions:
    """
    Copy these methods into the Promotion class in promotion.py
    Add them AFTER the existing methods (after line 786)
    """
    
    def apply_promotion_by_type(self, quotation_doc):
        """
        Main router for promotion types.
        
        **WHERE TO ADD**: After get_promotion_summary() method (line 786)
        **WHEN TO CALL**: Use this instead of apply_promotion() for new types
        """
        try:
            promotion_type = getattr(self, 'promotion_type', 'Buy X Get Y')
            
            frappe.msgprint(f"=== ROUTING TO PROMOTION TYPE: {promotion_type} ===")
            
            if promotion_type == "Bundle - Fixed Price":
                return self.apply_bundle_fixed_price(quotation_doc)
            
            elif promotion_type == "Bundle - Percentage":
                return self.apply_bundle_percentage(quotation_doc)
            
            elif promotion_type == "Coupon - % with Cap":
                return self.apply_coupon_with_cap(quotation_doc)
            
            else:  # Default to existing "Buy X Get Y" logic
                return self.apply_promotion(quotation_doc)
                
        except Exception as e:
            frappe.log_error(f"Error in apply_promotion_by_type: {str(e)}")
            frappe.msgprint(f"Error: {str(e)}", alert=True)
            return False
    
    
    # ==========================================
    # BUNDLE - FIXED PRICE
    # ==========================================
    
    def apply_bundle_fixed_price(self, quotation_doc):
        """
        Example: Buy any 3 items from Vendor X for SAR 100
        
        Logic:
        1. Get items matching bundle_condition_field (Vendor/Brand/Item Group)
        2. If qty >= bundle_qty, select cheapest N items
        3. If original total > fixed_bundle_price, apply discount
        4. Distribute discount proportionally
        """
        try:
            # Validation
            if not self.is_valid(quotation_doc.transaction_date):
                frappe.msgprint("Promotion not valid for this date", alert=True)
                return False
            
            applicable_items = self.get_applicable_items(quotation_doc.items)
            
            if not applicable_items:
                frappe.msgprint("No applicable items found", alert=True)
                return False
            
            bundle_qty = flt(getattr(self, 'bundle_qty', 0))
            fixed_price = flt(getattr(self, 'fixed_bundle_price', 0))
            
            if bundle_qty <= 0 or fixed_price <= 0:
                frappe.msgprint("Invalid bundle configuration", alert=True)
                return False
            
            # Count total quantity
            total_qty = sum(flt(item.qty) for item in applicable_items)
            
            if total_qty < bundle_qty:
                frappe.msgprint(f"Need {bundle_qty} items, found {total_qty}", alert=True)
                return False
            
            # Sort deterministically (cheapest first)
            sorted_items = self._sort_items_for_bundle(applicable_items)
            
            # Calculate bundles to apply
            multiply_flag = getattr(self, 'multiply_by_min_qty', False)
            bundles_to_apply = int(total_qty / bundle_qty) if multiply_flag else 1
            
            frappe.msgprint(f"Applying {bundles_to_apply} bundle(s)")
            
            # Process bundles
            applied = False
            items_used = 0
            
            for bundle_num in range(bundles_to_apply):
                # Select items for this bundle
                bundle_items = []
                qty_collected = 0
                
                for item in sorted_items[items_used:]:
                    if qty_collected >= bundle_qty:
                        break
                    bundle_items.append(item)
                    qty_collected += flt(item.qty)
                    items_used += 1
                
                if not bundle_items:
                    break
                
                # Calculate original total
                original_total = sum(flt(item.rate) * flt(item.qty) for item in bundle_items)
                
                frappe.msgprint(f"Bundle {bundle_num+1}: {original_total} SAR → {fixed_price} SAR")
                
                # Apply discount if there's savings
                if original_total > fixed_price:
                    discount = original_total - fixed_price
                    self._distribute_discount_proportionally(
                        bundle_items, discount, original_total, self.name
                    )
                    applied = True
                else:
                    frappe.msgprint(f"No discount for bundle {bundle_num+1} (already cheaper)")
            
            if applied:
                quotation_doc.calculate_taxes_and_totals()
                frappe.msgprint("✅ Bundle Fixed Price applied!", alert=True)
            
            return applied
            
        except Exception as e:
            frappe.log_error(f"Error in apply_bundle_fixed_price: {str(e)}")
            return False
    
    
    # ==========================================
    # BUNDLE - PERCENTAGE DISCOUNT
    # ==========================================
    
    def apply_bundle_percentage(self, quotation_doc):
        """
        Example: Buy 3 Adidas items and get 15% off
        
        Logic:
        1. Get items matching condition
        2. If qty >= bundle_qty:
           - If apply_to_cheapest_only: discount cheapest N
           - Else: discount all matching items
        3. Apply percentage discount
        """
        try:
            # Validation
            if not self.is_valid(quotation_doc.transaction_date):
                frappe.msgprint("Promotion not valid", alert=True)
                return False
            
            applicable_items = self.get_applicable_items(quotation_doc.items)
            
            if not applicable_items:
                frappe.msgprint("No applicable items", alert=True)
                return False
            
            bundle_qty = flt(getattr(self, 'bundle_qty', 0))
            discount_pct = flt(getattr(self, 'bundle_discount_percentage', 0))
            
            if bundle_qty <= 0 or discount_pct <= 0:
                frappe.msgprint("Invalid bundle configuration", alert=True)
                return False
            
            total_qty = sum(flt(item.qty) for item in applicable_items)
            
            if total_qty < bundle_qty:
                frappe.msgprint(f"Need {bundle_qty} items, found {total_qty}", alert=True)
                return False
            
            # Determine items to discount
            apply_to_cheapest = getattr(self, 'apply_to_cheapest_only', False)
            
            if apply_to_cheapest:
                sorted_items = self._sort_items_for_bundle(applicable_items)
                items_to_discount = sorted_items[:int(bundle_qty)]
                frappe.msgprint(f"Applying to {len(items_to_discount)} cheapest items")
            else:
                items_to_discount = applicable_items
                frappe.msgprint(f"Applying to all {len(items_to_discount)} matching items")
            
            # Apply percentage discount
            applied = False
            for item in items_to_discount:
                # Store original rate
                if not hasattr(item, 'original_rate') or not item.original_rate:
                    item.original_rate = flt(item.rate)
                
                original_rate = item.original_rate
                item_amount = original_rate * flt(item.qty)
                discount_amount = item_amount * (discount_pct / 100)
                
                # Apply
                item.discount_percentage = discount_pct
                item.discount_amount = discount_amount
                item.promotion_applied = self.name
                item.promotion_discount = discount_amount
                item.amount = item_amount - discount_amount
                
                frappe.msgprint(f"  {item.item_code}: -{discount_pct}% = {discount_amount} SAR")
                applied = True
            
            if applied:
                quotation_doc.calculate_taxes_and_totals()
                frappe.msgprint(f"✅ {discount_pct}% Bundle discount applied!", alert=True)
            
            return applied
            
        except Exception as e:
            frappe.log_error(f"Error in apply_bundle_percentage: {str(e)}")
            return False
    
    
    # ==========================================
    # COUPON - PERCENTAGE WITH CAP
    # ==========================================
    
    def apply_coupon_with_cap(self, quotation_doc):
        """
        Example: 10% off capped at SAR 100
        
        Logic:
        1. Calculate discount = total * percentage
        2. If discount > cap, set discount = cap
        3. Distribute proportionally
        """
        try:
            # Validation
            if not self.is_valid(quotation_doc.transaction_date):
                frappe.msgprint("Promotion not valid", alert=True)
                return False
            
            applicable_items = self.get_applicable_items(quotation_doc.items)
            
            if not applicable_items:
                frappe.msgprint("No applicable items", alert=True)
                return False
            
            discount_pct = flt(getattr(self, 'coupon_discount_percentage', 0))
            cap_amount = flt(getattr(self, 'coupon_cap_amount', 0))
            
            if discount_pct <= 0:
                frappe.msgprint("Invalid discount percentage", alert=True)
                return False
            
            # Calculate total
            total_amount = sum(flt(item.rate) * flt(item.qty) for item in applicable_items)
            
            # Calculate discount
            calculated_discount = total_amount * (discount_pct / 100)
            
            frappe.msgprint(f"Total: {total_amount} SAR")
            frappe.msgprint(f"Discount ({discount_pct}%): {calculated_discount} SAR")
            
            # Apply cap
            final_discount = calculated_discount
            if cap_amount > 0 and calculated_discount > cap_amount:
                final_discount = cap_amount
                frappe.msgprint(f"⚠️ Capped at {cap_amount} SAR", alert=True)
            else:
                frappe.msgprint(f"Within cap limit")
            
            if final_discount <= 0:
                frappe.msgprint("No discount to apply", alert=True)
                return False
            
            # Distribute proportionally
            self._distribute_discount_proportionally(
                applicable_items, final_discount, total_amount, self.name
            )
            
            quotation_doc.calculate_taxes_and_totals()
            
            frappe.msgprint(f"✅ Coupon applied: {final_discount} SAR discount!", alert=True)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Error in apply_coupon_with_cap: {str(e)}")
            return False
    
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _sort_items_for_bundle(self, items):
        """
        Sort items deterministically for bundle selection.
        Priority: Price (low→high) → Brand → Item Code → Row Index
        
        **Ensures same input always yields same output**
        """
        enriched = []
        
        for item in items:
            # Get item brand for sorting
            item_brand = frappe.db.get_value("Item", item.item_code, "brand") or ""
            
            enriched.append({
                'item': item,
                'rate': flt(item.rate),
                'brand': item_brand,
                'item_code': item.item_code,
                'idx': getattr(item, 'idx', 0)
            })
        
        # Deterministic sort
        enriched.sort(key=lambda x: (
            x['rate'],      # Cheapest first
            x['brand'],     # A-Z
            x['item_code'], # A-Z
            x['idx']        # Row order
        ))
        
        return [x['item'] for x in enriched]
    
    
    def _distribute_discount_proportionally(self, items, total_discount, total_amount, promotion_name):
        """
        Distribute discount across items proportionally based on their amount.
        
        **Maintains determinism and fairness**
        
        Example:
        - Item A: 60% of total → gets 60% of discount
        - Item B: 40% of total → gets 40% of discount
        """
        frappe.msgprint(f"Distributing {total_discount} SAR across {len(items)} items")
        
        for item in items:
            # Store original rate
            if not hasattr(item, 'original_rate') or not item.original_rate:
                item.original_rate = flt(item.rate)
            
            original_rate = item.original_rate
            item_amount = original_rate * flt(item.qty)
            
            # Calculate proportional share
            if total_amount > 0:
                proportion = item_amount / total_amount
                item_discount = total_discount * proportion
            else:
                item_discount = 0
            
            # Apply discount
            item.discount_amount = item_discount
            item.discount_percentage = (item_discount / item_amount * 100) if item_amount > 0 else 0
            item.promotion_applied = promotion_name
            item.promotion_discount = item_discount
            item.amount = item_amount - item_discount
            
            frappe.msgprint(
                f"  {item.item_code}: {item_discount:.2f} SAR "
                f"({item.discount_percentage:.1f}%)"
            )


# ==========================================
# STEP 3: Update entry point functions
# ==========================================

def updated_apply_promotion_to_quotation(quotation_name, promotion_name):
    """
    REPLACE the existing apply_promotion_to_quotation function (line 844)
    with this updated version
    """
    try:
        quotation_doc = frappe.get_doc("Quotation", quotation_name)
        promotion_doc = frappe.get_doc("Promotion", promotion_name)
        
        # Route to appropriate method
        if hasattr(promotion_doc, 'apply_promotion_by_type'):
            success = promotion_doc.apply_promotion_by_type(quotation_doc)
        else:
            # Fallback for backward compatibility
            success = promotion_doc.apply_promotion(quotation_doc)
        
        if success:
            quotation_doc.save()
            frappe.msgprint("Promotion applied successfully")
            return True
        else:
            frappe.msgprint("Promotion conditions not met")
            return False
            
    except Exception as e:
        frappe.throw(f"Error applying promotion: {str(e)}")


def updated_apply_coupon_code(coupon_code, quotation_name):
    """
    REPLACE lines 978-985 in the existing apply_coupon_code function
    with this updated version
    """
    # ... existing validation code stays the same (lines 952-977) ...
    
    promotion_doc = frappe.get_doc("Promotion", coupon.promotion)
    
    frappe.msgprint(f"=== COUPON CODE DEBUG ===")
    frappe.msgprint(f"Coupon: {coupon_code}")
    frappe.msgprint(f"Promotion: {promotion_doc.name}")
    frappe.msgprint(f"Type: {getattr(promotion_doc, 'promotion_type', 'Buy X Get Y')}")
    
    # NEW: Route to appropriate method
    if hasattr(promotion_doc, 'apply_promotion_by_type'):
        success = promotion_doc.apply_promotion_by_type(quotation_doc)
    else:
        # Fallback for backward compatibility
        success = promotion_doc.apply_promotion(quotation_doc)
    
    # ... rest of existing code stays the same (lines 986-1017) ...


# ==========================================
# STEP 4: Enhanced validation
# ==========================================

def enhanced_validate_actions(self):
    """
    REPLACE the existing validate_actions method (line 36)
    with this enhanced version
    """
    promotion_type = getattr(self, 'promotion_type', 'Buy X Get Y')
    
    # Original Buy X Get Y validation
    if promotion_type == "Buy X Get Y":
        if not self.actions:
            frappe.throw("At least one action must be specified")
        
        for action in self.actions:
            if action.reward_type == "Discount %" and not action.discount_percentage:
                frappe.throw("Discount % is required for Discount % reward type")
            
            if action.reward_type == "Discount Amount" and not action.discount_amount:
                frappe.throw("Discount Amount is required for Discount Amount reward type")
    
    # Bundle validations
    elif promotion_type in ["Bundle - Fixed Price", "Bundle - Percentage"]:
        if not getattr(self, 'bundle_qty', 0) or self.bundle_qty <= 0:
            frappe.throw("Bundle Qty must be greater than 0")
        
        if promotion_type == "Bundle - Fixed Price":
            if not getattr(self, 'fixed_bundle_price', 0) or self.fixed_bundle_price <= 0:
                frappe.throw("Fixed Bundle Price must be greater than 0")
        else:  # Bundle - Percentage
            if not getattr(self, 'bundle_discount_percentage', 0) or self.bundle_discount_percentage <= 0:
                frappe.throw("Bundle Discount Percentage must be greater than 0")
    
    # Coupon cap validation
    elif promotion_type == "Coupon - % with Cap":
        if not getattr(self, 'coupon_discount_percentage', 0) or self.coupon_discount_percentage <= 0:
            frappe.throw("Coupon Discount Percentage must be greater than 0")
        
        if not getattr(self, 'coupon_cap_amount', 0) or self.coupon_cap_amount <= 0:
            frappe.throw("Coupon Cap Amount must be greater than 0")


# ==========================================
# TESTING EXAMPLES
# ==========================================

"""
TEST 1: Bundle Fixed Price
==========================
Setup:
- Create Promotion: Type = "Bundle - Fixed Price"
- Bundle Qty = 3
- Fixed Bundle Price = 100
- Based On = "Brand", Source Brands = ["Nike"]

Quotation Items:
1. Nike Shoe A - SAR 45 x 1
2. Nike Shoe B - SAR 40 x 1  
3. Nike Shoe C - SAR 35 x 1
Total: SAR 120

Expected Result:
- 3 items selected (all Nike)
- Original total: 120 SAR
- Fixed price: 100 SAR
- Discount: 20 SAR distributed proportionally:
  * Shoe A: 45/120 * 20 = 7.50 SAR
  * Shoe B: 40/120 * 20 = 6.67 SAR
  * Shoe C: 35/120 * 20 = 5.83 SAR

---

TEST 2: Bundle Percentage
==========================
Setup:
- Create Promotion: Type = "Bundle - Percentage"
- Bundle Qty = 2
- Bundle Discount % = 15
- Based On = "Brand", Source Brands = ["Adidas"]
- Apply to Cheapest Only = Yes

Quotation Items:
1. Adidas T-Shirt - SAR 100 x 1
2. Adidas Pants - SAR 80 x 1
3. Adidas Cap - SAR 50 x 1

Expected Result:
- Only 2 cheapest items discounted:
  * Adidas Cap: 50 SAR - 15% = 42.50 SAR
  * Adidas Pants: 80 SAR - 15% = 68 SAR
- Adidas T-Shirt: No discount (not in cheapest 2)

---

TEST 3: Coupon with Cap
========================
Setup:
- Create Promotion: Type = "Coupon - % with Cap"
- Discount % = 10
- Cap Amount = 50 SAR
- Based On = "Item Group", Source = ["Shoes"]

Quotation Items:
1. Nike Shoe - SAR 300 x 1
2. Adidas Shoe - SAR 400 x 1
Total: SAR 700

Expected Result:
- Calculated discount: 10% of 700 = 70 SAR
- Capped at: 50 SAR
- Distribution:
  * Nike Shoe: 300/700 * 50 = 21.43 SAR
  * Adidas Shoe: 400/700 * 50 = 28.57 SAR
"""


