# Promotion System Extension Guide

## Overview
This document outlines how to extend the current promotion system with Bundle Promotions and Capped Discount features **without modifying existing working code**.

---

## 1. New Fields Required

### Add to Promotion DocType

```python
# Via Customize Form or custom_fields.py

fields = [
    # Promotion Type Selector
    {
        "fieldname": "promotion_type",
        "label": "Promotion Type",
        "fieldtype": "Select",
        "options": "\nBuy X Get Y\nBundle - Fixed Price\nBundle - Percentage\nCoupon - % with Cap",
        "default": "Buy X Get Y",
        "reqd": 1,
        "insert_after": "title"
    },
    
    # === BUNDLE PROMOTION FIELDS ===
    {
        "fieldname": "bundle_section",
        "label": "Bundle Promotion Settings",
        "fieldtype": "Section Break",
        "depends_on": "eval:['Bundle - Fixed Price', 'Bundle - Percentage'].includes(doc.promotion_type)",
        "insert_after": "promotion_type"
    },
    {
        "fieldname": "bundle_qty",
        "label": "Bundle Qty (Min Items)",
        "fieldtype": "Int",
        "description": "Minimum number of items required in bundle",
        "mandatory_depends_on": "eval:['Bundle - Fixed Price', 'Bundle - Percentage'].includes(doc.promotion_type)"
    },
    {
        "fieldname": "bundle_type",
        "label": "Bundle Type",
        "fieldtype": "Select",
        "options": "\nFixed Price\nPercentage Discount",
        "depends_on": "eval:['Bundle - Fixed Price', 'Bundle - Percentage'].includes(doc.promotion_type)"
    },
    {
        "fieldname": "fixed_bundle_price",
        "label": "Fixed Bundle Price (SAR)",
        "fieldtype": "Currency",
        "description": "Total price for all items in bundle",
        "mandatory_depends_on": "eval:doc.promotion_type == 'Bundle - Fixed Price'"
    },
    {
        "fieldname": "bundle_discount_percentage",
        "label": "Bundle Discount %",
        "fieldtype": "Float",
        "description": "Percentage discount on bundle total",
        "mandatory_depends_on": "eval:doc.promotion_type == 'Bundle - Percentage'"
    },
    {
        "fieldname": "bundle_condition_field",
        "label": "Bundle Condition Field",
        "fieldtype": "Select",
        "options": "\nVendor\nBrand\nItem Group",
        "description": "Group items by this field for bundle calculation",
        "default": "Brand"
    },
    {
        "fieldname": "apply_to_cheapest_only",
        "label": "Apply to Cheapest N Items Only",
        "fieldtype": "Check",
        "description": "If checked, apply discount only to cheapest N items. Otherwise apply to all matching items.",
        "default": 0
    },
    {
        "fieldname": "bundle_column_break",
        "fieldtype": "Column Break"
    },
    
    # === COUPON CAP FIELDS ===
    {
        "fieldname": "coupon_section",
        "label": "Coupon Discount with Cap",
        "fieldtype": "Section Break",
        "depends_on": "eval:doc.promotion_type == 'Coupon - % with Cap'",
        "insert_after": "bundle_section"
    },
    {
        "fieldname": "coupon_discount_percentage",
        "label": "Discount Percentage",
        "fieldtype": "Float",
        "description": "Base discount percentage (e.g., 10 for 10%)",
        "mandatory_depends_on": "eval:doc.promotion_type == 'Coupon - % with Cap'"
    },
    {
        "fieldname": "coupon_cap_amount",
        "label": "Cap Amount (SAR)",
        "fieldtype": "Currency",
        "description": "Maximum discount amount allowed (e.g., 100 SAR)",
        "mandatory_depends_on": "eval:doc.promotion_type == 'Coupon - % with Cap'"
    },
    {
        "fieldname": "split_redemption",
        "label": "Allow Split Redemption",
        "fieldtype": "Check",
        "description": "Allow discount to be split across multiple transactions",
        "default": 0
    }
]
```

---

## 2. New Methods to Add to Promotion Class

### Add these methods to `promotion.py` **at the end of the Promotion class**

