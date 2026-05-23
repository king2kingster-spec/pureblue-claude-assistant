import frappe
import requests
import json

@frappe.whitelist()
def ask_claude(question, current_doctype=None, current_docname=None):
	api_key = frappe.db.get_default("claude_api_key")
	if not api_key:
		frappe.throw("Claude API key not set. Please enter it in the sidebar settings.")
	context = build_context(question, current_doctype, current_docname)
	system_prompt = "You are an AI assistant for PureBlue ERPNext, a DEF manufacturer in India. Use INR currency. Be concise.\n\nContext:\n" + context
	response = requests.post(
		"https://api.anthropic.com/v1/messages",
		headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
		json={"model": "claude-sonnet-4-20250514", "max_tokens": 1500, "system": system_prompt, "messages": [{"role": "user", "content": question}]},
		timeout=30,
	)
	if response.status_code != 200:
		frappe.throw(f"Claude API error: {response.status_code}")
	return response.json()["content"][0]["text"]

def build_context(question, current_doctype, current_docname):
	parts = []
	if current_doctype and current_docname:
		try:
			doc = frappe.get_doc(current_doctype, current_docname).as_dict()
			parts.append(f"CURRENT DOC ({current_doctype}: {current_docname}):\n{json.dumps({k:v for k,v in doc.items() if v}, default=str)}")
		except: pass
	q = question.lower()
	if any(w in q for w in ['customer','client']):
		try: parts.append(f"CUSTOMERS:\n{json.dumps(frappe.get_list('Customer', fields=['name','customer_name','customer_group'], limit=20), default=str)}")
		except: pass
	if any(w in q for w in ['invoice','outstanding','receivable']):
		try: parts.append(f"INVOICES:\n{json.dumps(frappe.get_list('Sales Invoice', fields=['name','customer','grand_total','outstanding_amount','status'], filters={'docstatus':1}, limit=20), default=str)}")
		except: pass
	if any(w in q for w in ['stock','inventory','item','def']):
		try: parts.append(f"STOCK:\n{json.dumps(frappe.db.sql('SELECT item_code,warehouse,actual_qty FROM `tabBin` WHERE actual_qty>0 LIMIT 20', as_dict=True), default=str)}")
		except: pass
	if any(w in q for w in ['order','sales order']):
		try: parts.append(f"ORDERS:\n{json.dumps(frappe.get_list('Sales Order', fields=['name','customer','grand_total','status'], filters={'docstatus':1}, limit=20), default=str)}")
		except: pass
	if any(w in q for w in ['payment','paid']):
		try: parts.append(f"PAYMENTS:\n{json.dumps(frappe.get_list('Payment Entry', fields=['name','payment_type','party','paid_amount'], filters={'docstatus':1}, limit=20), default=str)}")
		except: pass
	if not parts:
		try: parts.append(f"SUMMARY: {frappe.db.count('Customer')} customers, {frappe.db.count('Supplier')} suppliers")
		except: pass
	return "\n\n".join(parts) or "No context."

@frappe.whitelist()
def save_api_key(api_key):
	frappe.db.set_default("claude_api_key", api_key)
	frappe.db.commit()
	return "saved"

@frappe.whitelist()
def get_settings():
	return {"has_key": bool(frappe.db.get_default("claude_api_key"))}
