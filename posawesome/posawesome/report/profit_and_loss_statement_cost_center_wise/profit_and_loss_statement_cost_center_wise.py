# Copyright (c) 2025, Youssef Restom and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.report.financial_statements import (
	compute_growth_view_data,
	compute_margin_view_data,
	get_columns,
	get_data,
	get_filtered_list_for_consolidated_report,
	get_period_list,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})

	if filters.get("selected_view") == "Cost Center":
		return execute_cost_center_wise_pivot(filters)

	return execute_standard(filters)


def execute_standard(filters):
	period_list = get_period_list(
		filters.from_fiscal_year,
		filters.to_fiscal_year,
		filters.period_start_date,
		filters.period_end_date,
		filters.filter_based_on,
		filters.periodicity,
		company=filters.company,
	)

	income = get_data(
		filters.company,
		"Income",
		"Credit",
		period_list,
		filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	)

	expense = get_data(
		filters.company,
		"Expense",
		"Debit",
		period_list,
		filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	)

	net_profit_loss = get_net_profit_loss(
		income, expense, period_list, filters.company, filters.presentation_currency
	)

	data = []
	data.extend(income or [])
	data.extend(expense or [])
	if net_profit_loss:
		data.append(net_profit_loss)

	columns = get_columns(filters.periodicity, period_list, filters.accumulated_values, filters.company)

	currency = filters.presentation_currency or frappe.get_cached_value(
		"Company", filters.company, "default_currency"
	)
	chart = get_chart_data(filters, columns, income, expense, net_profit_loss, currency)

	report_summary, primitive_summary = get_report_summary(
		period_list, filters.periodicity, income, expense, net_profit_loss, currency, filters
	)

	if filters.get("selected_view") == "Growth":
		compute_growth_view_data(data, period_list)

	if filters.get("selected_view") == "Margin":
		compute_margin_view_data(data, period_list, filters.accumulated_values)

	return columns, data, None, chart, report_summary, primitive_summary


def execute_cost_center_wise_pivot(filters):
	filters = frappe._dict(filters or {})

	cost_centers = filters.get("cost_center") or []
	if isinstance(cost_centers, str):
		cost_centers = [cost_centers]
	cost_centers = [cc for cc in cost_centers if cc]

	if len(cost_centers) < 2:
		frappe.throw(_("Please select at least 2 Cost Centers for Cost Center Wise view."))

	period_list = get_period_list(
		filters.from_fiscal_year,
		filters.to_fiscal_year,
		filters.period_start_date,
		filters.period_end_date,
		filters.filter_based_on,
		filters.periodicity,
		company=filters.company,
	)

	period_keys = [p.key for p in period_list]
	from_date = period_list[0].from_date
	to_date = period_list[-1].to_date

	currency = filters.presentation_currency or frappe.get_cached_value(
		"Company", filters.company, "default_currency"
	)

	base_filters = frappe._dict(filters)
	base_filters.cost_center = None

	income_rows = get_data(
		filters.company,
		"Income",
		"Credit",
		period_list,
		filters=base_filters,
		accumulated_values=False,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	) or []

	expense_rows = get_data(
		filters.company,
		"Expense",
		"Debit",
		period_list,
		filters=base_filters,
		accumulated_values=False,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	) or []

	data = income_rows + expense_rows
	accounts = _extract_real_accounts(data)

	ccp_fields = {(cc, pk): f"cc_{frappe.scrub(cc)}_{pk}" for cc in cost_centers for pk in period_keys}

	for r in data:
		for f in ccp_fields.values():
			r[f] = 0.0
		r["cc_total"] = 0.0

	if accounts:
		gl_rows = _fetch_gl_rows_for_pivot(
			company=filters.company,
			from_date=from_date,
			to_date=to_date,
			accounts=accounts,
			cost_centers=cost_centers,
			filters=filters,
		)

		amt_map = _build_amt_map_by_period(gl_rows, period_list)

		for r in data:
			acc = r.get("account")
			if not _is_real_account(acc):
				continue

			total = 0.0
			for pk in period_keys:
				for cc in cost_centers:
					val = flt(amt_map.get((acc, cc, pk), 0.0))
					r[ccp_fields[(cc, pk)]] = val
					total += val
			r["cc_total"] = total

		_rollup_to_parents_multi_period(data, ccp_fields, cost_centers, period_keys)

	income_root = _find_root_row(income_rows)
	expense_root = _find_root_row(expense_rows)

	profit = {
		"account_name": "'" + _("Profit for the year") + "'",
		"account": "'" + _("Profit for the year") + "'",
		"warn_if_negative": True,
		"currency": currency,
	}

	for pk in period_keys:
		for cc in cost_centers:
			f = ccp_fields[(cc, pk)]
			inc = flt(income_root.get(f)) if income_root else 0.0
			exp = flt(expense_root.get(f)) if expense_root else 0.0
			profit[f] = inc - exp

	profit["cc_total"] = flt(sum(profit.get(f, 0.0) for f in ccp_fields.values()))
	data.append(profit)

	columns = _get_cc_period_columns_side_by_side(cost_centers, period_list)

	chart = _get_cost_center_wise_chart(filters, period_list, currency)

	return columns, data, None, chart, None, None


