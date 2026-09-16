(function () {
	var report = frappe.query_reports["General Ledger"];
	if (!report || report.__turk_customer_group_patch) return;
	report.__turk_customer_group_patch = true;

	report.filters.push({
		fieldname: "customer_group",
		label: __("Customer Group"),
		fieldtype: "Data",
		hidden: 1,
	});

	var party_filter = report.filters.find(function (f) {
		return f.fieldname === "party";
	});

	if (party_filter) {
		var original_on_change = party_filter.on_change;
		party_filter.on_change = function () {
			if (original_on_change) original_on_change();

			var party_type = frappe.query_report.get_filter_value("party_type");
			var parties = frappe.query_report.get_filter_value("party");

			if (party_type !== "Customer" || !parties || parties.length !== 1) {
				frappe.query_report.set_filter_value("customer_group", "");
				return;
			}

			frappe.db.get_value("Customer", parties[0], "customer_group", function (value) {
				frappe.query_report.set_filter_value("customer_group", value.customer_group);
			});
		};
	}
})();
