import frappe
from frappe.utils import flt


def apply_patches(*args, **kwargs):
	"""Patch erpnext stock ledger without modifying erpnext (called from before_job / before_request)."""
	from erpnext.stock.stock_ledger import update_entries_after

	if getattr(update_entries_after, "__turk_patched", False):
		return

	original_moving_average = update_entries_after.get_moving_average_values
	original_rate_from_transaction = update_entries_after.get_incoming_outgoing_rate_from_transaction

	def get_moving_average_values(self, sle):
		# Round running qty before moving-average maths. Float residue (e.g. 47.52 - 25.92 - 21.6 = 5e-13)
		# is treated as non-zero stock, so leftover value / residue qty gives a huge valuation rate that
		# overflows the valuation_rate column and fails Repost Item Valuation.
		self.wh_data.qty_after_transaction = flt(self.wh_data.qty_after_transaction, self.flt_precision)
		return original_moving_average(self, sle)

	def get_incoming_outgoing_rate_from_transaction(self, sle):
		# For moving average returns erpnext takes the rate from get_previous_sle(), which filters on
		# posting_datetime <= only. When several entries share a timestamp (returns and their auto-drafted
		# debit notes are all posted at 23:59:59) it picks an entry created *after* this one, often the
		# return's own debit note, so each repost feeds the bad rate back into itself.
		if (
			self.valuation_method == "Moving Average"
			and sle.voucher_type in ("Sales Invoice", "Delivery Note", "Purchase Invoice", "Purchase Receipt")
			and not sle.get("serial_no")
			and not sle.get("batch_no")
			and not sle.get("serial_and_batch_bundle")
			and frappe.get_cached_value(sle.voucher_type, sle.voucher_no, "is_return")
		):
			rate = None
			if sle.voucher_type in ("Sales Invoice", "Delivery Note") and flt(sle.actual_qty) > 0:
				# same rate erpnext uses on submit: cost of the original sale being returned
				rate = get_original_sale_rate(sle)
			if not rate:
				rate = get_previous_valuation_rate(sle)
			if rate:
				return rate

		return original_rate_from_transaction(self, sle)

	update_entries_after.get_moving_average_values = get_moving_average_values
	update_entries_after.get_incoming_outgoing_rate_from_transaction = get_incoming_outgoing_rate_from_transaction
	update_entries_after.__turk_patched = True


def get_original_sale_rate(sle):
	return_against = frappe.get_cached_value(sle.voucher_type, sle.voucher_no, "return_against")
	if not return_against:
		return None

	item_field = "dn_detail" if sle.voucher_type == "Delivery Note" else "sales_invoice_item"
	filters = {
		"voucher_type": sle.voucher_type,
		"voucher_no": return_against,
		"item_code": sle.item_code,
		"warehouse": sle.warehouse,
		"is_cancelled": 0,
	}
	if against_row := frappe.db.get_value(f"{sle.voucher_type} Item", sle.voucher_detail_no, item_field):
		filters["voucher_detail_no"] = against_row

	original = frappe.db.get_value(
		"Stock Ledger Entry", filters, ["sum(stock_value_difference)", "sum(actual_qty)"]
	)
	if original and flt(original[1]):
		return abs(flt(original[0]) / flt(original[1]))


def get_previous_valuation_rate(sle):
	"""Valuation rate of the entry immediately before this one in ledger order (posting_datetime, creation)."""
	if not sle.get("creation"):
		return None

	previous = frappe.db.sql(
		"""
		select valuation_rate from `tabStock Ledger Entry`
		where item_code = %(item_code)s and warehouse = %(warehouse)s and is_cancelled = 0 and name != %(name)s
			and (posting_datetime < %(posting_datetime)s
				or (posting_datetime = %(posting_datetime)s and creation < %(creation)s))
		order by posting_datetime desc, creation desc
		limit 1
		""",
		{
			"item_code": sle.item_code,
			"warehouse": sle.warehouse,
			"name": sle.name,
			"posting_datetime": sle.posting_datetime,
			"creation": sle.creation,
		},
	)
	return flt(previous[0][0]) if previous else None
