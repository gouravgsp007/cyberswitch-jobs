/**
 * CyberSwitch 10X - Phase 8 (Salary Intelligence & Negotiation) & Phase 9 (Interview Co-Pilot)
 */

// ==========================================
// Phase 8: Salary Negotiation & Benchmarks
// ==========================================
async function openSalaryIntelModal() {
  const modal = document.getElementById('salary-intel-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  if (window.lucide) lucide.createIcons();

  loadSalaryBenchmarks();
  calculateCtcLive();
}

function closeSalaryIntelModal() {
  const modal = document.getElementById('salary-intel-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

async function loadSalaryBenchmarks() {
  const container = document.getElementById('sal-benchmarks-tbody');
  if (!container) return;

  try {
    const res = await fetch('/api/salary-intel/benchmarks');
    const data = await res.json();
    const list = data.benchmarks || [];

    container.innerHTML = list.map(b => `
      <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 text-xs transition">
        <td class="py-2.5 px-3 font-bold text-white">${b.company}</td>
        <td class="py-2.5 px-3 text-slate-300">${b.location}</td>
        <td class="py-2.5 px-3 font-mono text-emerald-400 font-semibold">₹${b.min_ctc_lpa} - ₹${b.max_ctc_lpa} LPA</td>
        <td class="py-2.5 px-3 font-mono text-cyan-300 font-bold">₹${b.median_ctc_lpa} LPA</td>
        <td class="py-2.5 px-3 text-slate-400">${b.joining_bonus_typical}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load benchmarks:', err);
  }
}

async function calculateCtcLive() {
  const inputEl = document.getElementById('sal-target-input');
  const targetLpa = parseFloat(inputEl.value) || 13.5;

  try {
    const res = await fetch(`/api/salary-intel/calculate?target_lpa=${targetLpa}`);
    const data = await res.json();
    const b = data.breakdown;

    document.getElementById('sal-disp-target').textContent = `₹${b.target_ctc_lpa} LPA`;
    document.getElementById('sal-disp-hike').textContent = `+${b.hike_over_4lpa_pct}% over 4 LPA`;
    document.getElementById('sal-disp-fixed').textContent = `₹${b.fixed_lpa} LPA`;
    document.getElementById('sal-disp-variable').textContent = `₹${b.variable_lpa} LPA`;
    document.getElementById('sal-disp-inhand').textContent = `~₹${Math.round(b.estimated_inhand_monthly_inr).toLocaleString('en-IN')}/mo`;
    document.getElementById('sal-disp-gross').textContent = `₹${Math.round(b.monthly_gross_inr).toLocaleString('en-IN')}`;
  } catch (err) {
    console.error('CTC calc error:', err);
  }
}

function copyNegotiationScript(idx) {
  const scriptMap = {
    1: `I completely understand that standard HR policies work with 30-40% increments for lateral movements within IT services. However, my entry compensation of 4 LPA at Wipro reflected a campus trainee baseline. Over the past 2.5 years, I have been operating as an independent SOC L2 analyst managing tier-1 incidents, building production KQL hunting rules in Microsoft Sentinel, and administrating Palo Alto NGFW policies across Panorama.\n\nThe market rate for an SC-200 certified SOC L2 professional handling these responsibilities in Pune/Mumbai GCCs is established between 11 and 14 LPA. My goal is to align with the market valuation of this specific role and the immediate value I contribute from Day 1 rather than my campus joining baseline.`,
    2: `My current fixed compensation at Wipro is 4.0 LPA with a standard 30-day notice period. For this role, based on the job description requirements for Microsoft Sentinel, Palo Alto NGFW, and SOC L2 triage, I am targeting a band of 12 to 14 LPA, which aligns with market benchmarks for this tier of responsibility in Pune. Is that within your budgeted band for this requisition?`,
    3: `Thank you so much for the offer! I am genuinely excited about the role and the chance to contribute to the global SOC team. Regarding the compensation structure: while 8.5 LPA is an increase over my Wipro base, it falls below the budgeted 12-14 LPA band we discussed for this L2 position. If we can adjust the fixed base to 11.5 LPA (or bridge with a ₹1.5L joining bonus), I am prepared to sign and accept the offer today and initiate my formal resignation tomorrow morning.`
  };
  const text = scriptMap[idx] || '';
  navigator.clipboard.writeText(text).then(() => {
    alert('🎯 Negotiation script copied to clipboard! Practice saying it with steady confidence.');
  });
}

// ==========================================
// Phase 9: Interview Co-Pilot & KQL Sandbox
// ==========================================
async function openInterviewCopilotModal() {
  const modal = document.getElementById('interview-copilot-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  if (window.lucide) lucide.createIcons();

  loadKqlCheatsheet();
  loadPaloAltoTroubleshooting();
  loadInterviewQa();
}

function closeInterviewCopilotModal() {
  const modal = document.getElementById('interview-copilot-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function switchCopilotTab(tabName) {
  ['kql', 'paloalto', 'qa'].forEach(t => {
    const pane = document.getElementById(`copilot-pane-${t}`);
    const btn = document.getElementById(`copilot-btn-${t}`);
    if (pane) pane.classList.toggle('hidden', t !== tabName);
    if (btn) {
      if (t === tabName) {
        btn.classList.add('bg-cyan-600', 'text-white');
        btn.classList.remove('text-slate-400', 'hover:text-white');
      } else {
        btn.classList.remove('bg-cyan-600', 'text-white');
        btn.classList.add('text-slate-400', 'hover:text-white');
      }
    }
  });
}

async function loadKqlCheatsheet() {
  const container = document.getElementById('copilot-kql-list');
  if (!container) return;

  try {
    const res = await fetch('/api/interview-copilot/kql');
    const data = await res.json();
    const queries = data.queries || [];

    container.innerHTML = queries.map((q, idx) => `
      <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-white flex items-center space-x-1.5">
            <span class="px-2 py-0.5 rounded text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800 font-mono">SC-200 / Sentinel</span>
            <span>${q.title}</span>
          </span>
          <button onclick="copySnippet('kql-code-${idx}')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-semibold text-slate-300 transition">
            Copy KQL
          </button>
        </div>
        <p class="text-[11px] text-slate-400">${q.description}</p>
        <pre id="kql-code-${idx}" class="p-3 rounded-lg bg-slate-900 text-cyan-300 font-mono text-[11px] overflow-x-auto border border-slate-800">${q.kql}</pre>
        <div class="p-2 rounded bg-cyan-950/40 border border-cyan-900/60 text-[11px] text-cyan-200">
          <strong>💡 Interviewer Talking Point:</strong> ${q.talking_points}
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load KQL:', err);
  }
}

async function loadPaloAltoTroubleshooting() {
  const container = document.getElementById('copilot-pa-list');
  if (!container) return;

  try {
    const res = await fetch('/api/interview-copilot/palo-alto');
    const data = await res.json();
    const topics = data.topics || [];

    container.innerHTML = topics.map((t, idx) => `
      <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-white flex items-center space-x-1.5">
            <span class="px-2 py-0.5 rounded text-[10px] bg-purple-950 text-purple-300 border border-purple-800 font-mono">PAN-OS / Panorama</span>
            <span>${t.topic}</span>
          </span>
          <button onclick="copySnippet('pa-cmd-${idx}')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-semibold text-slate-300 transition">
            Copy CLI
          </button>
        </div>
        <pre id="pa-cmd-${idx}" class="p-2.5 rounded-lg bg-slate-900 text-purple-300 font-mono text-[11px] overflow-x-auto border border-slate-800">${t.command}</pre>
        <div class="p-2.5 rounded bg-slate-900/80 border border-slate-800 text-[11px] text-slate-300">
          <strong>Key Engineering Concept:</strong> ${t.key_concepts}
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load Palo Alto:', err);
  }
}

async function loadInterviewQa() {
  const container = document.getElementById('copilot-qa-list');
  if (!container) return;

  try {
    const res = await fetch('/api/interview-copilot/qa');
    const data = await res.json();
    const questions = data.questions || [];

    container.innerHTML = questions.map((q, idx) => `
      <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5">
        <div class="flex items-start justify-between gap-2">
          <h5 class="text-xs font-bold text-white">Q: ${q.question}</h5>
          <button onclick="copySnippet('qa-star-${idx}')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-semibold text-slate-300 transition flex-shrink-0">
            Copy STAR Story
          </button>
        </div>
        <div class="text-[10px] text-amber-400 font-mono">Expected Framework: ${q.expected_answer_framework}</div>
        <div id="qa-star-${idx}" class="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300 leading-relaxed italic">
          ${q.star_response}
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load QA:', err);
  }
}

function copySnippet(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.textContent.trim();
  navigator.clipboard.writeText(text).then(() => {
    alert('Copied to clipboard!');
  });
}

// ==========================================
// Inject Modals into DOM
// ==========================================
function injectSalaryAndCopilotModals() {
  if (document.getElementById('salary-intel-modal')) return;

  const wrapper = document.createElement('div');
  wrapper.id = 'phases-8-9-modals-wrapper';
  wrapper.innerHTML = `
    <!-- PHASE 8: SALARY INTELLIGENCE & NEGOTIATION MODAL -->
    <div id="salary-intel-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 hidden items-center justify-center p-3 sm:p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full p-5 space-y-4 shadow-2xl max-h-[92vh] flex flex-col">
        <div class="flex items-start justify-between pb-3 border-b border-slate-800">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">GCC Compensation Radar</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 border border-emerald-700 text-emerald-300">Phase 8</span>
            </div>
            <h3 class="text-base sm:text-lg font-black text-white mt-0.5">Salary Negotiation & Market Benchmark Intelligence</h3>
            <p class="text-[11px] text-slate-400">Targeting 10 - 15+ LPA from 4 LPA base in Pune / Mumbai GCCs</p>
          </div>
          <button onclick="closeSalaryIntelModal()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>

        <div class="space-y-3.5 overflow-y-auto flex-1 pr-1">
          <!-- Live Interactive CTC Calculator -->
          <div class="p-4 rounded-xl bg-gradient-to-r from-emerald-950/60 to-slate-950 border border-emerald-800/80 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-white flex items-center space-x-1.5">
                <span>💰 Live CTC Structuring Calculator</span>
              </span>
              <span id="sal-disp-hike" class="px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-emerald-900/80 border border-emerald-600 text-emerald-200">+237.5% over 4 LPA</span>
            </div>

            <div class="flex items-center space-x-3">
              <label class="text-xs text-slate-300 font-semibold flex-shrink-0">Target CTC (LPA):</label>
              <input type="range" id="sal-target-input" min="9.0" max="18.0" step="0.5" value="13.5" oninput="calculateCtcLive()" class="flex-1 accent-emerald-500 cursor-pointer">
              <span id="sal-disp-target" class="text-sm font-bold font-mono text-emerald-400 w-24 text-right">₹13.5 LPA</span>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
              <div class="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
                <span class="text-[10px] text-slate-400 block uppercase">Fixed Base (85%)</span>
                <span id="sal-disp-fixed" class="text-xs sm:text-sm font-mono font-bold text-white">₹11.48 LPA</span>
              </div>
              <div class="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
                <span class="text-[10px] text-slate-400 block uppercase">Performance (15%)</span>
                <span id="sal-disp-variable" class="text-xs sm:text-sm font-mono font-bold text-slate-300">₹2.02 LPA</span>
              </div>
              <div class="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
                <span class="text-[10px] text-slate-400 block uppercase">Monthly Gross</span>
                <span id="sal-disp-gross" class="text-xs sm:text-sm font-mono font-bold text-cyan-300">₹88,700</span>
              </div>
              <div class="p-2.5 rounded-lg bg-emerald-950/60 border border-emerald-700/80">
                <span class="text-[10px] text-emerald-300 block uppercase font-bold">Est. In-Hand / Mo</span>
                <span id="sal-disp-inhand" class="text-xs sm:text-sm font-mono font-bold text-emerald-300">~₹78,500/mo</span>
              </div>
            </div>
          </div>

          <!-- Verified GCC Benchmarks Table -->
          <div class="space-y-1.5">
            <span class="text-xs font-bold text-white block">Pune / Mumbai GCC Verified Bands (2-3 YOE):</span>
            <div class="border border-slate-800 rounded-xl overflow-hidden">
              <table class="w-full text-left">
                <thead class="bg-slate-950 text-[10px] text-slate-400 uppercase font-mono border-b border-slate-800">
                  <tr>
                    <th class="py-2 px-3">Company</th>
                    <th class="py-2 px-3">Location</th>
                    <th class="py-2 px-3">Verified Band</th>
                    <th class="py-2 px-3">Median</th>
                    <th class="py-2 px-3">Typical Bonus</th>
                  </tr>
                </thead>
                <tbody id="sal-benchmarks-tbody"></tbody>
              </table>
            </div>
          </div>

          <!-- Objection Scripts -->
          <div class="space-y-2">
            <span class="text-xs font-bold text-white block">Tactical Objection Scripts (Click to Copy):</span>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <button onclick="copyNegotiationScript(1)" class="p-2.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-emerald-600 text-left transition space-y-1">
                <span class="text-[11px] font-bold text-emerald-300 block">1. 'Why 100%+ Hike?' Trap</span>
                <p class="text-[10px] text-slate-400">Reframes entry campus baseline to market SOC L2 value.</p>
              </button>
              <button onclick="copyNegotiationScript(2)" class="p-2.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-emerald-600 text-left transition space-y-1">
                <span class="text-[11px] font-bold text-cyan-300 block">2. Initial HR Call Quote</span>
                <p class="text-[10px] text-slate-400">Firmly anchors 12-14 LPA band before technical rounds.</p>
              </button>
              <button onclick="copyNegotiationScript(3)" class="p-2.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-emerald-600 text-left transition space-y-1">
                <span class="text-[11px] font-bold text-purple-300 block">3. Countering Lowball Offer</span>
                <p class="text-[10px] text-slate-400">Counter-anchors to 11.5L + signing bonus with immediate acceptance.</p>
              </button>
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-slate-800 flex justify-end">
          <button onclick="closeSalaryIntelModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold">Close</button>
        </div>
      </div>
    </div>

    <!-- PHASE 9: INTERVIEW CO-PILOT MODAL -->
    <div id="interview-copilot-modal" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 hidden items-center justify-center p-3 sm:p-4">
      <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full p-5 space-y-4 shadow-2xl max-h-[92vh] flex flex-col">
        <div class="flex items-start justify-between pb-3 border-b border-slate-800">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-cyan-400 uppercase tracking-wider font-mono">Interview Co-Pilot</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950 border border-cyan-700 text-cyan-300">Phase 9</span>
            </div>
            <h3 class="text-base sm:text-lg font-black text-white mt-0.5">Sentinel KQL & Palo Alto Technical Sandbox</h3>
            <p class="text-[11px] text-slate-400">Production query cheatsheets & verified STAR answers for Gourav's target GCC interviews</p>
          </div>
          <button onclick="closeInterviewCopilotModal()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>

        <!-- Navigation Tabs -->
        <div class="flex items-center space-x-2 border-b border-slate-800 pb-2">
          <button id="copilot-btn-kql" onclick="switchCopilotTab('kql')" class="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-cyan-600 text-white transition">
            🛡️ Sentinel KQL Queries
          </button>
          <button id="copilot-btn-paloalto" onclick="switchCopilotTab('paloalto')" class="px-3.5 py-1.5 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition">
            🔥 Palo Alto & Panorama
          </button>
          <button id="copilot-btn-qa" onclick="switchCopilotTab('qa')" class="px-3.5 py-1.5 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition">
            ⭐ STAR Incident Stories
          </button>
        </div>

        <!-- Tab 1: KQL Queries -->
        <div id="copilot-pane-kql" class="space-y-3 overflow-y-auto flex-1 pr-1">
          <div id="copilot-kql-list" class="space-y-3"></div>
        </div>

        <!-- Tab 2: Palo Alto & Panorama -->
        <div id="copilot-pane-paloalto" class="space-y-3 overflow-y-auto flex-1 pr-1 hidden">
          <div id="copilot-pa-list" class="space-y-3"></div>
        </div>

        <!-- Tab 3: STAR Answers -->
        <div id="copilot-pane-qa" class="space-y-3 overflow-y-auto flex-1 pr-1 hidden">
          <div id="copilot-qa-list" class="space-y-3"></div>
        </div>

        <div class="pt-3 border-t border-slate-800 flex justify-end">
          <button onclick="closeInterviewCopilotModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold">Close</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(wrapper);
  if (window.lucide) lucide.createIcons();
}

window.addEventListener('DOMContentLoaded', () => {
  injectSalaryAndCopilotModals();
});
