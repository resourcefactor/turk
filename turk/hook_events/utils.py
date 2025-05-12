from __future__ import unicode_literals


import erpnext
import frappe
import json
from collections import defaultdict
from frappe.query_builder.custom import ConstantColumn



def create_landed_cost_voucher(self, method):
	three_s_settings = frappe.get_single("SI Home Settings")
	if three_s_settings.enable_rebate_and_discount:
		rebate_and_discount_accounts = frappe.db.get_value(
			"Rebate and Discount Accounts",
			{"company": self.company},
			["rebate_account", "discount_account"],
			as_dict=1,
		)
		accounts_info = []
		if self.total_discounted_amount and self.total_discounted_amount > 0:
			accounts_info.append(
				{
					"account": rebate_and_discount_accounts.discount_account,
					"amount": self.total_discounted_amount,
					"description": "Discounted Amount",
				}
			)
		if self.total_rebate_amount:
			accounts_info.append(
				{
					"account": rebate_and_discount_accounts.rebate_account,
					"amount": self.total_rebate_amount,
					"description": "Rebate Amount",
				}
			)

		for account_det in accounts_info:
			if self.doctype == "Purchase Invoice":
				if not self.update_stock:
					return

			lcv = make_lcv(self, account_det)
			lcv.insert()
			lcv.submit()


def make_lcv(self, account_det):
	landed_cost_voucher = frappe.new_doc("Landed Cost Voucher")
	landed_cost_voucher.company = self.company
	landed_cost_voucher.distribute_charges_based_on = "Distribute Manually"

	landed_cost_voucher.append(
		"purchase_receipts",
		{
			"receipt_document_type": self.doctype,
			"receipt_document": self.name,
			"grand_total": self.base_grand_total,
			"supplier": self.supplier,
		},
	)

	get_items_from_purchase_receipts(landed_cost_voucher, account_det)
	get_taxes_and_charges(self, landed_cost_voucher, account_det)

	return landed_cost_voucher


def get_items_from_purchase_receipts(landed_cost_voucher, account_det):
	landed_cost_voucher.set("items", [])
	for pr in landed_cost_voucher.get("purchase_receipts"):
		if pr.receipt_document_type and pr.receipt_document:
			pr_items = get_pr_items(pr, account_det)

			for d in pr_items:
				item = landed_cost_voucher.append("items")
				item.item_code = d.item_code
				item.description = d.description
				item.qty = d.qty
				item.rate = d.base_rate
				item.cost_center = d.cost_center or erpnext.get_default_cost_center(
					landed_cost_voucher.company
				)
				item.amount = d.base_amount
				item.applicable_charges = d.applicable_charges * -1
				item.receipt_document_type = pr.receipt_document_type
				item.receipt_document = pr.receipt_document
				item.purchase_receipt_item = d.name
				item.is_fixed_asset = d.is_fixed_asset




def get_pr_items(purchase_receipt, account_det):
	item = frappe.qb.DocType("Item")
	pr_item = frappe.qb.DocType(purchase_receipt.receipt_document_type + " Item")

	return (
		frappe.qb.from_(pr_item)
		.inner_join(item)
		.on(item.name == pr_item.item_code)
		.select(
			pr_item.item_code,
			pr_item.description,
			pr_item.qty,
			pr_item.base_rate,
			pr_item.base_amount,
			pr_item.name,
			pr_item.cost_center,
			pr_item.discounted_amount.as_("applicable_charges") if account_det.get("description") == "Discounted Amount" else pr_item.rebate_amount.as_("applicable_charges"),
			pr_item.is_fixed_asset,
			ConstantColumn(purchase_receipt.receipt_document_type).as_(
				"receipt_document_type"
			),
			ConstantColumn(purchase_receipt.receipt_document).as_("receipt_document"),
		)
		.where(
			(pr_item.parent == purchase_receipt.receipt_document)
			& ((item.is_stock_item == 1) | (item.is_fixed_asset == 1))
		)
		.run(as_dict=True)
	)


def get_taxes_and_charges(self, landed_cost_voucher, account_det):
	landed_cost_voucher.set("taxes", [])
	landed_cost_voucher.append(
		"taxes",
		{
			"expense_account": account_det.get("account"),
			"amount": account_det.get("amount") * -1,
			"description": account_det.get("description"),
		},
	)