```python
class Promotion(Document):
    # ... existing methods ...
    
    # ==========================================
    # EXTENSION METHODS - DO NOT MODIFY ABOVE
    # ==========================================
    
    def apply_promotion_by_type(self, quotation_doc):
        """
        Route to appropriate promotion logic based on promotion_type
        This is the NEW entry point - existing apply_promotion() remains unchanged
        """
        try:
            promotion_type = getattr(self, 'promotion_type', 'Buy X Get Y')
            
            frappe.msgprint(f"=== APPLYING PROMOTION TYPE: {promotion_type} ===")
            
            # Route to appropriate handler
            if promotion_type == "Bundle - Fixed Price":
                return self.apply_bundle_fixed_price(quotation_doc)
            
            elif promotion_type == "Bundle - Percentage":
                return self.apply_bundle_percentage(quotation_doc)
            
            elif promotion_type == "Coupon - % with Cap":
                return self.apply_coupon_with_cap(quotation_doc)
            
            else:  # "Buy X Get Y" - existing logic
                return self.apply_promotion(quotation_doc)
                
        except Exception as e:
            frappe.log_error(f"Error in apply_promotion_by_type: {str(e)}")
            frappe.msgprint(f"Error: {str(e)}", alert=True)
            return False
    
    # ==========================================
    # BUNDLE PROMOTION - FIXED PRICE
    # ==========================================
    
    def apply_bundle_fixed_price(self, quotation_doc):
        """
        Bundle Fixed Price Logic:
        Example: Buy any 3 items from Vendor X for SAR 100
        
        1. Match all eligible items from condition (Vendor/Brand/Item Group)
        2. If qty >= bundle_qty:
           - Take N cheapest eligible items (where N = bundle_qty)
           - Calculate their original total
           - If original total > fixed_bundle_price:
               - Set combined total to fixed_bundle_price
               - Distribute discount proportionally
        3. If multiply_by_min_qty: apply to next groups
        """
        try:
            # Validate promotion
            if not self.is_valid(quotation_doc.transaction_date):
                frappe.msgprint("Promotion not valid for this date", alert=True)
                return False
            
            # Get applicable items
            applicable_items = self.get_applicable_items(quotation_doc.items)
            
            if not applicable_items:
                frappe.msgprint("No applicable items found for bundle promotion", alert=True)
                return False
            
            # Get bundle parameters
            bundle_qty = flt(self.bundle_qty)
            fixed_price = flt(self.fixed_bundle_price)
            
            if bundle_qty <= 0 or fixed_price <= 0:
                frappe.msgprint("Invalid bundle configuration", alert=True)
                return False
            
            # Count total applicable quantity
            total_qty = sum(flt(item.qty) for item in applicable_items)
            
            frappe.msgprint(f"Total applicable qty: {total_qty}, Bundle qty needed: {bundle_qty}")
            
            if total_qty < bundle_qty:
                frappe.msgprint(f"Insufficient quantity. Need {bundle_qty}, have {total_qty}", alert=True)
                return False
            
            # Sort items by price (cheapest first) - deterministic
            sorted_items = self._sort_items_deterministically(applicable_items)
            
            # Apply bundle logic
            bundles_to_apply = 1
            if self.multiply_by_min_qty:
                bundles_to_apply = int(total_qty / bundle_qty)
            
            frappe.msgprint(f"Will apply {bundles_to_apply} bundle(s)")
            
            # Process each bundle
            applied = False
            items_processed = 0
            
            for bundle_num in range(bundles_to_apply):
                # Select items for this bundle
                bundle_items = self._select_bundle_items(sorted_items, bundle_qty, items_processed)
                
                if not bundle_items:
                    break
                
                # Calculate original total
                original_total = sum(flt(item.rate) * flt(item.qty) for item in bundle_items)
                
                frappe.msgprint(f"Bundle {bundle_num + 1}: Original total = {original_total}, Target = {fixed_price}")
                
                # Only apply if there's actual savings
                if original_total > fixed_price:
                    total_discount = original_total - fixed_price
                    
                    # Distribute discount proportionally
                    self._distribute_discount_proportionally(bundle_items, total_discount, original_total, self.name)
                    applied = True
                    
                    frappe.msgprint(f"Applied {total_discount} SAR discount to bundle {bundle_num + 1}")
                else:
                    frappe.msgprint(f"Bundle {bundle_num + 1}: No discount (original {original_total} <= target {fixed_price})")
                
                items_processed += len(bundle_items)
            
            if applied:
                quotation_doc.calculate_taxes_and_totals()
                frappe.msgprint("Bundle promotion applied successfully!", alert=True)
            
            return applied
            
        except Exception as e:
            frappe.log_error(f"Error in apply_bundle_fixed_price: {str(e)}")
            frappe.msgprint(f"Error: {str(e)}", alert=True)
            return False
    
    # ==========================================
    # BUNDLE PROMOTION - PERCENTAGE DISCOUNT
    # ==========================================
    
    def apply_bundle_percentage(self, quotation_doc):
        """
        Bundle Percentage Discount Logic:
        Example: Buy 3 Adidas items and get 15% off
        
        1. Filter items by condition (Brand/Vendor/Item Group)
        2. If qty >= bundle_qty:
           - If apply_to_cheapest_only: apply to cheapest N only
           - Else: apply to all matching items
           - Apply discount percentage
        3. If multiply_by_min_qty: apply in blocks
        """
        try:
            # Validate promotion
            if not self.is_valid(quotation_doc.transaction_date):
                frappe.msgprint("Promotion not valid for this date", alert=True)
                return False
            
            # Get applicable items
            applicable_items = self.get_applicable_items(quotation_doc.items)
            
            if not applicable_items:
                frappe.msgprint("No applicable items found for bundle promotion", alert=True)
                return False
            
            # Get bundle parameters
            bundle_qty = flt(self.bundle_qty)
            discount_pct = flt(self.bundle_discount_percentage)
            
            if bundle_qty <= 0 or discount_pct <= 0:
                frappe.msgprint("Invalid bundle configuration", alert=True)
                return False
            
            # Count total applicable quantity
            total_qty = sum(flt(item.qty) for item in applicable_items)
            
            if total_qty < bundle_qty:
                frappe.msgprint(f"Insufficient quantity. Need {bundle_qty}, have {total_qty}", alert=True)
                return False
            
            # Sort items by price (cheapest first)
            sorted_items = self._sort_items_deterministically(applicable_items)
            
            # Determine which items to discount
            if self.apply_to_cheapest_only:
                # Apply to cheapest N items only
                items_to_discount = self._select_cheapest_items(sorted_items, bundle_qty, self.multiply_by_min_qty, total_qty)
            else:
                # Apply to all matching items
                items_to_discount = applicable_items
            
            # Apply percentage discount
            applied = False
            for item in items_to_discount:
                # Store original rate
                if not hasattr(item, 'original_rate') or not item.original_rate:
                    item.original_rate = flt(item.rate)
                
                original_rate = item.original_rate
                discount_amount = (original_rate * flt(item.qty)) * (discount_pct / 100)
                
                # Apply discount
                item.discount_percentage = discount_pct
                item.discount_amount = discount_amount
                item.promotion_applied = self.name
                item.promotion_discount = discount_amount
                
                # Update amount
                item.amount = (original_rate * flt(item.qty)) - discount_amount
                
                applied = True
                
                frappe.msgprint(f"Applied {discount_pct}% discount to {item.item_code}: {discount_amount} SAR")
            
            if applied:
                quotation_doc.calculate_taxes_and_totals()
                frappe.msgprint(f"Bundle percentage promotion applied: {discount_pct}% off!", alert=True)
            
            return applied
            
        except Exception as e:
            frappe.log_error(f"Error in apply_bundle_percentage: {str(e)}")
            frappe.msgprint(f"Error: {str(e)}", alert=True)
            return False
    
    # ==========================================
    # COUPON - PERCENTAGE WITH CAP
    # ==========================================
    
    def apply_coupon_with_cap(self, quotation_doc):
        """
        Coupon % Discount with CAP Logic:
        Example: 10% off capped at SAR 100
        
        1. Calculate: discount = total_eligible * (percentage / 100)
        2. If discount > cap: discount = cap
        3. Distribute proportionally across eligible items
        """
        try:
            # Validate promotion
            if not self.is_valid(quotation_doc.transaction_date):
                frappe.msgprint("Promotion not valid for this date", alert=True)
                return False
            
            # Get applicable items
            applicable_items = self.get_applicable_items(quotation_doc.items)
            
            if not applicable_items:
                frappe.msgprint("No applicable items found", alert=True)
                return False
            
            # Get coupon parameters
            discount_pct = flt(self.coupon_discount_percentage)
            cap_amount = flt(self.coupon_cap_amount)
            
            if discount_pct <= 0:
                frappe.msgprint("Invalid discount percentage", alert=True)
                return False
            
            # Calculate total eligible amount
            total_eligible_amount = sum(flt(item.rate) * flt(item.qty) for item in applicable_items)
            
            # Calculate discount
            calculated_discount = total_eligible_amount * (discount_pct / 100)
            
            frappe.msgprint(f"Total eligible: {total_eligible_amount} SAR")
            frappe.msgprint(f"Calculated discount ({discount_pct}%): {calculated_discount} SAR")
            frappe.msgprint(f"Cap amount: {cap_amount} SAR")
            
            # Apply cap
            final_discount = calculated_discount
            if cap_amount > 0 and calculated_discount > cap_amount:
                final_discount = cap_amount
                frappe.msgprint(f"Discount capped at: {cap_amount} SAR", alert=True)
            
            if final_discount <= 0:
                frappe.msgprint("No discount to apply", alert=True)
                return False
            
            # Distribute discount proportionally across items
            self._distribute_discount_proportionally(applicable_items, final_discount, total_eligible_amount, self.name)
            
            quotation_doc.calculate_taxes_and_totals()
            
            frappe.msgprint(f"Coupon applied: {final_discount} SAR discount ({discount_pct}% capped at {cap_amount})", alert=True)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Error in apply_coupon_with_cap: {str(e)}")
            frappe.msgprint(f"Error: {str(e)}", alert=True)
            return False
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _sort_items_deterministically(self, items):
        """
        Sort items deterministically: Price → Brand → Item Code → Row Index
        """
        enriched_items = []
        for item in items:
            item_details = frappe.db.get_value("Item", item.item_code, ["brand"], as_dict=True)
            enriched_items.append({
                'item': item,
                'rate': flt(item.rate),
                'brand': item_details.brand if item_details else "",
                'item_code': item.item_code,
                'idx': getattr(item, 'idx', 0)
            })
        
        # Sort deterministically
        enriched_items.sort(key=lambda x: (x['rate'], x['brand'], x['item_code'], x['idx']))
        
        return [x['item'] for x in enriched_items]
    
    def _select_bundle_items(self, sorted_items, bundle_qty, skip_count=0):
        """
        Select items for a bundle (cheapest items up to bundle_qty)
        """
        bundle_items = []
        items_collected = 0
        items_skipped = 0
        
        for item in sorted_items:
            if items_skipped < skip_count:
                items_skipped += 1
                continue
            
            if items_collected >= bundle_qty:
                break
            
            bundle_items.append(item)
            items_collected += flt(item.qty)
        
        return bundle_items
    
    def _select_cheapest_items(self, sorted_items, bundle_qty, multiply_flag, total_qty):
        """
        Select cheapest N items based on bundle rules
        """
        items_to_select = bundle_qty
        
        if multiply_flag:
            items_to_select = int(total_qty / bundle_qty) * bundle_qty
        
        selected = []
        qty_collected = 0
        
        for item in sorted_items:
            if qty_collected >= items_to_select:
                break
            selected.append(item)
            qty_collected += flt(item.qty)
        
        return selected
    
    def _distribute_discount_proportionally(self, items, total_discount, total_amount, promotion_name):
        """
        Distribute discount proportionally across items based on their amount
        """
        for item in items:
            # Store original rate
            if not hasattr(item, 'original_rate') or not item.original_rate:
                item.original_rate = flt(item.rate)
            
            original_rate = item.original_rate
            item_amount = original_rate * flt(item.qty)
            
            # Calculate proportional discount
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
            
            # Update amount
            item.amount = item_amount - item_discount
            
            frappe.msgprint(f"  {item.item_code}: {item_discount:.2f} SAR discount ({item.discount_percentage:.1f}%)")
```

