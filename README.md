# Claude AI Assistant for ERPNext — PureBlue

A Claude AI sidebar embedded in every ERPNext page. Ask questions about your data, get insights, draft emails, and more.

**Site:** https://purebluestaging.m.frappe.cloud/

---

## Installation on Frappe Cloud

### Step 1 — Upload the App to GitHub
1. Create a new GitHub repository (e.g. `pureblue-claude-assistant`)
2. Upload all files from this folder to that repository
3. Make the repository **public**

### Step 2 — Install on Frappe Cloud
1. Log in to **frappecloud.com**
2. Go to your site: `purebluestaging.m.frappe.cloud`
3. Click **Apps** → **Install App**
4. Enter your GitHub repo URL: `https://github.com/yourusername/pureblue-claude-assistant`
5. Click **Install**
6. Wait 2-3 minutes for installation

### Step 3 — Configure Claude API Key
1. Open your ERPNext site
2. You will see a **✦ AI** button on the right side of every page
3. Click it — it will ask for your Claude API key
4. Get your key from: https://console.anthropic.com
5. Enter the key and click **Save API Key & Start**

### Step 4 — Start Using!
The Claude AI sidebar is now live on every ERPNext page.

---

## What It Can Do
- ✅ Answer questions about customers, suppliers, orders, invoices, stock, payments
- ✅ Summarize the current open document
- ✅ Draft professional emails
- ✅ Sales trend analysis (month over month)
- ✅ Outstanding receivables summary
- ✅ Current stock levels
- ✅ Top customers by sales

## Security
- Read-only by design — Claude only reads data, never writes
- API key stored securely in ERPNext database (encrypted)
- All requests go server-side — no CORS issues

---

Built for PureBlue by Claude AI.
