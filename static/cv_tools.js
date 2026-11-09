/**
 * CyberSwitch 10X - CV Tools & Intelligent Recruiter Engagement Engine
 * Phase 3 (CV Tracer Links) + Phase 4 (Alerts) + Phase 5 (Anti-Hallucination CV Tailor)
 */

let activeTracerLink = null;

// ==========================================
// Phase 5: Anti-Hallucination CV Tailor
// ==========================================
async function openCvTailorModal(company, title, description = '', applyUrl = '') {
  const modal = document.getElementById('cv-tailor-modal');
  if (!modal) return;

  document.getElementById('tailor-modal-company').textContent = company;
  document.getElementById('tailor-modal-role').textContent = title;
  document.getElementById('tailor-bullets-container').innerHTML = `
    <div class="py-8 text-center text-slate-400 text-xs flex items-center justify-center space-x-2">
      <i data-lucide="loader-2" class="w-4 h-4 animate-spin text-cyan-400"></i>
      <span>Analyzing job description & matching verified experience bank...</span>
    </div>
  `;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  if (window.lucide) lucide.createIcons();

  try {
    // 1. Auto-create or fetch CV tracer link for this company
    const linkRes = await fetch('/api/tracer-links/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company: company,
        role: title,
        destination_key: 'linkedin'
      })
    });
    const linkData = await linkRes.json();
    const fullTracerUrl = window.location.origin + linkData.tracking_path;
    activeTracerLink = fullTracerUrl;

    // 2. Tailor verified experience points
    const res = await fetch('/api/experience-bank/tailor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company: company,
        title: title,
        description: description,
        tracer_url: fullTracerUrl
      })
    });
    const data = await res.json();
    renderTailorResults(data, fullTracerUrl);
  } catch (err) {
    console.error('Tailoring error:', err);
    document.getElementById('tailor-bullets-container').innerHTML = `
      <div class="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
        Failed to tailor resume points. Please try again.
      </div>
    `;
  }
}

