import frappe
from frappe.model.document import Document


class ClaudeAssistantSettings(Document):

	def validate(self):
		# Only Administrator can save
		if "Administrator" not in frappe.get_roles():
			frappe.throw("Only Administrator can modify Claude Assistant Settings.")
