# Step-by-Step Implementation Guide
## Bundle Promotions & Coupon Cap Extension

---

## ⚠️ IMPORTANT - Read First

**This guide extends your working promotion system WITHOUT modifying existing code.**

- ✅ Existing "Buy X Get Y" promotions continue working
- ✅ All changes are additive (new methods, new fields)
- ✅ Backward compatible
- ✅ Can be rolled back if needed

**Estimated Time**: 2-3 hours

---

## 📋 Prerequisites

- [ ] Backup your database
- [ ] Access to Frappe bench
- [ ] Administrator access to ERPNext
- [ ] Current promotion system working correctly

---

## STEP 1: Backup Current System

```bash
# Navigate to bench directory
cd /home/erpnext/frappe-bench

# Backup database
bench --site [your-site-name] backup

# Backup promotion.py file
cp apps/promotion/promotion/promotion/doctype/promotion/promotion.py \
   apps/promotion/promotion/promotion/doctype/promotion/promotion.py.backup

# Verify backup created
ls -lh sites/[your-site-name]/private/backups/
```

**Expected Output**: 
```
✅ Database backup: [timestamp]-[site]-database.sql.gz
✅ promotion.py.backup created
```

---

## STEP 2: Add Custom Fields to Promotion DocType

### Option A: Via UI (Recommended for Testing)

1. **Login to ERPNext** as Administrator

2. **Go to**: Customize Form

3. **Select DocType**: Promotion

4. **Add New Field** with these details:

#### Field 1: Promotion Type
```
Label: Promotion Type
Field Name: promotion_type
Field Type: Select
Options: 
  Buy X Get Y
  Bundle - Fixed Price
  Bundle - Percentage
  Coupon - % with Cap
Default: Buy X Get Y
Mandatory: Yes
Insert After: title
```

#### Field 2: Bundle Section Break
```
Label: Bundle Promotion Settings
Field Name: bundle_section
Field Type: Section Break
Depends On: eval:['Bundle - Fixed Price', 'Bundle - Percentage'].includes(doc.promotion_type)
Insert After: promotion_type
```

#### Field 3: Bundle Qty
```
Label: Bundle Qty
Field Name: bundle_qty
Field Type: Int
Description: Minimum number of items required in bundle
Mandatory Depends On: eval:['Bundle - Fixed Price', 'Bundle - Percentage'].includes(doc.promotion_type)
Insert After: bundle_section
```

#### Field 4: Bundle Condition Field
```
Label: Bundle Condition
Field Name: bundle_condition_field
Field Type: Select
Options:
  Vendor
  Brand
  Item Group
Default: Brand
Description: Group items by this field for bundle calculation
Depends On: eval:['Bundle - Fixed Price', 'Bundle - Percentage'].includes(doc.promotion_type)
Insert After: bundle_qty
```

#### Field 5: Column Break
```
Field Name: bundle_column_break_1
Field Type: Column Break
Insert After: bundle_condition_field
```

#### Field 6: Apply to Cheapest Only
```
Label: Apply to Cheapest Items Only
Field Name: apply_to_cheapest_only
Field Type: Check
Default: 0
Description: If checked, apply discount only to cheapest N items
Depends On: eval:doc.promotion_type == 'Bundle - Percentage'
Insert After: bundle_column_break_1
```

#### Field 7: Fixed Price Section
```
Label: Fixed Price Settings
Field Name: fixed_price_section
Field Type: Section Break
Depends On: eval:doc.promotion_type == 'Bundle - Fixed Price'
Insert After: apply_to_cheapest_only
```

#### Field 8: Fixed Bundle Price
```
Label: Fixed Bundle Price
Field Name: fixed_bundle_price
Field Type: Currency
Description: Total price for all items in bundle
Mandatory Depends On: eval:doc.promotion_type == 'Bundle - Fixed Price'
Insert After: fixed_price_section
```

#### Field 9: Percentage Section
```
Label: Percentage Discount Settings
Field Name: percentage_section
Field Type: Section Break
Depends On: eval:doc.promotion_type == 'Bundle - Percentage'
Insert After: fixed_bundle_price
```

