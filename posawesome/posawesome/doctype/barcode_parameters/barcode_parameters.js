frappe.ui.form.on('Barcode Parameters', {
	validate(frm) {
	    if (frm.doc.barcode_number_limit < 1) {
	        frappe.throw("Limit should be greater than 0.");
	    }
	}
});