function closeCvTailorModal() {
  const modal = document.getElementById('cv-tailor-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function renderTailorResults(data, tracerUrl) {
  const container = document.getElementById('tailor-bullets-container');
  if (!container) return;

  const skillsHtml = (data.matched_skills || []).map(s => 
    `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 border border-cyan-800 text-cyan-300">${s}</span>`
  ).join('');

  const bulletsHtml = (data.tailored_bullets || []).map((b, idx) => `
    <li class="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 hover:border-cyan-500/50 transition flex items-start space-x-2.5">
      <span class="flex-shrink-0 w-5 h-5 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-300 flex items-center justify-center font-mono text-[10px] font-bold">
        ${idx + 1}
      </span>
      <p class="text-xs text-slate-200 leading-relaxed select-all">${b}</p>
    </li>
  `).join('');

  container.innerHTML = `
    <!-- Matched Skills Strip -->
    <div class="space-y-1.5 pb-2 border-b border-slate-800">
      <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">🎯 Matched Core Competencies:</div>
      <div class="flex items-center flex-wrap gap-1.5">
        ${skillsHtml || '<span class="text-xs text-slate-500">Cybersecurity Analyst (SOC L2)</span>'}
      </div>
    </div>

    <!-- Verified STAR Bullets -->
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-white flex items-center space-x-1.5">
          <span>✨ 5 Anti-Hallucination Resume Bullets</span>
          <span class="text-[10px] font-normal text-emerald-400 font-mono">(100% Truthful • Wipro SOC L2)</span>
        </span>
        <button onclick="copyAllTailoredBullets()" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-300 text-[10px] font-semibold flex items-center space-x-1 transition">
          <i data-lucide="copy" class="w-3 h-3"></i>
          <span id="btn-copy-bullets-text">Copy All</span>
        </button>
      </div>
      <ul class="space-y-2" id="tailored-bullets-list">
        ${bulletsHtml}
      </ul>
    </div>

    <!-- 30-Second Elevator Pitch -->
    <div class="space-y-1.5 p-3 rounded-xl bg-purple-950/30 border border-purple-800/50">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-purple-300">🎙️ 30-Second Interview Elevator Pitch:</span>
        <button onclick="copyTextToClipboard('${escapeAttr(data.elevator_pitch)}', this)" class="text-[10px] text-purple-300 hover:underline">
          Copy Pitch
        </button>
      </div>
      <p class="text-xs text-slate-300 italic leading-relaxed select-all">"${data.elevator_pitch}"</p>
    </div>

    <!-- Recruiter Outreach DM with Tracer Link -->
    <div class="space-y-1.5 p-3 rounded-xl bg-cyan-950/30 border border-cyan-800/50">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-1.5">
          <span class="text-xs font-bold text-cyan-300">📨 LinkedIn InMail & Referral Outreach:</span>
          <span class="px-1.5 py-0.2 rounded text-[9px] font-mono bg-emerald-950 border border-emerald-700 text-emerald-300">Includes Tracer Link</span>
        </div>
        <button onclick="copyTextToClipboard('${escapeAttr(data.recruiter_dm)}', this)" class="text-[10px] text-cyan-300 hover:underline">
          Copy Message
        </button>
      </div>
      <pre class="text-[11px] text-slate-300 font-sans whitespace-pre-wrap select-all bg-slate-950/80 p-2.5 rounded-lg border border-slate-800">${escapeHtml(data.recruiter_dm)}</pre>
    </div>

    <!-- Tracer Link Box -->
    <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
      <div class="flex items-center space-x-2">
        <span class="text-slate-400 font-mono text-[11px]">Tracer URL:</span>
        <code class="text-cyan-400 font-mono text-[11px] select-all">${tracerUrl}</code>
      </div>
      <button onclick="copyTextToClipboard('${tracerUrl}', this)" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-[10px] font-semibold">
        Copy Link
      </button>
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

function copyAllTailoredBullets() {
  const items = document.querySelectorAll('#tailored-bullets-list p');
  const text = Array.from(items).map(i => `• ${i.textContent.trim()}`).join('\n\n');
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('btn-copy-bullets-text');
    if (btn) {
      btn.textContent = 'Copied!';
      setTimeout(() => btn.textContent = 'Copy All', 2000);
    }
    if (typeof showToast === 'function') showToast('Copied 5 tailored bullets to clipboard!', 'success');
  });
}

// ==========================================
// Phase 3: CV Tracer Links Management
// ==========================================
async function openTracerModal() {
  const modal = document.getElementById('tracer-manager-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  loadTracerStatsView();
}

function closeTracerModal() {
  const modal = document.getElementById('tracer-manager-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function loadTracerStatsView() {
  const container = document.getElementById('tracer-links-list');
  if (!container) return;

  try {
    const res = await fetch('/api/tracer-links');
    const data = await res.json();

    document.getElementById('tracer-stat-active').textContent = data.total_active_links || 0;
    document.getElementById('tracer-stat-clicks').textContent = data.total_recruiter_clicks || 0;

    const links = data.links || [];
    if (links.length === 0) {
      container.innerHTML = `
        <div class="py-10 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
          No tracer links generated yet. Generate one when tailoring a CV or using the form above!
        </div>
      `;
      return;
    }

    container.innerHTML = links.map(l => {
      const fullUrl = window.location.origin + l.tracking_path;
      return `
        <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between gap-3">
          <div class="space-y-1 min-w-0">
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-white">${l.company}</span>
              <span class="px-1.5 py-0.2 rounded text-[10px] font-mono bg-cyan-950 border border-cyan-800 text-cyan-300">${l.destination_key}</span>
            </div>
            <div class="text-[11px] font-mono text-cyan-400 truncate">${fullUrl}</div>
            <div class="text-[10px] text-slate-400">Created: ${l.created_at} ${l.last_clicked ? `• Last clicked: <strong class="text-emerald-400">${l.last_clicked}</strong>` : ''}</div>
          </div>
          <div class="flex items-center space-x-2 flex-shrink-0">
            <span class="px-2.5 py-1 rounded-lg ${l.total_clicks > 0 ? 'bg-emerald-950 border border-emerald-700 text-emerald-300 font-black' : 'bg-slate-950 border border-slate-800 text-slate-400 font-mono'} text-xs">
              👀 ${l.total_clicks} clicks
            </span>
            <button onclick="copyTextToClipboard('${fullUrl}', this)" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white" title="Copy tracking link">
              <i data-lucide="copy" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Failed to load tracer links:', err);
  }
}

