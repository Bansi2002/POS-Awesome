frappe.ui.form.on('Barcode Parameters', {
    validate(frm) {
        // Check if the barcode number limit is less than 1
        if (frm.doc.barcode_number_limit < 1) {
            frappe.throw("Limit should be greater than 0.");
        }

        // Check if the starting number is not provided or does not have exactly 10 digits
        if (!frm.doc.starting_number || frm.doc.starting_number.toString().length !== 10) {
            frappe.throw("The starting number must have exactly 10 digits.");
        }
    }
});
    