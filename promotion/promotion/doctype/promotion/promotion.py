import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, flt, cint
from datetime import datetime, timedelta
import json


class Promotion(Document):
	def validate(self):
		self.validate_dates()
		self.validate_conditions()
		self.validate_actions()

	def validate_dates(self):
		if self.valid_from and self.valid_upto:
			if getdate(self.valid_from) > getdate(self.valid_upto):
				frappe.throw(_("Valid From date cannot be greater than Valid Upto date"))

	def validate_conditions(self):
		if not self.min_qty and not self.min_amount:
			frappe.throw(_("Either Min Qty or Min Amount must be specified"))

		if self.based_on == "Brand" and not self.source_brands:
			frappe.throw(_("Source Brands must be specified when Based On is Brand"))
		
		if self.based_on == "Item Group" and not self.source_item_groups:
			frappe.throw(_("Source Item Groups must be specified when Based On is Item Group"))
		
		if self.based_on == "Item Group + Brand" and not self.source_item_groups:
			frappe.throw(_("Source Item Groups must be specified when Based On is Item Group + Brand"))
		
		if self.based_on == "Item Group + Brand + Vendor Code + Season" and not self.source_item_groups:
			frappe.throw(_("Source Item Groups must be specified when Based On is Item Group + Brand + Vendor Code + Season"))

	def validate_actions(self):
		if not self.actions:
			frappe.throw(_("At least one action must be specified"))

		for action in self.actions:
			if action.reward_type == "Discount %" and not action.discount_percentage:
				frappe.throw(_("Discount % is required for Discount % reward type"))
			
			if action.reward_type == "Discount Amount" and not action.discount_amount:
				frappe.throw(_("Discount Amount is required for Discount Amount reward type"))

	def is_valid(self, doc_date=None):
		"""Check if promotion is valid for given date"""
		if self.disabled:
			return False
		
		if not doc_date:
			doc_date = today()
		
		if self.valid_from and getdate(doc_date) < getdate(self.valid_from):
			return False
		
		if self.valid_upto and getdate(doc_date) > getdate(self.valid_upto):
			return False
		
		return True

	def get_applicable_items(self, quotation_items):
		"""Get items that match the promotion criteria with wildcard NULL handling"""
		applicable_items = []
		
		frappe.msgprint(f"Checking {len(quotation_items)} items for promotion criteria")
		
		for item in quotation_items:
			frappe.msgprint(f"Checking item: {item.item_code}")
			
			if self.based_on == "Brand":
				if self.is_brand_match(item):
					applicable_items.append(item)
					frappe.msgprint(f"  ✓ Matches Brand criteria")
				else:
					frappe.msgprint(f"  ✗ Does not match Brand criteria")
			elif self.based_on == "Item Group":
				if self.is_item_group_match(item):
					applicable_items.append(item)
					frappe.msgprint(f"  ✓ Matches Item Group criteria")
				else:
					frappe.msgprint(f"  ✗ Does not match Item Group criteria")
			elif self.based_on == "Item Group + Brand":
				if self.is_item_group_brand_match(item):
					applicable_items.append(item)
					frappe.msgprint(f"  ✓ Matches Item Group + Brand criteria")
				else:
					frappe.msgprint(f"  ✗ Does not match Item Group + Brand criteria")
			elif self.based_on == "Item Group + Brand + Vendor Code + Season":
				if self.is_item_group_brand_vendor_season_match(item):
					applicable_items.append(item)
					frappe.msgprint(f"  ✓ Matches Item Group + Brand + Vendor Code + Season criteria")
				else:
					frappe.msgprint(f"  ✗ Does not match Item Group + Brand + Vendor Code + Season criteria")
			elif self.based_on == "Item":
				if self.is_item_match(item):
					applicable_items.append(item)
					frappe.msgprint(f"  ✓ Matches Item criteria")
				else:
					frappe.msgprint(f"  ✗ Does not match Item criteria")
		
		return applicable_items

	def is_brand_match(self, item):
		"""Check if item brand matches source brands"""
		if not self.source_brands:
			return False
		
		item_brand = frappe.db.get_value("Item", item.item_code, "brand")
		if not item_brand:
			return False
		
		for source_brand in self.source_brands:
			if source_brand.brand == item_brand and source_brand.enabled:
				return True
		
		return False

	def is_item_group_match(self, item):
		"""Check if item group matches source item groups with wildcard NULL handling"""
		if not self.source_item_groups:
			return False
		
		item_group = frappe.db.get_value("Item", item.item_code, "item_group")
		if not item_group:
			return False
		
		for source_item_group in self.source_item_groups:
			# Check if this rule is enabled (default to True if not specified)
			is_enabled = getattr(source_item_group, 'enabled', True)
			if not is_enabled:
				continue
				
			# Check item group match (if specified in source)
			# If item_group is None/null, it matches all item groups
			if source_item_group.item_group is not None and source_item_group.item_group != "":
				if source_item_group.item_group != item_group:
					continue
			
			# Check brand match (if specified in source)
			# If brand is None/null, it matches all brands
			if source_item_group.brand is not None and source_item_group.brand != "":
				item_brand = frappe.db.get_value("Item", item.item_code, "brand")
				if item_brand != source_item_group.brand:
					continue
			
			# All criteria matched
			return True
		
		return False

	def is_item_group_brand_match(self, item):
		"""Check if item group and brand combination matches source item groups with wildcard NULL handling"""
		if not self.source_item_groups:
			return False
		
		item_group = frappe.db.get_value("Item", item.item_code, "item_group")
		item_brand = frappe.db.get_value("Item", item.item_code, "brand")
		
		if not item_group:
			return False
		
		for source_item_group in self.source_item_groups:
			# Check if this rule is enabled (default to True if not specified)
			is_enabled = getattr(source_item_group, 'enabled', True)
			if not is_enabled:
				continue
			
			# Check item group match (if specified in source)
			# If item_group is None/null, it matches all item groups
			if source_item_group.item_group is not None and source_item_group.item_group != "":
				if source_item_group.item_group != item_group:
					continue
			
			# Check brand match (if specified in source)
			# If brand is None/null, it matches all brands
			if source_item_group.brand is not None and source_item_group.brand != "":
				if source_item_group.brand != item_brand:
					continue
			
			# All criteria matched
			return True
		
		return False

	def is_item_group_brand_vendor_season_match(self, item):
		"""Check if item matches item group, brand, vendor code, and season combination with wildcard NULL handling"""
		if not self.source_item_groups:
			return False
		
		# Get item details
		item_details = frappe.db.get_value("Item", item.item_code, 
			["item_group", "brand", "custom_vendor_code"], as_dict=True)
		
		if not item_details:
			return False
		
		item_group = item_details.get("item_group")
		item_brand = item_details.get("brand")
		item_vendor_code = item_details.get("custom_vendor_code")
		
		# Get item's season from variant attributes
		item_season = self.get_item_season(item.item_code)
		
		for source_item_group in self.source_item_groups:
			# Check if this rule is enabled (default to True if not specified)
			is_enabled = getattr(source_item_group, 'enabled', True)
			if not is_enabled:
				continue
			
			# Check item group match (if specified in source)
			# If item_group is None/null, it matches all item groups
			if source_item_group.item_group is not None and source_item_group.item_group != "":
				if source_item_group.item_group != item_group:
					continue
			
			# Check brand match (if specified in source)
			# If brand is None/null, it matches all brands
			if source_item_group.brand is not None and source_item_group.brand != "":
				if source_item_group.brand != item_brand:
					continue
			
			# Check vendor code match (if specified in source)
			# If vendor_code is None/null, it matches all vendor codes
			if source_item_group.custom_vendor_code is not None and source_item_group.custom_vendor_code != "":
				if source_item_group.custom_vendor_code != item_vendor_code:
					continue
			
			# Check season match (if specified in source)
			# If season_attribute is None/null, it matches all seasons
			if source_item_group.season_attribute is not None and source_item_group.season_attribute != "":
				# Check for exact match first (for codes like SS24, FW24)
				if source_item_group.season_attribute != item_season:
					# If no exact match, try to match mapped seasons
					# For example, if source has "Summer" and item has "SS24", they should match
					if not self.seasons_match(source_item_group.season_attribute, item_season):
						continue
			
			# All criteria matched
			return True
		
		return False

	def seasons_match(self, source_season, item_season):
		"""Check if two seasons match (handles both standard names and codes)"""
		# Direct match first - this should handle most cases now
		if source_season == item_season:
			return True
		
		# Season code mappings for backward compatibility
		season_mappings = {
			"Summer": ["SS25", "SS24", "SS23", "SS22", "SS"],
			"Fall": ["FW25", "FW24", "FW23", "FW22", "AW25", "AW24", "AW23", "AW22", "FW", "AW"],
			"Spring": ["SP25", "SP24", "SP23", "SP22", "SP"],
			"Winter": ["WI25", "WI24", "WI23", "WI22", "WI"]
		}
		
		# Check if source season is a standard name and item season is a code
		for standard_name, codes in season_mappings.items():
			if source_season == standard_name and item_season in codes:
				return True
		
		# Check if source season is a code and item season is a standard name
		for standard_name, codes in season_mappings.items():
			if source_season in codes and item_season == standard_name:
				return True
		
		# No pattern matching - only exact matches or mapped matches
		return False

	def get_item_season(self, item_code):
		"""Get item's season from variant attributes"""
		try:
			# Check if the item has variant attributes for Season
			variant_attributes = frappe.db.sql("""
				SELECT attribute_value 
				FROM `tabItem Variant Attribute` 
				WHERE parent = %s AND attribute = 'Season'
				LIMIT 1
			""", (item_code,), as_dict=True)
			
			if variant_attributes and variant_attributes[0].attribute_value:
				season_value = variant_attributes[0].attribute_value
				# Return the original season code for direct matching
				# This allows exact matches like "SS25" to work properly
				return season_value
			
			# If no variant attributes, check custom field on Item as fallback
			season_value = frappe.db.get_value("Item", item_code, "season_attribute")
			if season_value:
				return season_value
			
			# Default to "All Seasons" if no season is specified
			return "All Seasons"
			
		except Exception as e:
			# Log the error for debugging
			frappe.log_error(f"Error getting season for item {item_code}: {str(e)}")
			# If there's any error, default to "All Seasons"
			return "All Seasons"

	def is_item_match(self, item):
		"""Check if specific item matches (to be implemented based on requirements)"""
		# This would need to be implemented based on specific item logic
		return False

	def check_quantity_condition(self, applicable_items):
		"""Check if minimum quantity condition is met"""
		total_qty = sum(flt(item.qty) for item in applicable_items)
		return total_qty >= flt(self.min_qty)

	def check_amount_condition(self, applicable_items):
		"""Check if minimum amount condition is met"""
		total_amount = sum(flt(item.amount) for item in applicable_items)
		return total_amount >= flt(self.min_amount)

	def calculate_reward_quantity(self, applicable_items):
		"""Calculate reward quantity based on Buy X Get Y logic"""
		total_qty = sum(flt(item.qty) for item in applicable_items)
		min_qty = flt(self.min_qty)
		reward_qty = flt(self.reward_qty)
		
		frappe.msgprint(f"=== REWARD CALCULATION DEBUG ===")
		frappe.msgprint(f"Total qty: {total_qty}")
		frappe.msgprint(f"Min qty (Buy): {min_qty}")
		frappe.msgprint(f"Reward qty (Get): {reward_qty}")
		
		# Correct Buy X Get Y formula: floor(total_qty / min_qty) * reward_qty
		# For Buy 2 Get 1: floor(2 / 2) * 1 = floor(1) * 1 = 1 * 1 = 1 free item
		# For Buy 2 Get 1: floor(4 / 2) * 1 = floor(2) * 1 = 2 * 1 = 2 free items
		complete_sets = int(total_qty / min_qty) if min_qty > 0 else 0
		total_free_items = complete_sets * reward_qty
		
		frappe.msgprint(f"Complete sets: {complete_sets}")
		frappe.msgprint(f"Total free items before multiply flag: {total_free_items}")
		
		# Apply multiply_by_min_qty flag
		if not self.multiply_by_min_qty:
			# Apply only once per quotation
			total_free_items = min(total_free_items, reward_qty)
			frappe.msgprint(f"Applied multiply_by_min_qty flag, final free items: {total_free_items}")
		
		return total_free_items

	def find_cheapest_items_for_promotion(self, quotation_doc, target_items, num_free_items):
		"""Find the cheapest items to make free with deterministic sorting priority"""
		try:
			frappe.msgprint(f"=== FINDING CHEAPEST ITEMS DEBUG ===")
			frappe.msgprint(f"Target items: {target_items}")
			frappe.msgprint(f"Number of free items needed: {num_free_items}")
			
			# Get all items in quotation that match target criteria
			candidate_items = []
			
			for item in quotation_doc.items:
				frappe.msgprint(f"Checking item {item.item_code} against target criteria...")
				if self.item_matches_target_criteria(item, target_items):
					frappe.msgprint(f"  ✓ Item {item.item_code} matches target criteria")
					# Ensure original rate is stored
					if not hasattr(item, 'original_rate') or not item.original_rate:
						if getattr(item, 'is_free_item', False) and hasattr(item, 'promotion_discount'):
							item.original_rate = flt(item.promotion_discount)
						else:
							item.original_rate = flt(item.rate)
					
					# Skip already free items
					if not getattr(item, 'is_free_item', False):
						candidate_items.append(item)
						frappe.msgprint(f"  ✓ Added to candidates")
					else:
						frappe.msgprint(f"  ✗ Skipped (already free)")
				else:
					frappe.msgprint(f"  ✗ Item {item.item_code} does not match target criteria")
			
			frappe.msgprint(f"Total candidate items: {len(candidate_items)}")
			if not candidate_items:
				frappe.msgprint("No candidate items found for promotion")
				return []
			
			# Create individual item units for proper quantity handling
			individual_items = []
			for item in candidate_items:
				item_qty = int(flt(item.qty))
				original_rate = getattr(item, 'original_rate', item.rate)
				
				# Get item details for sorting
				item_details = frappe.db.get_value("Item", item.item_code, 
					["brand"], as_dict=True)
				item_brand = item_details.brand if item_details else ""
				
				# Add each individual unit with unique line identifier
				for i in range(item_qty):
					individual_items.append({
						'item': item,
						'rate': original_rate,
						'brand': item_brand,
						'item_code': item.item_code,
						'row_index': getattr(item, 'idx', 0),
						'unit_index': i + 1,
						'line_id': f"{item.item_code}_{getattr(item, 'idx', 0)}_{id(item)}"  # Unique line identifier
					})
			
			# Sort with deterministic priority: Unit Price → Brand → Item Code → Row Index
			individual_items.sort(key=lambda x: (
				x['rate'],           # Unit Price (lowest first)
				x['brand'] or "",    # Brand (A-Z)
				x['item_code'],      # Item Code (A-Z)
				x['row_index']       # Row Index (ascending)
			))
			
			# Select the cheapest individual items
			selected_items = {}
			selected_lines = set()  # Track which lines we've already selected
			remaining_free_qty = num_free_items
			
			for item_unit in individual_items:
				if remaining_free_qty <= 0:
					break
				
				item = item_unit['item']
				item_code = item.item_code
				line_id = item_unit['line_id']
				
				# Skip if we've already selected this line
				if line_id in selected_lines:
					continue
				
				# Track how many units of this item we're making free
				if item_code not in selected_items:
					selected_items[item_code] = {
						'items': [],  # Store all item objects for this item_code
						'free_units': 0,
						'total_units': 0
					}
				
				# Add this specific item object to the list
				selected_items[item_code]['items'].append(item)
				selected_items[item_code]['free_units'] += 1
				selected_items[item_code]['total_units'] += int(flt(item.qty))
				selected_lines.add(line_id)
				remaining_free_qty -= 1
			
			# Convert selected items to free_items list
			free_items = []
			for item_code, data in selected_items.items():
				if data['free_units'] > 0:
					frappe.msgprint(f"  Item {item_code}: {data['free_units']} units to make free across {len(data['items'])} lines")
					# Distribute free units across different lines
					units_per_line = data['free_units'] // len(data['items'])
					remaining_units = data['free_units'] % len(data['items'])
					
					for i, item in enumerate(data['items']):
						units_for_this_line = units_per_line
						if i < remaining_units:  # Distribute remaining units to first few lines
							units_for_this_line += 1
						
						# Add this item object for each unit that should be free on this line
						for j in range(units_for_this_line):
							free_items.append(item)
			
			frappe.msgprint(f"Final free_items list: {len(free_items)} items")
			for i, item in enumerate(free_items):
				frappe.msgprint(f"  {i+1}. {item.item_code}")
			
			frappe.msgprint(f"=== RETURNING {len(free_items)} FREE ITEMS ===")
			return free_items
			
		except Exception as e:
			frappe.log_error(f"Error finding cheapest items for promotion: {str(e)}")
			return []

	def item_matches_target_criteria(self, item, target_items):
		"""Check if an item matches the target criteria for promotion"""
		try:
			# Get item details
			item_details = frappe.db.get_value("Item", item.item_code,
				["item_group", "brand"], as_dict=True)
			
			if not item_details:
				frappe.msgprint(f"  ✗ No item details found for {item.item_code}")
				return False
			
			item_brand = item_details.brand
			frappe.msgprint(f"  Item brand: {item_brand}")
			
			# Check if item matches any target criteria
			for target in target_items:
				frappe.msgprint(f"  Checking against target: {target}")
				
				if target.get("target_brand"):
					target_brand = target.get("target_brand")
					frappe.msgprint(f"    Target brand: {target_brand}")
					if target_brand == item_brand:
						frappe.msgprint(f"    ✓ Brand match: {item_brand} == {target_brand}")
						return True
					else:
						frappe.msgprint(f"    ✗ Brand mismatch: {item_brand} != {target_brand}")
				
				if target.get("target_item"):
					target_item = target.get("target_item")
					frappe.msgprint(f"    Target item: {target_item}")
					if target_item == item.item_code:
						frappe.msgprint(f"    ✓ Item match: {item.item_code} == {target_item}")
						return True
					else:
						frappe.msgprint(f"    ✗ Item mismatch: {item.item_code} != {target_item}")
			
			frappe.msgprint(f"  ✗ No target criteria matched for {item.item_code}")
			return False
			
		except Exception as e:
			frappe.log_error(f"Error checking target criteria: {str(e)}")
			frappe.msgprint(f"  ✗ Error checking target criteria: {str(e)}")
			return False

	def apply_promotion(self, quotation_doc):
		"""Apply promotion to quotation document with robotics logic"""
		try:
			# Debug: Show promotion details
			frappe.msgprint(f"=== PROMOTION DEBUG START ===")
			frappe.msgprint(f"Promotion: {self.name}")
			frappe.msgprint(f"Based On: {self.based_on}")
			frappe.msgprint(f"Min Qty: {self.min_qty}, Min Amount: {self.min_amount}")
			frappe.msgprint(f"Reward Qty: {self.reward_qty}")
			frappe.msgprint(f"Total items in quotation: {len(quotation_doc.items)}")
			frappe.msgprint(f"Actions count: {len(self.actions) if self.actions else 0}")
			
			# Show all actions
			for i, action in enumerate(self.actions or []):
				frappe.msgprint(f"Action {i+1}: Reward Brand={action.reward_brand}, Target Brand={action.target_brand}, Discount %={action.discount_percentage}")
			
			# Validate promotion is active
			if not self.is_valid(quotation_doc.transaction_date):
				frappe.msgprint("Promotion not valid for this date", alert=True)
				return False
			
			# Get applicable items
			applicable_items = self.get_applicable_items(quotation_doc.items)
			frappe.msgprint(f"Applicable items found: {len(applicable_items)}")
			
			# Show details of applicable items
			for i, item in enumerate(applicable_items):
				frappe.msgprint(f"  {i+1}. {item.item_code} - Qty: {item.qty}, Rate: {item.rate}, Amount: {item.amount}")
		
			if not applicable_items:
				frappe.msgprint("No applicable items found for this promotion", alert=True)
				frappe.msgprint("Check your source filters (Item Groups, Brands, etc.)", alert=True)
				return False
		
			# Check conditions with detailed logging
			total_applicable_qty = sum(flt(item.qty) for item in applicable_items)
			total_applicable_amount = sum(flt(item.amount) for item in applicable_items)
			
			frappe.msgprint(f"Total applicable quantity: {total_applicable_qty}")
			frappe.msgprint(f"Total applicable amount: {total_applicable_amount}")
			frappe.msgprint(f"Required min quantity: {self.min_qty}")
			frappe.msgprint(f"Required min amount: {self.min_amount}")
			
			quantity_ok = self.check_quantity_condition(applicable_items)
			amount_ok = self.check_amount_condition(applicable_items)
			
			frappe.msgprint(f"Quantity condition met: {quantity_ok}")
			frappe.msgprint(f"Amount condition met: {amount_ok}")
			
			if not quantity_ok and not amount_ok:
				frappe.msgprint("Promotion conditions not met", alert=True)
				frappe.msgprint(f"Need at least {self.min_qty} quantity OR {self.min_amount} amount", alert=True)
				return False

			# Calculate reward quantity using correct Buy X Get Y formula
			total_free_items = self.calculate_reward_quantity(applicable_items)
			frappe.msgprint(f"Calculated total free items: {total_free_items}")
			if total_free_items <= 0:
				frappe.msgprint("No free items to apply", alert=True)
				return False
			
			# Get target items from all actions
			all_target_items = self.get_all_target_items()
			frappe.msgprint(f"Target items found: {len(all_target_items)}")
			for i, target in enumerate(all_target_items):
				frappe.msgprint(f"  Target {i+1}: {target}")
			if not all_target_items:
				frappe.msgprint("No target items found for promotion", alert=True)
				return False
		
			# Find cheapest items to make free
			frappe.msgprint(f"Looking for {total_free_items} free items...")
			free_items = self.find_cheapest_items_for_promotion(quotation_doc, all_target_items, total_free_items)
			frappe.msgprint(f"Found {len(free_items)} items to make free")
			
			# Fallback: If no target items match, apply to cheapest applicable items
			if not free_items:
				frappe.msgprint("No target items match, applying to cheapest applicable items...")
				free_items = self.find_cheapest_applicable_items(quotation_doc, applicable_items, total_free_items)
				frappe.msgprint(f"Fallback: Found {len(free_items)} applicable items to make free")
				if not free_items:
					frappe.msgprint("No suitable items found for free promotion", alert=True)
					return False
			
			# Apply discounts to selected items
			applied = self.apply_discounts_to_items(quotation_doc, free_items, total_free_items)
			
			if applied:
				frappe.msgprint(f"Promotion applied successfully: {total_free_items} items made free", alert=True)
			
			return applied
			
		except Exception as e:
			frappe.log_error(f"Error applying promotion: {str(e)}")
			frappe.msgprint(f"Error applying promotion: {str(e)}", alert=True)
			return False

	def find_cheapest_applicable_items(self, quotation_doc, applicable_items, num_free_items):
		"""Find cheapest items from applicable items as fallback"""
		try:
			# Sort applicable items by price (cheapest first)
			sorted_items = sorted(applicable_items, key=lambda x: flt(x.rate))
			
			free_items = []
			remaining_free_qty = num_free_items
			
			for item in sorted_items:
				if remaining_free_qty <= 0:
					break
				
				# Skip already free items
				if not getattr(item, 'is_free_item', False):
					free_items.append(item)
					remaining_free_qty -= 1
			
			return free_items
			
		except Exception as e:
			frappe.log_error(f"Error finding cheapest applicable items: {str(e)}")
			return []

	def apply_discounts_to_items(self, quotation_doc, free_items, total_free_items):
		"""Apply discounts to selected items using proper discount fields"""
		try:
			frappe.msgprint(f"=== APPLYING DISCOUNTS DEBUG ===")
			frappe.msgprint(f"Total free items to apply: {total_free_items}")
			frappe.msgprint(f"Free items received: {len(free_items)}")
			
			remaining_free_qty = total_free_items
			applied = False
			
			# Group items by item_code to handle multiple units
			item_groups = {}
			for item in free_items:
				if item.item_code not in item_groups:
					item_groups[item.item_code] = {
						'items': [],
						'count': 0
					}
				item_groups[item.item_code]['items'].append(item)
				item_groups[item.item_code]['count'] += 1
			
			frappe.msgprint(f"Item groups: {[(code, data['count']) for code, data in item_groups.items()]}")
			
			for item_code, data in item_groups.items():
				if remaining_free_qty <= 0:
					break
				
				free_units_needed = data['count']
				frappe.msgprint(f"Processing {item_code}: {free_units_needed} units needed across {len(data['items'])} lines")
				
				# Process each line of this item code
				for item in data['items']:
					if remaining_free_qty <= 0:
						break
					
					frappe.msgprint(f"  Processing line: {item.item_code} (Row {getattr(item, 'idx', '?')})")
					
					# Store original rate if not already stored
					if not hasattr(item, 'original_rate') or not item.original_rate:
						item.original_rate = flt(item.rate)
					
					original_rate = item.original_rate
					item_qty = flt(item.qty)
					
					# Calculate how much of this line should be free
					free_qty = min(item_qty, remaining_free_qty)
					
					frappe.msgprint(f"    Item qty: {item_qty}, Free qty: {free_qty}, Original rate: {original_rate}")
					
					if free_qty > 0:
						# Calculate discount amount for the free quantity
						discount_amount = free_qty * original_rate
						
						# Apply discount using proper fields
						item.discount_percentage = 100.0  # 100% discount for free items
						item.discount_amount = discount_amount
						item.is_free_item = 1
						item.promotion_applied = self.name
						item.promotion_discount = discount_amount
						
						# Update amount to reflect discount
						item.amount = (item_qty * original_rate) - discount_amount
						
						frappe.msgprint(f"    Applied discount: {discount_amount}, New amount: {item.amount}")
						
						remaining_free_qty -= free_qty
						applied = True
					else:
						frappe.msgprint(f"    No free units to apply to this line")
			
			frappe.msgprint(f"Remaining free qty after processing: {remaining_free_qty}")
			return applied
			
		except Exception as e:
			frappe.log_error(f"Error applying discounts to items: {str(e)}")
		return False

	def get_all_target_items(self):
		"""Get all target items from all actions"""
		target_items = []
		
		for action in self.actions:
			if action.target_brand:
				target_items.append({"target_brand": action.target_brand})
		
			if action.target_item:
				target_items.append({"target_item": action.target_item})
		
		return target_items

	def remove_promotion(self, quotation_doc):
		"""Remove all promotion-related discounts and restore original values"""
		try:
			# Reset promotion-related fields
			quotation_doc.promotion_applied = 0
			quotation_doc.coupon_code = ""
			
			# Remove discounts from all items (DO NOT DELETE ITEMS)
			for item in quotation_doc.items:
				# Reset discount fields
				item.discount_percentage = 0
				item.discount_amount = 0
				
				# Restore original rate if it was stored
				if hasattr(item, 'original_rate') and item.original_rate:
					item.rate = flt(item.original_rate)
					# Clear the original_rate field
					item.original_rate = 0
				
				# If this was a free item, restore to normal item
				if hasattr(item, 'is_free_item') and item.is_free_item:
					item.is_free_item = 0
				
				# Recalculate item amount based on current rate
				item.amount = flt(item.rate) * flt(item.qty)
				
				# Remove any promotion-specific fields if they exist
				if hasattr(item, 'promotion_discount'):
					item.promotion_discount = 0
				if hasattr(item, 'promotion_applied'):
					item.promotion_applied = ""
			
			# Recalculate taxes and totals
			quotation_doc.calculate_taxes_and_totals()
			
			return True
			
		except Exception as e:
			frappe.log_error(f"Error removing promotion: {str(e)}")
			return False

	def get_promotion_summary(self, quotation_doc):
		"""Get summary of applied promotions"""
		summary = {
			"promotion_title": self.title,
			"discount_amount": 0,
			"applied_items": []
		}
		
		for item in quotation_doc.items:
			if hasattr(item, 'promotion_discount') and item.promotion_discount:
				summary["discount_amount"] += flt(item.promotion_discount)
				summary["applied_items"].append({
					"item_code": item.item_code,
					"item_name": item.item_name,
					"discount_amount": item.promotion_discount
				})
		
		return summary

	@frappe.whitelist()
	def test_promotion_on_quotation(self, quotation):
		"""Test promotion on a specific quotation"""
		try:
			quotation_doc = frappe.get_doc("Quotation", quotation)
			
			# Check if promotion is valid
			if not self.is_valid(quotation_doc.transaction_date):
				return {
					"success": False,
					"message": "Promotion is not valid for this quotation date"
				}
			
			# Get applicable items
			applicable_items = self.get_applicable_items(quotation_doc.items)
			
			if not applicable_items:
				return {
					"success": False,
					"message": "No applicable items found for this promotion"
				}
			
			# Check conditions
			qty_condition = self.check_quantity_condition(applicable_items)
			amount_condition = self.check_amount_condition(applicable_items)
			
			if not qty_condition and not amount_condition:
				return {
					"success": False,
					"message": "Promotion conditions not met (quantity: {}, amount: {})".format(
						qty_condition, amount_condition
					)
				}
			
			# Apply promotion
			if self.apply_promotion(quotation_doc):
				quotation_doc.save()
				return {
					"success": True,
					"message": "Promotion applied successfully",
					"summary": self.get_promotion_summary(quotation_doc)
				}
			else:
				return {
					"success": False,
					"message": "Failed to apply promotion"
				}
				
		except Exception as e:
			return {
				"success": False,
				"message": "Error testing promotion: {}".format(str(e))
			}


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
		else:
			frappe.msgprint(_("Promotion conditions not met"))
			return False
			
	except Exception as e:
		frappe.throw(_("Error applying promotion: {0}").format(str(e)))


