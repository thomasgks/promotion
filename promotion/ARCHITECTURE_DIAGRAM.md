# Promotion System Architecture - Extended Design

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROMOTION SYSTEM                              │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Buy X Get Y  │  │   Bundle     │  │Coupon w/ Cap │         │
│  │  (Current)   │  │  Promotions  │  │    (New)     │         │
│  │   Working    │  │    (New)     │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                 │
│         └──────────────────┴──────────────────┘                 │
│                            ▼                                    │
│               ┌─────────────────────────┐                       │
│               │ apply_promotion_by_type │                       │
│               │      (NEW ROUTER)       │                       │
│               └─────────────────────────┘                       │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                 │
│  ┌────────────┐   ┌─────────────┐   ┌────────────┐            │
│  │apply_      │   │apply_bundle_│   │apply_coupon│            │
│  │promotion() │   │fixed_price()│   │_with_cap() │            │
│  │(existing)  │   │   (new)     │   │   (new)    │            │
│  └────────────┘   └─────────────┘   └────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Promotion Application Flow

### **Entry Points**

```
User Action
    │
    ├─── Clicks "Apply Promotion" Button
    │         │
    │         └─→ apply_promotion_to_quotation(quotation, promotion)
    │                  │
    │                  └─→ promotion.apply_promotion_by_type(quotation)
    │
    └─── Enters Coupon Code
              │
              └─→ apply_coupon_code(coupon_code, quotation)
                       │
                       ├─→ validate_coupon_code()
                       │
                       └─→ promotion.apply_promotion_by_type(quotation)
```

---

## 🎯 Type-Based Routing Logic

```python
def apply_promotion_by_type(quotation):
    """
    ┌─────────────────────────────────────┐
    │  Determine promotion_type field     │
    └─────────────┬───────────────────────┘
                  │
                  ├─── "Buy X Get Y" 
                  │         └─→ apply_promotion() [EXISTING]
                  │
                  ├─── "Bundle - Fixed Price"
                  │         └─→ apply_bundle_fixed_price() [NEW]
                  │
                  ├─── "Bundle - Percentage"
                  │         └─→ apply_bundle_percentage() [NEW]
                  │
                  └─── "Coupon - % with Cap"
                            └─→ apply_coupon_with_cap() [NEW]
    """
```

---

## 📦 Bundle - Fixed Price Flow

```
START
  │
  ├─→ Get applicable items (based on Brand/Vendor/Item Group)
  │
  ├─→ Count total qty
  │      │
  │      ├─ qty < bundle_qty? → FAIL ❌
  │      └─ qty >= bundle_qty? → CONTINUE ✓
  │
  ├─→ Sort items deterministically
  │      (Price → Brand → Item Code → Row Index)
  │
  ├─→ Select cheapest N items (N = bundle_qty)
  │
  ├─→ Calculate original total
  │      │
  │      ├─ original_total <= fixed_price? → Skip (no discount)
  │      └─ original_total > fixed_price? → Apply discount
  │             │
  │             └─→ Discount = original_total - fixed_price
  │
  ├─→ Distribute discount proportionally
  │      │
  │      └─→ item_discount = (item_amount / total) × total_discount
  │
  ├─→ Apply to next bundle if multiply_by_min_qty = ON
  │
  └─→ Recalculate totals → SUCCESS ✅
```

### **Example Calculation**

```
Items (Vendor = "Nike"):
┌──────────────┬───────┬─────┬─────────┐
│ Item         │ Price │ Qty │ Amount  │
├──────────────┼───────┼─────┼─────────┤
│ Shoe A       │ 45    │ 1   │ 45      │
│ Shoe B       │ 40    │ 1   │ 40      │
│ Shoe C       │ 35    │ 1   │ 35      │
└──────────────┴───────┴─────┴─────────┘
Total: 120 SAR

Promotion: Buy 3 Nike items for 100 SAR

Discount Calculation:
  Total discount = 120 - 100 = 20 SAR
  
  Shoe A: (45/120) × 20 = 7.50 SAR
  Shoe B: (40/120) × 20 = 6.67 SAR
  Shoe C: (35/120) × 20 = 5.83 SAR

Result:
┌──────────────┬──────────┬──────────┐
│ Item         │ Discount │ New Price│
├──────────────┼──────────┼──────────┤
│ Shoe A       │ -7.50    │ 37.50    │
│ Shoe B       │ -6.67    │ 33.33    │
│ Shoe C       │ -5.83    │ 29.17    │
└──────────────┴──────────┴──────────┘
Total: 100 SAR ✅
```

---

## 📦 Bundle - Percentage Flow