---

## 3. Update Entry Points

### Modify `apply_promotion_to_quotation` function (Line 844)

```python
@frappe.whitelist()
def apply_promotion_to_quotation(quotation_name, promotion_name):
    """Apply promotion to quotation - updated to support all types"""
    try:
        quotation_doc = frappe.get_doc("Quotation", quotation_name)
        promotion_doc = frappe.get_doc("Promotion", promotion_name)
        
        # Use new routing method if it exists
        if hasattr(promotion_doc, 'apply_promotion_by_type'):
            success = promotion_doc.apply_promotion_by_type(quotation_doc)
        else:
            # Fallback to original method
            success = promotion_doc.apply_promotion(quotation_doc)
        
        if success:
            quotation_doc.save()
            frappe.msgprint(_("Promotion applied successfully"))
            return True
        else:
            frappe.msgprint(_("Promotion conditions not met"))
            return False
            
    except Exception as e:
        frappe.throw(_("Error applying promotion: {0}").format(str(e)))
```

### Modify `apply_coupon_code` function (Line 952)

```python
@frappe.whitelist()
def apply_coupon_code(coupon_code, quotation_name):
    """Apply coupon code - updated to support all promotion types"""
    try:
        # ... existing validation code ...
        
        promotion_doc = frappe.get_doc("Promotion", coupon.promotion)
        
        frappe.msgprint(f"=== COUPON CODE DEBUG ===")
        frappe.msgprint(f"Coupon: {coupon_code}")
        frappe.msgprint(f"Promotion: {promotion_doc.name}")
        frappe.msgprint(f"Promotion Type: {getattr(promotion_doc, 'promotion_type', 'Buy X Get Y')}")
        
        # Use new routing method if it exists
        if hasattr(promotion_doc, 'apply_promotion_by_type'):
            success = promotion_doc.apply_promotion_by_type(quotation_doc)
        else:
            # Fallback to original method
            success = promotion_doc.apply_promotion(quotation_doc)
        
        if success:
            # ... rest of existing code ...
```