@frappe.whitelist()
def get_available_promotions(quotation_name):
	"""Get available promotions for quotation"""
	try:
		quotation_doc = frappe.get_doc("Quotation", quotation_name)
		
		promotions = frappe.db.sql("""
			SELECT name, title, valid_from, valid_upto, min_qty, min_amount
			FROM `tabPromotion`
			WHERE disabled = 0
			AND (valid_from IS NULL OR valid_from <= %s)
			AND (valid_upto IS NULL OR valid_upto >= %s)
			ORDER BY creation DESC
		""", (quotation_doc.transaction_date or today(), quotation_doc.transaction_date or today()), as_dict=True)
		
		available_promotions = []
		for promotion in promotions:
			promotion_doc = frappe.get_doc("Promotion", promotion.name)
			if promotion_doc.is_valid(quotation_doc.transaction_date):
				available_promotions.append(promotion)
		
		return available_promotions
		
	except Exception as e:
		frappe.throw(_("Error getting promotions: {0}").format(str(e)))


@frappe.whitelist()
def validate_coupon_code(coupon_code, quotation_name):
	"""Validate coupon code and return associated promotion"""
	try:
		# Check if coupon code exists and is valid
		coupon = frappe.db.get_value("Coupon Code", {
			"coupon_code": coupon_code,
			"disabled": 0
		}, ["name", "promotion", "valid_from", "valid_upto", "maximum_use", "used"], as_dict=True)
		
		if not coupon:
			return {
				"valid": False,
				"message": "Invalid coupon code"
			}
		
		# Check if coupon has reached maximum use
		if coupon.maximum_use and coupon.used >= coupon.maximum_use:
			return {
				"valid": False,
				"message": "Coupon code has reached maximum usage limit"
			}
		
		# Check validity dates
		quotation_doc = frappe.get_doc("Quotation", quotation_name)
		quotation_date = quotation_doc.transaction_date or today()
		
		if coupon.valid_from and getdate(quotation_date) < getdate(coupon.valid_from):
			return {
				"valid": False,
				"message": "Coupon code not yet valid"
			}
		
		if coupon.valid_upto and getdate(quotation_date) > getdate(coupon.valid_upto):
			return {
				"valid": False,
				"message": "Coupon code has expired"
			}
		
		# Get promotion details
		if coupon.promotion:
			promotion_doc = frappe.get_doc("Promotion", coupon.promotion)
			
			return {
				"valid": True,
				"message": "Coupon code is valid",
				"promotion": {
					"name": promotion_doc.name,
					"title": promotion_doc.title,
					"description": getattr(promotion_doc, 'description', '')
				}
			}
		
		return {
			"valid": False,
			"message": "No promotion associated with this coupon code"
		}
		
	except Exception as e:
		frappe.throw(_("Error validating coupon code: {0}").format(str(e)))


