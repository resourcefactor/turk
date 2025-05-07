// Copyright (c) 2025, RC and contributors
// For license information, please see license.txt

frappe.ui.form.on("SI Home Settings", {
	refresh(frm, cdt, cdn) {
		frm.set_query("account", "taxes_purchase_invoice", function (frm, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company,
					is_group: 0
				},
			};
		});

		frm.set_query("rebate_account", "rebate_and_discount_accounts", function (frm, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company,
					is_group: 0
				},
			};
		});

		frm.set_query("discount_account", "rebate_and_discount_accounts", function (frm, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company,
					is_group: 0
				},
			};
		});

		frm.set_query("debitor_account", "supplier_payment", function (frm, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: {
					company: d.company,
					is_group: 0
				},
			};
		});
	},
});
