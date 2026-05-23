import frappe
import requests
import json


@frappe.whitelist()
def ask_claude(question, current_doctype=None, current_docname=None):
	if not frappe.has_permission("System Settings", "read"):
		frappe.throw("Not permitted")

	api_key = frappe.db.get_default("claude_api_key")
	if not api_key:
		frappe.throw("Claude API key not configured. Please save it first.")

	context = build_context(question, current_doctype, current_docname)

	system_prompt = """You are an AI assistant embedded inside ERPNext for PureBlue, a Diesel Exhaust Fluid (DEF) manufacturing and sales company based in India.

You have access to the company's live ERP data. You can:
1. Answer questions about any business data (sales, purchases, inventory, accounts, customers, suppliers)
2. Analyze documents currently open in ERPNext
3. Draft professional emails to customers or suppliers
4. Provide business insights and flag anomalies
5. Summarize reports and financial data

Always:
- Use INR (Rs) for currency, Indian number format (lakhs/crores)
- Be concise and actionable
- For emails, write professionally in the context of DEF supply business

Current ERP Context:
""" + context

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
		frappe.throw(f"Claude API error: {response.status_code} - {response.text}")

	data = response.json()
	return data["content"][0]["text"]


def build_context(question, current_doctype, current_docname):
	context_parts = []

	if current_doctype and current_docname:
		try:
			doc = frappe.get_doc(current_doctype, current_docname)
			doc_data = doc.as_dict()
			exclude = ['doctype', 'docstatus', 'idx', 'owner', 'creation', 'modified', 'modified_by', 'naming_series']
			clean = {k: v for k, v in doc_data.items() if k not in exclude and v is not None and v != ''}
			context_parts.append(f"CURRENT DOCUMENT ({current_doctype}: {current_docname}):\n{json.dumps(clean, default=str, indent=2)}")
		except Exception as e:
			context_parts.append(f"Current document: {current_doctype} - {current_docname}")

	q = question.lower()

	if any(w in q for w in ['customer', 'customers', 'client']):
		try:
			customers = frappe.get_list("Customer", fields=["name", "customer_name", "customer_group", "territory", "mobile_no"], limit=20)
			context_parts.append(f"CUSTOMERS:\n{json.dumps(customers, default=str)}")
		except: pass

	if any(w in q for w in ['supplier', 'suppliers', 'vendor']):
		try:
			suppliers = frappe.get_list("Supplier", fields=["name", "supplier_name", "supplier_group"], limit=20)
			context_parts.append(f"SUPPLIERS:\n{json.dumps(suppliers, default=str)}")
		except: pass

	if any(w in q for w in ['invoice', 'invoices', 'outstanding', 'unpaid', 'receivable']):
		try:
			invoices = frappe.get_list("Sales Invoice",
				fields=["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status"],
				filters={"docstatus": 1}, order_by="posting_date desc", limit=20)
			context_parts.append(f"RECENT SALES INVOICES:\n{json.dumps(invoices, default=str)}")
		except: pass

	if any(w in q for w in ['order', 'orders', 'sales order']):
		try:
			orders = frappe.get_list("Sales Order",
				fields=["name", "customer", "transaction_date", "grand_total", "status"],
				filters={"docstatus": 1}, order_by="transaction_date desc", limit=20)
			context_parts.append(f"RECENT SALES ORDERS:\n{json.dumps(orders, default=str)}")
		except: pass

	if any(w in q for w in ['stock', 'inventory', 'item', 'items', 'def', 'quantity']):
		try:
			stock = frappe.db.sql("""
				SELECT item_code, item_name, warehouse, actual_qty, valuation_rate
				FROM `tabBin` WHERE actual_qty > 0
				ORDER BY actual_qty DESC LIMIT 30
			""", as_dict=True)
			context_parts.append(f"CURRENT STOCK:\n{json.dumps(stock, default=str)}")
		except: pass

	if any(w in q for w in ['payment', 'payments', 'paid']):
		try:
			payments = frappe.get_list("Payment Entry",
				fields=["name", "payment_type", "party", "posting_date", "paid_amount"],
				filters={"docstatus": 1}, order_by="posting_date desc", limit=20)
			context_parts.append(f"RECENT PAYMENTS:\n{json.dumps(payments, default=str)}")
		except: pass

	if any(w in q for w in ['revenue', 'sales total', 'this month', 'last month']):
		try:
			monthly = frappe.db.sql("""
				SELECT DATE_FORMAT(posting_date, '%Y-%m') as month,
					COUNT(*) as count, SUM(grand_total) as total
				FROM `tabSales Invoice` WHERE docstatus = 1
				GROUP BY DATE_FORMAT(posting_date, '%Y-%m')
				ORDER BY month DESC LIMIT 6
			""", as_dict=True)
			context_parts.append(f"MONTHLY SALES:\n{json.dumps(monthly, default=str)}")
		except: pass

	if not context_parts:
		try:
			customer_count = frappe.db.count("Customer")
			supplier_count = frappe.db.count("Supplier")
			context_parts.append(f"COMPANY SUMMARY: {customer_count} customers, {supplier_count} suppliers.")
		except: pass

	return "\n\n".join(context_parts) if context_parts else "No specific context loaded."


@frappe.whitelist()
def save_api_key(api_key):
	if not frappe.has_permission("System Settings", "write"):
		frappe.throw("Not permitted. Only System Manager can save API key.")
	frappe.db.set_default("claude_api_key", api_key)
	frappe.db.commit()
	return "saved"


@frappe.whitelist()
def get_settings():
	try:
		key = frappe.db.get_default("claude_api_key")
		return {"has_key": bool(key)}
	except:
		return {"has_key": False}
