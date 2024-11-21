import frappe
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "ID", "fieldname": "id", "fieldtype": "Data", "width": 180},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Period Starting Date", "fieldname": "start_date", "fieldtype": "Date", "width": 140},
        {"label": "Period Ending Date", "fieldname": "end_date", "fieldtype": "Date", "width": 140},
        {"label": "Shortage/Overage", "fieldname": "shortage_overage", "fieldtype": "Data", "width": 140},
        {"label": "Difference", "fieldname": "difference", "fieldtype": "Currency", "width": 150},
    ]

def get_data(filters):
    user = filters.get("user")
    status_filter = filters.get("status") 
    
    # Base SQL query
    sql_query = """
        SELECT
            pcs.name AS id,
            CASE
                WHEN pcs.docstatus = 0 THEN 'Draft'
                WHEN pcs.docstatus = 1 THEN 'Submitted'
                WHEN pcs.docstatus = 2 THEN 'Cancelled'
                ELSE 'Unknown'
            END AS status,
            pcs.period_start_date AS start_date,
            pcs.period_end_date AS end_date,
            CASE
                WHEN pcs.is_shortage = 1 THEN 'Shortage'
                WHEN COALESCE(SUM(pcsd.difference), 0) = 0 THEN ''
                ELSE 'Overage'
            END AS shortage_overage,
            COALESCE(SUM(pcsd.difference), 0) AS difference
        FROM
            `tabPOS Closing Shift` pcs
        LEFT JOIN
            `tabPOS Closing Shift Detail` pcsd ON pcs.name = pcsd.parent
    """
    
    filters_values = []
    
    # Start WHERE clause if filters are applied
    where_clause_added = False

    # Add user filter only if provided
    if user:
        sql_query += " WHERE pcs.user = %s"
        filters_values.append(user)
        where_clause_added = True
    
    # Add status filter if provided
    if status_filter:
        status_map = {
            "Draft": 0,
            "Submitted": 1,
            "Cancelled": 2
        }
        if status_filter in status_map:
            if where_clause_added:
                sql_query += " AND pcs.docstatus = %s"
            else:
                sql_query += " WHERE pcs.docstatus = %s"
            filters_values.append(status_map[status_filter])
            where_clause_added = True

   
        
    
    # Complete the query with GROUP BY and ORDER BY
    sql_query += """
        GROUP BY
            pcs.name
        ORDER BY
            pcs.period_start_date ASC
    """
    
    # Execute query with filters
    data = frappe.db.sql(sql_query, tuple(filters_values), as_dict=True)
    
    # Calculate the net difference
    net_difference = sum([flt(row['difference']) for row in data])
    
    # Add a total row
    data.append({
        "id": "TOTAL",
        "status": "",
        "start_date": "",
        "end_date": "",
        "shortage_overage": "",
        "difference": net_difference,
    })
    
    return data
