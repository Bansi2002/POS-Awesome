// Copyright (c) 20201 Youssef Restom and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
    setup: function (frm) {
        frm.set_query("posa_delivery_charges", function (doc) {
            return {
                filters: { 'company': doc.company, 'disabled': 0 }
            };
        });
    },
    before_save: function(frm) {
        if (frm.doc.taxes && frm.doc.taxes.length > 0) {

            let lastRowIdx = frm.doc.taxes.length; 
            if(frm.doc.taxes[0].description === 'VAT' && frm.doc.taxes[frm.doc.taxes.length - 1].charge_type !== 'On Previous Row Total'){
                let firstTaxRow = frm.doc.taxes[0];
                frm.doc.taxes.splice(0, 1);
                firstTaxRow.charge_type = 'On Previous Row Total';
                frm.doc.taxes.push(firstTaxRow);

            }
            
            frm.doc.taxes[frm.doc.taxes.length - 1].row_id = lastRowIdx - 1
    
            frm.doc.taxes.forEach(function(row, index) {
                row.idx = index + 1;
            });
    
            let idxSet = new Set();
            frm.doc.taxes.forEach(function(row) {
                if (!row.idx) {
                    frappe.throw("Row ID is missing for some tax rows.");
                }
                if (idxSet.has(row.idx)) {
                    frappe.throw(`Duplicate Row ID found: ${row.idx}`);
                }
                idxSet.add(row.idx);
            });

            frm.refresh_field('taxes');
        }
    }
});