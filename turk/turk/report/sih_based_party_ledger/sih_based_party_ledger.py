# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	columns = [
		{
			"fieldname": "date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 150
		},
		{
			"label": "Voucher Type",
			"fieldtype": "Data",
			"fieldname": "voucher_type",
			"width": 150
		},
		{
			"label": "Voucher No.",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"fieldname": "voucher_no",
			"width": 150
		},
		{
			"label": "Shipment No.",
			"fieldtype": "Data",
			"fieldname": "shipment_no",
			"width": 150
		},
		{
			"label": "PO No.",
			"fieldtype": "Data",
			"fieldname": "po_no",
			"width": 150
		},
		{
			"label": "FAX No.",
			"fieldtype": "Data",
			"fieldname": "fax_no",
			"width": 150
		},
		{
			"fieldname": "item_code",
			"fieldtype": "Data",
			"label": "Item Code",
			"width": 150
		},
		{
			"label": "Size",
			"fieldtype": "Data",
			"fieldname": "size",
			"width": 150
		},
		{
			"fieldname": "qty",
			"fieldtype": "Float",
			"label": "Quantity",
			"width": 150
		},
		{
			"fieldname": "boxes",
			"fieldtype": "Float",
			"label": "Boxes",
			"width": 150
		},
		{
			"fieldname": "rate",
			"fieldtype": "Currency",
			"label": "Rate",
			"width": 150
		},
		{
			"fieldname": "debit",
			"fieldtype": "Currency",
			"label": "Debit",
			"width": 150
		},
		{
			"fieldname": "credit",
			"fieldtype": "Currency",
			"label": "Credit",
			"width": 150
		},
		{
			"fieldname": "balance",
			"fieldtype": "Currency",
			"label": "Balance",
			"width": 150
		},
		{
			"label": "Remarks",
			"fieldtype": "Data",
			"fieldname": "remarks",
			"width": 150
		}
	]
	return columns