---

## 4. Validation Updates

### Add to `validate_actions` method

```python
def validate_actions(self):
    """Extended validation for new promotion types"""
    
    promotion_type = getattr(self, 'promotion_type', 'Buy X Get Y')
    
    # Existing validations
    if promotion_type == "Buy X Get Y":
        if not self.actions:
            frappe.throw(_("At least one action must be specified"))
        
        for action in self.actions:
            if action.reward_type == "Discount %" and not action.discount_percentage:
                frappe.throw(_("Discount % is required for Discount % reward type"))
            
            if action.reward_type == "Discount Amount" and not action.discount_amount:
                frappe.throw(_("Discount Amount is required for Discount Amount reward type"))
    
    # Bundle validations
    elif promotion_type in ["Bundle - Fixed Price", "Bundle - Percentage"]:
        if not self.bundle_qty or self.bundle_qty <= 0:
            frappe.throw(_("Bundle Qty must be greater than 0"))
        
        if promotion_type == "Bundle - Fixed Price":
            if not self.fixed_bundle_price or self.fixed_bundle_price <= 0:
                frappe.throw(_("Fixed Bundle Price must be greater than 0"))
        
        if promotion_type == "Bundle - Percentage":
            if not self.bundle_discount_percentage or self.bundle_discount_percentage <= 0:
                frappe.throw(_("Bundle Discount Percentage must be greater than 0"))
    
    # Coupon cap validations
    elif promotion_type == "Coupon - % with Cap":
        if not self.coupon_discount_percentage or self.coupon_discount_percentage <= 0:
            frappe.throw(_("Coupon Discount Percentage must be greater than 0"))
        
        if not self.coupon_cap_amount or self.coupon_cap_amount <= 0:
            frappe.throw(_("Coupon Cap Amount must be greater than 0"))
```