@frappe.whitelist()
def apply_coupon_code(coupon_code, quotation_name):
	"""Apply coupon code and associated promotion to quotation"""
	try:
		# First validate the coupon code
		validation_result = validate_coupon_code(coupon_code, quotation_name)
		
		if not validation_result["valid"]:
			return {
				"success": False,
				"message": validation_result["message"]
			}
		
		# Get quotation and promotion
		quotation_doc = frappe.get_doc("Quotation", quotation_name)
		coupon = frappe.db.get_value("Coupon Code", {
			"coupon_code": coupon_code
		}, ["name", "promotion"], as_dict=True)
		
		if not coupon.promotion:
			return {
				"success": False,
				"message": "No promotion associated with this coupon code"
			}
		
		promotion_doc = frappe.get_doc("Promotion", coupon.promotion)
		
		frappe.msgprint(f"=== COUPON CODE DEBUG ===")
		frappe.msgprint(f"Coupon: {coupon_code}")
		frappe.msgprint(f"Promotion: {promotion_doc.name}")
		frappe.msgprint(f"Quotation: {quotation_name}")
		
		# Apply the promotion
		frappe.msgprint(f"Calling apply_promotion method...")
		if promotion_doc.apply_promotion(quotation_doc):
			# Set promotion applied flag and coupon code BEFORE saving
			quotation_doc.promotion_applied = 1
			quotation_doc.coupon_code = coupon.name
			
			# Save quotation with promotion changes
			quotation_doc.flags.ignore_validate = True
			quotation_doc.flags.ignore_on_update = True
			quotation_doc.save()
			
			# Force reload the document to ensure changes are persisted
			frappe.db.commit()
			
			# Update coupon usage count AFTER successful save
			frappe.db.sql("""
				UPDATE `tabCoupon Code` 
				SET used = used + 1 
				WHERE name = %s
			""", (coupon.name))
			
			return {
				"success": True,
				"message": "Coupon code applied successfully",
				"promotion": validation_result["promotion"]
			}
		else:
			return {
				"success": False,
				"message": "Promotion conditions not met for this quotation"
			}
			
	except Exception as e:
		frappe.throw(_("Error applying coupon code: {0}").format(str(e)))


