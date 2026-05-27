import frappe
import requests
import json


@frappe.whitelist()
def ask_claude(question, current_doctype=None, current_docname=None):
	"""Main API - takes question, fetches ERP context, calls Claude, returns answer."""

	if "Administrator" not in frappe.get_roles():
		frappe.throw("Not permitted. Only Administrator can use Claude AI.")

	# Get API key from Single DocType
	api_key = frappe.db.get_single_value("Claude Assistant Settings", "api_key")
	if not api_key:
		frappe.throw("Claude API key not configured. Please go to Claude Assistant Settings and save your API key.")

	# Build context from ERPNext data
	context = build_context(question, current_doctype, current_docname)

	system_prompt = (
		"You are an AI assistant embedded inside ERPNext for PureBlue, "
		"an Indian company that manufactures and sells Diesel Exhaust Fluid (DEF).\n\n"
		"You have access to live ERP data. You can:\n"
		"1. Answer questions about customers, suppliers, invoices, orders, stock, payments\n"
		"2. Analyze the currently open document\n"
		"3. Draft professional emails to customers or suppliers\n"
		"4. Provide business insights\n\n"
		"Guidelines:\n"
		"- Use INR (Rs) for currency, Indian number format (lakhs/crores)\n"
		"- Be concise and actionable\n"
		"- For emails, write professionally for B2B petroleum industry\n\n"
		"Current ERP Data:\n" + context
	)

	try:
		response = requests.post(
			"https://api.anthropic.com/v1/messages",
			headers={
				"x-api-key": api_key,
				"anthropic-version": "2023-06-01",
				"content-type": "application/json",
			},
			json={
				"model": "claude-sonnet-4-20250514",
				"max_tokens": 1500,
				"system": system_prompt,
				"messages": [{"role": "user", "content": question}],
			},
			timeout=30,
		)

		if response.status_code != 200:
			frappe.throw("Claude API error: " + str(response.status_code) + " - " + response.text[:200])

		return response.json()["content"][0]["text"]

	except requests.exceptions.Timeout:
		frappe.throw("Request timed out. Please try again.")
	except Exception as e:
		frappe.throw("Error calling Claude API: " + str(e))


def build_context(question, current_doctype, current_docname):
	"""Fetch relevant ERPNext data based on the question keywords."""
	parts = []

	# Always include current open document
	if current_doctype and current_docname:
		try:
			doc = frappe.get_doc(current_doctype, current_docname).as_dict()
			exclude = ["doctype", "docstatus", "idx", "owner", "creation", "modified", "modified_by"]
			clean = {k: v for k, v in doc.items() if k not in exclude and v not in [None, "", []]}
			parts.append("CURRENT DOCUMENT ({} - {}):\n{}".format(
				current_doctype, current_docname, json.dumps(clean, default=str, indent=2)))
		except Exception:
			pass

	q = question.lower()

	if any(w in q for w in ["customer", "client", "customers"]):
		try:
			data = frappe.get_list("Customer",
				fields=["name", "customer_name", "customer_group", "territory", "mobile_no"], limit=20)
			parts.append("CUSTOMERS:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["supplier", "vendor", "suppliers"]):
		try:
			data = frappe.get_list("Supplier",
				fields=["name", "supplier_name", "supplier_group"], limit=20)
			parts.append("SUPPLIERS:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["invoice", "outstanding", "receivable", "unpaid"]):
		try:
			data = frappe.get_list("Sales Invoice",
				fields=["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status"],
				filters={"docstatus": 1}, order_by="posting_date desc", limit=20)
			parts.append("SALES INVOICES:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["purchase invoice", "payable", "bill"]):
		try:
			data = frappe.get_list("Purchase Invoice",
				fields=["name", "supplier", "posting_date", "grand_total", "outstanding_amount", "status"],
				filters={"docstatus": 1}, order_by="posting_date desc", limit=20)
			parts.append("PURCHASE INVOICES:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["order", "sales order"]):
		try:
			data = frappe.get_list("Sales Order",
				fields=["name", "customer", "transaction_date", "grand_total", "status"],
				filters={"docstatus": 1}, order_by="transaction_date desc", limit=20)
			parts.append("SALES ORDERS:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["purchase order", "po", "buying"]):
		try:
			data = frappe.get_list("Purchase Order",
				fields=["name", "supplier", "transaction_date", "grand_total", "status"],
				filters={"docstatus": 1}, order_by="transaction_date desc", limit=20)
			parts.append("PURCHASE ORDERS:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["stock", "inventory", "item", "def", "quantity", "warehouse"]):
		try:
			data = frappe.db.sql("""
				SELECT item_code, item_name, warehouse, actual_qty, valuation_rate
				FROM `tabBin` WHERE actual_qty > 0
				ORDER BY actual_qty DESC LIMIT 30
			""", as_dict=True)
			parts.append("CURRENT STOCK:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["payment", "paid", "receipt"]):
		try:
			data = frappe.get_list("Payment Entry",
				fields=["name", "payment_type", "party", "posting_date", "paid_amount"],
				filters={"docstatus": 1}, order_by="posting_date desc", limit=20)
			parts.append("PAYMENTS:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["month", "revenue", "sales total", "trend"]):
		try:
			data = frappe.db.sql("""
				SELECT DATE_FORMAT(posting_date, '%Y-%m') as month,
					COUNT(*) as invoices, SUM(grand_total) as total_sales
				FROM `tabSales Invoice` WHERE docstatus = 1
				GROUP BY DATE_FORMAT(posting_date, '%Y-%m')
				ORDER BY month DESC LIMIT 6
			""", as_dict=True)
			parts.append("MONTHLY SALES:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if any(w in q for w in ["delivery", "dispatch", "shipped"]):
		try:
			data = frappe.get_list("Delivery Note",
				fields=["name", "customer", "posting_date", "grand_total", "status"],
				filters={"docstatus": 1}, order_by="posting_date desc", limit=20)
			parts.append("DELIVERY NOTES:\n" + json.dumps(data, default=str))
		except Exception:
			pass

	if not parts:
		try:
			c = frappe.db.count("Customer")
			s = frappe.db.count("Supplier")
			parts.append("COMPANY SUMMARY: {} customers, {} suppliers.".format(c, s))
		except Exception:
			pass

	return "\n\n".join(parts) if parts else "No specific data loaded."


@frappe.whitelist()
def get_settings():
	"""Check if API key is configured. Called on sidebar load."""
	try:
		if "Administrator" not in frappe.get_roles():
			return {"has_key": False, "permitted": False}
		api_key = frappe.db.get_single_value("Claude Assistant Settings", "api_key")
		return {"has_key": bool(api_key), "permitted": True}
	except Exception:
		return {"has_key": False, "permitted": True}
