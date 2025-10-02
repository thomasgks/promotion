// Copyright (c) 2024, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("Quotation", {
  refresh: function (frm) {
    // Add promotion buttons
    if (frm.doc.docstatus === 0) {
      // Only for draft documents
      frm.add_custom_button(
        __("Apply Promotions"),
        function () {
          frm.trigger("show_promotion_dialog");
        },
        __("Promotions")
      );

      frm.add_custom_button(
        __("Remove Promotions"),
        function () {
          frm.trigger("remove_promotions");
        },
        __("Promotions")
      );

      frm.add_custom_button(
        __("Validate Coupon"),
        function () {
          frm.trigger("show_coupon_dialog");
        },
        __("Promotions")
      );

      if (frm.doc.docstatus === 0) {
      // Only for draft documents
      frm.add_custom_button(
        __("Apply Coupon"),
        function () {
          frm.trigger("apply_promotion_from_coupon");
        },
        __("Promotions")
      );
    }
    }

    // Show promotion summary if promotions are applied
    if (frm.doc.promotion_applied) {
      frm.dashboard.add_comment(
        __("Promotions Applied"),
        __("Applied Promotions: {0}<br>Total Discount: {1}", [
          frm.doc.applied_promotions || "N/A",
          frm.doc.promotion_discount
            ? format_currency(frm.doc.promotion_discount)
            : "0.00",
        ]),
        "blue"
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

  show_promotion_dialog: function (frm) {
    // Get available promotions
    frappe.call({
      method:
        "promotion.promotion.doctype.promotion.quotation_integration.get_quotation_promotion_summary",
      args: {
        quotation_name: frm.doc.name,
      },
      callback: function (r) {
        if (r.message) {
          console.log(r);
          frm.events.show_promotion_selection_dialog(
            frm,
            r.message.available_promotions
          );
          console.log("Trigger0");
        }
      },
    });
  },

  show_promotion_selection_dialog: function (frm, available_promotions) {
    console.log("Trigger1");
    let fields = [
      {
        fieldtype: "HTML",
        fieldname: "promotion_info",
        options:
          '<div class="alert alert-info">Select promotions to apply to this quotation.</div>',
      },
    ];
    console.log(available_promotions);
    // Add promotion selection fields
    available_promotions.forEach(function (promotion_name, index) {
      fields.push({
        fieldtype: "Check",
        fieldname: "promotion_" + index,
        label: promotion_name,
        default: 0,
      });
    });
    console.log(fields);
    let d = new frappe.ui.Dialog({
      title: __("Apply Promotions"),
      fields: fields,
      primary_action_label: __("Apply Selected"),
      primary_action: function (values) {
        let selected_promotions = [];
        available_promotions.forEach(function (promotion_name, index) {
          if (values["promotion_" + index]) {
            selected_promotions.push(promotion_name);
          }
        });

        if (selected_promotions.length > 0) {
          frm.events.apply_selected_promotions(frm, selected_promotions);
        } else {
          frappe.msgprint(__("Please select at least one promotion"));
        }
        d.hide();
      },
    });
    d.show();
  },

  apply_selected_promotions: function (frm, selected_promotions) {
    let applied_count = 0;
    let total_promotions = selected_promotions.length;
    console.log("total_promotions");
    console.log(total_promotions);
    selected_promotions.forEach(function (promotion_name) {
      frappe.call({
        method:
          "promotion.promotion.doctype.promotion.quotation_integration.apply_promotion_to_quotation",
        args: {
          quotation_name: frm.doc.name,
          promotion_name: promotion_name,
        },
        callback: function (r) {
          if (r.message) {
            applied_count++;
            console.log(r);
            console.log("applied_count");
            console.log(applied_count);
          }

          if (applied_count === total_promotions) {
            frm.reload_doc();
            frappe.msgprint(__("Promotions applied successfully"));
          }
        },
      });
    });
  },

  remove_promotions: function (frm) {
    frappe.confirm(
      __("Are you sure you want to remove all promotions from this quotation?"),
      function () {
        frappe.call({
          method:
            "promotion.promotion.doctype.promotion.quotation_integration.remove_promotion_from_quotation",
          args: {
            quotation_name: frm.doc.name,
            promotion_name: "all",
          },
          callback: function (r) {
            if (r.message) {
              frm.reload_doc();
              frappe.msgprint(__("Promotions removed successfully"));
            }
          },
        });
      }
    );
  },

  show_coupon_dialog: function (frm) {
    let d = new frappe.ui.Dialog({
      title: __("Validate Coupon Code"),
      fields: [
        {
          fieldtype: "Data",
          fieldname: "coupon_code",
          label: __("Coupon Code"),
          reqd: 1,
        },
      ],
      primary_action_label: __("Validate"),
      primary_action: function (values) {
        frappe.call({
          method:
            //"promotion.promotion.doctype.promotion.quotation_integration.validate_coupon_code",
            "promotion.promotion.doctype.promotion.promotion.apply_coupon_code",
          args: {
            coupon_code: values.coupon_code,
            quotation_name: frm.doc.name,
          },
          callback: function (r) {
            if (r.message) {
              if (r.message.valid) {
                frappe.msgprint(__("Coupon code is valid!"));
                if (r.message.promotion) {
                  frappe.msgprint(
                    __("Associated Promotion: {0}", [r.message.promotion.title])
                  );
                }
              } else {
                frappe.msgprint(
                  __("Coupon code validation failed: {0}", [r.message.message])
                );
              }
            }
          },
        });
        d.hide();
      },
    });
    d.show();
  },
});

// Add promotion fields to quotation
frappe.ui.form.on("Quotation", {
  onload: function (frm) {
    // Add custom fields for promotion tracking
    frm.add_custom_field("promotion_applied", "Check", "Promotions");
    frm.add_custom_field("promotion_discount", "Currency", "Promotions");
    frm.add_custom_field("applied_promotions", "Small Text", "Promotions");
    frm.add_custom_field("coupon_code", "Data", "Promotions");
  },
});

// Add promotion discount column to items table
frappe.ui.form.on("Quotation Item", {
  refresh: function (frm, cdt, cdn) {
    // Add promotion discount column if not exists
    if (!frm.fields_dict.items.grid.get_field("promotion_discount")) {
      frm.fields_dict.items.grid.add_column(
        "promotion_discount",
        "Currency",
        "Promotion Discount"
      );
    }
  },
});