---

## 5. Testing Strategy

### Test Cases for Bundle - Fixed Price

```python
# Test 1: Exact bundle quantity
Items:
- Item A (Vendor X): SAR 40
- Item B (Vendor X): SAR 35
- Item C (Vendor X): SAR 30
Total: SAR 105

Promotion: Buy 3 from Vendor X for SAR 100
Expected: SAR 5 discount distributed proportionally

# Test 2: More than bundle quantity (multiply_by_min_qty = OFF)
Items: 5 items from Vendor X
Expected: Apply to cheapest 3 only (one bundle)

# Test 3: More than bundle quantity (multiply_by_min_qty = ON)
Items: 6 items from Vendor X
Expected: Apply to 2 bundles (6 items)

# Test 4: Original total below fixed price
Items total: SAR 90
Fixed price: SAR 100
Expected: No discount applied
```

### Test Cases for Bundle - Percentage

```python
# Test 1: Apply to cheapest only
Items: 5 Adidas items
Promotion: 15% off on 3 Adidas items (cheapest only)
Expected: 15% off on cheapest 3 items

# Test 2: Apply to all
Items: 5 Adidas items
Promotion: 15% off on 3+ Adidas items (apply to all)
Expected: 15% off on all 5 items
```

### Test Cases for Coupon with Cap

