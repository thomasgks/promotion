import frappe

def test():
    print("OKOKOKO")
    
def copy_promotion_fields_from_quotation(doc, method):
    """Copy promotion fields from linked Quotation Items into Sales Order Items."""
    for item in doc.items:
        if not item.get("quotation_item"):
            continue

        # quotation_item is a Data field, so we must fetch manually
        quotation_item = frappe.db.get_value(
            "Quotation Item",
            item.quotation_item,
            ["promotion_applied", "promotion_discount", "applied_promotions"],
            as_dict=True
        )

        if quotation_item:
            item.promotion_applied = quotation_item.get("promotion_applied")
            item.promotion_discount = quotation_item.get("promotion_discount")
            item.applied_promotions = quotation_item.get("applied_promotions")