#### Field 10: Bundle Discount Percentage
```
Label: Bundle Discount %
Field Name: bundle_discount_percentage
Field Type: Float
Description: Percentage discount on bundle
Mandatory Depends On: eval:doc.promotion_type == 'Bundle - Percentage'
Insert After: percentage_section
```

#### Field 11: Coupon Section
```
Label: Coupon Discount with Cap
Field Name: coupon_section
Field Type: Section Break
Depends On: eval:doc.promotion_type == 'Coupon - % with Cap'
Insert After: bundle_discount_percentage
```

#### Field 12: Coupon Discount Percentage
```
Label: Discount Percentage
Field Name: coupon_discount_percentage
Field Type: Float
Description: Base discount percentage (e.g., 10 for 10%)
Mandatory Depends On: eval:doc.promotion_type == 'Coupon - % with Cap'
Insert After: coupon_section
```

#### Field 13: Coupon Cap Amount
```
Label: Cap Amount
Field Name: coupon_cap_amount
Field Type: Currency
Description: Maximum discount amount allowed
Mandatory Depends On: eval:doc.promotion_type == 'Coupon - % with Cap'
Insert After: coupon_discount_percentage
```

#### Field 14: Coupon Column Break
```
Field Name: coupon_column_break
Field Type: Column Break
Insert After: coupon_cap_amount
```

#### Field 15: Split Redemption
```
Label: Allow Split Redemption
Field Name: split_redemption
Field Type: Check
Default: 0
Description: Allow discount to be split across multiple transactions
Depends On: eval:doc.promotion_type == 'Coupon - % with Cap'
Insert After: coupon_column_break
```

5. **Click**: Update

6. **Verify**: Open a Promotion document, you should see new fields

---

### Option B: Via Code (For Production)

```bash
# Navigate to bench
cd /home/erpnext/frappe-bench

# Open bench console
bench --site [your-site-name] console
```

```python
# In the console, run:
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

custom_fields = {
    "Promotion": [
        {
            "fieldname": "promotion_type",
            "label": "Promotion Type",
            "fieldtype": "Select",
            "options": "Buy X Get Y\nBundle - Fixed Price\nBundle - Percentage\nCoupon - % with Cap",
            "default": "Buy X Get Y",
            "reqd": 1,
            "insert_after": "title"
        },
        # Add all 15 fields here from custom_fields_config.json
        # (Copy from the JSON file provided)
    ]
}

create_custom_fields(custom_fields)
frappe.db.commit()
exit()
```

**Expected Output**: 
```
✅ Custom fields created successfully
```

---

## STEP 3: Update Existing Promotions

```bash
# Open bench console
bench --site [your-site-name] console
```

```python
import frappe

# Update all existing promotions to "Buy X Get Y" type
promotions = frappe.get_all("Promotion")

for promo in promotions:
    doc = frappe.get_doc("Promotion", promo.name)
    if not hasattr(doc, 'promotion_type') or not doc.promotion_type:
        doc.promotion_type = "Buy X Get Y"
        doc.save()
        print(f"Updated {doc.name}")

frappe.db.commit()
print("\n✅ All existing promotions updated to 'Buy X Get Y' type")
exit()
```

**Expected Output**: 
```
Updated PROMO-0001
Updated PROMO-0002
...
✅ All existing promotions updated to 'Buy X Get Y' type
```

---

## STEP 4: Add New Methods to promotion.py

**Location**: `/home/erpnext/frappe-bench/apps/promotion/promotion/promotion/doctype/promotion/promotion.py`

### 4.1: Open the file

```bash
cd /home/erpnext/frappe-bench
nano apps/promotion/promotion/promotion/doctype/promotion/promotion.py
```

### 4.2: Add new methods AFTER line 786 (after `get_promotion_summary` method)

Copy the following methods from `IMPLEMENTATION_EXAMPLE.py`:

