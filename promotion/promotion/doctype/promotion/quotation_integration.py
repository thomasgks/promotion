# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, flt
from promotion.promotion.doctype.promotion.promotion import Promotion

@frappe.whitelist()
def test():
    print("OK")

def validate_quotation_promotions(quotation_doc, method):
	"""Validate promotions on quotation"""
	if quotation_doc.docstatus != 0:  # Only for draft documents
		return
	
	# Handle coupon code changes
	if quotation_doc.coupon_code and not quotation_doc.promotion_applied:
		# Coupon code is present but promotion not applied - apply it
		apply_quotation_promotions(quotation_doc, method)
	elif not quotation_doc.coupon_code and quotation_doc.promotion_applied:
		# Coupon code is cleared but promotion is still applied - remove it
		remove_quotation_promotions(quotation_doc, method)
	elif quotation_doc.coupon_code and quotation_doc.promotion_applied:
		# Check if the current coupon code matches the applied promotion
		# If different, remove old and apply new
		# current_coupon = frappe.db.get_value("Coupon Code", {"coupon_code": quotation_doc.coupon_code}, "name")
		# if current_coupon and hasattr(quotation_doc, '_doc_before_save'):
		# 	old_coupon_code = quotation_doc._doc_before_save.get('coupon_code', '')
		# 	if old_coupon_code != quotation_doc.coupon_code:
		# 		# Coupon code changed - remove old promotion and apply new
		remove_quotation_promotions(quotation_doc, method)
		apply_quotation_promotions(quotation_doc, method)


def apply_quotation_promotions(quotation_doc, method):
	"""Apply promotions to quotation"""
	# If quotation is being submitted, preserve promotion data
	if quotation_doc.docstatus == 1:
		preserve_promotion_on_submit(quotation_doc, method)
		return
	
	if quotation_doc.docstatus != 0 or quotation_doc.promotion_applied:  # Only for draft documents
		return
	
	# If coupon code is provided, apply promotion based on coupon
	if quotation_doc.coupon_code:
		try:
			# Validate and apply coupon code
			coupon = frappe.db.get_value("Coupon Code", {
				"coupon_code": quotation_doc.coupon_code,
				"disabled": 0
			}, ["name", "promotion"], as_dict=True)
			
			if coupon and coupon.promotion:
				promotion_doc = frappe.get_doc("Promotion", coupon.promotion)
				
				if promotion_doc.apply_promotion(quotation_doc):
					# Set promotion applied flag
					quotation_doc.promotion_applied = 1
					
					# Set flags to avoid validation loops
					quotation_doc.flags.ignore_validate = True
					quotation_doc.flags.ignore_on_update = True
					quotation_doc.flags.ignore_version = True
					
					# Recalculate taxes and totals
					quotation_doc.calculate_taxes_and_totals()
					
					return
		except Exception as e:
			frappe.log_error(f"Error applying coupon promotion: {str(e)}")
	
	# Fallback to general promotion logic if no coupon code
	available_promotions = get_available_promotions_for_quotation(quotation_doc)
	
	applied_promotions = []
	total_discount = 0
	
	for promotion_name in available_promotions:
		promotion_doc = frappe.get_doc("Promotion", promotion_name)
		
		if promotion_doc.apply_promotion(quotation_doc):
			applied_promotions.append(promotion_doc.title)
			
			# Calculate total discount
			for item in quotation_doc.items:
				if hasattr(item, 'promotion_discount') and item.promotion_discount:
					total_discount += flt(item.promotion_discount)
	
	# Store promotion information
	if applied_promotions:
		quotation_doc.promotion_applied = 1
		quotation_doc.promotion_discount = total_discount
		quotation_doc.applied_promotions = ", ".join(applied_promotions)
		
		# Set flags to avoid validation loops
		quotation_doc.flags.ignore_validate = True
		quotation_doc.flags.ignore_on_update = True
		quotation_doc.flags.ignore_version = True
		
		# Recalculate taxes and totals
		quotation_doc.calculate_taxes_and_totals()
		
		# Add comment
		quotation_doc.add_comment(
			"Info",
			_("Promotions applied: {0}. Total discount: {1}").format(
				", ".join(applied_promotions),
				frappe.format(total_discount, {"fieldtype": "Currency"})
			)
		)


def remove_quotation_promotions(quotation_doc, method):
	"""Remove promotions from quotation"""
	if quotation_doc.docstatus != 0:  # Only for draft documents
		return
	
	# Reset promotion fields
	quotation_doc.promotion_applied = 0
	quotation_doc.promotion_discount = 0
	quotation_doc.applied_promotions = ""
	
	# Remove promotion discounts from items
	for item in quotation_doc.items:
		# Reset discount fields
		item.discount_percentage = 0
		item.discount_amount = 0
		
		# Recalculate item amount based on original rate
		item.amount = flt(item.rate) * flt(item.qty)
		
		# Remove any promotion-specific fields if they exist
		if hasattr(item, 'promotion_discount'):
			item.promotion_discount = 0
	
	# Set flags to avoid validation loops
	quotation_doc.flags.ignore_validate = True
	quotation_doc.flags.ignore_on_update = True
	quotation_doc.flags.ignore_version = True
	
	# Recalculate taxes and totals
	quotation_doc.calculate_taxes_and_totals()
   


