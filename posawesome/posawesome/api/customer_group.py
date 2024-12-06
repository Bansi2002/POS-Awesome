import frappe


def on_update(doc, method):    
    old_custom_discount = frappe.db.get_value('Customer Group', doc.name, 'custom_discount')
    
    # check custom discount is changes or not
    if old_custom_discount != doc.custom_discount:
        update_custom_discount_in_customers(doc)

def update_custom_discount_in_customers(doc):
    # get all customer from the customer master with filterd customer_group field
    customers = frappe.get_all('Customer', filters={'customer_group': doc.name}, fields=['name'])

    for customer in customers:
        # Set new discount value in customer
        frappe.db.set_value('Customer', customer.name, 'posa_discount', doc.custom_discount)
