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
	
	# Check if promotion is being applied
	#if hasattr(quotation_doc, 'apply_promotion') and quotation_doc.apply_promotion:
	if  quotation_doc.coupon_code:
		apply_quotation_promotions(quotation_doc, method)


def apply_quotation_promotions(quotation_doc, method):
	"""Apply promotions to quotation"""
	if quotation_doc.docstatus != 0:  # Only for draft documents
		return
	
	# Get available promotions
	available_promotions = get_available_promotions_for_quotation(quotation_doc)
	
	applied_promotions = []
	total_discount = 0
	
	for promotion_name in available_promotions:
		promotion_doc = frappe.get_doc("Promotion", promotion_name)
		
		if promotion_doc.apply_promotion(quotation_doc):
			applied_promotions.append(promotion_doc.title)
			quotation_doc.calculate_taxes_and_totals()
			quotation_doc.flags.ignore_validate = True
			quotation_doc.flags.ignore_on_update = True
			quotation_doc.save()
			
			# Calculate total discount
			for item in quotation_doc.items:
				if hasattr(item, 'promotion_discount') and item.promotion_discount:
					total_discount += flt(item.promotion_discount)
	
	# Store promotion information
	if applied_promotions:
		quotation_doc.promotion_applied = 1
		quotation_doc.promotion_discount = total_discount
		quotation_doc.applied_promotions = ", ".join(applied_promotions)
		
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
	if quotation_doc.docstatus != 1:  # Only for submitted documents
		return
	
	# Reset promotion fields
	quotation_doc.promotion_applied = 0
	quotation_doc.promotion_discount = 0
	quotation_doc.applied_promotions = ""
	
	# Remove promotion discounts from items
	for item in quotation_doc.items:
		if hasattr(item, 'promotion_discount'):
			item.promotion_discount = 0


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
