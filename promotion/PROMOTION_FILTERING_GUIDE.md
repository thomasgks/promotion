# Promotion Filtering System - Comprehensive Guide

## Overview

This enhanced promotion system now supports advanced filtering based on multiple criteria including **Item Group**, **Brand**, **Custom Vendor Code**, and **Season** attributes. This allows for highly targeted promotions that can be applied to specific combinations of these attributes.

## New Features Added

### 1. Enhanced Promotion Source Item Group

The `Promotion Source Item Group` doctype now includes two new fields:

- **Custom Vendor Code**: Text field to filter by vendor-specific codes
- **Season**: Text field to filter by season (leave empty to include all seasons)

### 2. New "Based On" Option

Added a new option: **"Item Group + Brand + Vendor Code + Season"**

This allows promotions to filter items based on all four criteria simultaneously.

### 3. Advanced Filtering Logic

The system now supports flexible matching where:
- If a field is left empty in the source filter, it matches any value
- If a field is specified, it must match exactly
- Season "All Seasons" matches items from any season

## How to Use the New Filtering System

### Step 1: Set Up Items with Required Attributes

#### Option A: Using Item Custom Fields
Add custom fields to the Item doctype:
- `custom_vendor_code` (Data field)
- `season_attribute` (Data field for season text - leave empty for all seasons)

#### Option B: Using Item Variant Attributes
For items with variants, set up variant attributes:
- Create a variant attribute named "Season"
- Add variant values: Spring, Summer, Fall, Winter

### Step 2: Create a Promotion

1. Go to **Promotion** doctype
2. Set **Based On** to **"Item Group + Brand + Vendor Code + Season"**
3. In the **Source Item Groups** table, add rows with:
   - **Item Group**: Required (e.g., "Clothing")
   - **Brand**: Optional (e.g., "Nike" or leave empty for any brand)
   - **Custom Vendor Code**: Optional (e.g., "VENDOR001" or leave empty for any vendor)
   - **Season**: Optional (e.g., "Summer" or "All Seasons" for any season)
   - **Enabled**: Check to activate the filter

### Step 3: Configure Promotion Conditions

Set your promotion conditions:
- **Min Qty**: Minimum quantity required
- **Min Amount**: Minimum amount required
- **Valid From/To**: Promotion validity period

### Step 4: Set Up Actions

Configure what happens when the promotion is applied:
- **Discount %**: Percentage discount
- **Discount Amount**: Fixed amount discount
- **Free Item**: Free item reward
- **Bundle Price**: Special bundle pricing

## Examples

### Example 1: Summer Nike Clothing Promotion

**Scenario**: 20% discount on Nike clothing from vendor VENDOR001 during summer season

**Configuration**:
- Based On: Item Group + Brand + Vendor Code + Season
- Source Item Groups:
  - Item Group: Clothing
  - Brand: Nike
  - Custom Vendor Code: VENDOR001
  - Season: Summer
  - Enabled: Yes
- Min Qty: 2
- Action: 20% Discount

**Result**: Only Nike clothing items from vendor VENDOR001 with summer season will qualify for this promotion.

### Example 2: Flexible Electronics Promotion

**Scenario**: 15% discount on any electronics from TECH001 vendor during winter, regardless of brand

**Configuration**:
- Based On: Item Group + Brand + Vendor Code + Season
- Source Item Groups:
  - Item Group: Electronics
  - Brand: (leave empty)
  - Custom Vendor Code: TECH001
  - Season: Winter
  - Enabled: Yes
- Min Amount: 200
- Action: 15% Discount

**Result**: Any electronics items from TECH001 vendor with winter season will qualify, regardless of brand.

### Example 3: Year-Round Sports Promotion

**Scenario**: Buy 3 Get 1 Free on sports items from SPORT001 vendor, any season

**Configuration**:
- Based On: Item Group + Brand + Vendor Code + Season
- Source Item Groups:
  - Item Group: Sports
  - Brand: (leave empty)
  - Custom Vendor Code: SPORT001
  - Season: All Seasons
  - Enabled: Yes
- Min Qty: 3
- Action: 100% Discount on 1 item

**Result**: Sports items from SPORT001 vendor will qualify regardless of season or brand.

## Technical Implementation Details

### Filtering Logic

The new filtering function `is_item_group_brand_vendor_season_match()` works as follows:

1. **Item Group Match**: Must match exactly if specified
2. **Brand Match**: Must match exactly if specified, ignored if empty
3. **Vendor Code Match**: Must match exactly if specified, ignored if empty
4. **Season Match**: Must match exactly if specified and not "All Seasons"

### Season Detection

The system checks for season information in this order:
1. **Item Variant Attributes**: Looks for "Season" attribute in `tabItem Variant Attribute`
2. **Item Custom Field**: Falls back to `season_attribute` custom field on Item
3. **Default**: Returns "All Seasons" if no season information found

### Performance Considerations

- The filtering logic is optimized to check criteria in order of selectivity
- Database queries are minimized by fetching item details once
- Season lookup is cached for repeated calls

## Migration Guide

### For Existing Promotions

Existing promotions will continue to work without changes. The new filtering option is additive and doesn't affect existing functionality.

### For New Implementations

1. **Update Item Data**: Ensure items have the required custom fields or variant attributes
2. **Create New Promotions**: Use the new "Item Group + Brand + Vendor Code + Season" option
3. **Test Thoroughly**: Use the test functions provided in the example script

## Testing

Use the provided `promotion_filtering_example.py` script to:
- Create sample items with different attributes
- Test promotion filtering logic
- Validate that promotions apply correctly to matching items

## Best Practices

1. **Be Specific**: Use all four criteria when you need very targeted promotions
2. **Be Flexible**: Leave fields empty when you want broader matching
3. **Test Scenarios**: Always test with sample data before deploying
4. **Document Rules**: Keep clear documentation of your promotion rules
5. **Monitor Performance**: Watch for any performance issues with complex filtering

## Troubleshooting

### Common Issues

1. **Promotions Not Applying**: Check that all required criteria match exactly
2. **Season Not Detected**: Ensure items have season information in variant attributes or custom fields
3. **Vendor Code Mismatch**: Verify that custom_vendor_code field exists and is populated
4. **Performance Issues**: Consider adding database indexes on frequently filtered fields

### Debug Mode

Enable debug logging to see detailed filtering information:
```python
# In your promotion testing code
frappe.local.debug = True
```

This will show which items match and which criteria they meet or fail.

## Conclusion

This enhanced promotion filtering system provides powerful and flexible options for creating targeted promotions based on multiple criteria. The system is designed to be both powerful and easy to use, with clear examples and comprehensive testing capabilities.
