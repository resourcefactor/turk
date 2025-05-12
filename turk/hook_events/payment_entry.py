import frappe
from frappe import _



def validate_sales_order(pe, method):
	for reference in pe.references:
		if reference.reference_doctype in ["Sales Invoice", "Sales Order"]:
			if reference.reference_doctype == "Sales Invoice":
				so = frappe.db.get_value("Sales Invoice", reference.reference_name, "cust_sales_order_number")
			elif reference.reference_doctype == "Sales Order":
				so = reference.reference_name
			if reference.sales_order != so:
				reference.sales_order = so
    
    

def create_payment_entry_against_payment_entry(self, method):
    ts_settings = frappe.get_single("SI Home Settings")
    mode_of_payment = frappe.db.get_value(
        "Supplier Payment", {"company": self.company}, "mode_of_payment"
    )

    if self.payment_type == "Receive" and (
        mode_of_payment and mode_of_payment == self.mode_of_payment
    ):
        if ts_settings.enable_direct_transfer_to_supplier:
            # Get account from Mode of Payment
            paid_from_account = frappe.db.get_value(
                "Mode of Payment Account",
                {"parent": mode_of_payment, "company": self.company},
                "default_account",
            )

            if not paid_from_account:
                frappe.throw(
                    _(
                        "No default account set for Mode of Payment {0} in company {1}"
                    ).format(mode_of_payment, self.company)
                )

            account_currency = frappe.db.get_value(
                "Account", paid_from_account, "account_currency"
            )

            pe = frappe.new_doc("Payment Entry")
            pe.company = self.company
            pe.posting_date = self.posting_date
            pe.mode_of_payment = mode_of_payment
            pe.payment_type = "Pay"
            pe.party_type = "Supplier"
            pe.party_type_ts = "Supplier"
            pe.party = self.supplier
            pe.reference_no = self.reference_no
            pe.reference_date = self.reference_date
            pe.remarks = self.remarks
            pe.manual_sheet_no = self.manual_sheet_no
            pe.supplier_payment_entry = self.name
            pe.paid_amount = self.paid_amount
            pe.received_amount = self.received_amount
            pe.source_exchange_rate = self.source_exchange_rate

            pe.paid_from = paid_from_account
            pe.paid_from_account_currency = account_currency

            pe.insert(ignore_permissions=True)
            pe.set_missing_values()
            pe.save(ignore_permissions=True)
            pe.submit()
