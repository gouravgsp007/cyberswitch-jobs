/**
 * CyberSwitch 10X - Application Kanban Tracker Engine
 * Real-time tracking from Wishlist to 10+ LPA Offer
 */

const KANBAN_STAGES = [
  { id: 'wishlist', title: '🎯 Wishlist / Target', border: 'border-slate-700', badge: 'bg-slate-800 text-slate-300' },
  { id: 'applied', title: '📨 Applied / Referred', border: 'border-cyan-800/80', badge: 'bg-cyan-950 text-cyan-300' },
  { id: 'screening', title: '📞 HR Screening', border: 'border-blue-800/80', badge: 'bg-blue-950 text-blue-300' },
  { id: 'technical', title: '💻 Technical L2 Drill', border: 'border-purple-800/80', badge: 'bg-purple-950 text-purple-300' },
  { id: 'managerial', title: '👔 Managerial Round', border: 'border-amber-800/80', badge: 'bg-amber-950 text-amber-300' },
  { id: 'offer', title: '🎉 10+ LPA Offer', border: 'border-emerald-600', badge: 'bg-emerald-950 text-emerald-300' }
];

let trackerCache = {
  total_tracked: 0,
  stage_counts: {},
  items: []
};

let activeNoteEditId = null;

// Tab switcher
function switchMainView(viewName) {
  const radarView = document.getElementById('view-radar');
  const trackerView = document.getElementById('view-tracker');
  const btnRadar = document.getElementById('tab-btn-radar');
  const btnTracker = document.getElementById('tab-btn-tracker');

  if (viewName === 'tracker') {
    radarView.classList.add('hidden');
    trackerView.classList.remove('hidden');
    btnTracker.classList.remove('bg-transparent', 'text-slate-400');
    btnTracker.classList.add('bg-cyan-600', 'text-white', 'shadow-lg');
    btnRadar.classList.remove('bg-cyan-600', 'text-white', 'shadow-lg');
    btnRadar.classList.add('bg-transparent', 'text-slate-400');
    loadTrackerData();
  } else {
    trackerView.classList.add('hidden');
    radarView.classList.remove('hidden');
    btnRadar.classList.remove('bg-transparent', 'text-slate-400');
    btnRadar.classList.add('bg-cyan-600', 'text-white', 'shadow-lg');
    btnTracker.classList.remove('bg-cyan-600', 'text-white', 'shadow-lg');
    btnTracker.classList.add('bg-transparent', 'text-slate-400');
  }
}

// Fetch tracker data
async function loadTrackerData() {
  try {
    const res = await fetch('/api/tracker');
    const data = await res.json();
    trackerCache = data;
    renderKanbanBoard(data);
    updateTrackerBadge(data.total_tracked);
  } catch (err) {
    console.error('Error fetching tracker items:', err);
  }
}

function updateTrackerBadge(count) {
  const badge = document.getElementById('nav-tracker-count');
  if (badge) {
    badge.textContent = count;
    badge.classList.toggle('hidden', count === 0);
  }
}

