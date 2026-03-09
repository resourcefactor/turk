# Copyright (c) 2026, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Date"),
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Customer Code"),
			"fieldname": "customer_code",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 120
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 140
		},
		{
			"label": _("PO #"),
			"fieldname": "po_number",
			"fieldtype": "Data",
			"width": 130
		},
		{
			"label": _("Shipment #"),
			"fieldname": "shipment_no",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Box Qty"),
			"fieldname": "box_qty",
			"fieldtype": "Float",
			"width": 90
		},
		{
			"label": _("Supplier Name"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 160
		},
		{
			"label": _("Purchase Invoice"),
			"fieldname": "purchase_invoice",
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 140
		},
		{
			"label": _("Remarks"),
			"fieldname": "remarks",
			"fieldtype": "Data",
			"width": 180
		}
	]


def get_data(filters):
	conditions = get_conditions(filters)

	data = frappe.db.sql("""
		SELECT
			si.posting_date AS date,
			si.customer AS customer_code,
			si.customer_name,
			si.name AS sales_invoice,
			si.po_number,
			si.shipment_no,
			si.cust_total_box AS box_qty,
			pi.supplier_name,
			pi.name AS purchase_invoice,
			si.remarks
		FROM
			`tabSales Invoice` si
		LEFT JOIN `tabPurchase Invoice` pi
			ON (
				(pi.shipment_no = si.shipment_no AND pi.shipment_no != '' AND pi.shipment_no IS NOT NULL)
				OR
				(pi.cust_shipment_no = si.shipment_no AND pi.cust_shipment_no != '' AND pi.cust_shipment_no IS NOT NULL)
			)
			AND pi.is_return = 1
			AND pi.docstatus = 1
		WHERE
			si.is_return = 1
			AND si.docstatus = 1
			{conditions}
		ORDER BY
			si.posting_date DESC, si.name DESC
	""".format(conditions=conditions), filters, as_dict=1)

	return data


def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " AND si.posting_date >= %(from_date)s"

	if filters.get("to_date"):
		conditions += " AND si.posting_date <= %(to_date)s"

	if filters.get("company"):
		conditions += " AND si.company = %(company)s"

	if filters.get("customer"):
		conditions += " AND si.customer = %(customer)s"

	if filters.get("shipment_no"):
		conditions += " AND si.shipment_no LIKE %(shipment_no)s"
		filters["shipment_no"] = "%" + filters["shipment_no"] + "%"

	return conditions
