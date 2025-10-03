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
		"""Get items that match the promotion criteria"""
		applicable_items = []
		
		for item in quotation_items:
			if self.based_on == "Brand":
				if self.is_brand_match(item):
					applicable_items.append(item)
			elif self.based_on == "Item Group":
				if self.is_item_group_match(item):
					applicable_items.append(item)
			elif self.based_on == "Item":
				if self.is_item_match(item):
					applicable_items.append(item)
		
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
		"""Check if item group matches (to be implemented based on requirements)"""
		# This would need to be implemented based on specific item group logic
		return False

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

	def calculate_reward_quantity(self, applicable_items, action):
		"""Calculate reward quantity based on multiply_by_min_qty flag"""
		if not self.multiply_by_min_qty:
			return flt(action.reward_qty)
		
		total_qty = sum(flt(item.qty) for item in applicable_items)
		multiplier = int(total_qty / flt(self.min_qty)) if flt(self.min_qty) > 0 else 0
		return flt(action.reward_qty) * multiplier

	def apply_promotion(self, quotation_doc):
		"""Apply promotion to quotation document"""
		# Fix: Pass the quotation date to is_valid method
		if not self.is_valid(quotation_doc.transaction_date):
			return False
		
		applicable_items = self.get_applicable_items(quotation_doc.items)
		
		if not applicable_items:
			return False
		
		# Check conditions
		if not self.check_quantity_condition(applicable_items) and not self.check_amount_condition(applicable_items):
			return False
		#frappe.msgprint(_("Promotion applied: {0} items discounted").format(self.name))
		# Apply actions
		applied = False
		for action in self.actions:
			if self.apply_action(quotation_doc, applicable_items, action):
				applied = True
		
		return applied

	def apply_action(self, quotation_doc, applicable_items, action):
		"""Apply specific action to quotation"""
		if action.reward_type == "Discount %":
			return self.apply_discount_percentage(quotation_doc, applicable_items, action)
		elif action.reward_type == "Discount Amount":
			return self.apply_discount_amount(quotation_doc, applicable_items, action)
		elif action.reward_type == "Bundle Price (Fixed)":
			return self.apply_bundle_price(quotation_doc, applicable_items, action)
		elif action.reward_type == "Free Item":
			return self.apply_free_item(quotation_doc, applicable_items, action)
		
		return False

	def apply_discount_percentage(self, quotation_doc, applicable_items, action):
		"""Apply percentage discount to target items"""
		# Get target items based on action configuration
		target_items = self.get_target_items(action)
		
		if not target_items:
			frappe.msgprint(_("No target items found for this action"))
			return False
		
		discount_applied = False
		items_discounted = 0
		
		# Calculate how many items should get the discount based on promotion logic
		if self.multiply_by_min_qty:
			# For "Buy 2 Get 1 Free" - apply discount to every 2nd item
			total_qty = sum(flt(item.qty) for item in applicable_items)
			# Calculate how many complete sets of min_qty we have
			complete_sets = int(total_qty / flt(self.min_qty))
			# Each complete set gives us reward_qty free items
			discount_qty = complete_sets * flt(action.reward_qty)
		else:
			# Apply discount to reward quantity only
			discount_qty = flt(action.reward_qty)
		
		#frappe.msgprint(_("Total applicable qty: {0}, Min qty: {1}, Discount qty: {2}").format(
		#	sum(flt(item.qty) for item in applicable_items), self.min_qty, discount_qty
		#))
		
		# Apply discount to target items - only to the number that should be free
		for item in quotation_doc.items:
			if item.item_code in target_items and items_discounted < discount_qty:
				# Calculate how much of this item should be discounted
				remaining_discount = discount_qty - items_discounted
				item_qty_to_discount = min(flt(item.qty), remaining_discount)
				
				if item_qty_to_discount > 0:
					# Calculate discount percentage for the portion that should be free
					# For 100% discount on 1 out of 2 items, we need 50% discount on the whole item
					discount_percentage = (flt(action.discount_percentage) * item_qty_to_discount) / flt(item.qty)
					
					# Calculate discount amount for the portion that should be free
					discount_amount = (flt(item.rate) * item_qty_to_discount) * flt(action.discount_percentage) / 100
					
					# Ensure discount doesn't exceed the item amount
					item_total_amount = flt(item.rate) * flt(item.qty)
					discount_amount = min(discount_amount, item_total_amount)
					
					# Apply discount to the correct fields
					item.discount_percentage = flt(item.discount_percentage or 0) + discount_percentage
					item.discount_amount = flt(item.discount_amount or 0) + discount_amount
					
					# Update the item amount - only discount the portion that should be free
					item.rate = (item_total_amount - discount_amount)/item.qty
					item.amount = item_total_amount - discount_amount
					
					# Ensure amount doesn't go negative
					if item.amount < 0:
						item.amount = 0
						item.discount_amount = item_total_amount
						item.discount_percentage = 100
					
					items_discounted += item_qty_to_discount
					discount_applied = True
					
					#frappe.msgprint(_("Applied {0}% discount to {1} qty of item {2}. Discount amount: {3}, New amount: {4}").format(
					#	discount_percentage, item_qty_to_discount, item.item_code, discount_amount, item.amount
					#))
		
		# if discount_applied:
		# 	frappe.msgprint(_("Promotion applied: {0} items discounted").format(items_discounted))
		# else:
		# 	frappe.msgprint(_("No items qualified for discount"))
		
		return discount_applied

	def apply_discount_amount(self, quotation_doc, applicable_items, action):
		"""Apply fixed discount amount to target items"""
		# Get target items based on action configuration
		target_items = self.get_target_items(action)
		
		if not target_items:
			frappe.msgprint(_("No target items found for this action"))
			return False
		
		discount_applied = False
		items_discounted = 0
		
		# Calculate how many items should get the discount based on promotion logic
		if self.multiply_by_min_qty:
			# For "Buy 2 Get 1 Free" - apply discount to every 2nd item
			total_qty = sum(flt(item.qty) for item in applicable_items)
			# Calculate how many complete sets of min_qty we have
			complete_sets = int(total_qty / flt(self.min_qty))
			# Each complete set gives us reward_qty free items
			discount_qty = complete_sets * flt(action.reward_qty)
		else:
			# Apply discount to reward quantity only
			discount_qty = flt(action.reward_qty)
		
		#frappe.msgprint(_("Total applicable qty: {0}, Min qty: {1}, Discount qty: {2}").format(
		#	sum(flt(item.qty) for item in applicable_items), self.min_qty, discount_qty
		#))
		
		# Apply discount to target items - only to the number that should be free
		for item in quotation_doc.items:
			if item.item_code in target_items and items_discounted < discount_qty:
				# Calculate how much of this item should be discounted
				remaining_discount = discount_qty - items_discounted
				item_qty_to_discount = min(flt(item.qty), remaining_discount)
				
				if item_qty_to_discount > 0:
					# Calculate discount amount for the portion that should be free
					discount_amount = flt(action.discount_amount) * item_qty_to_discount
					
					# Ensure discount doesn't exceed the item amount
					item_total_amount = flt(item.rate) * flt(item.qty)
					discount_amount = min(discount_amount, item_total_amount)
					
					# Calculate discount percentage based on the discount amount
					discount_percentage = (discount_amount / item_total_amount) * 100 if item_total_amount > 0 else 0
					
					# Apply discount to the correct fields
					item.discount_percentage = flt(item.discount_percentage or 0) + discount_percentage
					item.discount_amount = flt(item.discount_amount or 0) + discount_amount
					
					# Update the item amount - only discount the portion that should be free
					item.amount = item_total_amount - discount_amount
					
					# Ensure amount doesn't go negative
					if item.amount < 0:
						item.amount = 0
						item.discount_amount = item_total_amount
						item.discount_percentage = 100
					
					items_discounted += item_qty_to_discount
					discount_applied = True
					
					#frappe.msgprint(_("Applied {0} discount to {1} qty of item {2}. Discount amount: {3}, New amount: {4}").format(
					#	action.discount_amount, item_qty_to_discount, item.item_code, discount_amount, item.amount
					#))
		
		# if discount_applied:
		# 	frappe.msgprint(_("Promotion applied: {0} items discounted").format(items_discounted))
		# else:
		# 	frappe.msgprint(_("No items qualified for discount"))
		
		return discount_applied

	def apply_bundle_price(self, quotation_doc, applicable_items, action):
		"""Apply bundle pricing (to be implemented)"""
		# This would need to be implemented based on specific bundle pricing logic
		return False

	def apply_free_item(self, quotation_doc, applicable_items, action):
		"""Apply free item reward (to be implemented)"""
		# This would need to be implemented based on specific free item logic
		return False

	def get_target_items(self, action):
		"""Get target items based on action configuration"""
		target_items = []
		
		if action.target_brand:
			# Get all items from target brand
			items = frappe.db.sql("""
				SELECT name FROM `tabItem` 
				WHERE brand = %s AND disabled = 0
			""", (action.target_brand,), as_dict=True)
			target_items.extend([item.name for item in items])
		
		if action.target_item:
			target_items.append(action.target_item)
		
		return list(set(target_items))  # Remove duplicates

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
		
		# Apply the promotion
		if promotion_doc.apply_promotion(quotation_doc):
			# Update coupon usage count
			frappe.db.sql("""
				UPDATE `tabCoupon Code` 
				SET used = used + 1 
				WHERE name = %s
			""", (coupon.name))
			
			# Save quotation
			quotation_doc.calculate_taxes_and_totals()
			quotation_doc.coupon_code=coupon.name
			quotation_doc.flags.ignore_validate = True
			quotation_doc.flags.ignore_on_update = True
			quotation_doc.save()
			
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