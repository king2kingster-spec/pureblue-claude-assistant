/* Claude AI Assistant Sidebar - PureBlue ERPNext */
(function () {
  'use strict';

  var sidebarOpen = false;
  var hasApiKey = false;
  var isLoading = false;

  function isSystemManager() {
    try {
      var roles = frappe.user_roles || [];
      return roles.indexOf('System Manager') !== -1 || roles.indexOf('Administrator') !== -1;
    } catch (e) { return false; }
  }

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
    var btn = document.createElement('button');
    btn.id = 'claude-toggle-btn';
    btn.title = 'Claude AI Assistant';
    btn.innerHTML = '<span class="btn-icon">✦</span><span class="btn-text">AI</span>';
    btn.onclick = toggleSidebar;
    document.body.appendChild(btn);

    // Sidebar container
    var sidebar = document.createElement('div');
    sidebar.id = 'claude-sidebar';
    sidebar.innerHTML =
      '<div class="cs-header">' +
        '<div class="cs-header-info"><h3>✦ Claude AI</h3><p>PureBlue ERP Assistant</p></div>' +
        '<div class="cs-header-actions">' +
          '<button class="cs-icon-btn" onclick="claudeAI.clear()" title="Clear">↺</button>' +
          '<button class="cs-icon-btn" onclick="claudeAI.close()" title="Close">✕</button>' +
        '</div>' +
      '</div>' +
      '<div class="cs-context" id="cs-context" style="display:none;">' +
        '<div class="cs-context-dot"></div>' +
        '<span id="cs-context-text"></span>' +
      '</div>' +
      '<div id="cs-body"></div>';
    document.body.appendChild(sidebar);

    checkSetup();
  }

  function checkSetup() {
    $.ajax({
      url: '/api/method/claude_assistant.api.get_settings',
      type: 'GET',
      headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
      success: function(r) {
        if (r && r.message && r.message.has_key) {
          hasApiKey = true;
          renderChat();
        } else {
          renderSetup();
        }
      },
      error: function() { renderSetup(); }
    });
  }

  function renderSetup() {
    var body = document.getElementById('cs-body');
    if (!body) return;
    body.innerHTML =
      '<div class="cs-setup">' +
        '<p><strong>Welcome to Claude AI for PureBlue ERP!</strong></p>' +
        '<p>Enter your Anthropic API key to get started. Get one at <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a></p>' +
        '<input type="password" id="cs-key-input" placeholder="sk-ant-api..." />' +
        '<button onclick="claudeAI.saveKey()">Save API Key & Start</button>' +
      '</div>';
  }

  function renderChat() {
    var body = document.getElementById('cs-body');
    if (!body) return;
    body.innerHTML =
      '<div class="cs-chips">' +
        '<span class="cs-chip" onclick="claudeAI.quick(\'Summarize this document\')">📋 Summarize</span>' +
        '<span class="cs-chip" onclick="claudeAI.quick(\'Draft a payment reminder email for this customer\')">✉️ Reminder email</span>' +
        '<span class="cs-chip" onclick="claudeAI.quick(\'Show all outstanding receivables\')">💰 Receivables</span>' +
        '<span class="cs-chip" onclick="claudeAI.quick(\'What is the current stock of DEF items?\')">📦 Stock</span>' +
        '<span class="cs-chip" onclick="claudeAI.quick(\'Compare sales this month vs last month\')">📈 Sales trend</span>' +
        '<span class="cs-chip" onclick="claudeAI.quick(\'Who are the top 5 customers by revenue?\')">⭐ Top customers</span>' +
      '</div>' +
      '<div class="cs-messages" id="cs-messages">' +
        '<div class="cs-msg assistant">👋 Hello! I am your Claude AI assistant for PureBlue ERP.\n\nI can help you with:\n• Questions about customers, stock, invoices, orders\n• Analysing open documents\n• Drafting emails\n• Business insights\n\nTap a quick action or ask me anything!</div>' +
      '</div>' +
      '<div class="cs-input-area">' +
        '<textarea class="cs-input" id="cs-input" placeholder="Ask about your ERP data..." rows="1" onkeydown="claudeAI.key(event)" oninput="this.style.height=\'auto\';this.style.height=Math.min(this.scrollHeight,100)+\'px\'"></textarea>' +
        '<button class="cs-send" id="cs-send" onclick="claudeAI.send()">➤</button>' +
      '</div>' +
      '<div class="cs-footer">Read-only · Powered by Claude · PureBlue</div>';
  }

  function addMsg(role, text) {
    var msgs = document.getElementById('cs-messages');
    if (!msgs) return null;
    var div = document.createElement('div');
    div.className = 'cs-msg ' + role;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  function setLoading(val) {
    isLoading = val;
    var btn = document.getElementById('cs-send');
    var inp = document.getElementById('cs-input');
    if (btn) { btn.disabled = val; btn.textContent = val ? '⏳' : '➤'; }
    if (inp) inp.disabled = val;
  }

function checkSetup() {
    $.ajax({
      url: '/api/method/claude_assistant.api.get_settings',
      type: 'GET',
      headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
      success: function(r) {
        if (r && r.message && r.message.has_key) {
          hasApiKey = true;
          renderChat();
        } else {
          renderSetup();
        }
      },
      error: function() { renderSetup(); }
    });
  }

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
    var s = document.getElementById('claude-sidebar');
    if (s) {
      s.classList.toggle('open', sidebarOpen);
      if (sidebarOpen) updateContext();
    }
  }

  window.claudeAI = {
    close: function () {
      sidebarOpen = false;
      var s = document.getElementById('claude-sidebar');
      if (s) s.classList.remove('open');
    },
    clear: function () {
      if (hasApiKey) renderChat();
    },
    saveKey: function () {
      var inp = document.getElementById('cs-key-input');
      if (!inp || !inp.value.trim()) { frappe.msgprint('Please enter your API key.'); return; }
      frappe.call({
        method: 'claude_assistant.api.save_api_key',
        args: { api_key: inp.value.trim() },
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
      var inp = document.getElementById('cs-input');
      if (!inp) return;
      var q = inp.value.trim();
      if (!q) return;
      inp.value = '';
      inp.style.height = 'auto';
      addMsg('user', q);
      var thinking = addMsg('thinking', '⏳ Thinking...');
      setLoading(true);
      var doc = getCurrentDoc();
      frappe.call({
        method: 'claude_assistant.api.ask_claude',
        args: { question: q, current_doctype: doc.doctype, current_docname: doc.docname },
        callback: function (r) {
          setLoading(false);
          if (thinking) thinking.remove();
          if (r.exc) {
            addMsg('error', '❌ ' + (r.exc || 'Something went wrong'));
          } else {
            addMsg('assistant', r.message);
          }
        },
        error: function () {
          setLoading(false);
          if (thinking) thinking.remove();
          addMsg('error', '❌ Connection error. Please try again.');
        }
      });
    },
    key: function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.send(); }
    },
    quick: function (q) {
      var inp = document.getElementById('cs-input');
      if (inp) { inp.value = q; this.send(); }
    }
  };

  // Boot after Frappe is ready - only for System Manager
  $(document).ready(function () {
    setTimeout(function () {
      if (!isSystemManager()) return;
      buildSidebar();
    }, 1500);

    $(document).on('page-change', function () {
      setTimeout(updateContext, 500);
    });
  });

})();
