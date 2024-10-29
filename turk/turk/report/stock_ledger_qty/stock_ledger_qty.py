# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    items = get_items(filters)
    sl_entries = get_stock_ledger_entries(filters, items)
    item_details = get_item_details(items, sl_entries)
    opening_row = get_opening_balance(filters, columns)

    data = []
    if opening_row:
        data.append(opening_row)
    if item_details:
        for sle in sl_entries:
            item_detail = item_details[sle.item_code]

            boxes = 0
            pieces = 0

            if sle.actual_qty:
                item_doc = frappe.get_doc("Item", sle.item_code)
                boxes, pieces = calculate_boxes_and_pieces(
                    sle.actual_qty, item_doc.boxes, item_doc.pieces
                )

            # boxes = 1
            # pieces = 1
            # if item_detail["boxes"] == boxes:
            #     boxes = sle.actual_qty
            # else:
            #     boxes = sle.actual_qty / item_detail["boxes"]

            # if item_detail["pieces"] == pieces:
            #     pieces = 0
            # else:
            #     pieces = (
            #         sle.actual_qty / (item_detail["boxes"] / item_detail["pieces"])
            #     ) % item_detail["pieces"]
            #     if sle.actual_qty < 0:
            #         pieces = pieces * -1

            data.append(
                [
                    sle.date,
                    sle.item_code,
                    item_detail.item_name,
                    item_detail.item_group,
                    item_detail.brand,
                    # item_detail.description,
                    sle.warehouse,
                    item_detail.stock_uom,
                    sle.actual_qty,
                    boxes,
                    pieces,
                    sle.qty_after_transaction,
                    # (sle.incoming_rate if sle.actual_qty > 0 else 0.0),
                    # sle.valuation_rate, sle.stock_value,
                    sle.voucher_type,
                    sle.voucher_no,
                    # sle.batch_no, sle.serial_no, sle.project,
                    sle.company,
                ]
            )

    return columns, data


def get_columns():
	columns = [
		_("Date") + ":Datetime:95",
		_("Item") + ":Link/Item:130",
		_("Item Name") + "::100",
		_("Item Group") + ":Link/Item Group:100",
		_("Brand") + ":Link/Brand:100",
	#	_("Description") + "::200",
		_("Warehouse") + ":Link/Warehouse:100",
		_("Stock UOM") + ":Link/UOM:100",
		_("Qty") + ":Float:50",
		_("Boxes") + ":Int:50",
		_("Pieces") + ":Int:50",
		_("Balance Qty SQM") + ":Float:100",
	#	{"label": _("Incoming Rate"), "fieldtype": "Currency", "width": 110,
	#		"options": "Company:company:default_currency"},
	#	{"label": _("Valuation Rate"), "fieldtype": "Currency", "width": 110,
	#		"options": "Company:company:default_currency"},
	#	{"label": _("Balance Value"), "fieldtype": "Currency", "width": 110,
	#		"options": "Company:company:default_currency"},
		_("Voucher Type") + "::110",
		_("Voucher #") + ":Dynamic Link/" + _("Voucher Type") + ":100",
	#	_("Batch") + ":Link/Batch:100",
	#	_("Serial #") + ":Link/Serial No:100",
	#	_("Project") + ":Link/Project:100",
		{"label": _("Company"), "fieldtype": "Link", "width": 110,
			"options": "company", "fieldname": "company"}
	]

	return columns


def get_stock_ledger_entries(filters, items):
	item_conditions_sql = ''
	if items:
		item_conditions_sql = 'and sle.item_code in ({})'\
			.format(', '.join([frappe.db.escape(i) for i in items]))

	return frappe.db.sql("""select concat_ws(" ", posting_date, posting_time) as date,
			item_code, warehouse, actual_qty, qty_after_transaction, incoming_rate, valuation_rate,
			stock_value, voucher_type, voucher_no, batch_no, serial_no, company, project
		from `tabStock Ledger Entry` sle
		where is_cancelled = 0 and company = %(company)s and
			posting_date between %(from_date)s and %(to_date)s
			{sle_conditions}
			{item_conditions_sql}
			order by posting_date asc, posting_time asc, name asc"""\
		.format(
			sle_conditions=get_sle_conditions(filters),
			item_conditions_sql = item_conditions_sql
		), filters, as_dict=1)


def get_items(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("item.name=%(item_code)s")
	else:
		if filters.get("brand"):
			conditions.append("item.brand=%(brand)s")
		if filters.get("item_group"):
			conditions.append(get_item_group_condition(filters.get("item_group")))

	items = []
	if conditions:
		items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
			.format(" and ".join(conditions)), filters)
	return items


def get_item_details(items, sl_entries):
	item_details = {}
	if not items:
		items = list(set([d.item_code for d in sl_entries]))
	if not items:
		return item_details

	for item in frappe.db.sql("""
		select name, item_name, description, item_group, brand, stock_uom ,boxes, pieces
		from `tabItem`
		where name in ({0})
		""".format(', '.join([frappe.db.escape(i,percent=False) for i in items])), as_dict=1):
			item_details.setdefault(item.name, item)

	return item_details


def get_sle_conditions(filters):
	conditions = []
	if filters.get("warehouse"):
		warehouse_condition = get_warehouse_condition(filters.get("warehouse"))
		if warehouse_condition:
			conditions.append(warehouse_condition)
	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")
	if filters.get("batch_no"):
		conditions.append("batch_no=%(batch_no)s")
	if filters.get("project"):
		conditions.append("project=%(project)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_opening_balance(filters, columns):
	if not (filters.item_code and filters.warehouse and filters.from_date):
		return

	from erpnext.stock.stock_ledger import get_previous_sle
	last_entry = get_previous_sle({
		"item_code": filters.item_code,
		"warehouse_condition": get_warehouse_condition(filters.warehouse),
		"posting_date": filters.from_date,
		"posting_time": "00:00:00"
	})
	row = [""]*len(columns)
	row[1] = _("'Opening'")
	for i, v in ((9, 'qty_after_transaction'), (11, 'valuation_rate'), (12, 'stock_value')):
			row[i] = last_entry.get(v, 0)

	return row


def get_warehouse_condition(warehouse):
	warehouse_details = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)
	if warehouse_details:
		return " exists (select name from `tabWarehouse` wh \
			where wh.lft >= %s and wh.rgt <= %s and warehouse = wh.name)"%(warehouse_details.lft,
			warehouse_details.rgt)

	return ''


def get_item_group_condition(item_group):
	item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
	if item_group_details:
		return "item.item_group in (select ig.name from `tabItem Group` ig \
			where ig.lft >= %s and ig.rgt <= %s and item.item_group = ig.name)"%(item_group_details.lft,
			item_group_details.rgt)

	return ''


def calculate_boxes_and_pieces(total_sqm, sqm_per_box, pieces_per_box):
    # Calculate total full boxes needed
    boxes = int(total_sqm // sqm_per_box)

    # Calculate remaining sqm after full boxes
    remaining_sqm = total_sqm % sqm_per_box

    # Calculate the number of loose pieces if there is any remaining sqm
    pieces = (
        round((remaining_sqm / sqm_per_box) * pieces_per_box)
        if remaining_sqm > 0
        else 0
    )

    # Check if the loose pieces fill an entire box
    if pieces == pieces_per_box:
        boxes += 1
        pieces = 0  # Reset loose pieces if they form a full box

    return boxes, pieces
