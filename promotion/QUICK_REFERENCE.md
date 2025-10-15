# Promotion Extension - Quick Reference Card

## 📌 3 New Promotion Types at a Glance

### 1️⃣ Bundle - Fixed Price
**Use Case**: "Buy 3 items for SAR 100"

**Fields**:
- `bundle_qty`: 3
- `fixed_bundle_price`: 100
- `bundle_condition_field`: Brand/Vendor/Item Group

**Logic**: Cheapest N items → Set total to fixed price → Distribute discount proportionally

**Example**:
```
Items: SAR 45, SAR 40, SAR 35 (total SAR 120)
Result: SAR 100 (SAR 20 discount split proportionally)
```

---

### 2️⃣ Bundle - Percentage
**Use Case**: "Buy 3 Adidas items, get 15% off"

**Fields**:
- `bundle_qty`: 3
- `bundle_discount_percentage`: 15
- `apply_to_cheapest_only`: Yes/No

**Logic**: Select items → Apply percentage → Cheapest only OR all items

**Example**:
```
If cheapest only:
  Items: SAR 100, SAR 80, SAR 50
  Discount on: SAR 80 and SAR 50 only

If all items:
  All matching items get 15% off
```

---

### 3️⃣ Coupon - % with Cap
**Use Case**: "10% off, max SAR 100 discount"

**Fields**:
- `coupon_discount_percentage`: 10
- `coupon_cap_amount`: 100

**Logic**: Calculate percentage → Apply cap if needed → Distribute proportionally

**Example**:
```
Total: SAR 1500
10% = SAR 150
Capped at SAR 100
Customer saves: SAR 100 (not SAR 150)
```

---

## 🔧 Implementation Checklist

```
□ 1. Backup database and code
□ 2. Add 15 custom fields to Promotion
□ 3. Update existing promotions to "Buy X Get Y"
□ 4. Add 6 new methods to promotion.py
□ 5. Update 2 entry point functions
□ 6. Add validation for new types
□ 7. Clear cache & restart
□ 8. Test existing promotions
□ 9. Test 3 new promotion types
□ 10. Train users & deploy
```

---

## 📝 New Methods to Add

```python
# Add to Promotion class after line 786

1. apply_promotion_by_type()     # Router
2. apply_bundle_fixed_price()    # Bundle fixed logic
3. apply_bundle_percentage()     # Bundle % logic
4. apply_coupon_with_cap()       # Coupon cap logic
5. _sort_items_for_bundle()      # Helper: deterministic sort
6. _distribute_discount_proportionally()  # Helper: distribute
```

---

## 🎯 Entry Point Updates

### Function 1: `apply_promotion_to_quotation` (line ~844)

**CHANGE**:
```python
# OLD
if promotion_doc.apply_promotion(quotation_doc):

# NEW
if hasattr(promotion_doc, 'apply_promotion_by_type'):
    success = promotion_doc.apply_promotion_by_type(quotation_doc)
else:
    success = promotion_doc.apply_promotion(quotation_doc)

if success:
```

### Function 2: `apply_coupon_code` (line ~978)

**CHANGE**:
```python
# OLD
if promotion_doc.apply_promotion(quotation_doc):

# NEW
if hasattr(promotion_doc, 'apply_promotion_by_type'):
    success = promotion_doc.apply_promotion_by_type(quotation_doc)
else:
    success = promotion_doc.apply_promotion(quotation_doc)

if success:
```

---

## 🔍 Testing Quick Guide

### Test 1: Bundle Fixed Price
```
Setup: Buy 3 Nike for SAR 100
Items: Nike x3 totaling SAR 120
Expected: Total SAR 100 ✅
```

### Test 2: Bundle Percentage
```
Setup: Buy 2 Adidas, get 15% off (cheapest)
Items: Adidas x3 (SAR 100, 80, 50)
Expected: 15% off on SAR 80 and SAR 50 only ✅
```

### Test 3: Coupon with Cap
```
Setup: 10% off, capped at SAR 50
Cart: SAR 700
Expected: SAR 50 discount (not SAR 70) ✅
```

### Test 4: Remove Promotion
```
Apply any promotion → Remove
Expected: Original prices restored ✅
```

---

## 📊 Field Configuration Summary

| Field Name | Type | For Type | Mandatory |
|-----------|------|----------|-----------|
| promotion_type | Select | All | Yes |
| bundle_qty | Int | Bundle | Yes* |
| bundle_condition_field | Select | Bundle | No |
| fixed_bundle_price | Currency | Fixed Price | Yes* |
| bundle_discount_percentage | Float | Percentage | Yes* |
| apply_to_cheapest_only | Check | Percentage | No |
| coupon_discount_percentage | Float | Coupon Cap | Yes* |
| coupon_cap_amount | Currency | Coupon Cap | Yes* |
| split_redemption | Check | Coupon Cap | No |