```python
# ==========================================
# EXTENSION METHODS - ADD AFTER LINE 786
# ==========================================

def apply_promotion_by_type(self, quotation_doc):
    """Route to appropriate promotion logic based on promotion_type"""
    # [Copy full method from IMPLEMENTATION_EXAMPLE.py]

def apply_bundle_fixed_price(self, quotation_doc):
    """Bundle Fixed Price Logic"""
    # [Copy full method from IMPLEMENTATION_EXAMPLE.py]

def apply_bundle_percentage(self, quotation_doc):
    """Bundle Percentage Discount Logic"""
    # [Copy full method from IMPLEMENTATION_EXAMPLE.py]

def apply_coupon_with_cap(self, quotation_doc):
    """Coupon % Discount with CAP Logic"""
    # [Copy full method from IMPLEMENTATION_EXAMPLE.py]

def _sort_items_for_bundle(self, items):
    """Sort items deterministically"""
    # [Copy full method from IMPLEMENTATION_EXAMPLE.py]

def _distribute_discount_proportionally(self, items, total_discount, total_amount, promotion_name):
    """Distribute discount proportionally"""
    # [Copy full method from IMPLEMENTATION_EXAMPLE.py]
```

**Full code available in**: `IMPLEMENTATION_EXAMPLE.py` lines 30-300

---

## STEP 5: Update Entry Point Functions

### 5.1: Update `apply_promotion_to_quotation` (around line 844)

**FIND** this code:
```python
@frappe.whitelist()
def apply_promotion_to_quotation(quotation_name, promotion_name):
    """Apply promotion to quotation"""
    try:
        quotation_doc = frappe.get_doc("Quotation", quotation_name)
        promotion_doc = frappe.get_doc("Promotion", promotion_name)
        
        if promotion_doc.apply_promotion(quotation_doc):
            quotation_doc.save()
            frappe.msgprint(_("Promotion applied successfully"))
            return True
```

**REPLACE** the line `if promotion_doc.apply_promotion(quotation_doc):` with:

```python
        # Route to appropriate method
        if hasattr(promotion_doc, 'apply_promotion_by_type'):
            success = promotion_doc.apply_promotion_by_type(quotation_doc)
        else:
            success = promotion_doc.apply_promotion(quotation_doc)
        
        if success:
```

### 5.2: Update `apply_coupon_code` (around line 978)

**FIND** this code:
```python
        frappe.msgprint(f"Calling apply_promotion method...")
        if promotion_doc.apply_promotion(quotation_doc):
```

**REPLACE** with:
```python
        frappe.msgprint(f"Calling apply_promotion method...")
        
        # Route to appropriate method
        if hasattr(promotion_doc, 'apply_promotion_by_type'):
            success = promotion_doc.apply_promotion_by_type(quotation_doc)
        else:
            success = promotion_doc.apply_promotion(quotation_doc)
        
        if success:
```

---

## STEP 6: Update Validation (Optional but Recommended)

**FIND** the `validate_actions` method (around line 36):

**ADD** this code at the END of the method:

```python
def validate_actions(self):
    # ... existing code ...
    
    # NEW: Add validation for new promotion types
    promotion_type = getattr(self, 'promotion_type', 'Buy X Get Y')
    
    if promotion_type in ["Bundle - Fixed Price", "Bundle - Percentage"]:
        if not getattr(self, 'bundle_qty', 0) or self.bundle_qty <= 0:
            frappe.throw(_("Bundle Qty must be greater than 0"))
        
        if promotion_type == "Bundle - Fixed Price":
            if not getattr(self, 'fixed_bundle_price', 0) or self.fixed_bundle_price <= 0:
                frappe.throw(_("Fixed Bundle Price must be greater than 0"))
        
        if promotion_type == "Bundle - Percentage":
            if not getattr(self, 'bundle_discount_percentage', 0) or self.bundle_discount_percentage <= 0:
                frappe.throw(_("Bundle Discount Percentage must be greater than 0"))
    
    elif promotion_type == "Coupon - % with Cap":
        if not getattr(self, 'coupon_discount_percentage', 0) or self.coupon_discount_percentage <= 0:
            frappe.throw(_("Coupon Discount Percentage must be greater than 0"))
        
        if not getattr(self, 'coupon_cap_amount', 0) or self.coupon_cap_amount <= 0:
            frappe.throw(_("Coupon Cap Amount must be greater than 0"))
```

