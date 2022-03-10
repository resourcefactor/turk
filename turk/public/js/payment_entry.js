{% include "turk/public/js/utils.js" %}


frappe.ui.form.on("Payment Entry", {
	onload: function (frm) {
		if (frm.doc.docstatus == 0) {
			$.each(frm.doc.references || [], function (i, d) {
				get_sales_order_owner(d.reference_doctype, d.reference_name, d);
			});
		}
	},
	validate: function (frm) {
		if (frm.doc.docstatus == 0) {
			if (frm.doc.unallocated_amount > 0 && (frm.doc.party == "LOADER BIKE" || frm.doc.party == "GL PAYMENT")) {
				msgprint("Excess Payment Not Allowed. Unallocated should be 0");
				frappe.validated = false;
				return;
			}
		}
	},
	company: function (frm) {
		link_si_to_so(frm);
	},
	references_on_form_rendered: function (frm) {
		link_si_to_so(frm);
	},
	mode_of_payment: function (frm) {
		frm.events.set_total_allocated_amount(frm);
		for (var row of frm.doc.references) {
			if (row.reference_doctype == "Sales Invoice" || row.reference_doctype == "Sales Order") {
				if (row.reference_doctype == "Sales Invoice") {
					var doctype = "Sales Invoice";
					var fieldname = "cust_sales_order_number"
				}
				else if (row.reference_doctype == "Sales Order") {
					var doctype = "Sales Order";
					var fieldname = "name";
				}
				get_sales_order(row, doctype, fieldname);
			}
		}
	},
	party: function (frm) {
		if (frm.doc.party) {
			frappe.call({
				method: "turk.hook_events.payment_entry.get_party_primary_role",
				args: {
					party_type: frm.doc.party_type,
					party: frm.doc.party
				},
				callback: function (r) {
					frm.doc.primary_role = r.message
					frm.refresh_field('primary_role')
					if (frm.doc.party_type != frm.doc.primary_role && frm.doc.primary_role) {
						frappe.msgprint('Party Type and Primary Role does not match, please double check your transaction!')
					}
				}
			})
		}
	}
});

frappe.ui.form.on('Payment Entry Reference', {
	reference_name: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.reference_doctype == "Sales Invoice" && row.reference_name) {
			frappe.db.get_value("Sales Invoice", row.reference_name, "cust_sales_order_number", (r) => {
				if (r.cust_sales_order_number) {
					frappe.model.set_value(cdt, cdn, "sales_order", r.cust_sales_order_number);
				}
			});
		}
		else if (row.reference_doctype == "Sales Order" && row.reference_name) {
			frappe.model.set_value(cdt, cdn, "sales_order", row.reference_name);
		}
	}
});

function get_sales_order(row, doctype, fieldname) {
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: doctype,
			fieldname: fieldname,
			filters: { "name": row.reference_name }
		},
		callback: function (r) {
			if (r.message) {
				frappe.model.set_value(row.doctype, row.name, "sales_order", r.message.cust_sales_order_number || r.message.name);
			}
		}
	});
}

function link_si_to_so(frm) {
	for (var reference of frm.get_field("references").grid.grid_rows) {
		if (reference.get_field("reference_doctype").value == "Sales Invoice") {
			var fieldname = "cust_sales_order_number";
			frappe.db.get_value("Sales Invoice", reference.get_field("reference_name").value, fieldname, function (value) {
				reference.get_field("sales_order").set_model_value(value[fieldname]);
			});
		}
		else if (reference.get_field("reference_doctype").value == "Sales Order") {
			var sales_order = reference.get_field("reference_name").value
			reference.get_field("sales_order").set_model_value(sales_order);
		}
	}
}

function get_sales_order_owner(doctype, docnumber, row) {
	var fieldfetch = "";
	if (doctype == "Sales Order") {
		fieldfetch = "owner";
	}
	if (doctype == "Sales Invoice") {
		fieldfetch = "cust_sales_order_owner";
	}
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: doctype,
			filters: { "name": docnumber },
			fieldname: fieldfetch
		},
		callback: function (r) {
			if (doctype == "Sales Order") {
				row.cust_sales_order_owner = r.message.owner;
			}
			if (doctype == "Sales Invoice") {
				row.cust_sales_order_owner = r.message.cust_sales_order_owner;
			}
		}
	});
}