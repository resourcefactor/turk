
import frappe


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(obj, target, source_parent):
        expense_account = frappe.db.get_value(
            "Company", source_parent.company, "default_expense_account"
        )
        item_expense_account = frappe.db.get_value(
            "Item Default",
            {"parent": target.item_code, "company": source_parent.company},
            "expense_account",
        )
        target.expense_account = item_expense_account or expense_account

    from frappe.model.mapper import get_mapped_doc

    return get_mapped_doc(
        "Purchase Invoice",
        source_name,
        {
            "Purchase Invoice": {
                "doctype": "Sales Invoice",
                "field_map": {
                    "due_date": "due_date"
                },
                "validation": {
                    "docstatus": ["=", 1]
                }
            },
            "Purchase Invoice Item": {
                "doctype": "Sales Invoice Item",
                "field_map": {
                    "item_code": "item_code",
                    "qty": "qty",
                    "rate": "rate"
                },
                "postprocess": update_item
            }
        },
        target_doc,
        set_missing_values
    )
