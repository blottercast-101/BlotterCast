/**
 * frontend/public/js/certificates.js
 * Frontend Strict Lockout & Dynamic Punong Barangay Signatory Data Binding
 */

/**
 * Fallback helper to ensure the Punong Barangay / Captain's name is never empty or undefined.
 * Checks localStorage cached configuration first, then default fallback.
 * @returns {string}
 */
function getCaptainName() {
  try {
    const cachedConfig = JSON.parse(localStorage.getItem('barangayConfig') || '{}');
    return (
      cachedConfig.punong_barangay ||
      cachedConfig.captain_name ||
      'Kapitan Jose Reyes'
    );
  } catch (e) {
    return 'Kapitan Jose Reyes';
  }
}

/**
 * Dynamically binds and populates the active Punong Barangay / Captain name across
 * all document and certificate signatory DOM elements and templates.
 *
 * @param {Object} [documentData={}] - Document payload containing captain_name or punong_barangay
 */
function bindCertificateCaptainName(documentData = {}) {
  const captain = (
    documentData.captain_name ||
    documentData.punong_barangay ||
    documentData.fullName ||
    getCaptainName()
  );
  const upperCaptain = String(captain || 'HON. PUNONG BARANGAY').toUpperCase();

  // 1. Target all signatory DOM placeholders and signature blocks
  const selectors = [
    '.cert-captain-name',
    '#c_captain',
    '#r_captain',
    '#i_captain',
    '#nr_captain',
    '#captainSignatureName',
    '[data-bind="punong_barangay"]',
    '[data-bind="captain_name"]'
  ];

  document.querySelectorAll(selectors.join(', ')).forEach(el => {
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      el.value = upperCaptain;
    } else {
      el.textContent = upperCaptain;
    }
  });

  // 2. Also populate jurisdiction and municipality headers if available
  const cachedConfig = JSON.parse(localStorage.getItem('barangayConfig') || '{}');
  const bName = documentData.barangay_name || cachedConfig.barangay_name || 'Barangay Mapulang Lupa';
  const muni = documentData.municipality || cachedConfig.municipality || 'Pandi, Bulacan';
  const prov = documentData.province || cachedConfig.province || 'Bulacan';

  document.querySelectorAll('.cert-header-barangay').forEach(el => {
    el.textContent = bName.toUpperCase();
  });
  document.querySelectorAll('.cert-header-municipality').forEach(el => {
    el.textContent = muni;
  });
  document.querySelectorAll('.cert-header-province').forEach(el => {
    el.textContent = prov;
  });
}

/**
 * Handles resident selection in the Certificate of Non-Residency form.
 * Programmatically disables submit button and renders a strict blocking banner
 * if the resident has any pending/unresolved blotter cases as a respondent.
 */
async function onNonResidencyResidentSelected(resident, options = {}) {
  const submitBtn = document.getElementById('nr_submit_btn') || document.querySelector('#nonResidencyFormModal button.btn-primary');
  const alertContainer = document.getElementById('nr_blotter_warning');
  const listEl = document.getElementById('nr_blotter_list');
  const nameDisplay = document.getElementById('nr_name_display');
  const prevAddrInput = document.getElementById('nr_prevaddr_input');

  if (nameDisplay) {
    nameDisplay.value = resident ? `${resident.lastName}, ${resident.firstName} ${resident.middleName || ''}`.trim() : '';
  }
  if (resident && resident.address && prevAddrInput && !prevAddrInput.value) {
    prevAddrInput.value = resident.address;
  }

  // Reset state
  if (alertContainer) alertContainer.classList.add('hidden');
  if (listEl) listEl.innerHTML = '';
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.removeAttribute('aria-disabled');
    submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    submitBtn.title = 'Issue & Preview Certificate';
  }

  if (!resident || !resident.id) return;

  try {
    const blotterRecords = typeof BCApi !== 'undefined' && BCApi.checkBlotterRecords
      ? await BCApi.checkBlotterRecords(resident.lastName, resident.firstName, resident.id)
      : [];

    const resolvedStatuses = ['RESOLVED', 'SETTLED', 'DISMISSED', 'COMPLIED'];
    const activeCases = blotterRecords.filter(b => {
      const isRespondent = b.role === 'Respondent' || (b.respondent && b.respondent.toLowerCase().includes(resident.lastName.toLowerCase()));
      const isUnresolved = !resolvedStatuses.includes(String(b.status).toUpperCase());
      return isRespondent && isUnresolved;
    });

    if (activeCases.length > 0) {
      // 1. Programmatically LOCK OUT submit button
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.setAttribute('aria-disabled', 'true');
        submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        submitBtn.title = 'Issuance blocked: Resident has active derogatory records';
      }

      // 2. Render strict blocking error banner
      if (alertContainer) {
        alertContainer.className = 'bg-rose-50 border border-rose-300 rounded-xl p-4';
        alertContainer.innerHTML = `
          <div class="flex items-start gap-2.5 mb-3">
            <span class="text-rose-600 text-lg flex-shrink-0">⛔</span>
            <div>
              <div class="font-bold text-rose-900 text-sm">Issuance Blocked</div>
              <div class="text-xs text-rose-700 mt-0.5 leading-relaxed">
                This transferred resident has active derogatory records. Resolution via Lupon / Barangay Settlement is required before any certificate can be released.
              </div>
            </div>
          </div>
          <div class="space-y-2 mb-2">
            ${activeCases.map(c => `
              <div class="bg-white border border-rose-200 rounded-lg p-2.5 text-xs">
                <div class="flex justify-between items-center mb-1">
                  <span class="font-mono font-bold text-forest-800">${c.docket_no || c.docketNo}</span>
                  <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">UNSETTLED CASE</span>
                </div>
                <div class="text-forest-700"><strong>${c.complainant}</strong> vs <strong>${c.respondent}</strong></div>
                <div class="text-forest-500 text-[11px] mt-0.5">${c.nature} &middot; Status: <span class="text-rose-600 font-semibold">${c.status}</span></div>
              </div>
            `).join('')}
          </div>
        `;
        alertContainer.classList.remove('hidden');
      }

      if (typeof showToast === 'function') {
        showToast('Issuance blocked: Resident has active/unsettled blotter records.', 'error');
      }
    }
  } catch (err) {
    console.error('[certificates.js] Error checking blotter eligibility:', err);
  }
}

/**
 * Validates non-residency submission failsafe
 */
function validateNonResidencySubmission(e) {
  const submitBtn = document.getElementById('nr_submit_btn') || document.querySelector('#nonResidencyFormModal button.btn-primary');
  if (submitBtn && submitBtn.disabled) {
    if (e && e.preventDefault) e.preventDefault();
    if (typeof bcAlert === 'function') {
      bcAlert('⛔ Issuance Blocked: Cannot issue Certificate of Non-Residency. This resident has active derogatory/blotter records that require resolution.');
    } else {
      alert('Issuance Blocked: Resident has active derogatory records.');
    }
    return false;
  }
  return true;
}

// ── Global Reactive Event Listeners for Signatory Updates ──
window.addEventListener('barangayConfigUpdated', (e) => {
  if (e.detail) {
    bindCertificateCaptainName(e.detail);
  }
});

// ── Automatic Initialization on Document Ready ──
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      bindCertificateCaptainName();
    });
  } else {
    bindCertificateCaptainName();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getCaptainName,
    bindCertificateCaptainName,
    onNonResidencyResidentSelected,
    validateNonResidencySubmission,
  };
}