@frappe.whitelist()
def remove_coupon_promotion(quotation_name):
	"""Remove coupon promotion from quotation when coupon code is cleared"""
	try:
		quotation_doc = frappe.get_doc("Quotation", quotation_name)
		
		# Reset promotion-related fields
		quotation_doc.promotion_applied = 0
		quotation_doc.coupon_code = ""
		
		frappe.msgprint("=== REMOVING PROMOTION ===")
		frappe.msgprint(f"Total items before removal: {len(quotation_doc.items)}")
		
		# Remove discounts from all items (DO NOT DELETE ITEMS)
		for item in quotation_doc.items:
			frappe.msgprint(f"Processing item: {item.item_code}, Qty: {item.qty}, Rate: {item.rate}")
			
			# Store current values for debugging
			old_rate = item.rate
			old_discount_pct = getattr(item, 'discount_percentage', 0)
			old_discount_amt = getattr(item, 'discount_amount', 0)
			
			# Reset discount fields
			item.discount_percentage = 0
			item.discount_amount = 0
			
			# Restore original rate if it was stored
			if hasattr(item, 'original_rate') and item.original_rate:
				item.rate = flt(item.original_rate)
				frappe.msgprint(f"  Restored rate from {old_rate} to {item.rate}")
				# Clear the original_rate field
				item.original_rate = 0
			
			# If this was a free item, restore to normal item
			if hasattr(item, 'is_free_item') and item.is_free_item:
				item.is_free_item = 0
				frappe.msgprint(f"  Removed free item flag")
			
			# Recalculate item amount based on current rate
			item.amount = flt(item.rate) * flt(item.qty)
			frappe.msgprint(f"  Reset: Discount %: {old_discount_pct}->0, Discount Amt: {old_discount_amt}->0, Amount: {item.amount}")
			
			# Remove any promotion-specific fields if they exist
			if hasattr(item, 'promotion_discount'):
				item.promotion_discount = 0
			if hasattr(item, 'promotion_applied'):
				item.promotion_applied = ""
		
		# Recalculate taxes and totals
		quotation_doc.calculate_taxes_and_totals()
		
		frappe.msgprint(f"Total items after processing: {len(quotation_doc.items)}")
		
		# Save the document
		quotation_doc.flags.ignore_validate = True
		quotation_doc.flags.ignore_on_update = True
		quotation_doc.save()
		
		frappe.msgprint(f"Total items after save: {len(quotation_doc.items)}")
		frappe.msgprint("Promotion removed successfully!", alert=True)
		
		return {
			"success": True,
			"message": "Promotion removed successfully"
		}
		
	except Exception as e:
		frappe.throw(_("Error removing coupon promotion: {0}").format(str(e)))