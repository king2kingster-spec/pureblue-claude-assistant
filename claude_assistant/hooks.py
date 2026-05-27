app_name = "claude_assistant"
app_title = "Claude Assistant"
app_publisher = "PureBlue"
app_description = "Claude AI Assistant sidebar for ERPNext"
app_email = "ahad@pureblue.co.in"
app_license = "MIT"
app_version = "1.0.1"
app_color = "orange"
app_icon = "octicon octicon-hubot"

app_include_js = "/assets/claude_assistant/js/claude_sidebar.js"
app_include_css = "/assets/claude_assistant/css/claude_sidebar.css"

# Hooks
after_app_install = "claude_assistant.hooks.create_default_settings"


def create_default_settings():
	"""Create default Claude Assistant Settings record on app installation."""
	import frappe

	if not frappe.db.exists("Claude Assistant Settings", "Claude Assistant Settings"):
		doc = frappe.get_doc({
			"doctype": "Claude Assistant Settings",
			"name": "Claude Assistant Settings"
		})
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
