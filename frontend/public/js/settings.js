/**
 * frontend/public/js/settings.js
 * Barangay Information Settings: Reactive Synchronization & Global UI Layout Handlers
 */

const BARANGAY_CONFIG_STORAGE_KEY = 'barangayConfig';

/**
 * Default fallback configuration for Barangay Mapulang Lupa, Pandi, Bulacan
 */
const DEFAULT_BARANGAY_CONFIG = {
  barangay_name: 'Barangay Mapulang Lupa',
  municipality: 'Pandi, Bulacan',
  province: 'Bulacan',
  region: 'Region III – Central Luzon',
  captain_name: 'Kapitan Jose Reyes',
  punong_barangay: 'Kapitan Jose Reyes',
  contact_number: '0917-000-0000',
  contact_no: '0917-000-0000',
  email: 'mapulanglupa@pandi.gov.ph',
  official_logo_url: ''
};

/**
 * Reads the cached barangay configuration from localStorage
 * @returns {Object}
 */
function getCachedBarangayConfig() {
  try {
    const raw = localStorage.getItem(BARANGAY_CONFIG_STORAGE_KEY);
    if (raw) {
      return { ...DEFAULT_BARANGAY_CONFIG, ...JSON.parse(raw) };
    }
  } catch (e) {
    console.warn('[settings.js] Failed reading cached barangayConfig:', e);
  }
  return { ...DEFAULT_BARANGAY_CONFIG };
}

/**
 * Updates DOM elements across the application to reflect the latest barangay information
 * @param {Object} config - Updated configuration object
 */
function applyBarangayConfigToDOM(config) {
  if (!config) return;

  const bName = config.barangay_name || DEFAULT_BARANGAY_CONFIG.barangay_name;
  const muni = config.municipality || DEFAULT_BARANGAY_CONFIG.municipality;
  const prov = config.province || DEFAULT_BARANGAY_CONFIG.province;
  const capt = config.captain_name || config.punong_barangay || DEFAULT_BARANGAY_CONFIG.captain_name;
  const contact = config.contact_number || config.contact_no || DEFAULT_BARANGAY_CONFIG.contact_number;
  const email = config.email || DEFAULT_BARANGAY_CONFIG.email;
  const logo = config.official_logo_url || '';

  // 1. Sidebar Branding & Header Subtitles
  document.querySelectorAll('.brgy-name-display').forEach(el => {
    el.textContent = bName;
  });

  document.querySelectorAll('.brgy-location-display').forEach(el => {
    el.textContent = `${bName}, ${muni}${prov && !muni.includes(prov) ? `, ${prov}` : ''}`;
  });

  document.querySelectorAll('.brgy-captain-display').forEach(el => {
    el.textContent = capt;
  });

  document.querySelectorAll('.brgy-contact-display').forEach(el => {
    el.textContent = contact;
  });

  document.querySelectorAll('.brgy-email-display').forEach(el => {
    el.textContent = email;
  });

  // 2. Dynamic Logo / Seal Elements
  if (logo) {
    document.querySelectorAll('.brgy-logo-img').forEach(img => {
      img.src = logo;
    });
  }

  // 3. Active Certificate Preview Headers & Letterheads
  document.querySelectorAll('.cert-header-barangay').forEach(el => {
    el.textContent = bName.toUpperCase();
  });

  document.querySelectorAll('.cert-header-municipality').forEach(el => {
    el.textContent = muni;
  });

  document.querySelectorAll('.cert-header-province').forEach(el => {
    el.textContent = prov;
  });

  document.querySelectorAll('.cert-captain-name').forEach(el => {
    el.textContent = capt;
  });
}

/**
 * Asynchronously loads the latest Barangay Information from the backend,
 * caches it in localStorage, dispatches the update event, and refreshes the DOM.
 * @returns {Promise<Object>}
 */
async function fetchAndApplyBarangayConfig() {
  try {
    const res = await fetch('/api/settings/general', {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      credentials: 'include'
    });

    if (res.ok) {
      const json = await res.json();
      const config = json.data || json;
      if (config && config.barangay_name) {
        localStorage.setItem(BARANGAY_CONFIG_STORAGE_KEY, JSON.stringify(config));
        applyBarangayConfigToDOM(config);
        window.dispatchEvent(new CustomEvent('barangayConfigUpdated', { detail: config }));
        return config;
      }
    }
  } catch (err) {
    console.debug('[settings.js] Backend config fetch unavailable, using cached/default config.');
  }

  const cached = getCachedBarangayConfig();
  applyBarangayConfigToDOM(cached);
  return cached;
}

/**
 * Saves updated Barangay Information via POST/PUT /api/settings/general,
 * persists to localStorage, dispatches the global reactive event, and displays a success toast.
 * @param {Object} updatedData - Key-value settings to update
 * @returns {Promise<Object>}
 */
async function saveGeneralSettings(updatedData) {
  const current = getCachedBarangayConfig();
  const mergedData = { ...current, ...updatedData };

  try {
    const res = await fetch('/api/settings/general', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify(mergedData)
    });

    let savedRecord = mergedData;
    if (res.ok) {
      const json = await res.json();
      savedRecord = json.data || mergedData;
    }

    // 1. Update local client state / localStorage
    localStorage.setItem(BARANGAY_CONFIG_STORAGE_KEY, JSON.stringify(savedRecord));

    // 2. Dispatch custom global window event
    window.dispatchEvent(new CustomEvent('barangayConfigUpdated', { detail: savedRecord }));

    // 3. Immediately apply to active DOM elements
    applyBarangayConfigToDOM(savedRecord);

    // 4. Show success toast notification
    if (typeof showToast === 'function') {
      showToast('Barangay details successfully saved and updated.', 'success');
    }

    return { success: true, data: savedRecord };
  } catch (err) {
    console.error('[settings.js] Error saving general settings:', err);

    // Fallback: save to localStorage and dispatch event
    localStorage.setItem(BARANGAY_CONFIG_STORAGE_KEY, JSON.stringify(mergedData));
    window.dispatchEvent(new CustomEvent('barangayConfigUpdated', { detail: mergedData }));
    applyBarangayConfigToDOM(mergedData);

    if (typeof showToast === 'function') {
      showToast('Barangay details saved locally.', 'warning');
    }

    return { success: false, error: err.message, data: mergedData };
  }
}

// ── Global Event Listener for Reactive Synchronization ──
window.addEventListener('barangayConfigUpdated', (e) => {
  const config = e.detail;
  if (config) {
    applyBarangayConfigToDOM(config);
  }
});

// ── Initial Page Load Execution (Immediate DOM Population) ──
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      // 1. Instant synchronous render from cache
      applyBarangayConfigToDOM(getCachedBarangayConfig());
      // 2. Background async refresh from backend API
      fetchAndApplyBarangayConfig();
    });
  } else {
    applyBarangayConfigToDOM(getCachedBarangayConfig());
    fetchAndApplyBarangayConfig();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    BARANGAY_CONFIG_STORAGE_KEY,
    DEFAULT_BARANGAY_CONFIG,
    getCachedBarangayConfig,
    applyBarangayConfigToDOM,
    fetchAndApplyBarangayConfig,
    saveGeneralSettings
  };
}
