/* Claude AI Assistant Sidebar - PureBlue ERPNext */
/* Only visible to System Manager / Administrator */

(function () {
  'use strict';

  var sidebarOpen = false;
  var isLoading = false;

  /* ── Helpers ── */

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

  function updateContext() {
    var doc = getCurrentDoc();
    var ctx = document.getElementById('cs-context');
    var txt = document.getElementById('cs-context-text');
    if (!ctx || !txt) return;
    if (doc.doctype && doc.docname) {
      ctx.style.display = 'flex';
      txt.textContent = doc.doctype + ': ' + doc.docname;
    } else {
      ctx.style.display = 'none';
    }
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

  /* ── Render: No API Key ── */

  function renderNoKey() {
    var body = document.getElementById('cs-body');
    if (!body) return;
    body.innerHTML =
      '<div class="cs-no-key">' +
        '<p style="font-size:28px;margin-bottom:12px;">🔑</p>' +
        '<p><strong>API Key Not Configured</strong></p>' +
        '<p style="margin-top:8px;">Please go to <a href="/app/claude-assistant-settings" target="_blank">Claude Assistant Settings</a> and enter your Anthropic API key.</p>' +
        '<p style="margin-top:8px;font-size:11px;color:#999;">Only System Manager can configure this.</p>' +
      '</div>';
  }

  /* ── Render: Chat Interface ── */

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
        '<div class="cs-msg assistant">' +
          'Hello! I am your Claude AI assistant for PureBlue ERP.\n\n' +
          'I can help you with:\n' +
          '• Questions about customers, stock, invoices, orders\n' +
          '• Analysing open documents\n' +
          '• Drafting emails to customers or suppliers\n' +
          '• Business insights and trends\n\n' +
          'Tap a quick action above or ask me anything!' +
        '</div>' +
      '</div>' +
      '<div class="cs-input-area">' +
        '<textarea class="cs-input" id="cs-input" placeholder="Ask about your ERP data..." rows="1"' +
          ' onkeydown="claudeAI.key(event)"' +
          ' oninput="this.style.height=\'auto\';this.style.height=Math.min(this.scrollHeight,100)+\'px\'">' +
        '</textarea>' +
        '<button class="cs-send" id="cs-send" onclick="claudeAI.send()">➤</button>' +
      '</div>' +
      '<div class="cs-footer">Read-only · Powered by Claude · PureBlue</div>';
  }

  /* ── Build Sidebar DOM ── */

  function buildSidebar() {
    // Toggle button
    var btn = document.createElement('button');
    btn.id = 'claude-toggle-btn';
    btn.title = 'Claude AI Assistant';
    btn.innerHTML = '<span class="btn-icon">✦</span><span class="btn-text">AI</span>';
    btn.onclick = function () { claudeAI.toggle(); };
    document.body.appendChild(btn);

    // Sidebar
    var sidebar = document.createElement('div');
    sidebar.id = 'claude-sidebar';
    sidebar.innerHTML =
      '<div class="cs-header">' +
        '<div class="cs-header-info">' +
          '<h3>✦ Claude AI</h3>' +
          '<p>PureBlue ERP Assistant</p>' +
        '</div>' +
        '<div class="cs-header-actions">' +
          '<button class="cs-icon-btn" onclick="claudeAI.clear()" title="Clear chat">↺</button>' +
          '<button class="cs-icon-btn" onclick="claudeAI.toggle()" title="Close">✕</button>' +
        '</div>' +
      '</div>' +
      '<div class="cs-context" id="cs-context" style="display:none;">' +
        '<div class="cs-context-dot"></div>' +
        '<span id="cs-context-text"></span>' +
      '</div>' +
      '<div id="cs-body"></div>';
    document.body.appendChild(sidebar);

    // Load initial state
    loadState();
  }

  /* ── Check API Key Status ── */

  function loadState() {
    $.ajax({
      url: '/api/method/claude_assistant.api.get_settings',
      type: 'GET',
      headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
      success: function (r) {
        if (r && r.message && r.message.has_key) {
          renderChat();
        } else {
          renderNoKey();
        }
      },
      error: function () {
        renderNoKey();
      }
    });
  }

  /* ── Public API ── */

  window.claudeAI = {

    toggle: function () {
      sidebarOpen = !sidebarOpen;
      var s = document.getElementById('claude-sidebar');
      if (s) {
        s.classList.toggle('open', sidebarOpen);
        if (sidebarOpen) updateContext();
      }
    },

    clear: function () {
      loadState();
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
      var thinking = addMsg('thinking', '⏳ Claude is thinking...');
      setLoading(true);

      var doc = getCurrentDoc();

      $.ajax({
        url: '/api/method/claude_assistant.api.ask_claude',
        type: 'POST',
        data: {
          question: q,
          current_doctype: doc.doctype || '',
          current_docname: doc.docname || ''
        },
        headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
        success: function (r) {
          setLoading(false);
          if (thinking) thinking.remove();
          if (r && r.message) {
            addMsg('assistant', r.message);
          } else {
            addMsg('error', '❌ No response received. Please try again.');
          }
        },
        error: function (xhr) {
          setLoading(false);
          if (thinking) thinking.remove();
          var msg = '❌ Error. Please try again.';
          try {
            var resp = JSON.parse(xhr.responseText);
            if (resp._server_messages) {
              var parsed = JSON.parse(resp._server_messages);
              var inner = JSON.parse(parsed[0]);
              msg = '❌ ' + (inner.message || msg);
            }
          } catch (e) {}
          addMsg('error', msg);
        }
      });
    },

    key: function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    },

    quick: function (q) {
      var inp = document.getElementById('cs-input');
      if (inp) {
        inp.value = q;
        this.send();
      }
    }
  };

  /* ── Init ── */

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