def _get_cc_period_columns_side_by_side(cost_centers, period_list):
	cols = [{
		"fieldname": "account",
		"label": _("Account"),
		"fieldtype": "Link",
		"options": "Account",
		"width": 320,
	}]

	for p in period_list:
		for cc in cost_centers:
			cols.append({
				"fieldname": f"cc_{frappe.scrub(cc)}_{p.key}",
				"label": f"{p.label} {cc}",
				"fieldtype": "Currency",
				"width": 120,
				"options": "currency",
			})

	cols.append({
		"fieldname": "cc_total",
		"label": _("Total"),
		"fieldtype": "Currency",
		"width": 140,
		"options": "currency",
	})

	cols.append({
		"fieldname": "currency",
		"label": _("Currency"),
		"fieldtype": "Link",
		"options": "Currency",
		"hidden": 1,
	})
	return cols


def _get_cost_center_wise_chart(filters, period_list, currency):
	labels = [p.label for p in period_list]
	cost_centers = filters.get("cost_center") or []

	if isinstance(cost_centers, str):
		cost_centers = [cost_centers]

	datasets = []

	for cc in cost_centers:
		cc_filters = frappe._dict(filters)
		cc_filters.cost_center = cc

		income = get_data(
			filters.company,
			"Income",
			"Credit",
			period_list,
			filters=cc_filters,
			accumulated_values=filters.accumulated_values,
			ignore_closing_entries=True,
			ignore_accumulated_values_for_fy=True,
		)

		expense = get_data(
			filters.company,
			"Expense",
			"Debit",
			period_list,
			filters=cc_filters,
			accumulated_values=filters.accumulated_values,
			ignore_closing_entries=True,
			ignore_accumulated_values_for_fy=True,
		)

		net_profit = []
		for p in period_list:
			key = p.key
			inc = income[-2].get(key) if income else 0
			exp = expense[-2].get(key) if expense else 0
			net_profit.append(flt(inc) - flt(exp))

		datasets.append({
			"name": cc,
			"values": net_profit,
		})

	chart = {
		"data": {
			"labels": labels,
			"datasets": datasets,
		},
		"type": "line" if filters.accumulated_values else "bar",
		"fieldtype": "Currency",
		"options": "currency",
		"currency": currency,
	}

	return chart


def get_report_summary(
	period_list, periodicity, income, expense, net_profit_loss, currency, filters, consolidated=False
):
	net_income, net_expense, net_profit = 0.0, 0.0, 0.0

	if filters.get("accumulated_in_group_company"):
		period_list = get_filtered_list_for_consolidated_report(filters, period_list)

	for period in period_list:
		key = period if consolidated else period.key
		if income:
			net_income += income[-2].get(key)
		if expense:
			net_expense += expense[-2].get(key)
		if net_profit_loss:
			net_profit += net_profit_loss.get(key)

	if len(period_list) == 1 and periodicity == "Yearly":
		profit_label = _("Profit This Year")
		income_label = _("Total Income This Year")
		expense_label = _("Total Expense This Year")
	else:
		profit_label = _("Net Profit")
		income_label = _("Total Income")
		expense_label = _("Total Expense")

	return [
		{"value": net_income, "label": income_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "-"},
		{"value": net_expense, "label": expense_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "=", "color": "blue"},
		{
			"value": net_profit,
			"indicator": "Green" if net_profit > 0 else "Red",
			"label": profit_label,
			"datatype": "Currency",
			"currency": currency,
		},
	], net_profit


def get_net_profit_loss(income, expense, period_list, company, currency=None, consolidated=False):
	total = 0
	net_profit_loss = {
		"account_name": "'" + _("Profit for the year") + "'",
		"account": "'" + _("Profit for the year") + "'",
		"warn_if_negative": True,
		"currency": currency or frappe.get_cached_value("Company", company, "default_currency"),
	}

	has_value = False

	for period in period_list:
		key = period if consolidated else period.key
		total_income = flt(income[-2][key], 3) if income else 0
		total_expense = flt(expense[-2][key], 3) if expense else 0

		net_profit_loss[key] = total_income - total_expense

		if net_profit_loss[key]:
			has_value = True

		total += flt(net_profit_loss[key])
		net_profit_loss["total"] = total

	if has_value:
		return net_profit_loss


