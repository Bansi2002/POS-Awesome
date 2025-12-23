// Copyright (c) 2025, Youssef Restom and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/erpnext/js/financial_statements.js", function () {
	frappe.query_reports["Profit and Loss Statement Cost Center Wise"] = $.extend({}, erpnext.financial_statements);

	erpnext.utils.add_dimensions("Profit and Loss Statement Cost Center Wise", 10);

	frappe.query_reports["Profit and Loss Statement Cost Center Wise"]["filters"].push({
		fieldname: "selected_view",
		label: __("Select View"),
		fieldtype: "Select",
		options: [
			{ value: "Report", label: __("Report View") },
			{ value: "Cost Center", label: __("Cost Center Wise (Pivot)") },
			{ value: "Growth", label: __("Growth View") },
			{ value: "Margin", label: __("Margin View") },
		],
		default: "Report",
		reqd: 1,
		on_change: function () {
			if (frappe.query_report) frappe.query_report.refresh();
		},
	});

	frappe.query_reports["Profit and Loss Statement Cost Center Wise"]["filters"].push({
		fieldname: "include_default_book_entries",
		label: __("Include Default Book Entries"),
		fieldtype: "Check",
		default: 1,
	});

	frappe.query_reports["Profit and Loss Statement Cost Center Wise"]["before_refresh"] = function (report) {
		const view = report.get_filter_value("selected_view");

		if (view === "Cost Center") {
			const cc = report.get_filter_value("cost_center") || [];
			if (!Array.isArray(cc) || cc.length < 2) {
				frappe.throw(__("Please select at least 2 Cost Centers for Cost Center Wise (Pivot) view."));
			}
		}
	};
});