---

## STEP 7: Restart Services

```bash
cd /home/erpnext/frappe-bench

# Clear cache
bench --site [your-site-name] clear-cache

# Restart bench
bench restart
```

**Expected Output**: 
```
✅ Cache cleared
✅ Services restarted
```

---

## STEP 8: Test Existing Promotions

### 8.1: Test "Buy X Get Y" Still Works

1. **Create a test quotation** with items matching an existing promotion
2. **Apply the promotion**
3. **Verify**: Discount applied correctly
4. **Click "Remove Promotion"**
5. **Verify**: Original prices restored

**Expected Result**: ✅ No changes in behavior

---

## STEP 9: Test New Promotion Types

### Test 1: Bundle - Fixed Price

```
1. Create Promotion:
   - Name: "3-for-100-Nike"
   - Promotion Type: Bundle - Fixed Price
   - Based On: Brand
   - Source Brands: Nike
   - Bundle Qty: 3
   - Fixed Bundle Price: 100
   - Valid From/To: Today

2. Create Quotation with:
   - Item 1: Nike Shoe A - SAR 45 x 1
   - Item 2: Nike Shoe B - SAR 40 x 1
   - Item 3: Nike Shoe C - SAR 35 x 1
   Total: SAR 120

3. Apply Promotion:
   - Click "Apply Promotion"
   - Select "3-for-100-Nike"

4. Expected Result:
   - Item 1: SAR 37.50 (45 - 7.50)
   - Item 2: SAR 33.33 (40 - 6.67)
   - Item 3: SAR 29.17 (35 - 5.83)
   - Total: SAR 100 ✅

5. Test Remove:
   - Click "Remove Promotion"
   - Total should return to SAR 120 ✅
```

### Test 2: Bundle - Percentage

```
1. Create Promotion:
   - Name: "Adidas-15%-Off"
   - Promotion Type: Bundle - Percentage
   - Based On: Brand
   - Source Brands: Adidas
   - Bundle Qty: 2
   - Bundle Discount %: 15
   - Apply to Cheapest Only: Yes

2. Create Quotation with:
   - Item 1: Adidas T-Shirt - SAR 100 x 1
   - Item 2: Adidas Pants - SAR 80 x 1
   - Item 3: Adidas Cap - SAR 50 x 1

3. Apply Promotion

4. Expected Result:
   - Cap: 50 - 15% = SAR 42.50 ✅
   - Pants: 80 - 15% = SAR 68.00 ✅
   - T-Shirt: SAR 100 (no discount - not in cheapest 2)
```

### Test 3: Coupon - % with Cap

```
1. Create Promotion:
   - Name: "10%-Capped-50"
   - Promotion Type: Coupon - % with Cap
   - Based On: Item Group
   - Source Item Groups: All
   - Coupon Discount %: 10
   - Coupon Cap Amount: 50

2. Create Coupon Code:
   - Coupon Code: SAVE10
   - Promotion: 10%-Capped-50

3. Create Quotation with:
   - Item 1: Product A - SAR 300 x 1
   - Item 2: Product B - SAR 400 x 1
   Total: SAR 700

4. Apply Coupon: SAVE10

5. Expected Result:
   - 10% of 700 = 70 SAR
   - Capped at 50 SAR
   - Product A: 300 - 21.43 = 278.57 (60% of discount)
   - Product B: 400 - 28.57 = 371.43 (40% of discount)
   - Total: 650 SAR (50 SAR saved) ✅
```

---

## STEP 10: Edge Case Testing

### Test 1: Bundle Below Fixed Price
```
Items total: SAR 90
Fixed Price: SAR 100
Expected: No discount applied ✅
```

### Test 2: Insufficient Quantity
```
Bundle Qty: 3
Items in cart: 2
Expected: Error message "Insufficient quantity" ✅
```

### Test 3: Multiple Bundles (multiply_by_min_qty = ON)
```
Bundle Qty: 3
Items in cart: 6
Expected: 2 bundles applied ✅
```

---

## STEP 11: User Training

