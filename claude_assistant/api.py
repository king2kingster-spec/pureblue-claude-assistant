import frappe
import requests
import json


@frappe.whitelist()
def ask_claude(question, current_doctype=None, current_docname=None):
	"""
	Main API endpoint: takes a user question, gathers ERPNext context,
	calls Claude API, returns the answer.
	"""
	api_key = frappe.db.get_single_value("Claude Assistant Settings", "api_key")
	if not api_key:
		frappe.throw("Claude API key not configured. Go to Claude Assistant Settings.")

	# Build context from current document + relevant ERPNext data
	context = build_context(question, current_doctype, current_docname)

	system_prompt = """You are an AI assistant embedded inside ERPNext for PureBlue, a Diesel Exhaust Fluid (DEF) manufacturing and sales company based in India.

You have access to the company's live ERP data. You can:
1. Answer questions about any business data (sales, purchases, inventory, accounts, customers, suppliers)
2. Analyze documents currently open in ERPNext
3. Draft professional emails to customers or suppliers
4. Provide business insights and flag anomalies
5. Summarize reports and financial data

Always:
- Use INR (₹) for currency, Indian number format (lakhs/crores)
- Be concise and actionable
- If data is provided in context, use it directly
- If you need data not in context, suggest what report to run in ERPNext
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
	"""Build context from current document and relevant ERPNext data."""
	context_parts = []

	# 1. Current document context
	if current_doctype and current_docname:
		try:
			doc = frappe.get_doc(current_doctype, current_docname)
			doc_data = doc.as_dict()
			# Remove internal Frappe fields
			exclude = ['doctype', 'docstatus', 'idx', 'owner', 'creation', 'modified', 'modified_by', 'naming_series']
			clean = {k: v for k, v in doc_data.items() if k not in exclude and v is not None and v != ''}
			context_parts.append(f"CURRENT DOCUMENT ({current_doctype}: {current_docname}):\n{json.dumps(clean, default=str, indent=2)}")
		except Exception as e:
			context_parts.append(f"Current document: {current_doctype} - {current_docname} (could not load: {e})")

	# 2. Smart context based on question keywords
	q = question.lower()

	if any(w in q for w in ['customer', 'customers', 'client']):
		try:
			customers = frappe.get_list("Customer", fields=["name", "customer_name", "customer_group", "territory", "mobile_no"], limit=20)
			context_parts.append(f"CUSTOMERS (top 20):\n{json.dumps(customers, default=str)}")
		except: pass

	if any(w in q for w in ['supplier', 'suppliers', 'vendor']):
		try:
			suppliers = frappe.get_list("Supplier", fields=["name", "supplier_name", "supplier_group"], limit=20)
			context_parts.append(f"SUPPLIERS (top 20):\n{json.dumps(suppliers, default=str)}")
		except: pass

	if any(w in q for w in ['invoice', 'invoices', 'outstanding', 'unpaid', 'receivable']):
		try:
			invoices = frappe.get_list("Sales Invoice",
				fields=["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status"],
				filters={"docstatus": 1},
				order_by="posting_date desc",
				limit=20)
			context_parts.append(f"RECENT SALES INVOICES:\n{json.dumps(invoices, default=str)}")
		except: pass

	if any(w in q for w in ['purchase invoice', 'purchase invoices', 'payable', 'bill']):
		try:
			pinvoices = frappe.get_list("Purchase Invoice",
				fields=["name", "supplier", "posting_date", "grand_total", "outstanding_amount", "status"],
				filters={"docstatus": 1},
				order_by="posting_date desc",
				limit=20)
			context_parts.append(f"RECENT PURCHASE INVOICES:\n{json.dumps(pinvoices, default=str)}")
		except: pass

	if any(w in q for w in ['order', 'orders', 'sales order', 'so']):
		try:
			orders = frappe.get_list("Sales Order",
				fields=["name", "customer", "transaction_date", "grand_total", "status"],
				filters={"docstatus": 1},
				order_by="transaction_date desc",
				limit=20)
			context_parts.append(f"RECENT SALES ORDERS:\n{json.dumps(orders, default=str)}")
		except: pass

	if any(w in q for w in ['purchase order', 'po', 'buying']):
		try:
			porders = frappe.get_list("Purchase Order",
				fields=["name", "supplier", "transaction_date", "grand_total", "status"],
				filters={"docstatus": 1},
				order_by="transaction_date desc",
				limit=20)
			context_parts.append(f"RECENT PURCHASE ORDERS:\n{json.dumps(porders, default=str)}")
		except: pass

	if any(w in q for w in ['stock', 'inventory', 'item', 'items', 'def', 'quantity']):
		try:
			stock = frappe.db.sql("""
				SELECT item_code, item_name, warehouse, actual_qty, reserved_qty, valuation_rate
				FROM `tabBin`
				WHERE actual_qty > 0
				ORDER BY actual_qty DESC
				LIMIT 30
			""", as_dict=True)
			context_parts.append(f"CURRENT STOCK:\n{json.dumps(stock, default=str)}")
		except: pass

	if any(w in q for w in ['payment', 'payments', 'paid', 'receipt']):
		try:
			payments = frappe.get_list("Payment Entry",
				fields=["name", "payment_type", "party", "posting_date", "paid_amount", "mode_of_payment"],
				filters={"docstatus": 1},
				order_by="posting_date desc",
				limit=20)
			context_parts.append(f"RECENT PAYMENTS:\n{json.dumps(payments, default=str)}")
		except: pass

	if any(w in q for w in ['delivery', 'deliveries', 'shipped', 'dispatch']):
		try:
			deliveries = frappe.get_list("Delivery Note",
				fields=["name", "customer", "posting_date", "grand_total", "status"],
				filters={"docstatus": 1},
				order_by="posting_date desc",
				limit=20)
			context_parts.append(f"RECENT DELIVERY NOTES:\n{json.dumps(deliveries, default=str)}")
		except: pass

	if any(w in q for w in ['revenue', 'sales total', 'total sales', 'this month', 'last month']):
		try:
			monthly = frappe.db.sql("""
				SELECT 
					DATE_FORMAT(posting_date, '%Y-%m') as month,
					COUNT(*) as count,
					SUM(grand_total) as total
				FROM `tabSales Invoice`
				WHERE docstatus = 1
				GROUP BY DATE_FORMAT(posting_date, '%Y-%m')
				ORDER BY month DESC
				LIMIT 6
			""", as_dict=True)
			context_parts.append(f"MONTHLY SALES (last 6 months):\n{json.dumps(monthly, default=str)}")
		except: pass

	if not context_parts:
		# Generic context - company summary
		try:
			customer_count = frappe.db.count("Customer")
			supplier_count = frappe.db.count("Supplier")
			pending_invoices = frappe.db.sql("""
				SELECT COUNT(*) as count, SUM(outstanding_amount) as total
				FROM `tabSales Invoice`
				WHERE docstatus=1 AND outstanding_amount > 0
			""", as_dict=True)
			context_parts.append(f"COMPANY SUMMARY: {customer_count} customers, {supplier_count} suppliers. Pending receivables: {pending_invoices[0] if pending_invoices else 'N/A'}")
		except: pass

	return "\n\n".join(context_parts) if context_parts else "No specific context loaded."


@frappe.whitelist()
def save_api_key(api_key):
	"""Save Claude API key to settings."""
	if not frappe.db.exists("DocType", "Claude Assistant Settings"):
		frappe.throw("Claude Assistant Settings DocType not found.")
	settings = frappe.get_single("Claude Assistant Settings")
	settings.api_key = api_key
	settings.save(ignore_permissions=True)
	return "saved"


@frappe.whitelist()
def get_settings():
	"""Get current settings."""
	try:
		key = frappe.db.get_single_value("Claude Assistant Settings", "api_key")
		return {"has_key": bool(key)}
	except:
		return {"has_key": False}
