# Copyright (c) 2024, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PromotionSourceItemGroup(Document):
	def validate(self):
		# At least one field must be specified
		if not self.item_group and not self.brand and not self.custom_vendor_code and not self.season_attribute:
			frappe.throw(_("At least one field (Item Group, Brand, Vendor Code, or Season) must be specified"))
		
		# If item_group is specified, it cannot be null/empty
		if self.item_group and not self.item_group.strip():
			frappe.throw(_("Item Group cannot be empty if specified"))
		
		# If brand is specified, it cannot be null/empty
		if self.brand and not self.brand.strip():
			frappe.throw(_("Brand cannot be empty if specified"))
		
		# If vendor_code is specified, it cannot be null/empty
		if self.custom_vendor_code and not self.custom_vendor_code.strip():
			frappe.throw(_("Vendor Code cannot be empty if specified"))
		
		# If season is specified, it cannot be null/empty
		if self.season_attribute and not self.season_attribute.strip():
			frappe.throw(_("Season cannot be empty if specified"))
