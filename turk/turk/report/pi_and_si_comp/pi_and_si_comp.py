# Copyright (c) 2023, RC and contributors
# For license information, please see license.txt


import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	columns = [
		{
			"fieldname": "pi_date",
			"fieldtype": "Date",
			"label": "Date of PI",
			"width": 100
		},
		{
			"fieldname": "pi_no",
			"fieldtype": "Link",
			"label": "PI Number",
			"options": "Purchase Invoice",
			"width": 100
		},
		{
			"fieldname": "item_code",
			"fieldtype": "Link",
			"label": "Item Code",
			"options": "Item",
			"width": 150
		},
		{
			"fieldname": "item_name",
			"fieldtype": "Data",
			"label": "Item Name",
			"width": 200
		},
		{
			"fieldname": "pi_qty",
			"fieldtype": "Float",
			"label": "PI Qty",
			"width": 100
		},
		{
			"fieldname": "si_no",
			"fieldtype": "Data",
			"label": "SI Number",
			"width": 100
		},
		{
			"fieldname": "si_date",
			"fieldtype": "Date of SI",
			"label": "Data",
			"width": 100
		},
		{
			"fieldname": "si_qty",
			"fieldtype": "Float",
			"label": "SI Qty",
			"width": 100
		}
	]
	return columns


def get_data(filters):
	data = []
	result = frappe.db.sql("""select
		pi.posting_date as pi_date, pi.name as pi_no, pii.item_code, pii.item_name, pii.qty as pi_qty
		from `tabPurchase Invoice` as pi
		left join `tabPurchase Invoice Item` as pii on pi.name = pii.parent
		where pi.docstatus = 1 and pi.posting_date >= '{0}' and pi.posting_date <= '{1}'
	""".format(filters.get('from_date'), filters.get('to_date')), as_dict=True)

	for row in result:
		si_result = frappe.db.sql("""select
			si.name as si_no, si.posting_date as si_date, sum(sii.qty) as si_qty
			from `tabSales Invoice Item` as sii
			left join `tabSales Invoice` as si on si.name = sii.parent
			where si.docstatus = 1 and sii.purchase_invoice = '{0}' and sii.item_code = '{1}'
			group by si.name""".format(row.pi_no, row.item_code), as_dict=True)

		si_names = si_dates = ""
		si_qty = 0
		for si_row in si_result:
			si_names += si_row.si_no + ", "
			si_dates += str(si_row.si_date) + ", "
			si_qty += si_row.si_qty

		row = {
			"pi_date": row.pi_date,
			"pi_no": row.pi_no,
			"item_code": row.item_code,
			"item_name": row.item_name,
			"pi_qty": row.pi_qty,
			"si_no": si_names,
			"si_date": si_dates,
			"si_qty": si_qty,
		}
		data.append(row)
	return data
