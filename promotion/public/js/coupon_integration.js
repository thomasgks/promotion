// Copyright (c) 2024, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("Quotation", {
  refresh: function (frm) {
    // Add promotion functionality for existing coupon code field
    if (frm.doc.docstatus === 0) {
      // Only for draft documents
      frm.add_custom_button(
        __("Apply Promotion"),
        function () {
          frm.trigger("apply_promotion_from_coupon");
        },
        __("Promotions")
      );
    }
  },

  // Listen to changes in the existing coupon_code field
  coupon_code: function (frm) {
    // Auto-apply promotion when coupon code is entered
    if (frm.doc.coupon_code && frm.doc.coupon_code.length > 0) {
      // Add a small delay to prevent multiple calls
      clearTimeout(frm.coupon_timeout);
      frm.coupon_timeout = setTimeout(function () {
        frm.trigger("apply_promotion_from_coupon");
      }, 1000); // 1 second delay
    }
  },

  apply_promotion_from_coupon: function (frm) {
    if (!frm.doc.coupon_code) {
      frappe.msgprint(__("Please enter a coupon code first"));
      return;
    }

    // Show loading
    frappe.show_alert({
      message: __("Applying promotion from coupon code..."),
      indicator: "blue",
    });

    // Apply promotion using the coupon code
    frappe.call({
      method:
        "promotion.promotion.doctype.promotion.promotion.apply_coupon_code",
      args: {
        coupon_code: frm.doc.coupon_code,
        quotation_name: frm.doc.name,
      },
      callback: function (r) {
        if (r.message) {
          if (r.message.success) {
            frappe.show_alert({
              message: __("Promotion applied successfully!"),
              indicator: "green",
            });

            // Show promotion details
            if (r.message.promotion) {
              frappe.msgprint(
                __("Promotion Applied: {0}", [r.message.promotion.title])
              );
            }

            // Reload the document to show updated amounts
            frm.reload_doc();
          } else {
            frappe.msgprint(__("Promotion error: {0}", [r.message.message]));
          }
        }
      },
    });
  },
});
