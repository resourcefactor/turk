// Copyright (c) 2023, RC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["PI and SI Comp"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": get_today(),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": get_today(),
			"reqd": 1
		}
	]
};
