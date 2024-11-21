frappe.query_reports["POS Closing Shift"] = {
	"filters": [
		{
			"fieldname": "user",
			"label": "User",
			"fieldtype": "Link",
			"options": "User",
			"default": frappe.session.user
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"options": ["" ,"Draft", "Submitted", "Cancelled"], 
		}
	],
};
