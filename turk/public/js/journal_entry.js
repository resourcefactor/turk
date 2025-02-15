frappe.ui.form.on("Journal Entry Account", {
	party_type: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (!row.party_type) {
			frappe.model.set_value(cdt, cdn, "party", "");
		}
	},
	party: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.party) {
			var fieldname = erpnext.utils.get_party_name(row.party_type);
			frappe.db.get_value(row.party_type, row.party, fieldname, function (value) {
				frappe.model.set_value(cdt, cdn, "party_name", value[fieldname]);
			});
		} else {
			frappe.model.set_value(cdt, cdn, "party", "");
			frappe.model.set_value(cdt, cdn, "party_name", "");
		}
	},
});
