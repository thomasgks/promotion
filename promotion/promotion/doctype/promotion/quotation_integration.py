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
		#frappe.throw("one")
		# Coupon code is present but promotion not applied - apply it
		apply_quotation_promotions(quotation_doc, method)
	elif not quotation_doc.coupon_code and quotation_doc.promotion_applied:
		#frappe.throw("two")

		# Coupon code is cleared but promotion is still applied - remove it
		remove_quotation_promotions(quotation_doc, method)
	elif quotation_doc.coupon_code and quotation_doc.promotion_applied:
		#frappe.throw("three")

		# Coupon code changed - remove old promotion and apply new
		remove_quotation_promotions(quotation_doc, method)
		apply_quotation_promotions(quotation_doc, method)

def apply_quotation_promotions(quotation_doc, method):
	"""Apply promotions to quotation"""
	# If quotation is being submitted, preserve promotion data
	if quotation_doc.docstatus == 1:
		preserve_promotion_on_submit(quotation_doc, method)
		return
	
	if quotation_doc.docstatus != 0 or quotation_doc.promotion_applied:
		return
	
	# If coupon code is provided, apply promotion based on coupon
	if quotation_doc.coupon_code:
		try:
			coupon = frappe.db.get_value("Coupon Code", {
				"coupon_code": quotation_doc.coupon_code
			}, ["name", "promotion", "custom_disabled"], as_dict=True)
			
			# Skip if coupon is disabled
			if coupon and getattr(coupon, 'custom_disabled', 0):
				frappe.log_error(f"Coupon code {quotation_doc.coupon_code} is disabled")
				return
			
			if coupon and coupon.promotion:
				promotion_doc = frappe.get_doc("Promotion", coupon.promotion)
				
				if promotion_doc.apply_promotion(quotation_doc):
					quotation_doc.promotion_applied = 1
					quotation_doc.flags.ignore_validate = True
					quotation_doc.flags.ignore_on_update = True
					quotation_doc.calculate_taxes_and_totals()
					return
		except Exception as e:
			frappe.log_error(f"Error applying coupon promotion: {str(e)}")
	
	# Fallback to general promotion logic
	available_promotions = get_available_promotions_for_quotation(quotation_doc)
	
	applied_promotions = []
	total_discount = 0
	
	for promotion_name in available_promotions:
		promotion_doc = frappe.get_doc("Promotion", promotion_name)
		
		if promotion_doc.apply_promotion(quotation_doc):
			applied_promotions.append(promotion_doc.title)
			
			# Calculate total discount from free items
			for item in quotation_doc.items:
				if getattr(item, 'promotion_applied', False) and hasattr(item, 'promotion_discount'):
					total_discount += flt(item.promotion_discount)
	
	# Store promotion information
	if applied_promotions:
		quotation_doc.promotion_applied = 1
		quotation_doc.promotion_discount = total_discount
		quotation_doc.applied_promotions = ", ".join(applied_promotions)
		
		quotation_doc.flags.ignore_validate = True
		quotation_doc.flags.ignore_on_update = True
		quotation_doc.calculate_taxes_and_totals()
		
		quotation_doc.add_comment(
			"Info",
			_("Promotions applied: {0}. Total discount: {1}").format(
				", ".join(applied_promotions),
				frappe.format(total_discount, {"fieldtype": "Currency"})
			)
		)

def remove_quotation_promotions(quotation_doc, method):
    """Remove promotions from quotation"""
    if quotation_doc.docstatus != 0:
        return
    
    # Reset promotion fields
    quotation_doc.promotion_applied = 0
    quotation_doc.promotion_discount = 0
    quotation_doc.applied_promotions = ""
    
    # Remove discount from items that were part of promotions
    for item in quotation_doc.items:
        if getattr(item, 'promotion_applied', False):
            # Reset discount fields
            item.discount_percentage = 0
            item.discount_amount = 0
            item.rate = item.price_list_rate  # Reset to original price
            
            # Reset promotion flags on item
            item.promotion_applied = 0
            item.promotion_discount=0
            item.applied_promotions = ""
    
    quotation_doc.flags.ignore_validate = True
    quotation_doc.flags.ignore_on_update = True
    quotation_doc.calculate_taxes_and_totals()

def preserve_promotion_on_submit(quotation_doc, method=None):
	"""Preserve promotion data when quotation is submitted"""
	try:
		# Ensure free items are preserved with their zero rate
		for item in quotation_doc.items:
			if getattr(item, 'promotion_applied', False):
				# Ensure free items keep their zero rate and free item flag
				item.rate = 0.00
				item.amount = 0.00
				item.promotion_applied = 1
				
				frappe.msgprint(f"Preserved free item: {item.item_code}, Qty: {item.qty}")
	except Exception as e:
		frappe.log_error(f"Error preserving promotion on submit: {str(e)}")

def get_available_promotions_for_quotation(quotation_doc):
	"""Get available promotions for quotation"""
	available_promotions = []
	
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
		
		if promotion_doc.is_valid(quotation_doc.transaction_date):
			applicable_items = promotion_doc.get_applicable_items(quotation_doc.items)
			
			if applicable_items:
				if (promotion_doc.check_quantity_condition(applicable_items) or 
					promotion_doc.check_amount_condition(applicable_items)):
					available_promotions.append(promotion.name)
	
	return available_promotions

# Keep other existing whitelist methods unchanged
# ... [rest of the whitelist methods remain the same]