async function createManualTracerLink() {
  const compInput = document.getElementById('manual-tracer-company');
  const roleInput = document.getElementById('manual-tracer-role');
  const destSelect = document.getElementById('manual-tracer-dest');

  const company = compInput.value.trim();
  if (!company) {
    if (typeof showToast === 'function') showToast('Please enter a company name', 'error');
    return;
  }

  try {
    const res = await fetch('/api/tracer-links/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company: company,
        role: roleInput.value.trim() || 'Cybersecurity Analyst',
        destination_key: destSelect.value
      })
    });
    const data = await res.json();
    compInput.value = '';
    loadTracerStatsView();
    if (typeof showToast === 'function') showToast(`Generated Tracer Link for ${company}!`, 'success');
  } catch (err) {
    console.error('Error generating link:', err);
  }
}

// ==========================================
// Phase 4: Alert Notifications Center
// ==========================================
async function openAlertCenter() {
  const modal = document.getElementById('alert-center-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  loadAlertsList();
  loadTelegramConfig();
}

function closeAlertCenter() {
  const modal = document.getElementById('alert-center-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function loadAlertsList() {
  const container = document.getElementById('alerts-feed-container');
  if (!container) return;

  try {
    const res = await fetch('/api/alerts');
    const data = await res.json();
    const alerts = data.alerts || [];

    updateAlertBadge(data.unread_count || 0);

    if (alerts.length === 0) {
      container.innerHTML = `
        <div class="py-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
          No alerts yet. When 10+ LPA P1 jobs in Pune/Mumbai are detected, they appear here instantly!
        </div>
      `;
      return;
    }

    container.innerHTML = alerts.map(a => `
      <div class="p-3 rounded-xl bg-slate-900/80 border ${a.is_read ? 'border-slate-800' : 'border-cyan-800/80 bg-cyan-950/20'} space-y-1.5 transition">
        <div class="flex items-start justify-between gap-2">
          <div>
            <div class="text-xs font-bold text-white">${a.title}</div>
            <div class="text-[11px] font-semibold text-cyan-300">${a.company} • ${a.location}</div>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-950 border border-emerald-700 text-emerald-300">
            ${a.salary}
          </span>
        </div>
        <div class="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/60 font-mono">
          <span>${a.created_at}</span>
          <a href="${a.apply_url}" target="_blank" class="text-cyan-400 hover:underline flex items-center space-x-0.5">
            <span>Apply Now</span>
            <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        </div>
      </div>
    `).join('');

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Failed to load alerts:', err);
  }
}

async function markAllAlertsAsRead() {
  try {
    await fetch('/api/alerts/mark-read', { method: 'POST' });
    updateAlertBadge(0);
    loadAlertsList();
    if (typeof showToast === 'function') showToast('Marked all alerts as read', 'info');
  } catch (err) {
    console.error('Error marking alerts read:', err);
  }
}

function updateAlertBadge(count) {
  const badge = document.getElementById('nav-alert-badge');
  if (badge) {
    badge.textContent = count;
    badge.classList.toggle('hidden', count === 0);
  }
}

async function loadTelegramConfig() {
  try {
    const res = await fetch('/api/alerts/config');
    const data = await res.json();
    document.getElementById('tg-bot-token').value = data.telegram_bot_token || '';
    document.getElementById('tg-chat-id').value = data.telegram_chat_id || '';
    document.getElementById('tg-enabled-toggle').checked = !!data.enabled;
  } catch (err) {
    console.error('Error loading TG config:', err);
  }
}

async function saveTelegramSettings() {
  const token = document.getElementById('tg-bot-token').value;
  const chatId = document.getElementById('tg-chat-id').value;
  const enabled = document.getElementById('tg-enabled-toggle').checked;

  try {
    await fetch('/api/alerts/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        telegram_bot_token: token,
        telegram_chat_id: chatId,
        enabled: enabled
      })
    });
    if (typeof showToast === 'function') showToast('Alert settings saved successfully!', 'success');
  } catch (err) {
    console.error('Error saving TG config:', err);
  }
}