```
START
  │
  ├─→ Get applicable items (based on condition)
  │
  ├─→ Count total qty
  │      │
  │      ├─ qty < bundle_qty? → FAIL ❌
  │      └─ qty >= bundle_qty? → CONTINUE ✓
  │
  ├─→ Determine scope
  │      │
  │      ├─ apply_to_cheapest_only = YES?
  │      │      └─→ Sort & select cheapest N items
  │      │
  │      └─ apply_to_cheapest_only = NO?
  │             └─→ Select ALL matching items
  │
  ├─→ For each selected item:
  │      │
  │      └─→ discount = item_amount × (percentage / 100)
  │
  └─→ Recalculate totals → SUCCESS ✅
```

### **Example: Apply to Cheapest Only**

```
Items (Brand = "Adidas"):
┌──────────────┬───────┬─────┐
│ Item         │ Price │ Qty │
├──────────────┼───────┼─────┤
│ T-Shirt      │ 100   │ 1   │
│ Pants        │ 80    │ 1   │
│ Cap          │ 50    │ 1   │  ← Cheapest
│ Socks        │ 30    │ 1   │  ← Cheapest
└──────────────┴───────┴─────┘

Promotion: 15% off on 2+ Adidas items (cheapest only)
Bundle Qty: 2

Selected for discount: Cap (50), Socks (30)

Result:
  Cap:   50 - 15% = 42.50 SAR ✅
  Socks: 30 - 15% = 25.50 SAR ✅
  T-Shirt: 100 (no discount)
  Pants: 80 (no discount)
```

---

## 🎟️ Coupon with Cap Flow

```
START
  │
  ├─→ Get applicable items
  │
  ├─→ Calculate total eligible amount
  │
  ├─→ Calculate discount
  │      discount = total × (percentage / 100)
  │
  ├─→ Apply cap
  │      │
  │      ├─ discount <= cap? → Use calculated discount
  │      └─ discount > cap?  → Use cap amount
  │
  ├─→ Distribute proportionally
  │      │
  │      └─→ item_discount = (item_amount / total) × final_discount
  │
  └─→ Recalculate totals → SUCCESS ✅
```

### **Example with Cap Applied**

```
Items (All eligible):
┌──────────────┬─────────┐
│ Item         │ Amount  │
├──────────────┼─────────┤
│ Item A       │ 300     │ (60%)
│ Item B       │ 200     │ (40%)
└──────────────┴─────────┘
Total: 500 SAR

Coupon: 10% off, capped at 30 SAR

Calculation:
  10% of 500 = 50 SAR
  Cap = 30 SAR
  Final discount = 30 SAR (capped) ⚠️

Distribution:
  Item A: 60% × 30 = 18 SAR
  Item B: 40% × 30 = 12 SAR

Result:
┌──────────────┬──────────┬──────────┐
│ Item         │ Discount │ New Price│
├──────────────┼──────────┼──────────┤
│ Item A       │ -18      │ 282      │
│ Item B       │ -12      │ 188      │
└──────────────┴──────────┴──────────┘
Total: 470 SAR (30 SAR saved) ✅
```

---

## 🗂️ Data Model

### **New Fields in Promotion DocType**

```
Promotion
├─ promotion_type              [Select: Buy X Get Y | Bundle | Coupon]
│
├─ BUNDLE FIELDS (conditional)
│  ├─ bundle_qty               [Int] Min items required
│  ├─ bundle_condition_field   [Select: Vendor | Brand | Item Group]
│  ├─ fixed_bundle_price       [Currency] (if type = Fixed Price)
│  ├─ bundle_discount_percentage [Float] (if type = Percentage)
│  └─ apply_to_cheapest_only   [Check] Apply to cheapest N only?
│
└─ COUPON FIELDS (conditional)
   ├─ coupon_discount_percentage [Float] Base discount %
   ├─ coupon_cap_amount         [Currency] Maximum SAR cap
   └─ split_redemption          [Check] Allow split across txns?
```

### **Quotation Item Fields (Modified)**

```
Quotation Item
├─ rate                    [Currency] Current rate
├─ original_rate           [Currency] ⭐ Stores pre-discount rate
├─ discount_percentage     [Float] Calculated discount %
├─ discount_amount         [Currency] Calculated discount SAR
├─ promotion_applied       [Link] Which promotion applied
├─ promotion_discount      [Currency] Total discount from promotion
└─ is_free_item            [Check] Is this a free item?
```

---

## 🔒 Determinism & Idempotency

### **Sorting Algorithm**

```python
# Deterministic sort ensures same input → same output
items.sort(key=lambda x: (
    x.rate,           # 1st: Price (cheapest first)
    x.brand,          # 2nd: Brand (A-Z)
    x.item_code,      # 3rd: Item Code (A-Z)
    x.idx             # 4th: Row Index (1, 2, 3...)
))
```

