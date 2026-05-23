/* Claude AI Assistant Sidebar — PureBlue ERPNext */
(function () {
  'use strict';

  let sidebarOpen = false;
  let hasApiKey = false;
  let isLoading = false;

  function getCurrentDoc() {
    try {
      if (cur_frm && cur_frm.doctype && cur_frm.docname) {
        return { doctype: cur_frm.doctype, docname: cur_frm.docname };
      }
    } catch (e) {}
    return { doctype: null, docname: null };
  }

  function buildSidebar() {
    // Toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'claude-toggle-btn';
    toggleBtn.title = 'Claude AI Assistant';
    toggleBtn.innerHTML = '✦ AI';
    toggleBtn.onclick = toggleSidebar;
    document.body.appendChild(toggleBtn);

    // Sidebar
    const sidebar = document.createElement('div');
    sidebar.id = 'claude-sidebar';
    sidebar.innerHTML = `
      <div class="cs-header">
        <div>
          <h3>✦ Claude AI</h3>
          <div class="cs-subtitle">PureBlue ERP Assistant</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
          <button class="cs-clear" onclick="claudeAI.clearChat()" title="Clear chat">⟳ Clear</button>
          <button class="cs-close" onclick="claudeAI.toggle()">×</button>
        </div>
      </div>
      <div class="cs-context" id="cs-context" style="display:none;">
        📄 <span id="cs-context-text"></span>
      </div>
      <div id="cs-body">
        <!-- filled dynamically -->
      </div>
    `;
    document.body.appendChild(sidebar);

    checkSetup();
  }

  function updateContextBar() {
    const doc = getCurrentDoc();
    const ctx = document.getElementById('cs-context');
    const ctxText = document.getElementById('cs-context-text');
    if (doc.doctype && doc.docname) {
      ctx.style.display = 'flex';
      ctxText.textContent = `${doc.doctype}: ${doc.docname}`;
    } else {
      ctx.style.display = 'none';
    }
  }

  function renderSetup() {
    document.getElementById('cs-body').innerHTML = `
      <div class="cs-setup">
        <p>Welcome to <strong>Claude AI Assistant</strong> for PureBlue ERP.</p>
        <p>To get started, enter your Anthropic API key. You can get one at <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a></p>
        <input type="password" id="cs-api-key-input" placeholder="sk-ant-..." />
        <button onclick="claudeAI.saveKey()">Save API Key & Start</button>
      </div>
    `;
  }

  function renderChat() {
    document.getElementById('cs-body').innerHTML = `
      <div class="cs-quick-actions">
        <span class="cs-chip" onclick="claudeAI.quickAsk('Summarize this document')">📋 Summarize doc</span>
        <span class="cs-chip" onclick="claudeAI.quickAsk('Show outstanding invoices and total receivables')">💰 Receivables</span>
        <span class="cs-chip" onclick="claudeAI.quickAsk('What is the current stock of all items?')">📦 Stock</span>
        <span class="cs-chip" onclick="claudeAI.quickAsk('Show sales this month vs last month')">📈 Sales trend</span>
        <span class="cs-chip" onclick="claudeAI.quickAsk('Draft a payment reminder email for this customer')">✉️ Draft email</span>
        <span class="cs-chip" onclick="claudeAI.quickAsk('Who are my top 5 customers by sales?')">⭐ Top customers</span>
      </div>
      <div class="cs-messages" id="cs-messages">
        <div class="cs-msg assistant">👋 Hello! I'm your Claude AI assistant for PureBlue ERP.<br><br>I can help you with:<br>• Answering questions about your data<br>• Analysing open documents<br>• Drafting emails to customers/suppliers<br>• Business insights & trends<br><br>Ask me anything!</div>
      </div>
      <div class="cs-input-area">
        <textarea class="cs-input" id="cs-input" placeholder="Ask anything about your ERP data..." rows="1"
          onkeydown="claudeAI.handleKey(event)"></textarea>
        <button class="cs-send" id="cs-send-btn" onclick="claudeAI.send()">➤</button>
      </div>
    `;

    // Auto-resize textarea
    const input = document.getElementById('cs-input');
    input.addEventListener('input', function () {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });
  }

  function appendMessage(role, text) {
    const messages = document.getElementById('cs-messages');
    if (!messages) return;
    const div = document.createElement('div');
    div.className = `cs-msg ${role}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function setLoading(loading) {
    isLoading = loading;
    const btn = document.getElementById('cs-send-btn');
    const input = document.getElementById('cs-input');
    if (btn) { btn.disabled = loading; btn.textContent = loading ? '⏳' : '➤'; }
    if (input) input.disabled = loading;
  }

  window.claudeAI = {
    toggle: function () {
      sidebarOpen = !sidebarOpen;
      const sidebar = document.getElementById('claude-sidebar');
      if (sidebar) {
        sidebar.classList.toggle('open', sidebarOpen);
        if (sidebarOpen) updateContextBar();
      }
    },

    clearChat: function () {
      if (hasApiKey) renderChat();
    },

    saveKey: function () {
      const input = document.getElementById('cs-api-key-input');
      if (!input || !input.value.trim()) {
        frappe.msgprint('Please enter an API key.');
        return;
      }
      frappe.call({
        method: 'claude_assistant.api.save_api_key',
        args: { api_key: input.value.trim() },
        callback: function (r) {
          if (!r.exc) {
            hasApiKey = true;
            renderChat();
            frappe.show_alert({ message: 'Claude AI connected!', indicator: 'green' });
          }
        }
      });
    },

    send: function () {
      if (isLoading) return;
      const input = document.getElementById('cs-input');
      if (!input) return;
      const question = input.value.trim();
      if (!question) return;

      input.value = '';
      input.style.height = 'auto';
      appendMessage('user', question);

      const doc = getCurrentDoc();
      const thinkingEl = appendMessage('thinking', '⏳ Thinking...');
      setLoading(true);

      frappe.call({
        method: 'claude_assistant.api.ask_claude',
        args: {
          question: question,
          current_doctype: doc.doctype,
          current_docname: doc.docname
        },
        callback: function (r) {
          setLoading(false);
          if (thinkingEl) thinkingEl.remove();
          if (r.exc) {
            appendMessage('error', '❌ Error: ' + (r.exc || 'Something went wrong'));
          } else {
            appendMessage('assistant', r.message);
          }
        },
        error: function (r) {
          setLoading(false);
          if (thinkingEl) thinkingEl.remove();
          appendMessage('error', '❌ Connection error. Please try again.');
        }
      });
    },

    handleKey: function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    },

    quickAsk: function (question) {
      const input = document.getElementById('cs-input');
      if (input) { input.value = question; this.send(); }
    }
  };

  function toggleSidebar() { claudeAI.toggle(); }

  function checkSetup() {
    frappe.call({
      method: 'claude_assistant.api.get_settings',
      callback: function (r) {
        if (r.message && r.message.has_key) {
          hasApiKey = true;
          renderChat();
        } else {
          renderSetup();
        }
      },
      error: function () { renderSetup(); }
    });
  }

  function hasAccess() {
    try {
      return frappe.user_roles && (
        frappe.user_roles.includes('System Manager') ||
        frappe.user_roles.includes('Administrator')
      );
    } catch(e) { return false; }
  }

  // Init after Frappe loads
  $(document).ready(function () {
    setTimeout(function() {
      if (!hasAccess()) return;
      buildSidebar();
    }, 1500);

    $(document).on('page-change', function () {
      setTimeout(updateContextBar, 500);
    });
  });

})();
