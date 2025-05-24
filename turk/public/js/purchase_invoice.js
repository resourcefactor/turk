{% include "turk/public/js/utils.js" %}

frappe.ui.form.on('Purchase Invoice', {
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 1) {
            frm.add_custom_button(
                __("Sales Invoice"),
                () => {
                    frappe.model.open_mapped_doc({
                        method: "turk.hook_events.purchase_invoice.make_sales_invoice",
                        frm: frm,
                    });
                },
                __("Create")
            );
        }
    }
});


frappe.ui.form.on("Purchase Invoice", "onload", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		$.each(frm.doc.items || [], function (i, d) {
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
		})
	}
	if(frm.is_new()){
		frm.doc.items.forEach((d) => {
			if(d.item_group && !d.rebate_rate) {
				frappe.db.get_value("Item Group", d.item_group, "rebate_rate", (r) => {
					d.rebate_rate = r.rebate_rate;
					frappe.model.set_value(cdt, cdn, "rebate_rate", r.rebate_rate);
					calculate_rabate_and_discount_amount(frm);
				});
			} else if(!d.item_group) {
				frappe.model.set_value(cdt, cdn, "rebate_rate", 0);
			}
		});
		frm.refresh_field("items");
	}
});

frappe.ui.form.on("Purchase Invoice", "validate", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		validateBoxes(frm);
		// var ret_obj = setseries(frm.doc.company); cur_frm.set_value("naming_series", ret_obj.series);
		calculate_total_boxes(frm);
	}
	frm.doc.items.forEach((d) => {
		if(d.item_group && !d.rebate_rate) {
			frappe.db.get_value("Item Group", d.item_group, "rebate_rate", (r) => {
				frappe.model.set_value(cdt, cdn, "rebate_rate", r.rebate_rate);
			});
		} else if(!d.item_group) {
			frappe.model.set_value(cdt, cdn, "rebate_rate", 0);
		}
	});
	validate_rabate_and_discount_amount(frm);
});

// frappe.ui.form.on('Purchase Invoice', {
// 	company: function (frm) {
// 		var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
// 	}
// });

frappe.ui.form.on('Purchase Invoice Item',
	{
		pieces: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn); },
		sqm: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); },
		boxes: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); },
		qty: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_name: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_code: function (frm, cdt, cdn) {
			var d = locals[cdt][cdn];
			frappe.model.set_value(cdt, cdn, "qty", 1);
			frappe.model.set_value(cdt, cdn, "discount_percentage", 0);
			frappe.model.set_value(cdt, cdn, "discount_amount", 0);
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
			if(d.item_group) {
			frappe.db.get_value("Item Group", d.item_group, "rebate_rate", (r) => {
				d.rebate_rate = r.rebate_rate;
			});
			}
			frm.refresh_field("items");
		},
		rebate_rate: function (frm) {
			calculate_rabate_and_discount_amount(frm);
		},
		discounted_rate: function (frm) {
			calculate_rabate_and_discount_amount(frm);
		},
	})

function CalculateSQM(crow, field, cdt, cdn) {
	if (typeof crow.def_boxes != 'undefined' && crow.def_boxes && crow.def_boxes > 0) {
		var total_piece = 0.0;
		switch (field) {
			case "pieces": total_piece = Math.round(crow.pieces + (crow.boxes * crow.def_pieces)); break;
			case "boxes": total_piece = Math.round(crow.boxes * crow.def_pieces); break;
			case "sqm": total_piece = Math.round(crow.sqm / (crow.def_boxes / crow.def_pieces)); break;
			case "qty": total_piece = Math.round(crow.qty / (crow.def_boxes / crow.def_pieces));
		}
		var new_sqm = parseFloat((total_piece * (crow.def_boxes / crow.def_pieces)).toFixed(4));
		if (new_sqm > 0) {
			crow.boxes = Math.floor((new_sqm / crow.def_boxes).toFixed(4));
		} else { crow.boxes = Math.ceil((new_sqm / crow.def_boxes).toFixed(4)); }
		crow.pieces = (total_piece % crow.def_pieces);
		frappe.model.set_value(cdt, cdn, 'qty', new_sqm);
		crow.sqm = new_sqm;
		cur_frm.refresh_field("items");
	}
	else {
		var new_sqm = 0;
		switch (field) {
			case "pieces": new_sqm = crow.pieces; break;
			case "boxes": new_sqm = crow.boxes; break;
			case "sqm": new_sqm = crow.sqm; break;
			case "qty": new_sqm = crow.qty; break;
		}
		crow.sqm = new_sqm; crow.boxes = new_sqm; crow.pieces = new_sqm; crow.qty = new_sqm;
		cur_frm.refresh_field("items");
	}
	
}


function calculate_rabate_and_discount_amount(frm) {
	frm.doc.total_rebate_amount = 0;
	frm.doc.total_discounted_amount = 0;
	frm.doc.items.forEach((d) => {
		if (d.rebate_rate >= 0) {
			d.rebate_amount = 0;
			d.rebate_amount = d.qty * d.rebate_rate;
			frm.doc.total_rebate_amount += d.rebate_amount; 
		}
		if (d.discounted_rate >= 0) {
			d.discounted_amount = 0;
			d.discounted_amount = d.qty * d.discounted_rate;
			frm.doc.total_discounted_amount += d.discounted_amount;
		}
	});
	frm.refresh_field("items");
}

function validate_rabate_and_discount_amount(frm) {
	if (!frm.doc.is_return) {
		frm.doc.items.forEach((d) => {
			if (d.rate && d.rate < d.rebate_rate) {
				frappe.throw(
					__("Row {0}: Rebate Rate {1} must be less than Rate {2}", [
						d.idx,
						d.rebate_rate,
						d.rate,
					])
				);
			} else if(d.rate < d.discounted_rate) {
				frappe.throw(
					__("Row {0}: Discounted Rate {1} must be less than Rate {2}", [
						d.idx,
						d.discounted_rate,
						d.rate,
					])
				);
			} else if (d.amount < (d.rebate_amount + d.discounted_amount)) {
				frappe.throw(
					__("Row {0}: Rebate and Discounted Amount {1} must be less than Item Amount {2}", [
						d.idx,
						(d.rebate_amount + d.discounted_amount),
						d.amount,
					])
				);
			}
		});
	}
}