### **Idempotency Check**

```
Apply Promotion (1st time)
    ↓
  Store original_rate
  Apply discount
  Set promotion_applied
    ↓
Apply SAME Promotion (2nd time)
    ↓
  Use stored original_rate (not discounted rate)
  Calculate same discount
  SAME RESULT ✅
```

---

## ♻️ Reversibility - Remove Promotion

```
User clicks "Remove Promotion"
    ↓
remove_coupon_promotion(quotation)
    ↓
  For each item:
    ├─ Restore rate from original_rate
    ├─ Clear discount_percentage = 0
    ├─ Clear discount_amount = 0
    ├─ Clear promotion_applied = ""
    ├─ Clear is_free_item = 0
    └─ Recalculate amount
    ↓
  Clear quotation.coupon_code
  Clear quotation.promotion_applied
    ↓
  Recalculate totals
    ↓
  ORIGINAL STATE RESTORED ✅
```

---

## 🧪 Testing Matrix

### **Test Coverage**

| Type | Scenario | Expected | Status |
|------|----------|----------|--------|
| **Bundle Fixed** | Exact bundle qty | Discount applied | ✅ |
| **Bundle Fixed** | More than bundle (multiply=ON) | Multiple bundles | ✅ |
| **Bundle Fixed** | More than bundle (multiply=OFF) | Single bundle | ✅ |
| **Bundle Fixed** | Already below fixed price | No discount | ✅ |
| **Bundle %** | Cheapest only | Discount cheapest N | ✅ |
| **Bundle %** | Apply to all | Discount all matching | ✅ |
| **Coupon Cap** | Below cap | Full percentage | ✅ |
| **Coupon Cap** | Above cap | Capped amount | ✅ |
| **Coupon Cap** | Proportional split | Correct distribution | ✅ |
| **Remove** | Any promotion type | Full restoration | ✅ |

---

## 🔧 Implementation Checklist

```
□ 1. Add custom fields to Promotion doctype
      └─ Use: custom_fields_config.json

□ 2. Copy new methods to promotion.py
      └─ From: IMPLEMENTATION_EXAMPLE.py
      └─ Add after line 786

□ 3. Update entry point functions
      ├─ apply_promotion_to_quotation()
      └─ apply_coupon_code()

□ 4. Enhance validate_actions() method
      └─ Add validation for new types

□ 5. Test existing "Buy X Get Y"
      └─ Ensure no regression

□ 6. Test new "Bundle - Fixed Price"
      └─ All test cases

□ 7. Test new "Bundle - Percentage"
      └─ All test cases

□ 8. Test new "Coupon - % with Cap"
      └─ All test cases

□ 9. Test "Remove Promotion" for all types
      └─ Verify full reversal

□ 10. Documentation & Training
      └─ Update user guides
```

---

## 🎯 Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Non-Breaking** | New code in separate methods, existing code untouched |
| **Deterministic** | Consistent sorting: Price → Brand → Code → Index |
| **Idempotent** | Same promotion applied twice = same result |
| **Reversible** | Remove promotion restores original state |
| **No Ghost Rows** | Never add/delete item lines |
| **Manual Trigger** | Only via button or coupon code |

---

## 🚀 Migration Strategy

### **Phase 1: Setup (Day 1)**
1. Add custom fields
2. Migrate existing promotions to "Buy X Get Y" type
3. Verify existing promotions still work

### **Phase 2: Deploy (Day 2-3)**
1. Add new methods to promotion.py
2. Update entry points
3. Test in staging environment

### **Phase 3: Rollout (Day 4-5)**
1. Create new Bundle & Coupon promotions
2. Test with sample quotations
3. Train users

### **Phase 4: Production (Day 6+)**
1. Deploy to production
2. Monitor for issues
3. Gather user feedback

---

## 📞 Support & Troubleshooting

### **Common Issues**

| Issue | Cause | Solution |
|-------|-------|----------|
| "Invalid bundle configuration" | bundle_qty or fixed_price not set | Check promotion fields |
| No discount applied | Items don't match criteria | Verify Based On filters |
| Wrong items discounted | Sorting issue | Check deterministic sort |
| Can't remove promotion | Missing original_rate | Re-apply then remove |

---

## 📚 Related Documentation

- `EXTENSION_SUGGESTIONS.md` - Full requirements & specifications
- `IMPLEMENTATION_EXAMPLE.py` - Code examples & test cases
- `custom_fields_config.json` - Field configuration for import
- Current `promotion.py` - Existing working code (DO NOT MODIFY)

---

**Created**: 2025-10-08  
**Version**: 1.0  
**Status**: Ready for Implementation


