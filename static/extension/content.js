/**
 * CyberSwitch 10X - Content Script for Workday, Greenhouse, and Lever
 * Injects floating 1-click button to autofill applicant forms from localhost:8000
 */

(function () {
  const SERVER_URL = "http://localhost:8000/api/autofill/profile";

  function injectFloatingButton() {
    if (document.getElementById("cyberswitch-autofill-btn")) return;

    const btn = document.createElement("button");
    btn.id = "cyberswitch-autofill-btn";
    btn.innerHTML = `
      <span style="display:inline-block; margin-right:6px;">⚡</span>
      <span>CyberSwitch Autofill</span>
    `;
    btn.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      background: linear-gradient(135deg, #06b6d4, #3b82f6);
      color: #ffffff;
      border: 1px solid rgba(255,255,255,0.3);
      padding: 12px 20px;
      border-radius: 9999px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 10px 25px -5px rgba(6, 182, 212, 0.5);
      transition: all 0.2s ease;
    `;

    btn.onmouseenter = () => btn.style.transform = "scale(1.05)";
    btn.onmouseleave = () => btn.style.transform = "scale(1.0)";
    btn.onclick = triggerAutofill;

    document.body.appendChild(btn);
  }

  async function triggerAutofill() {
    const btn = document.getElementById("cyberswitch-autofill-btn");
    const origText = btn.innerHTML;
    btn.innerHTML = "⏳ Filling Application...";

    try {
      const res = await fetch(SERVER_URL);
      if (!res.ok) throw new Error("Could not reach CyberSwitch local server");
      const p = await res.json();

      let filledCount = 0;

      const fill = (selectors, val) => {
        if (!val) return;
        for (const sel of selectors) {
          const el = document.querySelector(sel);
          if (el && !el.disabled) {
            el.focus();
            el.value = val;
            el.dispatchEvent(new Event("input", { bubbles: true }));
            el.dispatchEvent(new Event("change", { bubbles: true }));
            el.dispatchEvent(new Event("blur", { bubbles: true }));
            el.style.border = "2px solid #10b981";
            filledCount++;
            return;
          }
        }
      };

      // Workday CXS / Classic & Greenhouse selectors
      fill(['input[data-automation-id="legalNameSection_firstName"]', 'input[id*="first_name"]', 'input[name*="first_name"]'], p.first_name);
      fill(['input[data-automation-id="legalNameSection_lastName"]', 'input[id*="last_name"]', 'input[name*="last_name"]'], p.last_name);
      fill(['input[data-automation-id="email"]', 'input[id*="email"]', 'input[type="email"]'], p.email);
      fill(['input[data-automation-id="phone-number"]', 'input[id*="phone"]', 'input[type="tel"]'], p.phone);
      fill(['input[data-automation-id="addressSection_city"]', 'input[id*="city"]'], p.city);
      fill(['input[data-automation-id="addressSection_postalCode"]', 'input[id*="postal"]'], p.postal_code);
      fill(['input[data-automation-id="addressSection_addressLine1"]', 'input[id*="address"]'], p.address_line);
      fill(['input[id*="linkedin"]', 'input[name*="linkedin"]'], p.linkedin_url);
      fill(['input[id*="github"]', 'input[name*="github"]'], p.github_url);
      fill(['input[id*="website"]', 'input[name*="website"]', 'input[id*="portfolio"]'], p.portfolio_url);
      fill(['input[data-automation-id="jobTitle"]', 'input[id*="title"]', 'input[name*="title"]'], p.current_title);
      fill(['input[data-automation-id="company"]', 'input[id*="company"]', 'input[name*="company"]'], p.current_company);
      fill(['textarea[id*="summary"]', 'textarea[name*="summary"]', 'textarea[id*="comments"]'], p.summary);

      btn.innerHTML = `✅ Filled ${filledCount} Fields!`;
      btn.style.background = "#10b981";
      setTimeout(() => {
        btn.innerHTML = origText;
        btn.style.background = "linear-gradient(135deg, #06b6d4, #3b82f6)";
      }, 3500);

    } catch (err) {
      console.error("Autofill error:", err);
      btn.innerHTML = "❌ Local Server Offline";
      btn.style.background = "#ef4444";
      setTimeout(() => {
        btn.innerHTML = origText;
        btn.style.background = "linear-gradient(135deg, #06b6d4, #3b82f6)";
      }, 3000);
    }
  }

  // Inject once DOM is interactive
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectFloatingButton);
  } else {
    injectFloatingButton();
  }
})();
