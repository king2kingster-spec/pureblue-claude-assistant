from . import __version__ as app_version

app_name = "claude_assistant"
app_title = "Claude AI Assistant"
app_publisher = "PureBlue"
app_description = "Claude AI Assistant sidebar for ERPNext"
app_email = "ahad@pureblue.co.in"
app_license = "MIT"
app_version = app_version

# Include JS and CSS in every page
app_include_js = "/assets/claude_assistant/js/claude_sidebar.js"
app_include_css = "/assets/claude_assistant/css/claude_sidebar.css"

# Whitelisted methods (callable from frontend)
# These are defined in api.py