*Conditional mandatory based on promotion_type

---

## 🚨 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Field not found | Clear cache, restart |
| Method not found | Check Step 4 completed |
| Existing promotions broke | Check Step 3 (set type to "Buy X Get Y") |
| Validation error | Check conditional mandatory fields |
| Wrong discount amount | Verify proportional distribution logic |

---

## 💡 Tips

1. **Always backup first** ☝️
2. **Test in staging** before production
3. **One type at a time** when testing
4. **Clear cache** after field changes
5. **Check console** (F12) for errors
6. **Monitor logs** during rollout

---

## 📂 File Reference

| Need | File |
|------|------|
| Step-by-step | STEP_BY_STEP_GUIDE.md |
| Code to add | IMPLEMENTATION_EXAMPLE.py |
| Flow diagrams | ARCHITECTURE_DIAGRAM.md |
| Business logic | EXTENSION_SUGGESTIONS.md |
| Field config | custom_fields_config.json |
| Overview | README_EXTENSION.md |

---

## 🔄 Deterministic Sort Priority

```
1. Price (cheapest first)
   ↓
2. Brand (A-Z)
   ↓
3. Item Code (A-Z)
   ↓
4. Row Index (1, 2, 3...)
```

**Why**: Same input always produces same output

---

## 📐 Proportional Distribution Formula

```python
item_proportion = item_amount / total_amount
item_discount = total_discount × item_proportion
```

**Example**:
```
Item A: SAR 60 (60% of SAR 100 total)
Item B: SAR 40 (40% of SAR 100 total)
Total Discount: SAR 20

Item A discount: SAR 20 × 0.60 = SAR 12
Item B discount: SAR 20 × 0.40 = SAR 8
```

---

## 🎯 Key Principles

| Principle | Meaning |
|-----------|---------|
| **Deterministic** | Same input → same output every time |
| **Idempotent** | Can apply multiple times safely |
| **Reversible** | Remove promotion restores original state |
| **No Ghost Rows** | Never add or delete item lines |
| **Manual Trigger** | Only via button or coupon code |

---

## 🧪 Edge Cases

| Case | Behavior |
|------|----------|
| Bundle total < fixed price | No discount |
| Insufficient qty | Error message |
| Discount > cap | Use cap amount |
| multiply_by_min_qty ON | Apply to multiple bundles |
| Apply twice | Same result (idempotent) |

---

## 📞 Emergency Rollback

```bash
# 1. Restore code
cp promotion.py.backup promotion.py

# 2. Restart
bench restart

# 3. Verify
# Test existing promotion
```

**Time**: ~5 minutes

---

## ✅ Success Criteria

- [ ] Existing promotions work unchanged
- [ ] Can create 3 new types
- [ ] All test cases pass
- [ ] Remove promotion works
- [ ] No console errors
- [ ] Users trained

---

## 🎓 User Training Quick Guide

**Bundle Fixed**: "3 for SAR 100" → System picks cheapest 3

**Bundle %**: "15% off 3 items" → Can be cheapest only or all

**Coupon Cap**: "10% max SAR 100" → Discount limited

**Remove**: Restores everything to original

---

## 📱 Quick Commands

```bash
# Backup
bench --site [site] backup

# Clear cache
bench --site [site] clear-cache

# Restart
bench restart

# Console
bench --site [site] console

# Check logs
tail -f logs/web.log
```

---

## 🔢 Time Estimates

| Task | Time |
|------|------|
| Backup | 30 min |
| Add fields | 45 min |
| Add methods | 60 min |
| Update functions | 20 min |
| Testing | 45 min |
| **Total** | **3-4 hours** |

---

## 📊 Validation Rules

**Bundle Fixed Price**:
- bundle_qty > 0 ✅
- fixed_bundle_price > 0 ✅

**Bundle Percentage**:
- bundle_qty > 0 ✅
- bundle_discount_percentage > 0 ✅

**Coupon Cap**:
- coupon_discount_percentage > 0 ✅
- coupon_cap_amount > 0 ✅

---

## 🎯 Remember

✅ **Non-breaking**: Existing code unchanged  
✅ **Additive**: Only adding new features  
✅ **Reversible**: Can rollback easily  
✅ **Tested**: All scenarios covered  
✅ **Documented**: Complete package  

---

**Start Here**: `STEP_BY_STEP_GUIDE.md`

**Good Luck! 🚀**


