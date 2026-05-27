import frappe
from frappe.model.document import Document


class ClaudeAssistantSettings(Document):

	def validate(self):
		# Only System Manager can save
		if "System Manager" not in frappe.get_roles():
			frappe.throw("Only System Manager can modify Claude Assistant Settings.")