async function sendTestAlert() {
  try {
    const res = await fetch('/api/alerts/test', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      if (typeof showToast === 'function') showToast('Test alert dispatched!', 'success');
      loadAlertsList();
    }
  } catch (err) {
    console.error('Error sending test alert:', err);
  }
}

// Helper: copy text
function copyTextToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    if (btnElement) {
      const orig = btnElement.textContent;
      btnElement.textContent = 'Copied!';
      setTimeout(() => btnElement.textContent = orig, 2000);
    }
    if (typeof showToast === 'function') showToast('Copied to clipboard!', 'success');
  });
}

function escapeAttr(text) {
  if (!text) return '';
  return String(text)
    .replace(/'/g, "\\'")
    .replace(/"/g, '&quot;')
    .replace(/\n/g, '\\n');
}

// Dynamic Modal Injection (Keeps index.html lightweight and under 800 lines)
function injectModalsIfMissing() {
  if (document.getElementById('cv-tailor-modal')) return;

  const modalsWrapper = document.createElement('div');
  modalsWrapper.id = 'cv-tools-modals-root';
  modalsWrapper.innerHTML = `
    <!-- CV TAILOR MODAL (PHASE 5) -->
    <div id="cv-tailor-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 hidden items-center justify-center p-3 sm:p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-5 space-y-4 shadow-2xl max-h-[90vh] flex flex-col">
        <div class="flex items-start justify-between pb-3 border-b border-slate-800">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">Anti-Hallucination Tailor</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 border border-emerald-700 text-emerald-300">Phase 5</span>
            </div>
            <h3 class="text-base sm:text-lg font-black text-white mt-0.5" id="tailor-modal-company">Target Company</h3>
            <div class="text-xs text-slate-400 font-mono" id="tailor-modal-role">Cybersecurity Analyst</div>
          </div>
          <button onclick="closeCvTailorModal()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>
        <div class="space-y-4 overflow-y-auto flex-1 pr-1" id="tailor-bullets-container">
          <!-- Populated dynamically -->
        </div>
        <div class="pt-3 border-t border-slate-800 flex justify-end">
          <button onclick="closeCvTailorModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold">
            Done
          </button>
        </div>
      </div>
    </div>

    <!-- TRACER LINKS MANAGER MODAL (PHASE 3) -->
    <div id="tracer-manager-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 hidden items-center justify-center p-3 sm:p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-5 space-y-4 shadow-2xl max-h-[90vh] flex flex-col">
        <div class="flex items-start justify-between pb-3 border-b border-slate-800">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">CV Tracer Engine</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950 border border-purple-700 text-purple-300">Phase 3</span>
            </div>
            <h3 class="text-base sm:text-lg font-black text-white mt-0.5">Resume "Read Receipts" & Tracking</h3>
            <p class="text-[11px] text-slate-400">Notifies you the exact second an HR recruiter opens your LinkedIn or Credly link.</p>
          </div>
          <button onclick="closeTracerModal()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>

        <!-- Quick Generator Strip -->
        <div class="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 space-y-2">
          <div class="text-[11px] font-bold text-slate-300">Generate New CV Tracer Link:</div>
          <div class="grid grid-cols-1 sm:grid-cols-4 gap-2">
            <input type="text" id="manual-tracer-company" placeholder="Company (e.g. Barclays)" class="sm:col-span-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500">
            <input type="hidden" id="manual-tracer-role" value="Cybersecurity Analyst">
            <select id="manual-tracer-dest" class="px-2 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">
              <option value="linkedin">LinkedIn</option>
              <option value="credly">Credly (SC-200)</option>
              <option value="portfolio">GitHub Portfolio</option>
            </select>
            <button onclick="createManualTracerLink()" class="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition">
              + Generate
            </button>
          </div>
        </div>

        <!-- Stats Bar -->
        <div class="grid grid-cols-2 gap-3">
          <div class="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
            <span class="text-xs text-slate-400">Active Tracer Links:</span>
            <span class="text-base font-black font-mono text-cyan-300" id="tracer-stat-active">0</span>
          </div>
          <div class="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
            <span class="text-xs text-slate-400">Total Recruiter Clicks:</span>
            <span class="text-base font-black font-mono text-emerald-400" id="tracer-stat-clicks">0</span>
          </div>
        </div>

        <!-- Links List -->
        <div class="space-y-2 overflow-y-auto flex-1 pr-1" id="tracer-links-list">
          <!-- Populated dynamically -->
        </div>

        <div class="pt-3 border-t border-slate-800 flex justify-end">
          <button onclick="closeTracerModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- ALERTS CENTER MODAL (PHASE 4) -->
    <div id="alert-center-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 hidden items-center justify-center p-3 sm:p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-5 space-y-4 shadow-2xl max-h-[90vh] flex flex-col">
        <div class="flex items-start justify-between pb-3 border-b border-slate-800">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-amber-400 uppercase tracking-wider font-mono">Job Alert Radar</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 border border-amber-700 text-amber-300">Phase 4</span>
            </div>
            <h3 class="text-base sm:text-lg font-black text-white mt-0.5">Instant 10+ LPA Opportunities</h3>
            <p class="text-[11px] text-slate-400">Strictly 2–3 YOE | Direct ATS & GCC verified feeds</p>
          </div>
          <button onclick="closeAlertCenter()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>

        <!-- Telegram Config Accordion -->
        <details class="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 group">
          <summary class="text-xs font-bold text-slate-300 cursor-pointer flex items-center justify-between">
            <span class="flex items-center space-x-1.5">
              <span>✈️ Instant Telegram Alerts Setup</span>
              <span class="text-[10px] text-slate-500 font-normal">(Optional)</span>
            </span>
            <span class="text-[10px] text-cyan-400 group-open:hidden">Configure ▾</span>
          </summary>
          <div class="space-y-2.5 pt-3 border-t border-slate-800/60 mt-2">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div>
                <label class="block text-[10px] text-slate-400 font-semibold mb-1">Bot Token (@BotFather):</label>
                <input type="password" id="tg-bot-token" placeholder="123456:ABC-DEF..." class="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono placeholder-slate-600 focus:outline-none focus:border-cyan-500">
              </div>
              <div>
                <label class="block text-[10px] text-slate-400 font-semibold mb-1">Chat ID (@userinfobot):</label>
                <input type="text" id="tg-chat-id" placeholder="987654321" class="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono placeholder-slate-600 focus:outline-none focus:border-cyan-500">
              </div>
            </div>
            <div class="flex items-center justify-between pt-1">
              <label class="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                <input type="checkbox" id="tg-enabled-toggle" class="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0">
                <span>Enable Telegram push notifications</span>
              </label>
              <div class="flex items-center space-x-2">
                <button onclick="sendTestAlert()" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[10px] font-semibold">
                  Test Push
                </button>
                <button onclick="saveTelegramSettings()" class="px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-[10px] font-bold">
                  Save
                </button>
              </div>
            </div>
          </div>
        </details>

        <!-- Alerts Action Strip -->
        <div class="flex items-center justify-between text-xs pt-1">
          <span class="font-bold text-white">Recent Real-Time Alerts:</span>
          <button onclick="markAllAlertsAsRead()" class="text-[11px] text-cyan-400 hover:underline">
            Mark all read
          </button>
        </div>

        <!-- Feed List -->
        <div class="space-y-2 overflow-y-auto flex-1 pr-1" id="alerts-feed-container">
          <!-- Populated dynamically -->
        </div>

        <div class="pt-3 border-t border-slate-800 flex justify-end">
          <button onclick="closeAlertCenter()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold">
            Close
          </button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modalsWrapper);
  if (window.lucide) lucide.createIcons();
}

// Check alert badge on load & inject modals
window.addEventListener('DOMContentLoaded', () => {
  injectModalsIfMissing();
  fetch('/api/alerts')
    .then(r => r.json())
    .then(data => updateAlertBadge(data.unread_count || 0))
    .catch(() => {});
});
