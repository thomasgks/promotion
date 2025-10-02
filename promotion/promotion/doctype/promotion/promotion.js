// Copyright (c) 2024, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on("Promotion", {
  refresh: function (frm) {
    // Add custom buttons
    if (!frm.doc.__islocal) {
      frm.add_custom_button(
        __("Test Promotion"),
        function () {
          frm.trigger("test_promotion");
        },
        __("Actions")
      );
    }
  },

  based_on: function (frm) {
    // Show/hide relevant fields based on selection
    if (frm.doc.based_on === "Brand") {
      frm.set_df_property("source_brands", "hidden", 0);
    } else {
      frm.set_df_property("source_brands", "hidden", 1);
    }
  },

  multiply_by_min_qty: function (frm) {
    // Update help text based on selection
    if (frm.doc.multiply_by_min_qty) {
      frm.set_df_property(
        "min_qty",
        "description",
        "Minimum quantity required. Reward will be multiplied based on how many times this quantity is exceeded."
      );
    } else {
      frm.set_df_property(
        "min_qty",
        "description",
        "Minimum quantity required for promotion to apply."
      );
    }
  },

  test_promotion: function (frm) {
    // Open test dialog
    let d = new frappe.ui.Dialog({
      title: __("Test Promotion"),
      fields: [
        {
          fieldtype: "Link",
          fieldname: "quotation",
          label: __("Quotation"),
          options: "Quotation",
          reqd: 1,
        },
      ],
      primary_action_label: __("Test"),
      primary_action: function (values) {
        frm
          .call("test_promotion_on_quotation", {
            quotation: values.quotation,
          })
          .then((r) => {
            if (r.message) {
              frappe.msgprint(
                __(
                  "Promotion test completed. Check the quotation for applied discounts."
                )
              );
            }
          });
        d.hide();
      },
    });
    d.show();
  },
});

frappe.ui.form.on("Promotion Action", {
  reward_type: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    // Show/hide relevant fields based on reward type
    if (row.reward_type === "Discount %") {
      frm.set_df_property("discount_percentage", "hidden", 0, cdn, "actions");
      frm.set_df_property("discount_amount", "hidden", 1, cdn, "actions");
    } else if (row.reward_type === "Discount Amount") {
      frm.set_df_property("discount_percentage", "hidden", 1, cdn, "actions");
      frm.set_df_property("discount_amount", "hidden", 0, cdn, "actions");
    } else {
      frm.set_df_property("discount_percentage", "hidden", 1, cdn, "actions");
      frm.set_df_property("discount_amount", "hidden", 1, cdn, "actions");
    }
  },

  discount_percentage: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    // Validate discount percentage
    if (row.discount_percentage > 100) {
      frappe.msgprint(__("Discount percentage cannot be greater than 100%"));
      frappe.model.set_value(cdt, cdn, "discount_percentage", 100);
    }
  },
});

frappe.ui.form.on("Promotion Source Brand", {
  brand: function (frm, cdt, cdn) {
    // Auto-enable when brand is selected
    frappe.model.set_value(cdt, cdn, "enabled", 1);
  },
});