def get_data(filters):
	if filters.get('party_type') == "Customer":
		query = """select
			so.posting_date as date,
			"Sales Invoice" as voucher_type,
			so.name as voucher_no,
			so.shipment_no,
			so.po_number,
			so.discount_amount,
			soi.fax_no,
			soi.item_code,
			soi.item_name,
			soi.qty,
			soi.boxes,
			soi.rate,
			soi.amount as debit,
			0 as credit,
			so.remarks
			from `tabSales Invoice` as so
			left join `tabSales Invoice Item` as soi on so.name = soi.parent
			where so.docstatus = 1 and so.customer = '{0}' and so.posting_date >= '{1}' and so.posting_date <= '{2}'
		union all
		select
			pe.posting_date as date,
			"Payment Entry" as voucher_type,
			pe.name as voucher_no,
			'',
			'',
			0,
			'',
			'',
			'',
			0,
			0,
			0,
			0 as debit,
			pe.paid_amount as credit,
			pe.remarks
			from `tabPayment Entry` as pe
			where pe.docstatus = 1 and pe.party_type = 'Customer' and pe.party = '{0}' and pe.posting_date >= '{1}' and pe.posting_date <= '{2}'
		union all
		select
			je.posting_date as date,
			je.voucher_type,
			je.name as voucher_no,
			'',
			'',
			0,
			'',
			'',
			'',
			0,
			0,
			0,
			jea.debit,
			jea.credit,
			je.remark as remarks
			from `tabJournal Entry` as je
			left join `tabJournal Entry Account` as jea on je.name = jea.parent
			where je.docstatus = 1 and jea.party_type = 'Customer' and jea.party = '{0}' and je.posting_date >= '{1}' and je.posting_date <= '{2}'
			order by date
		""".format(filters.get('party'), filters.get('from_date'), filters.get('to_date'))

	elif filters.get('party_type') == "Supplier":
		query = """select
			po.posting_date as date,
			"Purchase Invoice" as voucher_type,
			po.name as voucher_no,
			po.shipment_no,
			po.po_number,
			poi.fax_no,
			poi.item_code,
			poi.item_name,
			poi.qty,
			poi.boxes,
			poi.rate,
			0 as debit,
			poi.amount as credit,
			po.remarks,
			po.discount_amount
			from `tabPurchase Invoice` as po
			left join `tabPurchase Invoice Item` as poi on po.name = poi.parent
			where po.docstatus = 1 and po.supplier = '{0}' and po.posting_date >= '{1}' and po.posting_date <= '{2}' 
		union all
		select
			pe.posting_date as date,
			"Payment Entry" as voucher_type,
			pe.name as voucher_no,
			'',
			'',
			'',
			'',
			'',
			0,
			0,
			0,
			pe.paid_amount as debit,
			0 as credit,
			pe.remarks,
			0
			from `tabPayment Entry` as pe
			where pe.docstatus = 1 and pe.party_type = 'Supplier' and pe.party = '{0}' and pe.posting_date >= '{1}' and pe.posting_date <= '{2}'
		union all
		select
			je.posting_date as date,
			je.voucher_type,
			je.name as voucher_no,
			'',
			'',
			'',
			'',
			'',
			0,
			0,
			0,
			jea.debit,
			jea.credit,
			je.remark as remarks,
			0
			from `tabJournal Entry` as je
			left join `tabJournal Entry Account` as jea on je.name = jea.parent
			where je.docstatus = 1 and jea.party_type = 'Supplier' and jea.party = '{0}' and je.posting_date >= '{1}' and je.posting_date <= '{2}'
			order by date
		""".format(filters.get('party'), filters.get('from_date'), filters.get('to_date'))
	result = frappe.db.sql(query, as_dict=True)
	data = []

	item_details = {}

	for res in result:
		item_details.setdefault((res.voucher_type, res.voucher_no), []).append(res)

	m_total_qty = m_total_boxes = m_total_debit = m_total_credit = c_balance = 0

	data = []
	for key in item_details.keys():
		voucher_type = key[0]
		voucher_no = key[1]

		s_total_qty = s_total_boxes = s_total_debit = s_total_credit = 0

		for d in item_details[key]:
			s_total_qty += d.qty
			s_total_boxes += d.boxes
			s_total_debit += d.debit
			s_total_credit += d.credit
			c_balance += (d.debit - d.credit)

			m_total_qty += d.qty
			m_total_boxes += d.boxes
			m_total_debit += d.debit
			m_total_credit += c_balance

			data.append({
				"date": d.date,
				"voucher_type": d.voucher_type,
				"voucher_no": d.voucher_no,
				"shipment_no": d.shipment_no,
				"po_no": d.po_number,
				"fax_no": d.fax_no,
				"item_code": d.item_code,
				"size": frappe.db.get_value("Item", d.item_code, "size"),
				"qty": d.qty,
				"boxes": d.boxes,
				"rate": d.rate,
				"debit": d.debit,
				"credit": d.credit,
				"balance": c_balance,
				"remarks": d.remarks
			})
		if voucher_type in ["Purchase Invoice", "Sales Invoice"]:
			v_doc = frappe.get_doc(voucher_type, voucher_no)
			if v_doc.discount_amount > 0:
				c_balance -= v_doc.discount_amount
				data.append({
					"date": "",
					"voucher_type": "",
					"voucher_no": "",
					"shipment_no": "",
					"po_no": "",
					"fax_no": "",
					"item_code": "<b>Discounted Amount</b>",
					"size": "",
					"qty": 0,
					"boxes": 0,
					"rate": 0,
					"debit": 0,
					"credit": v_doc.discount_amount,
					"balance": c_balance,
					"remarks": ""
				})
		data.append({
			"date": "",
			"voucher_type": "",
			"voucher_no": "",
			"shipment_no": "",
			"po_no": "",
			"fax_no": "",
			"item_code": "<b>Sub Total</b>",
			"size": "",
			"qty": s_total_qty,
			"boxes": s_total_boxes,
			"rate": "",
			"debit": s_total_debit,
			"credit": s_total_credit,
			"balance": "",
			"remarks": ""
		})
	if data:
		data.append({
			"date": "",
			"voucher_type": "",
			"voucher_no": "",
			"shipment_no": "",
			"po_no": "",
			"fax_no": "",
			"item_code": "<b>Grand Total</b>",
			"size": "",
			"qty": m_total_qty,
			"boxes": m_total_boxes,
			"rate": "",
			"debit": m_total_debit,
			"credit": m_total_credit,
			"balance": "",
			"remarks": ""
		})

	return data