### Create User Documentation

**Bundle - Fixed Price Example**:
```
"Buy any 3 Nike items for SAR 100"

How it works:
1. Customer adds 3+ Nike items
2. System selects cheapest 3 items
3. Total price set to SAR 100
4. Savings distributed proportionally
```

**Bundle - Percentage Example**:
```
"Buy 2 Adidas items, get 15% off"

How it works:
1. Customer adds 2+ Adidas items
2. If "cheapest only": discount applies to cheapest items
3. If "all items": discount applies to all
```

**Coupon with Cap Example**:
```
"10% off, maximum SAR 100 discount"

How it works:
1. Customer enters coupon code
2. 10% calculated on total
3. If over SAR 100, discount capped at SAR 100
4. Discount distributed proportionally
```

---

## 🚨 Troubleshooting

### Issue: "promotion_type field not found"

**Solution**:
```bash
bench --site [your-site-name] clear-cache
bench restart
```

### Issue: "Method apply_promotion_by_type not found"

**Solution**: Verify Step 4 completed correctly
```bash
grep -n "apply_promotion_by_type" apps/promotion/promotion/promotion/doctype/promotion/promotion.py
```
Should return line number where method is defined.

### Issue: Existing promotions not working

**Solution**: 
1. Check promotion_type is set to "Buy X Get Y"
2. Verify Step 3 completed successfully

### Issue: New promotions not applying

**Solution**: 
1. Check validation messages
2. Verify field values are set correctly
3. Check console for errors (F12 in browser)

---

## 📊 Verification Checklist

After implementation, verify:

- [ ] All existing "Buy X Get Y" promotions still work
- [ ] Can create "Bundle - Fixed Price" promotion
- [ ] Can create "Bundle - Percentage" promotion
- [ ] Can create "Coupon - % with Cap" promotion
- [ ] Fields show/hide based on promotion_type
- [ ] Validation works for all types
- [ ] Remove promotion works for all types
- [ ] Discounts calculate correctly
- [ ] Proportional distribution is accurate
- [ ] Cheapest items selected correctly
- [ ] Cap is applied correctly
- [ ] Multiply by min qty works
- [ ] Apply to cheapest only works

---

## 🔄 Rollback Procedure

If issues arise:

```bash
cd /home/erpnext/frappe-bench

# Restore promotion.py
cp apps/promotion/promotion/promotion/doctype/promotion/promotion.py.backup \
   apps/promotion/promotion/promotion/doctype/promotion/promotion.py

# Restart
bench restart

# Restore database (if needed)
bench --site [your-site-name] restore [backup-file-path]
```

---

## 📈 Success Criteria

Implementation is successful when:

1. ✅ All existing promotions work unchanged
2. ✅ 3 new promotion types can be created
3. ✅ All test cases pass
4. ✅ Remove promotion restores original state
5. ✅ No console errors
6. ✅ Users can create and apply new promotions

---

## 📞 Support

If you encounter issues:

1. Check `ARCHITECTURE_DIAGRAM.md` for flow diagrams
2. Review `EXTENSION_SUGGESTIONS.md` for detailed logic
3. Examine `IMPLEMENTATION_EXAMPLE.py` for code examples
4. Check Frappe/ERPNext logs:
   ```bash
   tail -f logs/web.log
   tail -f logs/worker.log
   ```

---

## 📝 Post-Implementation

After successful implementation:

1. **Document** new promotion types in user manual
2. **Train** staff on creating new promotions
3. **Monitor** first week of usage
4. **Gather** user feedback
5. **Optimize** based on real-world usage

---

**Implementation Date**: _______________  
**Implemented By**: _______________  
**Tested By**: _______________  
**Status**: ⬜ Pending | ⬜ In Progress | ⬜ Complete

---

## 🎉 Congratulations!

You've successfully extended your promotion system with:
- ✅ Bundle Fixed Price promotions
- ✅ Bundle Percentage promotions  
- ✅ Coupon with Cap promotions
- ✅ Maintained backward compatibility
- ✅ Preserved all existing functionality

**Next Steps**: Monitor usage and gather feedback for future improvements!


