/**
 * CyberSwitch 10X - Phase 6 (1-Click ATS Autofill) & Phase 7 (Recruiter Email / InMail Auto-Sync)
 */

// ==========================================
// Phase 6: 1-Click ATS Auto-Fill Modal
// ==========================================
async function openAutofillModal() {
  const modal = document.getElementById('autofill-profile-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  if (window.lucide) lucide.createIcons();

  try {
    const [profileRes, bmRes] = await Promise.all([
      fetch('/api/autofill/profile'),
      fetch('/api/autofill/bookmarklet')
    ]);
    const profile = await profileRes.json();
    const bmData = await bmRes.json();

    // Populate profile inputs
    document.getElementById('af-first-name').value = profile.first_name || '';
    document.getElementById('af-last-name').value = profile.last_name || '';
    document.getElementById('af-email').value = profile.email || '';
    document.getElementById('af-phone').value = profile.phone || '';
    document.getElementById('af-city').value = profile.city || '';
    document.getElementById('af-postal').value = profile.postal_code || '';
    document.getElementById('af-current-company').value = profile.current_company || '';
    document.getElementById('af-current-title').value = profile.current_title || '';
    document.getElementById('af-yoe').value = profile.years_experience || '';
    document.getElementById('af-ctc-curr').value = profile.current_ctc || '';
    document.getElementById('af-ctc-exp').value = profile.expected_ctc || '';
    document.getElementById('af-linkedin').value = profile.linkedin_url || '';
    document.getElementById('af-github').value = profile.github_url || '';
    document.getElementById('af-portfolio').value = profile.portfolio_url || '';
    document.getElementById('af-certs').value = profile.certifications || '';
    document.getElementById('af-skills').value = profile.primary_skills || '';

    // Set bookmarklet drag-and-drop link
    const bmLink = document.getElementById('af-bookmarklet-link');
    if (bmLink && bmData.bookmarklet) {
      bmLink.href = bmData.bookmarklet;
      bmLink.setAttribute('data-code', bmData.bookmarklet);
    }
  } catch (err) {
    console.error('Failed to load profile:', err);
  }
}

function closeAutofillModal() {
  const modal = document.getElementById('autofill-profile-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function saveAutofillProfile() {
  const saveBtn = document.getElementById('af-save-btn');
  const originalText = saveBtn.textContent;
  saveBtn.disabled = true;
  saveBtn.textContent = 'Saving...';

  const profile = {
    first_name: document.getElementById('af-first-name').value,
    last_name: document.getElementById('af-last-name').value,
    full_name: `${document.getElementById('af-first-name').value} ${document.getElementById('af-last-name').value}`.trim(),
    email: document.getElementById('af-email').value,
    phone: document.getElementById('af-phone').value,
    city: document.getElementById('af-city').value,
    postal_code: document.getElementById('af-postal').value,
    current_company: document.getElementById('af-current-company').value,
    current_title: document.getElementById('af-current-title').value,
    years_experience: document.getElementById('af-yoe').value,
    current_ctc: document.getElementById('af-ctc-curr').value,
    expected_ctc: document.getElementById('af-ctc-exp').value,
    linkedin_url: document.getElementById('af-linkedin').value,
    github_url: document.getElementById('af-github').value,
    portfolio_url: document.getElementById('af-portfolio').value,
    certifications: document.getElementById('af-certs').value,
    primary_skills: document.getElementById('af-skills').value
  };

  try {
    const res = await fetch('/api/autofill/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile)
    });
    if (res.ok) {
      saveBtn.textContent = 'Saved!';
      setTimeout(() => {
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
      }, 1500);
    }
  } catch (err) {
    alert('Failed to save profile: ' + err);
    saveBtn.textContent = originalText;
    saveBtn.disabled = false;
  }
}

function copyBookmarkletCode() {
  const bmLink = document.getElementById('af-bookmarklet-link');
  const code = bmLink ? bmLink.getAttribute('data-code') : '';
  if (code) {
    navigator.clipboard.writeText(code).then(() => {
      alert('⚡ Bookmarklet code copied to clipboard! You can paste it into a new browser bookmark.');
    });
  }
}

// ==========================================
// Phase 7: Recruiter Email / InMail Sync Modal
// ==========================================
async function openEmailSyncModal() {
  const modal = document.getElementById('email-sync-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  if (window.lucide) lucide.createIcons();

  loadRecentEmailFeed();
  loadEmailConfig();
}

function closeEmailSyncModal() {
  const modal = document.getElementById('email-sync-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function parseAndSyncMessage() {
  const text = document.getElementById('eml-raw-text').value.trim();
  const sender = document.getElementById('eml-sender-input').value.trim();
  const resultContainer = document.getElementById('eml-parse-result');

  if (!text) {
    alert('Please paste the email or recruiter message text.');
    return;
  }

  resultContainer.innerHTML = `
    <div class="p-3 text-center text-xs text-slate-400 flex items-center justify-center space-x-2">
      <i data-lucide="loader-2" class="w-4 h-4 animate-spin text-purple-400"></i>
      <span>Analyzing recruiter linguistics & matching Kanban tracker...</span>
    </div>
  `;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch('/api/email-sync/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: text, sender_email: sender })
    });
    const data = await res.json();
    const ev = data.event;

    const stageColors = {
      technical: 'bg-purple-950 border-purple-700 text-purple-300',
      screening: 'bg-cyan-950 border-cyan-700 text-cyan-300',
      managerial: 'bg-amber-950 border-amber-700 text-amber-300',
      offer: 'bg-emerald-950 border-emerald-700 text-emerald-300 font-bold',
      rejected: 'bg-rose-950 border-rose-700 text-rose-300'
    };
    const badgeClass = stageColors[ev.detected_stage] || 'bg-slate-800 text-slate-300';

    resultContainer.innerHTML = `
      <div class="p-3.5 rounded-xl bg-slate-950/80 border border-purple-500/40 space-y-2.5">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="text-xs font-bold text-white">${ev.company}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${badgeClass}">
              ${ev.detected_stage}
            </span>
          </div>
          <span class="text-[10px] text-slate-400 font-mono">${ev.timestamp}</span>
        </div>

        ${ev.meeting_link ? `
          <div class="p-2 rounded-lg bg-purple-950/40 border border-purple-800/60 flex items-center justify-between text-xs">
            <span class="text-purple-300 font-semibold truncate flex items-center space-x-1.5">
              <span>📹 Meeting Detected:</span>
            </span>
            <a href="${ev.meeting_link}" target="_blank" class="px-2.5 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white font-bold text-[10px] transition">
              Open Interview Link ↗
            </a>
          </div>
        ` : ''}

        <div class="text-[11px] ${ev.applied_to_tracker ? 'text-emerald-400' : 'text-slate-400'} flex items-center space-x-1">
          <span>${ev.applied_to_tracker ? '✅ Automatically moved ' + ev.company + ' Kanban card to ' + ev.detected_stage.toUpperCase() : 'ℹ️ Saved to history. (Job not currently tracked on Kanban)'}</span>
        </div>
      </div>
    `;

    document.getElementById('eml-raw-text').value = '';
    loadRecentEmailFeed();
    if (window.fetchKanbanBoard) window.fetchKanbanBoard();
  } catch (err) {
    resultContainer.innerHTML = `<div class="p-3 bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">Sync failed: ${err}</div>`;
  }
}

async function loadRecentEmailFeed() {
  const container = document.getElementById('eml-feed-list');
  if (!container) return;

  try {
    const res = await fetch('/api/email-sync/feed');
    const data = await res.json();
    const events = data.events || [];

    if (events.length === 0) {
      container.innerHTML = `<div class="py-4 text-center text-slate-500 text-xs">No recruiter emails parsed yet. Paste your first invite above!</div>`;
      return;
    }

    container.innerHTML = events.map(ev => `
      <div class="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition space-y-1">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-white">${ev.company}</span>
          <span class="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">${ev.detected_stage}</span>
        </div>
        <p class="text-[11px] text-slate-400 line-clamp-2">${ev.snippet}</p>
        <div class="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-0.5">
          <span>${ev.sender}</span>
          <span>${ev.timestamp}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading email feed:', err);
  }
}

async function loadEmailConfig() {
  try {
    const res = await fetch('/api/email-sync/config');
    const cfg = await res.json();
    document.getElementById('eml-cfg-address').value = cfg.email_address || '';
    document.getElementById('eml-cfg-password').value = cfg.app_password || '';
    document.getElementById('eml-cfg-enabled').checked = !!cfg.enabled;
  } catch (err) {
    console.error('Error loading config:', err);
  }
}

async function saveEmailConfig() {
  const payload = {
    email_address: document.getElementById('eml-cfg-address').value.trim(),
    app_password: document.getElementById('eml-cfg-password').value.trim(),
    enabled: document.getElementById('eml-cfg-enabled').checked
  };
  try {
    const res = await fetch('/api/email-sync/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) alert('Gmail IMAP settings saved!');
  } catch (err) {
    alert('Failed to save email settings: ' + err);
  }
}

async function triggerManualImapSync() {
  const btn = document.getElementById('eml-imap-sync-btn');
  btn.textContent = 'Syncing...';
  btn.disabled = true;
  try {
    const res = await fetch('/api/email-sync/trigger-imap', { method: 'POST' });
    const data = await res.json();
    alert(`IMAP Sync Result: ${data.message || (data.synced_messages + ' messages parsed')}`);
    loadRecentEmailFeed();
  } catch (err) {
    alert('IMAP Sync failed: ' + err);
  } finally {
    btn.textContent = 'Sync Inbox Now';
    btn.disabled = false;
  }
}

// ==========================================
// Inject Modals into DOM
// ==========================================
function injectAutofillAndEmailModals() {
  if (document.getElementById('autofill-profile-modal')) return;

  const wrapper = document.createElement('div');
  wrapper.id = 'phases-6-7-modals-wrapper';
  wrapper.innerHTML = `
    <!-- PHASE 6: CANDIDATE PROFILE & ATS AUTOFILL MODAL -->
    <div id="autofill-profile-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 hidden items-center justify-center p-3 sm:p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full p-5 space-y-4 shadow-2xl max-h-[92vh] flex flex-col">
        <div class="flex items-start justify-between pb-3 border-b border-slate-800">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">ATS Fast-Lane</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950 border border-cyan-700 text-cyan-300">Phase 6</span>
            </div>
            <h3 class="text-base sm:text-lg font-black text-white mt-0.5">1-Click ATS Auto-Fill Engine</h3>
            <p class="text-[11px] text-slate-400">Instantly fills Workday, Greenhouse & Lever portals for Gourav Pandit Parit</p>
          </div>
          <button onclick="closeAutofillModal()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>

        <!-- 1-Click Fast-Lane Activation Strip -->
        <div class="p-3.5 rounded-xl bg-gradient-to-r from-cyan-950/60 to-purple-950/60 border border-cyan-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="space-y-0.5">
            <span class="text-xs font-bold text-white flex items-center space-x-1.5">
              <span>⚡ 1-Click Browser Bookmarklet</span>
              <span class="px-1.5 py-0.2 rounded text-[9px] bg-emerald-950 border border-emerald-700 text-emerald-300">Zero-Install</span>
            </span>
            <p class="text-[11px] text-slate-300">Drag this button to your browser Bookmarks Bar. When on Workday, click it to auto-fill!</p>
          </div>
          <div class="flex items-center space-x-2 flex-shrink-0">
            <a id="af-bookmarklet-link" href="#" class="px-3.5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-black text-xs shadow-lg transition flex items-center space-x-1.5 cursor-grab">
              <span>⚡ Drag: Fill ATS</span>
            </a>
            <button onclick="copyBookmarkletCode()" class="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition">
              Copy Code
            </button>
          </div>
        </div>

        <!-- Candidate Profile Form -->
        <div class="space-y-3 overflow-y-auto flex-1 pr-1">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">First Name</label>
              <input type="text" id="af-first-name" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500">
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Last Name</label>
              <input type="text" id="af-last-name" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500">
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Email Address</label>
              <input type="email" id="af-email" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono">
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Phone Number</label>
              <input type="tel" id="af-phone" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono">
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">City / Location</label>
              <input type="text" id="af-city" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500">
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Postal Code</label>
              <input type="text" id="af-postal" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono">
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Current Company</label>
              <input type="text" id="af-current-company" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500">
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Current Job Title</label>
              <input type="text" id="af-current-title" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500">
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-400 mb-1">Years of Experience</label>
              <input type="text" id="af-yoe" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono">
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] font-semibold text-slate-400 mb-1">Current CTC</label>
                <input type="text" id="af-ctc-curr" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono">
              </div>
              <div>
                <label class="block text-[11px] font-semibold text-slate-400 mb-1">Target CTC</label>
                <input type="text" id="af-ctc-exp" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-emerald-400 focus:outline-none focus:border-cyan-500 font-mono font-bold">
              </div>
            </div>
          </div>

          <div>
            <label class="block text-[11px] font-semibold text-slate-400 mb-1">Certifications</label>
            <input type="text" id="af-certs" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-cyan-300 font-mono focus:outline-none focus:border-cyan-500">
          </div>

          <div>
            <label class="block text-[11px] font-semibold text-slate-400 mb-1">Primary Cybersecurity Skills</label>
            <input type="text" id="af-skills" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div>
              <label class="block text-[10px] text-slate-400 mb-1">LinkedIn URL</label>
              <input type="url" id="af-linkedin" class="w-full px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-300 font-mono focus:outline-none">
            </div>
            <div>
              <label class="block text-[10px] text-slate-400 mb-1">GitHub URL</label>
              <input type="url" id="af-github" class="w-full px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-300 font-mono focus:outline-none">
            </div>
            <div>
              <label class="block text-[10px] text-slate-400 mb-1">Credly / Portfolio URL</label>
              <input type="url" id="af-portfolio" class="w-full px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-300 font-mono focus:outline-none">
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-slate-800 flex items-center justify-between">
          <span class="text-[10px] text-slate-500 font-mono">Chrome Extension unpacked folder: /static/extension</span>
          <div class="flex items-center space-x-2">
            <button onclick="closeAutofillModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold">Close</button>
            <button onclick="saveAutofillProfile()" id="af-save-btn" class="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-lg">Save Profile</button>
          </div>
        </div>
      </div>
    </div>

    <!-- PHASE 7: RECRUITER EMAIL / INMAIL AUTO-SYNC MODAL -->
    <div id="email-sync-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 hidden items-center justify-center p-3 sm:p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-5 space-y-4 shadow-2xl max-h-[92vh] flex flex-col">
        <div class="flex items-start justify-between pb-3 border-b border-slate-800">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-purple-400 uppercase tracking-wider font-mono">Recruiter Sync</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950 border border-purple-700 text-purple-300">Phase 7</span>
            </div>
            <h3 class="text-base sm:text-lg font-black text-white mt-0.5">Interview & Rejection Auto-Sync</h3>
            <p class="text-[11px] text-slate-400">Classifies incoming messages and automatically moves cards on your Kanban board</p>
          </div>
          <button onclick="closeEmailSyncModal()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>

        <!-- Quick Paste Parser -->
        <div class="space-y-2.5">
          <div>
            <label class="block text-[11px] font-semibold text-slate-300 mb-1">Paste Recruiter Email / LinkedIn InMail / Offer Letter:</label>
            <textarea id="eml-raw-text" rows="3" placeholder="e.g. Hi Gourav, we would like to invite you for a Technical Round on Microsoft Sentinel via Teams: https://teams.microsoft.com/..." class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-purple-500"></textarea>
          </div>
          <div class="flex items-center space-x-2">
            <input type="text" id="eml-sender-input" placeholder="Sender (e.g. recruiter@barclays.com or InMail)" class="flex-1 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono placeholder-slate-600 focus:outline-none focus:border-purple-500">
            <button onclick="parseAndSyncMessage()" class="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition shadow-lg flex-shrink-0 flex items-center space-x-1.5">
              <span>⚡ Sync with Kanban</span>
            </button>
          </div>
        </div>

        <!-- Parse Result Area -->
        <div id="eml-parse-result"></div>

        <!-- IMAP Accordion -->
        <details class="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 group">
          <summary class="text-xs font-bold text-slate-300 cursor-pointer flex items-center justify-between">
            <span>⚙️ Automated Gmail IMAP Inbox Sync</span>
            <span class="text-[10px] text-purple-400 group-open:hidden">Configure ▾</span>
          </summary>
          <div class="space-y-2.5 pt-3 border-t border-slate-800/60 mt-2">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div>
                <label class="block text-[10px] text-slate-400 font-semibold mb-1">Gmail Address:</label>
                <input type="email" id="eml-cfg-address" placeholder="your.name@gmail.com" class="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono focus:outline-none">
              </div>
              <div>
                <label class="block text-[10px] text-slate-400 font-semibold mb-1">App Password (16-digit):</label>
                <input type="password" id="eml-cfg-password" placeholder="xxxx xxxx xxxx xxxx" class="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white font-mono focus:outline-none">
              </div>
            </div>
            <div class="flex items-center justify-between pt-1">
              <label class="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                <input type="checkbox" id="eml-cfg-enabled" class="rounded bg-slate-800 border-slate-700 text-purple-500 focus:ring-0">
                <span>Enable automatic IMAP inbox polling</span>
              </label>
              <div class="flex items-center space-x-2">
                <button onclick="triggerManualImapSync()" id="eml-imap-sync-btn" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-semibold">
                  Sync Inbox Now
                </button>
                <button onclick="saveEmailConfig()" class="px-3 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white text-[10px] font-bold">
                  Save Settings
                </button>
              </div>
            </div>
          </div>
        </details>

        <!-- Feed History -->
        <div class="space-y-2 flex-1 overflow-y-auto pr-1">
          <span class="text-xs font-bold text-white block">Recent Recruiter Signals:</span>
          <div id="eml-feed-list" class="space-y-1.5">
            <!-- Populated dynamically -->
          </div>
        </div>

        <div class="pt-3 border-t border-slate-800 flex justify-end">
          <button onclick="closeEmailSyncModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold">
            Close
          </button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(wrapper);
  if (window.lucide) lucide.createIcons();
}

window.addEventListener('DOMContentLoaded', () => {
  injectAutofillAndEmailModals();
});
