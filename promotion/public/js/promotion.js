// Copyright (c) 2024, Your Company and contributors
// For license information, please see license.txt

// Promotion utility functions
frappe.promotion = {
  apply_promotion: function (quotation_name, promotion_name) {
    return frappe.call({
      method:
        "promotion.promotion.doctype.promotion.quotation_integration.apply_promotion_to_quotation",
      args: {
        quotation_name: quotation_name,
        promotion_name: promotion_name,
      },
    });
  },

  remove_promotion: function (quotation_name, promotion_name) {
    return frappe.call({
      method:
        "promotion.promotion.doctype.promotion.quotation_integration.remove_promotion_from_quotation",
      args: {
        quotation_name: quotation_name,
        promotion_name: promotion_name,
      },
    });
  },

  validate_coupon: function (coupon_code, quotation_name) {
    return frappe.call({
      method:
        "promotion.promotion.doctype.promotion.quotation_integration.validate_coupon_code",
      args: {
        coupon_code: coupon_code,
        quotation_name: quotation_name,
      },
    });
  },

  get_promotion_summary: function (quotation_name) {
    return frappe.call({
      method:
        "promotion.promotion.doctype.promotion.quotation_integration.get_quotation_promotion_summary",
      args: {
        quotation_name: quotation_name,
      },
    });
  },
};
