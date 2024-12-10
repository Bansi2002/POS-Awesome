import frappe
import re

# Define a global variable to store the current starting number
# current_start_num = None

@frappe.whitelist()
def generate_barcode():
    # global current_start_num

    # Fetch the barcode parameters from Barcode Parameters doctype
    params = frappe.get_doc('Barcode Parameters')
    print(params.starting_number)
    # if current_start_num is None:
        # current_start_num = params.starting_number
    current_start_num = params.starting_number-1
    limit = params.barcode_number_limit

    barcodes = frappe.db.sql("""
        SELECT barcode FROM `tabItem Barcode`
    """, as_dict=True)
    # barcodes = [barcode['barcode'] for barcode in barcodes]
    
    numeric_barcodes = []
    for barcode in barcodes:
        if barcode['barcode'] and re.match(r'^\d+$', barcode['barcode']):
            numeric_barcodes.append(int(barcode['barcode']))

    # Determine the starting number for new barcodes
    if numeric_barcodes:
        current_start_num = max(max(numeric_barcodes), current_start_num)
    # if(barcodes):
    #     current_start_num = max(int(max(barcodes)), current_start_num)

    barcodes = [current_start_num+i+1 for i in range(limit)]
    
    # Increment the current start number for the next call
    # current_start_num += limit

    return barcodes