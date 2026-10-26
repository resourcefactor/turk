// Copyright (c) 2025, RC and contributors
// For license information, please see license.txt

(function () {
	if (frappe.ui.__customer_ledger_summary_sih_include_filters_patch) return;
	frappe.ui.__customer_ledger_summary_sih_include_filters_patch = true;

	var original_get_print_settings = frappe.ui.get_print_settings;
	frappe.ui.get_print_settings = function () {
		var dialog = original_get_print_settings.apply(this, arguments);

		if (
			dialog &&
			dialog.fields_dict &&
			dialog.fields_dict.include_filters &&
			frappe.query_report &&
			frappe.query_report.report_name === "Customer Ledger Summary SIH"
		) {
			dialog.set_value("include_filters", 1);
		}

		return dialog;
	};
})();

frappe.query_reports["Customer Ledger Summary SIH"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
			width: "60px",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			width: "60px",
		},
		{
			fieldname: "finance_book",
			label: __("Finance Book"),
			fieldtype: "Link",
			options: "Finance Book",
		},
		{
			fieldname: "party",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
			on_change: () => {
				var party = frappe.query_report.get_filter_value("party");
				if (party) {
					frappe.db.get_value("Customer", party, ["tax_id", "customer_name"], function (value) {
						frappe.query_report.set_filter_value("tax_id", value["tax_id"]);
						frappe.query_report.set_filter_value("customer_name", value["customer_name"]);
					});
				} else {
					frappe.query_report.set_filter_value("tax_id", "");
					frappe.query_report.set_filter_value("customer_name", "");
				}
			},
		},
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				// typeahead results for Customer Group
				return frappe.db.get_link_options("Customer Group", txt);
			},
		},
		{
			fieldname: "payment_terms_template",
			label: __("Payment Terms Template"),
			fieldtype: "Link",
			options: "Payment Terms Template",
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},
		{
			fieldname: "sales_partner",
			label: __("Sales Partner"),
			fieldtype: "Link",
			options: "Sales Partner",
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
		},
		{
			fieldname: "tax_id",
			label: __("Tax Id"),
			fieldtype: "Data",
			hidden: 1,
		},
		{
			fieldname: "customer_name",
			label: __("Customer Name"),
			fieldtype: "Data",
			hidden: 1,
		},
	],
};