def get_chart_data(filters, columns, income, expense, net_profit_loss, currency):
	labels = [d.get("label") for d in columns[2:]]

	income_data, expense_data, net_profit = [], [], []

	for p in columns[2:]:
		if income:
			income_data.append(income[-2].get(p.get("fieldname")))
		if expense:
			expense_data.append(expense[-2].get(p.get("fieldname")))
		if net_profit_loss:
			net_profit.append(net_profit_loss.get(p.get("fieldname")))

	datasets = []
	if income_data:
		datasets.append({"name": _("Income"), "values": income_data})
	if expense_data:
		datasets.append({"name": _("Expense"), "values": expense_data})
	if net_profit:
		datasets.append({"name": _("Net Profit/Loss"), "values": net_profit})

	chart = {"data": {"labels": labels, "datasets": datasets}}

	if not filters.accumulated_values:
		chart["type"] = "bar"
	else:
		chart["type"] = "line"

	chart["fieldtype"] = "Currency"
	chart["options"] = "currency"
	chart["currency"] = currency

	return chart


def _fetch_gl_rows_for_pivot(company, from_date, to_date, accounts, cost_centers, filters):
	cond = [
		"gle.company = %(company)s",
		"gle.docstatus = 1",
		"gle.is_cancelled = 0",
		"gle.posting_date between %(from_date)s and %(to_date)s",
		"gle.account in %(accounts)s",
		"gle.cost_center in %(cost_centers)s",
	]

	if filters.get("project"):
		cond.append("gle.project = %(project)s")

	finance_book = filters.get("finance_book")
	include_default = int(filters.get("include_default_book_entries") or 0)
	if finance_book:
		if include_default:
			cond.append("(gle.finance_book = %(finance_book)s OR gle.finance_book IS NULL OR gle.finance_book = '')")
		else:
			cond.append("gle.finance_book = %(finance_book)s")

	dimension_fields = _get_enabled_dimension_fields()
	for df in dimension_fields:
		if filters.get(df):
			cond.append(f"gle.{df} = %({df})s")

	where_clause = " AND ".join(cond)

	query = f"""
		select
			gle.account,
			gle.cost_center,
			gle.posting_date,
			gle.debit,
			gle.credit,
			acc.root_type
		from `tabGL Entry` gle
		inner join `tabAccount` acc on acc.name = gle.account
		where {where_clause}
	"""

	args = {
		"company": company,
		"from_date": from_date,
		"to_date": to_date,
		"accounts": tuple(accounts),
		"cost_centers": tuple(cost_centers),
		"project": filters.get("project"),
		"finance_book": finance_book,
	}

	for df in _get_enabled_dimension_fields():
		if filters.get(df):
			args[df] = filters.get(df)

	return frappe.db.sql(query, args, as_dict=True)


def _build_amt_map_by_period(gl_rows, period_list):
	out = {}
	for r in gl_rows:
		pk = _get_period_key_for_date(r.posting_date, period_list)
		if not pk:
			continue

		amt = flt(r.credit) - flt(r.debit) if r.root_type == "Income" else flt(r.debit) - flt(r.credit)
		key = (r.account, r.cost_center, pk)
		out[key] = flt(out.get(key, 0.0) + amt)
	return out


def _get_period_key_for_date(posting_date, period_list):
	for p in period_list:
		if p.from_date <= posting_date <= p.to_date:
			return p.key
	return None


def _rollup_to_parents_multi_period(rows, ccp_fields, cost_centers, period_keys):
	acc_row = {r.get("account"): r for r in rows if _is_real_account(r.get("account"))}

	real_rows = [r for r in rows if _is_real_account(r.get("account"))]
	real_rows.sort(key=lambda d: int(d.get("indent") or 0), reverse=True)

	for r in real_rows:
		parent = r.get("parent_account")
		if parent and parent in acc_row:
			pr = acc_row[parent]

			for pk in period_keys:
				for cc in cost_centers:
					f = ccp_fields[(cc, pk)]
					pr[f] = flt(pr.get(f)) + flt(r.get(f))

			pr["cc_total"] = flt(
				sum(flt(pr.get(ccp_fields[(cc, pk)])) for pk in period_keys for cc in cost_centers)
			)


def _extract_real_accounts(rows):
	accs = set()
	for r in rows:
		a = r.get("account")
		if _is_real_account(a):
			accs.add(a)
	return list(accs)


def _is_real_account(account):
	return bool(account) and isinstance(account, str) and not account.startswith("'")


def _find_root_row(rows):
	for r in rows or []:
		if _is_real_account(r.get("account")) and int(r.get("indent") or 0) == 0:
			return r
	return None


def _get_enabled_dimension_fields():
	try:
		from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_dimensions
		dims = get_dimensions()
		return [d.fieldname for d in dims if getattr(d, "fieldname", None)]
	except Exception:
		return []
