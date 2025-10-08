# Null Value Handling Implementation for Promotion Filtering

## Overview
This implementation allows null values in the Source Item Groups to be treated as "All" selections, while ensuring at least one field is mandatory to prevent completely empty rules.

## Changes Made

### 1. Validation Logic (`promotion_source_item_group.py`)
- **Added validation** to ensure at least one field (item_group, brand, custom_vendor_code, or season_attribute) must be specified
- **Added validation** to prevent empty/whitespace-only values when fields are specified
- **Error messages** provide clear guidance on what's required

### 2. JSON Schema Updates (`promotion_source_item_group.json`)
- **Removed mandatory requirement** from item_group field (removed `*` from label)
- **Added descriptions** to all fields explaining that leaving them empty includes all values:
  - Item Group: "Leave empty to include all item groups"
  - Brand: "Leave empty to include all brands" 
  - Vendor Code: "Leave empty to include all vendor codes"
  - Season: "Leave empty to include all seasons" (already existed)

### 3. Filtering Logic Updates (`promotion.py`)
Updated all matching methods to handle null values consistently:

#### `is_item_group_match()`
- If `item_group` is null/empty → matches all item groups
- If `brand` is null/empty → matches all brands
- Only checks specified fields, ignores null ones

#### `is_item_group_brand_match()`
- If `item_group` is null/empty → matches all item groups
- If `brand` is null/empty → matches all brands
- Only checks specified fields, ignores null ones

#### `is_item_group_brand_vendor_season_match()`
- If `item_group` is null/empty → matches all item groups
- If `brand` is null/empty → matches all brands
- If `custom_vendor_code` is null/empty → matches all vendor codes
- If `season_attribute` is null/empty → matches all seasons
- Only checks specified fields, ignores null ones

## How It Works

### Validation Rules
1. **At least one field must be specified** - prevents completely empty rules
2. **Specified fields cannot be empty/whitespace** - ensures data quality
3. **Null/empty fields are treated as "All"** - provides flexibility

### Filtering Behavior
- **Null/empty fields** = Match all values for that criteria
- **Specified fields** = Must match exactly
- **Combination** = All specified fields must match, null fields are ignored

## Examples

### Example 1: All Fields Null (Invalid)
```
Item Group: [empty]
Brand: [empty] 
Vendor Code: [empty]
Season: [empty]
```
**Result**: ❌ Validation Error - "At least one field must be specified"

### Example 2: Only Item Group Specified
```
Item Group: "Clothing"
Brand: [empty]
Vendor Code: [empty] 
Season: [empty]
```
**Result**: ✅ Matches all items in "Clothing" item group, regardless of brand, vendor, or season

### Example 3: Only Brand Specified
```
Item Group: [empty]
Brand: "Nike"
Vendor Code: [empty]
Season: [empty]
```
**Result**: ✅ Matches all "Nike" items, regardless of item group, vendor, or season

### Example 4: Mixed Specification
```
Item Group: "Clothing"
Brand: [empty]
Vendor Code: "GD"
Season: [empty]
```
**Result**: ✅ Matches all items in "Clothing" item group with vendor code "GD", regardless of brand or season

### Example 5: All Fields Specified
```
Item Group: "Clothing"
Brand: "Nike"
Vendor Code: "GD"
Season: "Summer"
```
**Result**: ✅ Matches only items that match all four criteria exactly

## Benefits

1. **Flexibility**: Users can create broad rules (e.g., all brands in a group) or specific rules (e.g., specific brand + vendor + season)
2. **Data Quality**: Prevents completely empty rules that would match everything
3. **User-Friendly**: Clear descriptions guide users on how to use null values
4. **Backward Compatible**: Existing rules with all fields specified continue to work unchanged
5. **Consistent**: All matching methods handle null values the same way

## Testing

A comprehensive test suite (`test_null_handling.py`) has been created to verify:
- Validation works correctly for all combinations
- Null values are properly treated as "All" in filtering
- Edge cases (whitespace, None values) are handled correctly
- Specific values still match exactly when specified

## Migration Notes

- **No database changes required** - this is purely a logic change
- **Existing promotions continue to work** - no breaking changes
- **New validation may catch invalid data** - review existing promotions if needed
- **UI descriptions help users understand** - no training required for basic usage
