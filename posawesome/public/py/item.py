import frappe
import re

@frappe.whitelist()
def generate_barcode():
    # Fetch the barcode parameters from Barcode Parameters doctype
    params = frappe.get_doc('Barcode Parameters')
    starting_number = params.starting_number
    limit = params.barcode_number_limit

    # Fetch the Barcode Settings doctype
    barcode_settings = frappe.get_single('Barcode Parameters')
    # Get the last generated barcode from Barcode Settings or default to starting_number - 1
    last_barcode = barcode_settings.get('last_barcode_generated', starting_number - 1)
    if last_barcode is None:
        last_barcode = starting_number - 1
    # Fetch existing barcodes from `tabItem Barcode`
    existing_barcodes = frappe.db.sql("""
        SELECT barcode FROM `tabItem Barcode`
    """, as_dict=True)

    # Extract numeric barcodes from the fetched data
    numeric_barcodes = []
    for barcode in existing_barcodes:
        if barcode['barcode'] and re.match(r'^\d+$', barcode['barcode']):
            numeric_barcodes.append(int(barcode['barcode']))

    # Determine the starting point for new barcodes
    current_start_num = last_barcode + 1

    # Ensure `current_start_num` is not in `numeric_barcodes`
    while current_start_num in numeric_barcodes:
        current_start_num += 1

    # Generate the required number of barcodes
    barcodes = [current_start_num + i for i in range(limit)]

    # Update the last barcode in Barcode Settings
    barcode_settings.last_barcode_generated = max(barcodes)
    barcode_settings.save()

    return barcodes