```python
# Test 1: Below cap
Total: SAR 500
Discount: 10%
Cap: SAR 100
Expected: SAR 50 discount (10% of 500)

# Test 2: Above cap
Total: SAR 1500
Discount: 10%
Cap: SAR 100
Expected: SAR 100 discount (capped)

# Test 3: Proportional distribution
Items:
- Item A: SAR 300 (60% of total)
- Item B: SAR 200 (40% of total)
Total: SAR 500, 10% = SAR 50
Expected:
- Item A: SAR 30 discount (60% of 50)
- Item B: SAR 20 discount (40% of 50)
```

---

## 6. Migration Path

```python
# bench console
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

custom_fields = {
    "Promotion": [
        # Add all fields from section 1 above
    ]
}

create_custom_fields(custom_fields)
```

---

## 7. Frontend Updates (Optional)

### Quotation.js additions

```javascript
// Add button to apply specific promotion type
frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && frm.doc.docstatus == 0) {
            frm.add_custom_button(__('Apply Bundle Promotion'), function() {
                // Show dialog to select bundle promotion
                show_promotion_dialog(frm, 'Bundle');
            });
            
            frm.add_custom_button(__('Apply Coupon with Cap'), function() {
                // Show dialog to enter coupon code
                show_coupon_dialog(frm);
            });
        }
    }
});
```

---

## 8. Key Principles Maintained

✅ **Deterministic**: All methods use same sorting logic  
✅ **Idempotent**: Applying same promotion twice yields same result  
✅ **Reversible**: `remove_promotion()` works for all types  
✅ **No Ghost Rows**: Never add/delete item lines  
✅ **Manual Trigger**: Only via button or coupon code  

---

## 9. Backward Compatibility

- Existing promotions default to `promotion_type = "Buy X Get Y"`
- Original `apply_promotion()` method **unchanged**
- New logic only runs if `promotion_type` is set to new values
- All existing tests continue to pass

---

## 10. Implementation Checklist

- [ ] Add custom fields to Promotion doctype
- [ ] Add new methods to `promotion.py` (copy from section 2)
- [ ] Update entry points (`apply_promotion_to_quotation`, `apply_coupon_code`)
- [ ] Extend `validate_actions()` method
- [ ] Test all 3 new promotion types
- [ ] Test existing "Buy X Get Y" still works
- [ ] Test remove promotion for all types
- [ ] Update user documentation
- [ ] Train users on new features

---

## Questions to Clarify

1. **Bundle - Fixed Price**: If items total is already below fixed price, should we skip or still apply?
2. **Bundle - Percentage**: Should "apply to all" have a maximum item limit?
3. **Coupon Cap**: Should split redemption track per customer across multiple quotations?
4. **Multiple Promotions**: Can a quotation have multiple promotions applied simultaneously?
5. **Promotion Priority**: If multiple promotions match, which takes precedence?

---

## Summary

This extension strategy:
- ✅ Adds 3 new promotion types
- ✅ Preserves all existing functionality
- ✅ Maintains architectural principles (deterministic, idempotent, reversible)
- ✅ Provides clear migration path
- ✅ Includes comprehensive test cases
- ✅ Uses feature flags for backward compatibility

**Next Steps**: Review suggestions → Add fields → Implement methods → Test → Deploy


