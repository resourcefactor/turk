{% include "turk/public/js/utils.js" %}


frappe.ui.form.on("Payment Entry", {
	onload: function (frm) {
		if (frm.doc.docstatus == 0) {
			$.each(frm.doc.references || [], function (i, d) {
				get_sales_order_owner(d.reference_doctype, d.reference_name, d);
			});
		}
		set_supplier_property(frm);
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
		set_supplier_property(frm);
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
	received_amount: function (frm) {
		if (frm.doc.payment_type == "Pay")
			frm.events.allocate_party_amount_against_ref_docs(frm, frm.doc.received_amount);
	},
	paid_amount: function (frm) {
		if (frm.doc.payment_type == "Receive")
			frm.events.allocate_party_amount_against_ref_docs(frm, frm.doc.paid_amount);
	},
	allocate_party_amount_against_ref_docs: async function (frm, paid_amount) {
		frappe.call({
			method: "turk.hook_events.payment_entry.allocate_amount_to_references",
			args: {
				doc: frm.doc,
				paid_amount: paid_amount,
				allocate_payment_amount: frappe.flags.allocate_payment_amount ?? false,
			},
			callback: function (r) {
				if (r.message) {
					frappe.msgprint(r.message);
				}
			},
		});
	},
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




function set_supplier_property(frm) {
	frappe.db.get_single_value("SI Home Settings", "enable_direct_transfer_to_supplier").then((value) => {
		if (value == 1) {
			frappe.db.get_doc("SI Home Settings", "SI Home Settings").then((settingsDoc) => {
				// Ensure the child table exists and has entries
				if (settingsDoc.supplier_payment && settingsDoc.supplier_payment.length > 0) {
					settingsDoc.supplier_payment.forEach((row) => {
						// Check if the mode_of_payment matches
						if (row.mode_of_payment == frm.doc.mode_of_payment && !frm.doc.supplier_payment_entry) {
							// Set supplier as required
							frm.set_df_property("supplier", "reqd", 1);
							frm.set_df_property("supplier", "hidden", 0);
						} else {
							frm.set_value("supplier", "");
							frm.set_df_property("supplier", "reqd", 0);
							frm.set_df_property("supplier", "hidden", 1);
						}
					});
				}
			});
		} else {
			frm.set_value("supplier", "");
			frm.set_df_property("supplier", "reqd", 0);
			frm.set_df_property("supplier", "hidden", 1);
		}
	});
}