// Render Kanban board columns
function renderKanbanBoard(data) {
  const container = document.getElementById('kanban-board-container');
  if (!container) return;

  const items = data.items || [];
  const counts = data.stage_counts || {};

  // Update summary header stats
  document.getElementById('trk-stat-total').textContent = data.total_tracked || 0;
  document.getElementById('trk-stat-applied').textContent = counts['applied'] || 0;
  document.getElementById('trk-stat-interviews').textContent = (counts['screening'] || 0) + (counts['technical'] || 0) + (counts['managerial'] || 0);
  document.getElementById('trk-stat-offers').textContent = counts['offer'] || 0;

  container.innerHTML = KANBAN_STAGES.map(stage => {
    const stageItems = items.filter(it => it.stage === stage.id);
    return `
      <div class="flex-shrink-0 w-80 bg-slate-900/60 rounded-2xl border ${stage.border} p-3 flex flex-col max-h-[80vh]">
        <!-- Column Header -->
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div class="flex items-center space-x-2">
            <h4 class="text-xs font-bold text-white tracking-wide">${stage.title}</h4>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${stage.badge}">
              ${stageItems.length}
            </span>
          </div>
        </div>

        <!-- Cards List -->
        <div class="space-y-3 pt-3 overflow-y-auto flex-1 pr-1" id="column-${stage.id}">
          ${stageItems.length === 0 ? `
            <div class="py-8 text-center text-slate-500 text-xs border border-dashed border-slate-800/80 rounded-xl">
              No applications here yet
            </div>
          ` : stageItems.map(item => renderKanbanCard(item, stage.id)).join('')}
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function renderKanbanCard(item, currentStageId) {
  const ghostBadge = (item.ghost_job_risk === 'Low Risk') 
    ? '<span class="px-1.5 py-0.5 rounded text-[9px] bg-emerald-950/80 border border-emerald-800 text-emerald-300 font-mono">🟢 Fresh Requisition</span>'
    : (item.ghost_job_risk === 'Moderate Risk')
    ? '<span class="px-1.5 py-0.5 rounded text-[9px] bg-amber-950/80 border border-amber-800 text-amber-300 font-mono">🟡 Moderate Age</span>'
    : '<span class="px-1.5 py-0.5 rounded text-[9px] bg-rose-950/80 border border-rose-800 text-rose-300 font-mono">⚠️ Stale (>35d)</span>';

  const stagesOptions = KANBAN_STAGES.map(s => 
    `<option value="${s.id}" ${s.id === currentStageId ? 'selected' : ''}>Move to: ${s.title}</option>`
  ).join('');

  return `
    <div class="bg-[#0f172a] hover:bg-[#131d35] border border-slate-800/90 rounded-xl p-3.5 space-y-2.5 shadow-md transition group" id="card-${item.id}">
      <!-- Top Badges -->
      <div class="flex items-start justify-between gap-1.5">
        <span class="text-[10px] font-bold text-cyan-400 truncate tracking-wide uppercase">${escapeHtml(item.company)}</span>
        <div class="flex items-center space-x-1 flex-shrink-0">
          ${ghostBadge}
          <button onclick="deleteTrackerItem('${item.id}')" title="Delete from tracker" class="text-slate-500 hover:text-rose-400 p-0.5 transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>

      <!-- Job Title -->
      <div>
        <h5 class="text-xs font-bold text-white leading-tight group-hover:text-cyan-200 transition">
          ${escapeHtml(item.title)}
        </h5>
        <div class="flex items-center justify-between text-[10px] text-slate-400 pt-1 font-mono">
          <span>📍 ${escapeHtml(item.location || 'Pune / Mumbai')}</span>
          <span class="text-emerald-400 font-semibold">${escapeHtml(item.salary || '10+ LPA')}</span>
        </div>
      </div>

      <!-- Notes / Referral Preview -->
      <div class="bg-slate-950/70 rounded-lg p-2 border border-slate-800/70 text-[11px] text-slate-300 space-y-1">
        <div class="flex items-center justify-between text-[10px] text-slate-400">
          <span class="font-semibold text-slate-300">Notes & Referral:</span>
          <button onclick="openNoteEditor('${item.id}')" class="text-cyan-400 hover:underline">
            Edit
          </button>
        </div>
        <p class="text-[10px] text-slate-300 line-clamp-2">${escapeHtml(item.notes || 'No notes yet. Click edit to add referral contact or interview date.')}</p>
        ${item.referral_contact ? `<div class="text-[10px] text-purple-300 font-mono">👤 Ref: ${escapeHtml(item.referral_contact)}</div>` : ''}
      </div>

      <!-- Footer Actions -->
      <div class="pt-1 flex items-center justify-between gap-2 border-t border-slate-800/60">
        <select onchange="changeJobStage('${item.id}', this.value)" class="bg-slate-900 border border-slate-700/80 text-[10px] text-slate-200 rounded px-2 py-1 focus:outline-none focus:border-cyan-500 font-mono">
          ${stagesOptions}
        </select>

        ${item.apply_url ? `
          <a href="${item.apply_url}" target="_blank" class="px-2.5 py-1 rounded bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 text-[10px] font-semibold flex items-center space-x-1 transition flex-shrink-0">
            <span>Apply</span>
            <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        ` : ''}
      </div>
    </div>
  `;
}

// Add Job to Tracker (Called from Main Radar View)
async function addJobToTracker(jobObj, initialStage = 'wishlist') {
  try {
    const res = await fetch('/api/tracker/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job: jobObj,
        stage: initialStage
      })
    });
    const result = await res.json();
    if (result.status === 'success') {
      showToast(`Added to Tracker: ${jobObj.company} (${jobObj.title})`, 'success');
      loadTrackerData();
    } else if (result.status === 'exists') {
      showToast(`${jobObj.company} is already on your tracking board`, 'info');
    }
  } catch (err) {
    console.error('Error adding to tracker:', err);
    showToast('Failed to add job to tracker', 'error');
  }
}

// Change Stage
async function changeJobStage(trackId, newStage) {
  try {
    const res = await fetch('/api/tracker/update-stage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: trackId,
        stage: newStage
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(`Moved to ${newStage.toUpperCase()}!`, 'success');
      loadTrackerData();
    }
  } catch (err) {
    console.error('Error updating stage:', err);
    showToast('Could not update stage', 'error');
  }
}

// Open Note Modal
function openNoteEditor(trackId) {
  activeNoteEditId = trackId;
  const item = (trackerCache.items || []).find(it => it.id === trackId) || {};

  document.getElementById('edit-note-textarea').value = item.notes || '';
  document.getElementById('edit-note-ref').value = item.referral_contact || '';
  document.getElementById('note-modal').classList.remove('hidden');
  document.getElementById('note-modal').classList.add('flex');
}

function closeNoteEditor() {
  activeNoteEditId = null;
  document.getElementById('note-modal').classList.add('hidden');
  document.getElementById('note-modal').classList.remove('flex');
}

async function saveNoteEditor() {
  if (!activeNoteEditId) return;
  const notes = document.getElementById('edit-note-textarea').value;
  const ref = document.getElementById('edit-note-ref').value;

  try {
    const res = await fetch('/api/tracker/update-notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: activeNoteEditId,
        notes: notes,
        referral_contact: ref
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('Notes updated successfully!', 'success');
      closeNoteEditor();
      loadTrackerData();
    }
  } catch (err) {
    console.error('Error saving notes:', err);
    showToast('Failed to save notes', 'error');
  }
}

// Delete item
async function deleteTrackerItem(trackId) {
  if (!confirm('Remove this application from your tracker?')) return;
  try {
    const res = await fetch(`/api/tracker/${trackId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('Application removed from tracker', 'info');
      loadTrackerData();
    }
  } catch (err) {
    console.error('Error deleting item:', err);
  }
}

// Toast notification helper
function showToast(message, type = 'success') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed bottom-4 right-4 z-50 flex flex-col space-y-2 pointer-events-none';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bg = type === 'success' ? 'bg-emerald-950 border-emerald-600 text-emerald-200' 
           : type === 'error' ? 'bg-rose-950 border-rose-600 text-rose-200'
           : 'bg-slate-900 border-cyan-600 text-cyan-200';

  toast.className = `px-4 py-2.5 rounded-xl border shadow-2xl text-xs font-semibold flex items-center space-x-2 transition-all duration-300 transform translate-y-2 pointer-events-auto ${bg}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-4');
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function trackJobBySlNo(slNo) {
  if (typeof allJobs !== 'undefined' && Array.isArray(allJobs)) {
    const job = allJobs.find(x => x.sl_no === slNo);
    if (job) {
      addJobToTracker(job);
      return;
    }
  }
  showToast('Could not find job to track', 'error');
}

function renderGhostJobBadge(j) {
  const risk = (j.ghost_job_risk || '').toLowerCase();
  const note = escapeHtml(j.ghost_job_note || '');
  if (risk.includes('high')) {
    return `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950/90 border border-rose-700 text-rose-300 ml-1.5 whitespace-nowrap" title="${note || 'Stale Requisition (>35d)'}">⚠️ Stale (>35d)</span>`;
  } else if (risk.includes('moderate')) {
    return `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-950/80 border border-amber-800 text-amber-300 ml-1.5 whitespace-nowrap" title="${note || 'Open >14d'}">⏳ Open &gt;14d</span>`;
  } else {
    const isDirect = (j.source || '').toLowerCase().includes('ats') || (j.source || '').toLowerCase().includes('workday') || (j.source || '').toLowerCase().includes('greenhouse');
    if (isDirect) {
      return `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950/90 border border-emerald-700 text-emerald-300 ml-1.5 whitespace-nowrap" title="${note || 'Direct Enterprise ATS Requisition'}">🟢 Direct ATS</span>`;
    }
    return `<span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-950/60 border border-emerald-800/80 text-emerald-400 ml-1.5 whitespace-nowrap" title="${note || 'Active Requisition'}">🟢 Active</span>`;
  }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  loadTrackerData();
});
