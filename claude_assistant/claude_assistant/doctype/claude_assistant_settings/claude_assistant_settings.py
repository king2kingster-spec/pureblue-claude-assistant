import frappe
from frappe.model.document import Document
from claude_assistant.api import is_user_allowed


class ClaudeAssistantSettings(Document):

	def validate(self):
		if not is_user_allowed():
			frappe.throw("Only Administrator or System Manager can modify Claude Assistant Settings.")
