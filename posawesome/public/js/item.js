frappe.ui.form.on('Item', {
    refresh: function(frm) {
        // If the item doesn't have a barcode, enable the Generate Barcode option
        if (frm.doc.barcodes.length == 0 && !frm.is_new()) {
            frm.add_custom_button(__('Generate Barcode'), function() {
                frappe.call({
                    method: 'posawesome.public.py.item.generate_barcode',
                    // args: {
                    //     item_code: frm.doc.item_code
                    // },
                    callback: function(r) {
                        if(r.message) {
                            let barcodes = r.message;
                            for (let barcode of barcodes){
                                frm.add_child("barcodes",{
                                    barcode: barcode
                                });
                                frm.refresh_field("barcodes");
                                frm.save();
                            }
                        }
                    }
                });
            });
        }
    }
});