def preserve_promotion_on_submit(quotation_doc, method=None):
	"""Preserve promotion data when quotation is submitted"""
	try:
		# Ensure all promotion-related fields are preserved
		for item in quotation_doc.items:
			# Check if item has promotion applied (100% discount or has promotion_discount)
			if (hasattr(item, 'promotion_discount') and item.promotion_discount) or \
			   (hasattr(item, 'discount_percentage') and flt(item.discount_percentage) == 100.0):
				# Make sure items keep their discount
				if not item.discount_amount:
					if hasattr(item, 'promotion_discount') and item.promotion_discount:
						item.discount_amount = item.promotion_discount
						item.discount_percentage = 100.0
				
				# Ensure amount reflects the discount
				if hasattr(item, 'original_rate') and item.original_rate:
					original_amount = flt(item.original_rate) * flt(item.qty)
					item.amount = original_amount - flt(item.discount_amount)
				
				frappe.msgprint(f"Preserved promotion item: {item.item_code}, Discount: {item.discount_amount}")
	except Exception as e:
		frappe.log_error(f"Error preserving promotion on submit: {str(e)}")


def get_available_promotions_for_quotation(quotation_doc):
	"""Get available promotions for quotation"""
	available_promotions = []
	
	# Get all active promotions
	promotions = frappe.db.sql("""
		SELECT name, title, valid_from, valid_upto, min_qty, min_amount, based_on
		FROM `tabPromotion`
		WHERE disabled = 0
		AND (valid_from IS NULL OR valid_from <= %s)
		AND (valid_upto IS NULL OR valid_upto >= %s)
		ORDER BY creation DESC
	""", (quotation_doc.transaction_date or today(), quotation_doc.transaction_date or today()), as_dict=True)
	
	for promotion in promotions:
		promotion_doc = frappe.get_doc("Promotion", promotion.name)
		
		# Check if promotion is valid for this quotation
		if promotion_doc.is_valid(quotation_doc.transaction_date):
			# Check if promotion conditions are met
			applicable_items = promotion_doc.get_applicable_items(quotation_doc.items)
			
			if applicable_items:
				# Check quantity and amount conditions
				if (promotion_doc.check_quantity_condition(applicable_items) or 
					promotion_doc.check_amount_condition(applicable_items)):
					available_promotions.append(promotion.name)
	
	return available_promotions


@frappe.whitelist()
def apply_promotion_to_quotation(quotation_name, promotion_name):
	"""Apply specific promotion to quotation"""
	try:
		quotation_doc = frappe.get_doc("Quotation", quotation_name)
		promotion_doc = frappe.get_doc("Promotion", promotion_name)
		
		if promotion_doc.apply_promotion(quotation_doc):
			quotation_doc.flags.ignore_validate = True
			quotation_doc.flags.ignore_on_update = True
			quotation_doc.save()
			#frappe.msgprint(_("Promotion '{0}' applied successfully").format(promotion_doc.title))
			return True
		else:
			frappe.msgprint(_("Promotion conditions not met"))
			return False
			
	except Exception as e:
		frappe.throw(_("Error applying promotion: {0}").format(str(e)))


@frappe.whitelist()
def remove_promotion_from_quotation(quotation_name, promotion_name):
	"""Remove specific promotion from quotation"""
	try:
		quotation_doc = frappe.get_doc("Quotation", quotation_name)
		
		# Reset promotion fields
		quotation_doc.promotion_applied = 0
		quotation_doc.promotion_discount = 0
		quotation_doc.applied_promotions = ""
		
		# Remove promotion discounts from items
		for item in quotation_doc.items:
			if hasattr(item, 'promotion_discount'):
				item.promotion_discount = 0
		
		quotation_doc.save()
		frappe.msgprint(_("Promotion removed successfully"))
		return True
		
	except Exception as e:
		frappe.throw(_("Error removing promotion: {0}").format(str(e)))


@frappe.whitelist()
def get_quotation_promotion_summary(quotation_name):
	"""Get promotion summary for quotation"""
	try:
		quotation_doc = frappe.get_doc("Quotation", quotation_name)
		
		summary = {
			"promotion_applied": getattr(quotation_doc, 'promotion_applied', 0),
			"promotion_discount": getattr(quotation_doc, 'promotion_discount', 0),
			"applied_promotions": getattr(quotation_doc, 'applied_promotions', ""),
			"available_promotions": get_available_promotions_for_quotation(quotation_doc)
		}
		
		return summary
		
	except Exception as e:
		frappe.throw(_("Error getting promotion summary: {0}").format(str(e)))


@frappe.whitelist()
def validate_coupon_code(coupon_code, quotation_name):
	"""Validate coupon code and return associated promotion"""
	try:
		# Check if coupon code exists and is valid
		coupon = frappe.db.get_value("Coupon Code", {
			"coupon_code": coupon_code,
			"disabled": 0
		}, ["name", "promotion", "valid_from", "valid_upto"], as_dict=True)
		
		if not coupon:
			return {
				"valid": False,
				"message": "Invalid coupon code"
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
					"description": promotion_doc.description if hasattr(promotion_doc, 'description') else ""
				}
			}
		
		return {
			"valid": False,
			"message": "No promotion associated with this coupon code"
		}
		
	except Exception as e:
		frappe.throw(_("Error validating coupon code: {0}").format(str(e)))
