// app.js — shared application logic
window.BC_MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
window.BC_SHORT_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

// ── View Transition Error Guard & AbortError Suppression ──
window.addEventListener('unhandledrejection', function (event) {
  const reason = event.reason;
  const message = reason?.message || String(reason || '');
  if (
    reason?.name === 'AbortError' ||
    message.includes('Transition was skipped') ||
    message.includes('Cross-Origin-Opener-Policy') ||
    message.includes('postMessage')
  ) {
    event.preventDefault(); // Suppresses the unhandled promise rejection in DevTools
  }
});
window.addEventListener('error', function (event) {
  const message = event?.message || String(event || '');
  if (
    message.includes('Cross-Origin-Opener-Policy') ||
    message.includes('postMessage') ||
    message.includes('Transition was skipped')
  ) {
    event.preventDefault();
  }
});

function safeStartViewTransition(updateCallback) {
  if (document.startViewTransition && typeof document.startViewTransition === 'function') {
    try {
      const transition = document.startViewTransition(() => {
        if (typeof updateCallback === 'function') {
          return updateCallback();
        }
      });

      if (transition) {
        if (transition.ready && typeof transition.ready.catch === 'function') {
          transition.ready.catch(() => {});
        }
        if (transition.updateCallbackDone && typeof transition.updateCallbackDone.catch === 'function') {
          transition.updateCallbackDone.catch(() => {});
        }
        if (transition.finished && typeof transition.finished.catch === 'function') {
          transition.finished.catch((err) => {
            if (err && err.name !== 'AbortError' && !String(err).includes('Transition was skipped')) {
              console.error(err);
            }
          });
        }
      }
      return transition;
    } catch (err) {
      if (typeof updateCallback === 'function') updateCallback();
      return null;
    }
  } else {
    if (typeof updateCallback === 'function') updateCallback();
    return null;
  }
}
window.safeStartViewTransition = safeStartViewTransition;

// Local "YYYY-MM-DD" for today — deliberately NOT `new Date().toISOString()`,
// since that gives the UTC date. In timezones ahead of UTC (e.g. the
// Philippines, UTC+8), during early-morning local hours the UTC date is
// still "yesterday", which would wrongly cap date pickers one day short
// and block today's own date from being selected.
function bcTodayLocalStr() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

document.addEventListener('DOMContentLoaded', () => {
  // Active nav highlight
  const current = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    link.classList.toggle('active', href === current);
  });

  // Cap any date input marked data-no-future so the native calendar
  // picker itself can't select a day after today — belt-and-suspenders
  // alongside the matching bcIsFutureDate() check each form also runs
  // on submit (this covers the picker UI; that covers typed/pasted
  // values and dates set programmatically when editing a record). Today
  // itself stays fully selectable — only strictly-later dates are capped.
  const todayStr = bcTodayLocalStr();
  document.querySelectorAll('input[type="date"][data-no-future]').forEach(el => { el.max = todayStr; });

  // Initial load fallback for Barangay Information across all views
  bcInitBarangayConfig();
  bcInitLanguage();

  // Responsive sidebar drawer & touch interaction initialization
  initGlobalSidebar();
});

// ── Persistent Global Sidebar Controller (Tablet & Mobile) ──
function initGlobalSidebar() {
  const sidebar = document.getElementById('sidebar') || document.getElementById('mainSidebar') || document.querySelector('aside');
  if (!sidebar) return;

  // 1. Ensure Backdrop overlay exists for tablet/mobile off-canvas navigation
  let overlay = document.getElementById('sidebarOverlay') || document.getElementById('sidebarBackdrop');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'sidebarOverlay';
    overlay.className = 'sidebar-backdrop-overlay hidden';
    document.body.appendChild(overlay);
  }

  // 2. Open / Close / Toggle Helpers
  const openSidebar = () => {
    document.body.classList.add('sidebar-open');
    sidebar.classList.remove('-translate-x-full');
    sidebar.classList.add('open');
    if (overlay) overlay.classList.remove('hidden');
  };

  const closeSidebar = () => {
    document.body.classList.remove('sidebar-open');
    sidebar.classList.add('-translate-x-full');
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.add('hidden');
  };

  const toggleSidebar = (e) => {
    if (e) e.stopPropagation();
    const isOpen = document.body.classList.contains('sidebar-open') ||
                   sidebar.classList.contains('open') ||
                   (!sidebar.classList.contains('-translate-x-full') && window.innerWidth < 1024);
    if (isOpen) {
      closeSidebar();
    } else {
      openSidebar();
    }
  };

  window.openGlobalSidebar = openSidebar;
  window.closeGlobalSidebar = closeSidebar;
  window.toggleGlobalSidebar = toggleSidebar;

  // 3. Bind click handler to existing buttons in the DOM
  document.querySelectorAll('#globalSidebarToggle, #sidebarToggle, [data-sidebar-toggle]').forEach(btn => {
    btn.onclick = toggleSidebar;
  });

  if (overlay) {
    overlay.onclick = (e) => {
      e.stopPropagation();
      closeSidebar();
    };
  }

  // 4. Close sidebar on link navigation for screens < 1024px
  sidebar.querySelectorAll('.nav-link, a').forEach(link => {
    if (link.dataset.navBound) return;
    link.dataset.navBound = 'true';
    link.addEventListener('click', () => {
      if (window.innerWidth < 1024) {
        closeSidebar();
      }
    });
  });

  // 5. Touch row selection compatibility
  document.querySelectorAll('.data-table').forEach(table => {
    if (table.dataset.touchSelectBound) return;
    table.dataset.touchSelectBound = 'true';

    table.addEventListener('click', (e) => {
      const isTouch = window.matchMedia('(hover: none), (max-width: 1023px)').matches;
      const target = e.target;
      if (target.closest('button, a, select, input[type="text"], .pw-toggle, .icon-btn')) return;

      const row = target.closest('tr');
      if (!row || row.closest('thead') || row.classList.contains('empty-state-row') || row.classList.contains('error-state-row')) return;

      const cb = row.querySelector('.bc-row-cb');
      if (cb && (isTouch || table.classList.contains('selection-mode-active'))) {
        if (target !== cb) {
          cb.checked = !cb.checked;
          cb.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    });
  });
}
window.initGlobalSidebar = initGlobalSidebar;
window.bcInitResponsiveSidebarAndTouch = initGlobalSidebar;

// Global Delegated Click Listener for Sidebar Toggles
document.addEventListener('click', (e) => {
  const toggleBtn = e.target.closest('#globalSidebarToggle, #sidebarToggle, [data-sidebar-toggle]');
  if (toggleBtn) {
    e.preventDefault();
    e.stopPropagation();
    if (typeof window.toggleGlobalSidebar === 'function') {
      window.toggleGlobalSidebar(e);
    }
    return;
  }

  const overlay = e.target.closest('#sidebarOverlay, #sidebarBackdrop, .sidebar-backdrop-overlay');
  if (overlay && document.body.classList.contains('sidebar-open')) {
    e.preventDefault();
    e.stopPropagation();
    if (typeof window.closeGlobalSidebar === 'function') {
      window.closeGlobalSidebar();
    }
  }
});

// Close sidebar on Escape or window resize >= 1024px
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && document.body.classList.contains('sidebar-open')) {
    if (typeof window.closeGlobalSidebar === 'function') {
      window.closeGlobalSidebar();
    }
  }
});

window.addEventListener('resize', () => {
  if (window.innerWidth >= 1024 && document.body.classList.contains('sidebar-open')) {
    if (typeof window.closeGlobalSidebar === 'function') {
      window.closeGlobalSidebar();
    }
  }
});

// ── Global Barangay Information Reactive Sync & Layout Handler ──
function bcApplyBarangayConfig(config) {
  if (!config) return;
  const bName = config.barangay_name || 'Barangay Mapulang Lupa';
  const muni = config.municipality || 'Pandi, Bulacan';
  const prov = config.province || 'Bulacan';
  const capt = config.captain_name || config.punong_barangay || config.barangay_captain || '';
  const contact = config.contact_number || config.contact_no || '0917-000-0000';
  const email = config.email || 'mapulanglupa@pandi.gov.ph';
  const logo = config.official_logo_url || '';

  // 1. Update Sidebar Branding & Header Subtitles
  document.querySelectorAll('.brgy-name-display').forEach(el => { el.textContent = bName; });
  document.querySelectorAll('.brgy-location-display').forEach(el => {
    el.textContent = `${bName}, ${muni}${prov && !muni.includes(prov) ? `, ${prov}` : ''}`;
  });
  if (capt) {
    document.querySelectorAll('.brgy-captain-display').forEach(el => { el.textContent = capt; });
  }
  document.querySelectorAll('.brgy-contact-display').forEach(el => { el.textContent = contact; });
  document.querySelectorAll('.brgy-email-display').forEach(el => { el.textContent = email; });

  // 2. Update Dynamic Logo / Seal Elements
  if (logo) {
    document.querySelectorAll('.brgy-logo-img').forEach(img => { img.src = logo; });
  }

  // 3. Update Active Certificate Preview Headers (if currently open)
  document.querySelectorAll('.cert-header-barangay').forEach(el => { el.textContent = bName.toUpperCase(); });
  document.querySelectorAll('.cert-header-municipality').forEach(el => { el.textContent = muni; });
  document.querySelectorAll('.cert-header-province').forEach(el => { el.textContent = prov; });
  document.querySelectorAll('.cert-captain-name').forEach(el => { el.textContent = capt; });

  if (config.default_language && typeof bcSetLanguage === 'function') {
    bcSetLanguage(config.default_language);
  }
}

window.addEventListener('barangayConfigUpdated', (e) => {
  if (e.detail) bcApplyBarangayConfig(e.detail);
});

function bcInitBarangayConfig() {
  try {
    const raw = localStorage.getItem('barangayConfig');
    if (raw) {
      bcApplyBarangayConfig(JSON.parse(raw));
    }
  } catch (e) {}

  if (typeof fetch === 'function') {
    fetch('/api/settings/general', { method: 'GET', headers: { 'Accept': 'application/json' }, credentials: 'include' })
      .then(res => res.ok ? res.json() : null)
      .then(json => {
        const config = json?.data || json;
        if (config && config.barangay_name) {
          localStorage.setItem('barangayConfig', JSON.stringify(config));
          bcApplyBarangayConfig(config);
        }
      })
      .catch(() => {});
  }
}

// ── Internationalization (i18n) Engine: English / Filipino ──
const BC_TRANSLATIONS = {
  fil: {
    // Nav & Sidebar
    "Main Menu": "Pangunahing Menu",
    "Dashboard": "Dashboard",
    "Blotter Records": "Mga Tala ng Blotter",
    "Incident Reports": "Mga Ulat ng Insidente",
    "Settlement Monitor": "Pagsubaybay sa Kasunduan",
    "Documents": "Mga Dokumento",
    "Census": "Sensus",
    "Brgy Clearance": "Barangay Clearance",
    "Cert. of Residency": "Katibayan ng Paninirahan",
    "Cert. of Non-Residency": "Katibayan ng Di-Paninirahan",
    "Cert. of Indigency": "Katibayan ng Kawalan ng Sapat na Kita",
    "Analytics": "Pagsusuri at Datos",
    "Heat Map": "Mapa ng Insidente",
    "Trends": "Mga Trend at Pagsusuri",
    "Predictions": "Mga Pagtataya",
    "System": "Sistema",
    "Users & Roles": "Mga Gumagamit at Tungkulin",
    "Reports": "Mga Ulat",
    "Settings": "Mga Setting",
    "Log out": "Mag-log out",

    // Page titles & Subtitles
    "System Settings": "Mga Setting ng Sistema",
    "Configure barangay information, notifications, security, and backup options": "Isaayos ang impormasyon ng barangay, mga abiso, seguridad, at mga opsyon sa pag-backup",
    "Save Changes": "I-save ang mga Pagbabago",
    "Barangay Information": "Impormasyon ng Barangay",
    "System Preferences": "Mga Kagustuhan sa Sistema",
    "Alert Thresholds": "Mga Limitasyon ng Alerto",
    "Notification Channels": "Mga Paraan ng Pag-abiso",
    "My Account": "Aking Account",
    "Change Password": "Palitan ang Password",
    "Two-Factor Authentication (2FA)": "Dalawahang Pagpapatotoo (2FA)",
    "Session & Idle Timeout": "Pagtatapos ng Sesyon at Kawalan ng Gawain",
    "Password Security Policy": "Patakaran sa Seguridad ng Password",
    "Compliance & Privacy": "Pagsunod sa Patakaran at Privacy",
    "Backup Database": "I-backup ang Database",
    "Backup Schedule": "Iskedyul ng Backup",
    "Backup History": "Kasaysayan ng Backup",
    "Recent Generated Reports": "Kamakailang Nabuo na mga Ulat",
    "Generate Report": "Gumawa ng Ulat",
    "Scheduled Reports": "Naka-iskedyul na mga Ulat",
    "Incident Summary Report": "Ulat sa Buod ng Insidente",
    "Settlement Compliance Report": "Ulat sa Pagtupad sa Kasunduan",
    "Settlement Compliance": "Ulat sa Pagtupad sa Kasunduan",
    "Blotter Summary Report": "Buod ng Ulat ng Blotter",
    "Trend Analysis Report": "Ulat sa Pagsusuri ng Trend",
    "Predictive Risk Assessment": "Pagtatasa ng Inaasahang Panganib",
    "Patrol Deployment Plan": "Plano ng Pagpapakalat ng Patrolya",
    "Comparative Period Report": "Ulat sa Paghahambing ng Panahon",

    // Settings tabs
    "General": "Pangkalahatan",
    "Notifications": "Mga Abiso",
    "Security": "Seguridad",
    "Backup & Recovery": "Pag-backup at Pagbawi",

    // Form labels
    "Barangay Name": "Pangalan ng Barangay",
    "Municipality / City": "Bayan / Lungsod",
    "Region": "Rehiyon",
    "Barangay Captain": "Kapitan ng Barangay",
    "Date Format": "Format ng Petsa",
    "Time Format": "Format ng Oras",
    "Records Per Page": "Mga Tala Bawat Pahina",
    "Default Language": "Pangunahing Wika",
    "Risk Score Threshold (0–100)": "Limitasyon ng Marka ng Panganib (0–100)",
    "Incident Spike Threshold": "Limitasyon sa Pagdami ng Insidente",
    "In-App Notifications": "Mga Abiso sa App",
    "Model Retraining Alerts": "Mga Alerto sa Pagsasanay ng Modelo",
    "Username": "Pangalan ng Gumagamit",
    "Role": "Tungkulin",
    "Full Name": "Buong Pangalan",
    "First Name": "Pangalan",
    "Last Name": "Apelyido",
    "Middle Name": "Gitnang Pangalan",
    "Date of Birth": "Araw ng Kapanganakan",
    "Sex": "Kasarian",
    "Civil Status": "Katayuang Sibil",
    "Nationality": "Nasyonalidad",
    "Zone / Purok": "Sona / Purok",
    "Address": "Tirahan / Kalye",
    "Street / House Address": "Tirahan / Kalye",
    "Household No.": "Blg. ng Sambahayan",
    "Contact Number": "Numero ng Telepono",
    "Contact No.": "Numero ng Telepono",
    "Email Address": "Email Address",
    "Account Status": "Katayuan ng Account",
    "Current Password": "Kasalukuyang Password",
    "New Password": "Bagong Password",
    "Confirm New Password": "Kumpirmahin ang Bagong Password",
    "Temporary Password": "Pansamantalang Password",
    "E-Signature": "E-Lagda",
    "Date From": "Petsa Mula",
    "Date To": "Petsa Hanggang",
    "Zone Filter": "Salain ayon sa Zone",
    "Export Format": "Format ng Pag-export",
    "Period": "Panahon",
    "Year": "Taon",
    "Month": "Buwan",
    "Docket No.": "Blg. ng Tala (Docket No.)",
    "Date Filed": "Petsa ng Pagkakasampa",
    "Name of Complainant": "Pangalan ng Nagrereklamo",
    "Complainant Address": "Tirahan ng Nagrereklamo",
    "Name of Respondent": "Pangalan ng Inirereklamo",
    "Respondent Address": "Tirahan ng Inirereklamo",
    "Nature of Case": "Uri ng Kaso",
    "Type": "Uri",
    "Report No.": "Blg. ng Ulat",
    "Date Reported": "Petsa ng Pag-ulat",
    "Time Reported": "Oras ng Pag-ulat",
    "Location Detail": "Detalye ng Lokasyon",
    "Category": "Kategorya",
    "Priority Level": "Antas ng Priyoridad",
    "Priority": "Priyoridad",
    "Description": "Deskripsyon",
    "Reporter Name": "Pangalan ng Nag-ulat",
    "Reporter Address": "Tirahan ng Nag-ulat",
    "Responding Officer": "Tumugong Opisyal",
    "Case No.": "Blg. ng Kaso",
    "Case Title": "Pamagat ng Kaso",
    "Date of Initial Confrontation": "Petsa ng Unang Paghaharap",
    "Action Taken": "Isinagawang Aksyon",
    "Date of Settlement or Award": "Petsa ng Kasunduan o Gawad",
    "Date of Execution": "Petsa ng Pagpapatupad",
    "Officer-in-Charge / Conciliator": "Namamahala / Tagapamagitan",
    "Main Point of Agreement / Settlement Terms": "Pangunahing Punto ng Kasunduan",
    "Status of Compliance / Resolution": "Katayuan ng Pagsunod / Paglutas",
    "Remarks": "Mga Tala / Puna",
    "Purpose of Clearance": "Layunin ng Clearance",
    "Purpose of Certificate": "Layunin ng Katibayan",
    "O.R. Number": "Blg. ng O.R.",
    "Amount Paid (₱)": "Halagang Binayaran (₱)",
    "Duration of Residency": "Tagal ng Paninirahan",

    // Modal Headers & Page Titles
    "Import Resident Data": "Mag-import ng Datos ng Residente",
    "Export Blotter Records": "I-export ang Tala ng Blotter",
    "Export Blotter Record": "I-export ang Tala ng Blotter",
    "Export Blotter Entry Record": "I-export ang Tala ng Entry sa Blotter",
    "Export Settlement Monitoring": "I-export ang Pagsubaybay sa Settlement",
    "Add Resident": "Magdagdag ng Residente",
    "Edit Resident": "I-edit ang Residente",
    "Import Blotter Data": "Mag-import ng Datos ng Blotter",
    "New Incident Report": "Bagong Ulat ng Insidente",
    "Edit Incident Report": "I-edit ang Ulat ng Insidente",
    "Issue Barangay Clearance": "Mag-isyu ng Barangay Clearance",
    "Issue Certificate of Residency": "Mag-isyu ng Katibayan ng Paninirahan",
    "Issue Certificate of Non-Residency": "Mag-isyu ng Katibayan ng Di-Paninirahan",
    "Issue Certificate of Indigency": "Mag-isyu ng Katibayan ng Kawalan ng Sapat na Kita",
    "New Settlement Record": "Bagong Rekord ng Settlement",
    "Edit Settlement Record": "I-edit ang Rekord ng Settlement",
    "Add New User": "Magdagdag ng Bagong Gumagamit",
    "Edit User": "I-edit ang Gumagamit",
    "Blotter Record Details": "Mga Detalye ng Tala ng Blotter",
    "Resident Profile Details": "Mga Detalye ng Profile ng Residente",
    "Incident Report Details": "Mga Detalye ng Ulat ng Insidente",
    "Settlement Hearing Details": "Mga Detalye ng Pagdinig sa Kasunduan",
    "Elevate Incident to Official Blotter?": "Iakyat ang Insidente sa Opisyal na Blotter?",

    // Dropdown Options
    "All Records": "Lahat ng Tala",
    "Specific Year": "Tiyak na Taon",
    "Specific Month": "Tiyak na Buwan",
    "All Status": "Lahat ng Katayuan",
    "All Sex": "Lahat ng Kasarian",
    "All Zones": "Lahat ng Zone",
    "All Categories": "Lahat ng Kategorya",
    "All Types": "Lahat ng Uri",
    "All Priorities": "Lahat ng Priyoridad",
    "All Roles": "Lahat ng Tungkulin",
    "All Periods": "Lahat ng Panahon",
    "-Select-": "-Pumili-",
    "Male": "Lalaki",
    "Female": "Babae",
    "Single": "Walang Asawa",
    "Married": "May Asawa",
    "Widowed": "Balo",
    "Separated": "Hiwalay",
    "Registered Voter": "Rehistradong Botante",
    "Not Registered": "Hindi Rehistrado",
    "Deactivated": "Hindi Aktibo (Deactivated)",
    "High": "Mataas",
    "Medium": "Katamtaman",
    "Low": "Mababa",
    "Criminal": "Kriminal",
    "Civil": "Sibil",
    "Daily": "Araw-araw",
    "Weekly": "Lingguhan",
    "Monthly": "Buwanan",
    "Quarterly": "Kada Tatlong Buwan",
    "Annually": "Taunan",
    "Today": "Ngayong Araw",
    "This Week": "Ngayong Linggo",
    "This Month": "Ngayong Buwan",
    "This Quarter": "Ngayong Kwarter",
    "This Year": "Ngayong Taon",

    // Months (Dropdown & Display)
    "January": "Enero",
    "February": "Pebreo",
    "March": "Marso",
    "April": "Abril",
    "May": "Mayo",
    "June": "Hunyo",
    "July": "Hulyo",
    "August": "Agosto",
    "September": "Setyembre",
    "October": "Oktubre",
    "November": "Nobyembre",
    "December": "Disyembre",

    // Table Column Headers
    "Resident No.": "Blg. ng Residente",
    "Name": "Pangalan",
    "Age": "Edad",
    "Actions": "Mga Aksyon",
    "Complainant": "Nagrereklamo",
    "Respondent": "Inirereklamo",
    "Nature": "Uri ng Kaso",
    "Date": "Petsa",
    "Time": "Oras",
    "Location": "Lokasyon",
    "Reporter": "Nag-ulat",
    "Officer": "Opisyal",
    "Complaint Title": "Pamagat ng Reklamo",
    "Status of Compliance": "Katayuan ng Pagsunod",
    "User": "Gumagamit",
    "Last Login": "Huling Pag-login",
    "Timestamp": "Petsa at Oras",
    "Details": "Mga Detalye",
    "Module": "Modyul",
    "Permission": "Pahintulot",
    "Frequency": "Dalas",
    "Next Run": "Susunod na Pagsasagawa",
    "Recipients": "Mga Tagatanggap",
    "Enabled": "Pinagana",
    "Report Name": "Pangalan ng Ulat",
    "Generated By": "Binuo Ni",
    "Control No.": "Blg. ng Kontrol",
    "Purpose": "Layunin",
    "Date Issued": "Petsa ng Pag-isyu",
    "OR No.": "Blg. ng O.R.",
    "File": "File",
    "Size": "Laki",
    "By": "Ni",
    "Zone": "Sona",
    "Hotspot Probability": "Probabilidad ng Hotspot",
    "Risk Level": "Antas ng Panganib",
    "Predicted Top Category": "Inaasahang Pangunahing Kategorya",
    "Peak Time Window": "Oras ng Pinakamataas na Insidente",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    "Weight": "Bigat",

    // Buttons and actions
    "Export to Excel": "I-export sa Excel",
    "Import Data": "I-import ang Datos",
    "Download": "I-download",
    "View & Edit": "Tignan at Baguhin",
    "Tingnan at I-edit": "Tignan at Baguhin",
    "Upload New Photo": "Mag-upload ng Bagong Larawan",
    "Remove": "Alisin",
    "Save Account Details": "I-save ang Detalye ng Account",
    "Update Password": "I-update ang Password",
    "Run Backup Now": "Magsagawa ng Backup Ngayon",
    "Cancel": "Kanselahin",
    "Save": "I-save",
    "Close": "Isara",
    "Edit": "I-edit",
    "Delete": "Burahin",
    "Tanggalin": "Burahin",
    "Preview": "Silipin",
    "Generate": "Bumuo",
    "Filter": "Salain",
    "Search": "Maghanap",
    "Add Incident": "Magdagdag ng Insidente",
    "New Blotter Entry": "Bagong Tala sa Blotter",
    "Add User": "Magdagdag ng Gumagamit",
    "Import": "Mag-import",
    "Permanent Delete": "Permanenteng Burahin",
    "Permanently Delete": "Permanenteng Burahin",
    "View Details": "Tingnan ang Detalye",
    "Restore to Active": "Ibalik sa Aktibo",
    "Archive": "I-archive",
    "Activate": "I-activate",
    "Suspend": "I-suspend",
    "Elevate to Blotter": "Iakyat sa Blotter",
    "Already Elevated": "Na-iakyat na sa Blotter",
    "Switch Zone": "Lumipat ng Zone",
    "Toggle Mini-Map": "I-toggle ang Mini-Map",
    "Wide View": "Malawak na Tanaw",
    "Geocode Location": "I-geocode ang Lokasyon",
    "Browse files": "Mag-browse ng mga file",
    "Browse Files": "Mag-browse ng mga File",
    "Upload & Import": "I-upload at I-import",
    "Save Resident": "I-save ang Residente",
    "Save Entry": "I-save ang Tala",
    "Save Report": "I-save ang Ulat",
    "Save Record": "I-save ang Rekord",
    "Save User": "I-save ang Gumagamit",
    "Issue & Preview": "Mag-isyu at Silipin",

    // Badges & Statuses
    "Active": "Aktibo",
    "ACTIVE": "AKTIBO",
    "Pending": "Nakabinbin",
    "PENDING": "NAKABINBIN",
    "Resolved": "Nalutas",
    "RESOLVED": "NALUTAS",
    "Settled": "Napagkasunduan",
    "SETTLED": "NAPAGKASUNDUAN",
    "Under Investigation": "Iniimbestigahan",
    "UNDER INVESTIGATION": "INIIMBESTIGAHAN",
    "Dismissed": "Ibinalewala",
    "DISMISSED": "IBINALEWALA",
    "Complied": "Nasunod",
    "COMPLIED": "NASUNOD",
    "Not Complied": "Hindi Nasunod",
    "NOT COMPLIED": "HINDI NASUNOD",
    "Hearing Scheduled": "Nakatakda ang Pagdinig",
    "HEARING SCHEDULED": "NAKATAKDA ANG PAGDINIG",
    "Suspended": "Suspendido",
    "SUSPENDED": "SUSPENDIDO",
    "Inactive": "Hindi Aktibo",
    "INACTIVE": "HINDI AKTIBO",
    "Deceased": "Yumao",
    "DECEASED": "YUMAO",
    "Transferred": "Lumipat",
    "TRANSFERRED": "LUMIPAT",
    "Elevated": "Iniakyat",
    "Elevated to Blotter": "Iniakyat sa Blotter",
    "ELEVATED TO BLOTTER": "INIAKYAT SA BLOTTER",
    "Closed": "Isinara",
    "CLOSED": "ISINARA",
    "Protected": "Protektado",
    "PROTECTED": "PROTEKTADO",
    "SENIOR": "SENIOR",
    "MALE": "LALAKI",
    "FEMALE": "BABAE",
    "All Zones": "Lahat ng Zone",
    "PDF Document": "Dokumentong PDF",
    "Excel / CSV": "Excel / CSV",
    "PDF Only": "PDF LAMANG",
    "PDF ONLY": "PDF LAMANG",
    "Next Monday": "Susunod na Lunes",
    "1st of month": "Unang araw ng buwan",
    "All incidents in a selected date range with category and status breakdown.": "Lahat ng insidente sa napiling saklaw ng petsa na may breakdown ng kategorya at katayuan.",
    "Zone-level risk forecast with patrol deployment recommendations.": "Pagtataya ng panganib sa antas ng sona na may mga rekomendasyon sa pagpapakalat ng patrolya.",
    "Recommended patrol schedules by zone, time, and risk level.": "Inirerekomendang mga iskedyul ng patrolya ayon sa sona, oras, at antas ng panganib.",
    "Historical patterns, seasonal trends, and category comparisons.": "Mga historikal na pattern, pana-panahong trend, at paghahambing ng kategorya.",
    "Status of all active settlement agreements and compliance tracking.": "Katayuan ng lahat ng aktibong kasunduan sa settlement at pagsubaybay sa pagsunod.",
    "Side-by-side comparison of two date ranges (e.g. Q1 vs Q2).": "Paghahambing ng dalawang saklaw ng petsa (hal. Q1 laban sa Q2).",
    "All Statuses": "Lahat ng Status",
    "View Archived": "Tignan ang Naka-arkibo",
    "View Active": "Tignan ang Aktibo",
    "records": "mga tala",
    "Showing": "Ipinapakita ang",
    "of": "ng",
    "‹ Prev": "‹ Nakalipas",
    "‹ Previous": "‹ Nakalipas",
    "Next ›": "Susunod ›",
    "Report": "Ulat",

    // Audit actions & badges
    "CREATED": "GINAWA",
    "Created": "GINAWA",
    "DELETED": "BINURA",
    "Deleted": "BINURA",
    "UPDATED": "INUPDATE",
    "Updated": "INUPDATE",
    "LOGIN": "NAG-LOGIN",
    "Login": "NAG-LOGIN",
    "Action": "KILOS",
    "ACTION": "KILOS",
    "action": "KILOS",

    // Common Messages
    "Barangay details successfully saved and updated.": "Matagumpay na na-save at na-update ang mga detalye ng barangay.",
    "Account details updated successfully.": "Matagumpay na na-update ang mga detalye ng account.",
    "Password updated successfully.": "Matagumpay na na-update ang password.",
    "Profile photo updated successfully.": "Matagumpay na na-update ang larawan sa profile.",
    "Profile photo removed.": "Naalis na ang larawan sa profile.",
    "Schedule enabled.": "Pinagana ang iskedyul.",
    "Schedule disabled.": "Hindi pinagana ang iskedyul.",
    "Report generated! Starting download…": "Nabuo na ang ulat! Simulan ang pag-download…",
    "Opening report preview in new tab…": "Binubuksan ang preview ng ulat sa bagong tab…",
    "Please enter a valid email address.": "Mangyaring maglagay ng wastong email address.",
    "Full Name is required.": "Kailangan ang Buong Pangalan.",
    "Username is required.": "Kailangan ang Pangalan ng Gumagamit.",
    "Contact Number is required.": "Kailangan ang Numero ng Telepono.",

    // Dashboard & Global Headers
    "Search records (Case ID, name, date)…": "Maghanap ng tala (Case ID, pangalan, petsa...)",
    "Search records (Case ID, name, date)...": "Maghanap ng tala (Case ID, pangalan, petsa...)",
    "Search users…": "Maghanap ng guma-gamit...",
    "Search users...": "Maghanap ng guma-gamit...",
    "Welcome back! Here's today's overview.": "Maligayang pagbabalik! Narito ang buod ngayong araw.",

    // Stat Cards & Metrics
    "Total Blotters": "Kabuuan ng Blotter",
    "blotter entries on file": "mga tala ng blotter sa file",
    "Incident Reports": "Mga Ulat ng Insidente",
    "New this week": "Bago ngayong linggo",
    "Pending Settlement": "Nakahimlay sa Pag-aayos",
    "awaiting settlement": "naghihintay ng pag-aayos",
    "Awaiting settlement": "Naghihintay ng pag-aayos",
    "Resolved Cases": "Mga Resolbadong Kaso",
    "resolved": "resolbado",
    "RISK FORECAST": "PREDIKSYON NG PANGANIB",
    "Risk Forecast": "Prediksyon ng Panganib",
    "View This Week's Zone Risk Rankings": "Tignan ang Antas ng Panganib sa Bawat Zone Ngayong Linggo",
    "View This Week's\nZone Risk Rankings": "Tignan ang Antas ng Panganib sa Bawat Zone Ngayong Linggo",
    "Model-predicted hotspots by zone →": "Mga inaasahang hotspot ayon sa zone →",

    // Quick Actions & Headers
    "Manage all barangay blotter records": "Pamahalaan ang lahat ng tala ng blotter sa barangay",
    "Recent Blotter Entries": "Mga Huling Tala ng Blotter",
    "Resolution Rate": "Antas ng Pagresolba",
    "View All →": "Tignan Lahat →",
    "Quick Actions": "Mabilis na Aksyon",
    "Blotter Records": "Mga Tala ng Blotter",
    "Blotter\nRecords": "Mga Tala ng Blotter",
    "New Incident Report": "Bagong Ulat ng Insidente",
    "New Incident\nReport": "Bagong Ulat ng Insidente",
    "Monitor Settlement": "Subaybayan ang Pag-aayos",
    "Monitor\nSettlement": "Subaybayan ang Pag-aayos",
    "Import Census CSV": "Mag-import ng Census CSV",
    "Import\nCensus CSV": "Mag-import ng Census CSV",
    "Users & Roles": "Mga Gumagamit at Tungkulin",
    "Users &\nRoles": "Mga Gumagamit at Tungkulin",

    // Role Permission Matrix
    "Role Permission Matrix": "Talahanayan ng Pahintulot ng Tungkulin",
    "Permission": "Pahintulot",
    "System Admin": "Tagapamahala ng Sistema",
    "SYSTEM ADMIN": "TAGAPAMAHALA NG SISTEMA",
    "Barangay Captain": "Punong Barangay",
    "BARANGAY CAPTAIN": "PUNONG BARANGAY",
    "Desk Officer": "Desk Officer",
    "DESK OFFICER": "DESK OFFICER",
    "Data Encoder": "Data Encoder",
    "DATA ENCODER": "DATA ENCODER",
    "View All Records": "Tignan ang Lahat ng Tala",
    "Add Blotter Entry": "Magdagdag ng Entry sa Blotter",
    "Edit Any Record": "Baguhin ang Anumang Tala",
    "Delete Records": "Burahin ang mga Tala",
    "Archive Records": "I-arkibo ang mga Tala",
    "Generate Reports": "Gumawa ng mga Ulat",
    "View Analytics": "Tignan ang Analytics",
    "Manage Users": "Pamahalaan ang mga Gumagamit",
    "Retrain ML Model": "I-retrain ang Modelong ML",
    "Import CSV/Excel": "Mag-import ng CSV/Excel",
    "System Settings": "Mga Setting ng Sistema",

    // System Badges & Headings
    "Protected": "Protektado",
    "System Users": "Mga Gumagamit ng Sistema",

    // Incident Reports Page
    "Log and track all reported incidents in the barangay": "I-tala at subaybayan ang lahat ng inulat na insidente sa barangay",
    "Total Reports": "Kabuuan ng Ulat",
    "incident logs on record": "mga tala ng insidente sa rekord",
    "High Priority": "Mataas na Priyoridad",
    "urgent attention required": "kailangang aksyunan agad",
    "Under Investigation": "Kasalukuyang Inimbestigahan",
    "in progress by officers": "inaaksyunan ng mga opisyal",
    "Referred": "Isinangguni / Naireselba",
    "referred to blotter & lupon": "isinangguni sa blotter at lupon",
    "Search report no., location, reporter…": "Maghanap ng no. ng ulat, lokasyon, nag-ulat...",
    "Search report no., location, reporter...": "Maghanap ng no. ng ulat, lokasyon, nag-ulat...",

    // Settlement / Compliance Monitoring Page
    "Monitoring of Compliance to Settlement or Award": "Pagsubaybay sa Pagtupad sa Pag-aayos o Gawad",
    "Track and manage settlement agreements and compliance status": "Subaybayan at pamahalaan ang mga kasunduan sa pag-aayos at katayuan ng pagtupad",
    "Total Cases": "Kabuuan ng Kaso",
    "Complied": "Nakatupad",
    "Not Complied": "Hindi Nakatupad",
    "Add Settlement Record": "Magdagdag ng Tala ng Pag-aayos",
    "+ Add Settlement Record": "+ Magdagdag ng Tala ng Pag-aayos",
    "Settlement Records": "Mga Tala ng Pag-aayos",
    "Search case no., title…": "Maghanap ng no. ng kaso, pamagat...",
    "Search case no., title...": "Maghanap ng no. ng kaso, pamagat...",

    // Barangay Census Page
    "Barangay Census": "Sensus ng Barangay",
    "Official list of registered residents of Barangay Mapulang Lupa": "Opisyal na talaan ng mga nakatatalang residente ng Barangay Mapulang Lupa",
    "Total Residents": "Kabuuan ng Residente",
    "registered in barangay": "nakatala sa barangay",
    "Total Households": "Kabuuan ng Kaya-bahayan",
    "indexed residences": "nakatalang mga tahanan",
    "Registered Voters": "Rehistradong Botante",
    "active precinct voters": "mga aktibong botante sa presinto",
    "Senior Citizens": "Mga Senior Citizen",
    "60+ years & special care": "60+ taong gulang at nangangailangan ng tanging pangangalaga",
    "Resident Records": "Mga Tala ng Residente",
    "Search name, address…": "Maghanap ng pangalan, tirahan...",
    "Search name, address...": "Maghanap ng pangalan, tirahan...",
    "Add Resident": "Magdagdag ng Residente",
    "+ Add Resident": "+ Magdagdag ng Residente",

    // Barangay Clearance Page
    "Barangay Clearance": "Barangay Clearance",
    "Issue and manage barangay clearance certificates": "Mag-isyu at pamahalaan ang mga sertipiko ng barangay clearance",
    "Issue New Clearance": "Mag-isyu ng Bagong Clearance",
    "+ Issue New Clearance": "+ Mag-isyu ng Bagong Clearance",
    "Issued This Month": "Nai-isyu Ngayong Buwan",
    "Total This Year": "Kabuuan Ngayong Taon",
    "Revenue (Fees)": "Kikita / Halaga (Bayad)",
    "Issuance Log": "Talaan ng Pag-iisyu",
    "Certificate Preview": "Pasilip sa Sertipiko",
    "Print": "I-print",

    // Trends & Comparative Analytics
    "Trends & Comparative Analytics": "Mga Trend at Paghahambing ng Analitika",
    "Incident-to-blotter elevation, Lupon settlement rates, and spatial performance": "Pagtataas mula insidente patungong blotter, antas ng pag-aayos sa Lupon, at pagganap ng bawat lugar",
    "Total Incidents": "Kabuuan ng mga Insidente",
    "Peak Month": "Buwan na may Pinakamataas na Bilang",
    "Highest incident volume": "May pinakamataas na bilang ng insidente",
    "All field incident logs": "Lahat ng tala ng insidente sa larangan",
    "Settlement Rate": "Antas ng Pagkakasundo / Pag-aayos",
    "Amicably resolved cases": "Mapayapang naresolbang mga kaso",
    "Elevated to Blotter": "Iniakyat sa Blotter",
    "Official docketed cases": "Opisyal na naitalang mga kaso",
    "Monthly Comparative Pipeline": "Paghahambing ng Daloy Kada Buwan",
    "Field Incidents vs. Elevated Blotter Cases vs. Resolved": "Mga Insidente sa Larangan vs. Iniakyat sa Blotter vs. Naresolba",
    "Elevated Blotters": "Iniakyat sa Blotter",
    "Category Severity": "Antas ng Lahi/Kategorya ng Insidente",
    "Incidents & Elevation Distribution": "Pamamahagi ng mga Insidente at Pag-aakyat ng Kaso",
    "Zonal Elevation & Settlement Matrix": "Matris ng Pag-aakyat at Pagkakasundo Bawat Sona",
    "Administrative Zone 1 to Zone 7 comparative performance": "Paghahambing ng pagganap ng Sona 1 hanggang Sona 7",
    "7 Official Administrative Zones": "7 Opisyal na Sonang Pampangasiwaan",
    "ZONE / SUBSTATION": "SONA / SUBSTATION",
    "Zone / Substation": "SONA / SUBSTATION",
    "TOTAL INCIDENTS": "KABUAN NG INSIDENTE",
    "ELEVATED TO BLOTTER": "INIAKYAT SA BLOTTER",
    "ELEVATION RATE": "ANTAS NG PAG-AAKYAT SA BLOTTER",
    "Elevation Rate": "ANTAS NG PAG-AAKYAT SA BLOTTER",
    "RESOLVED CASES": "NARESOLBANG MGA KASO",
    "Resolved Cases": "NARESOLBANG MGA KASO",
    "STATUS": "KALAGAYAN / STATUS",
    "Status": "KALAGAYAN / STATUS",
    "STABLE CONTROL": "MAAYOS NA KONTROL",
    "Stable Control": "MAAYOS NA KONTROL",
    "HIGH ELEVATION": "MATAAS NA PAG-AAKYAT",
    "High Elevation": "MATAAS NA PAG-AAKYAT",
    "Incidents by Day of Week": "Mga Insidente Ayon sa Araw ng Linggo",
    "Weekly occurrence distribution": "Pamamahagi ng paglitaw kada linggo",
    "Top Incident Categories": "Mga Nangungunang Kategorya ng Insidente",
    "Ranked by volume": "PinaSunod-sunod ayon sa dami",

    // Predictive Insights
    "Predictive Insights": "Mga Pahiwatig at Hula ng AI",
    "ML-based incident risk forecasting by zone, time, and category": "Paghula ng panganib ng insidente gamit ang Machine Learning batay sa sona, oras, at kategorya",
    "Loading latest insights...": "Ikinakarga ang pinakabagong pahiwatig...",
    "Loading latest insights…": "Ikinakarga ang pinakabagong pahiwatig...",
    "Retrain Model": "Muling Sanayin ang Modelo (Retrain)",
    "INCIDENT OCCURRENCE": "Pagkakaroon ng Insidente",
    "INCIDENT TYPE": "Uri ng Insidente",
    "HOTSPOT RISK": "Panganib sa Hotspot",
    "Incident Occurrence": "Pagkakaroon ng Insidente",
    "Incident Type": "Uri ng Insidente",
    "Hotspot Risk": "Panganib sa Hotspot",
    "Accuracy": "Katumpakan",
    "F1 Score": "F1 Score",
    "Showing {from} to {to} of {total} incidents": "Ipinapakita ang {from} hanggang {to} sa {total} na insidente",
    "7-Day Forecast — Expected Incidents": "Hula para sa 7 Araw — Inaasahang mga Insidente",
    "High Risk Zones": "Mga Sonang Mataas ang Panganib",
    "Moderate Risk Zones": "Mga Sonang Katamtaman ang Panganib",
    "Low Risk Zones": "Mga Sonang Mababa ang Panganib",
    "All Zones (1 - 7)": "Lahat ng Sona (1 - 7)",
    "Next 7 Days": "Susunod na 7 Araw",
    "Next 14 Days": "Susunod na 14 Araw",
    "Patrol Recommendations": "Mga Inirerekomendang Pagpapatrolya",
    "Category Forecast by Zone": "Hula ng Kategorya Bawat Sona",
    "Expected incidents per day, broken down by category, for the selected zone": "Inaasahang insidente bawat araw, na nakahimay ayon sa kategorya, para sa napiling sona",
    "Predicted Incident Risk by Zone": "Inaasahang Panganib ng Insidente Bawat Sona",
    "Hotspot Probability": "PROBABILIDAD NG HOTSPOT",
    "Expected Incidents (7d)": "INAASAHANG MGA INSIDENTE (7 ARAW)",
    "Risk Level": "ANTAS NG PANGANIB",
    "Predicted Top Category": "INAASAHANG PANGUNAHING KATEGORYA",
    "Peak Time Window": "ORAS NG PINAKAMATAAS NA INSIDENTE",
    "14-Day Trend": "TREND SA LOOB NG 14 ARAW",

    // System & Audit Settings
    "Manage personnel accounts, roles, and access permissions": "Pamahalaan ang mga account ng tauhan, papel (roles), at pahintulot sa pag-access",
    "Recent Audit Log": "Kamakailang Talaan ng Pagsusuri (Audit Log)",
    "Generate, schedule, and download formatted reports": "Gumawa, mag-iskedyul, at mag-download ng mga naka-pormat na ulat",

    // [DATA MANAGEMENT & EXPORT]
    "Data Management": "Pamamahala ng Data",
    "All records are stored in the PostgreSQL blottercast database. Records added on the Blotter and Incident pages automatically feed the Heat Map, Trends, and the Python ML Predictions module.": "Ang lahat ng tala ay nakaimbak sa PostgreSQL blottercast database. Ang mga talang idinadagdag sa mga pahina ng Blotter at Incident ay awtomatikong nagpapakain sa Heat Map, Trends, at Python ML Predictions module.",
    "Reset Demo Dataset": "I-reset ang Sample na Data",
    "Export Records (JSON)": "I-export ang mga Tala (JSON)",

    // [ALERTS & NOTIFICATIONS]
    "Trigger alert when predicted risk exceeds this value.": "Magpadala ng babala kapag ang inaasahang panganib ay lumampas sa halagang ito.",
    "Alert when new incidents exceed this count in 24 hours.": "Magpadala ng babala kapag ang mga bagong insidente ay lumampas sa bilang na ito sa loob ng 24 oras.",
    "In-App Notifications": "Mga Notification sa App",
    "Show alerts in the notification center": "Ipakita ang mga babala sa notification center",
    "Model Retraining Alerts": "Mga Babala sa Muling Pagsasanay ng Modelo",
    "Notify when ML model retraining completes": "Magbigay-alam kapag natapos ang muling pagsasanay ng ML model",

    // [SECURITY & PASSWORD RULES]
    "PASSWORD MUST CONTAIN:": "ANG PASSWORD AY DAPAT NAGLALAMAN NG:",
    "At least 6 characters long": "Hindi bababa sa 6 na character",
    "At least 1 uppercase letter (A–Z)": "Hindi bababa sa 1 malaking titik (A–Z)",
    "At least 1 uppercase letter (A-Z)": "Hindi bababa sa 1 malaking titik (A–Z)",
    "At least 1 lowercase letter (a–z)": "Hindi bababa sa 1 maliit na titik (a–z)",
    "At least 1 lowercase letter (a-z)": "Hindi bababa sa 1 maliit na titik (a–z)",
    "At least 1 number (0–9)": "Hindi bababa sa 1 numero (0–9)",
    "At least 1 number (0-9)": "Hindi bababa sa 1 numero (0–9)",
    "At least 1 special character (e.g., !@#$%^&*)": "Hindi bababa sa 1 espesyal na karakter (hal. !@#$%^&*)",
    "Security Tip": "Tip sa Seguridad",
    "NEVER REUSE PASSWORDS ACROSS MULTIPLE SYSTEMS": "HUWAG KAILANMAN GAMITIN ANG PAREHONG PASSWORD SA IBANG SYSTEM",

    // [DISPLAY & AUTHENTICATION SETTINGS]
    "Display Preferences": "Mga Kagustuhan sa Display",
    "System Time Format": "Format ng Oras ng System",
    "12-Hour (hh:mm A) (e.g. 01:45 PM)": "12-Oras (hh:mm A) (hal. 01:45 PM)",
    "Security & Authentication": "Seguridad at Pagpapatunay",
    "Admin Master Control": "Pangunahing Kontrol ng Admin",
    "Enforce 2FA for All Accounts": "Ipatupad ang 2FA sa Lahat ng Account",
    "Require Two-Factor Authentication across all roles during login.": "Hilingin ang Two-Factor Authentication sa lahat ng papel sa pag-login.",
    "Session Inactivity Auto-Logout (2 Hours)": "Awtomatikong Pag-logout kapag Walang Gawain (2 Oras)",
    "Automatically logs out inactive users after 120 minutes of inactivity.": "Awtomatikong nilog-out ang mga user na walang activity pagkaraan ng 120 minuto.",
    "Policy Thresholds & Password Rules": "Mga Patakaran at Tuntunin sa Password",
    "Inactivity Timeout Duration (minutes)": "Tagal bago i-Logout kapag walang Gawain (minuto)",
    "Default: 120 minutes (2 hours).": "Default: 120 minuto (2 oras).",
    "Max Failed Login Attempts": "Pinakamataas na Subok ng Maling Login",
    "Minimum Password Length": "Pinakamaikling Haba ng Password",
    "Password Expiry (days)": "Pagpasa ng Password (araw)",
    "Data Privacy": "Privacy ng Data",
    "Audit Trail Logging": "Pagtatala ng Audit Trail",
    "Log all data changes, logins, and report exports": "Itala ang lahat ng pagbabago sa data, pag-login, at pag-export ng ulat",
    "Data Subject Rights Module": "Module para sa Karapatan sa Data Privacy",
    "Allow data access/correction requests from data subjects": "Payagan ang kahilingan sa pag-access o pagwawasto ng data mula sa mga indibidwal",

    // [BACKUP & RECOVERY]
    "Automated Backup": "Awtomatikong Backup",
    "Backup Frequency": "Dalas ng Backup",
    "Backup Time": "Oras ng Backup",
    "Backup Destination": "Pupuntahan ng Backup",
    "Retain Backups For (days)": "Itabi ang Backup ng (mga araw)",
    "Backups are scheduled and executed autonomously by the backend server worker in Asia/Manila standard time (UTC+8).": "Ang mga backup ay naka-iskedyul at awtomatikong isinasagawa ng backend server worker batay sa Asia/Manila standard time (UTC+8).",
    "Perform Backup Now": "Magsagawa ng Backup Ngayon",
    "Run Backup Now": "Magsagawa ng Backup Ngayon",
    "Recovery Objectives": "Mga Layunin sa Pagbawi (Recovery)",
    "Recovery Time Objective (RTO)": "Target na Oras ng Pagbawi (RTO)",
    "Maximum acceptable downtime after failure.": "Pinakamatagal na katanggap-tanggap na pagtigil ng system pagkatapos ng pagkasira.",
    "Recovery Point Objective (RPO)": "Target na Halaga ng Nawalang Data (RPO)",
    "Maximum acceptable data loss window.": "Pinakamataas na katanggap-tanggap na saklaw ng nawalang data.",
    "Backup History": "Kasaysayan ng Backup",

    // [MODALS & DIALOGS]
    "Log Out": "Mag-log Out",
    "Are you sure you want to log out?": "Sigurado ka bang gusto mong mag-log out?",
    "Cancel": "Kanselahin",

    // Categories
    "Theft": "Pagnanakaw",
    "Public Disturbance": "Pambubulahaw sa Publiko",
    "Physical Assault": "Pananakit / Pag-atake",
    "Vandalism": "Pambaboy ng Ari-arian (Vandalism)",
    "Trespassing": "Panghihimasok (Trespassing)",
    "Domestic Dispute": "Alitan sa Pamamahay (Domestic Dispute)",
    "Vehicular Accident": "Aksidente sa Sasakyan",
    "Drug-Related Activity": "Aktibidad Kaugnay ng Droga"
  }
};

const i18n = {
  en: {
    // Common Actions
    cancel: "Cancel",
    import_data: "Import Data",
    export_excel: "Export to Excel",
    download: "Download",
    view_edit: "View & Edit",
    delete: "Delete",
    close: "Close",
    save: "Save",
    save_changes: "Save Changes",
    confirm: "Confirm",
    submit: "Submit",
    permanent_delete: "Permanent Delete",
    back: "Back",
    next: "Next",
    clear: "Clear",
    reset: "Reset",
    filter: "Filter",
    replace: "Replace",
    browse_files: "Browse files",
    browse_files_cap: "Browse Files",
    upload_import: "Upload & Import",
    processing: "Processing...",
    please_wait: "Please wait...",
    done: "Done",

    // Modal Headers & Labels
    import_resident_title: "Import Resident Data",
    export_blotter_title: "Export Blotter Records",
    period_label: "Period",
    year_label: "Year",
    month_label: "Month",

    // Dropdown Options
    period_all: "All Records",
    period_year: "Specific Year",
    period_month: "Specific Month",

    month_jan: "January",
    month_feb: "February",
    month_mar: "March",
    month_apr: "April",
    month_may: "May",
    month_jun: "June",
    month_jul: "July",
    month_aug: "August",
    month_sep: "September",
    month_oct: "October",
    month_nov: "November",
    month_dec: "December",

    months: {
      jan: "January",
      feb: "February",
      mar: "March",
      apr: "April",
      may: "May",
      jun: "June",
      jul: "July",
      aug: "August",
      sep: "September",
      oct: "October",
      nov: "November",
      dec: "December"
    },

    // Census Import Modal
    import_resident_title: "Import Resident Data",
    drag_drop_text: "Drag & Drop CSV or Excel file (.xlsx, .xls) here or Click to upload",
    supported_files_census: "Supported types: CSV, Excel (.xlsx, .xls)",
    download_resident_template: "Download Resident Census Template (.csv)",
    selected_file: "Selected File",
    file_ready_import: "File ready for import",

    // Resident Modal (Census)
    add_resident_title: "Add Resident",
    edit_resident_title: "Edit Resident",
    save_resident: "Save Resident",
    resident_no: "Resident No.",
    resident_no_ph: "Auto-generated on save",
    last_name: "Last Name",
    last_name_ph: "Last name",
    first_name: "First Name",
    first_name_ph: "First name",
    middle_name: "Middle Name",
    middle_name_ph: "Middle name (optional)",
    dob: "Date of Birth",
    sex: "Sex",
    select_sex: "-Select-",
    male: "Male",
    female: "Female",
    civil_status: "Civil Status",
    select_civil_status: "-Select-",
    single: "Single",
    married: "Married",
    widowed: "Widowed",
    separated: "Separated",
    nationality: "Nationality",
    zone: "Zone / Purok",
    select_zone: "-Select-",
    address: "Street / House Address",
    address_ph: "Blk, Lot, Street",
    household_no: "Household No.",
    household_no_ph: "HH-001",
    contact_no: "Contact Number",
    voter_status: "Voter Status",
    registered_voter: "Registered Voter",
    not_registered: "Not Registered",
    deactivated: "Deactivated",
    occupation: "Occupation",
    occupation_ph: "e.g. Farmer, Teacher",
    status: "Status",
    active: "Active",
    deceased: "Deceased",
    transferred: "Transferred",
    resident_profile_details: "Resident Profile Details",
    deceased_hint: "Voter Status is automatically set to Deactivated for deceased residents.",

    // Blotter Import Modal
    import_blotter_title: "Import Blotter Data",
    import_type: "Import Type",
    blotter_entry_record: "Blotter Entry Record",
    blotter_entry_record_desc: "Imports case logs and automatically creates linked Incident Reports with coordinates for Heatmap & Prediction.",
    blotter_record: "Blotter Record",
    blotter_record_desc: "Updates case progress and links records to the Settlement Monitor.",
    csv_templates: "CSV Templates:",
    blotter_entry_csv: "Blotter Entry (.csv)",
    blotter_record_csv: "Blotter Record (.csv)",
    click_choose_drag_drop: "Click to choose a file or drag & drop",
    supports_xlsx_csv: "Supports .xlsx and .csv (Max 10MB)",

    // Blotter Entry Modal
    new_blotter_entry: "New Blotter Entry",
    edit_blotter_entry: "Edit Blotter Record",
    docket_no: "Docket No.",
    date_filed: "Date Filed",
    name_of_complainant: "Name of Complainant",
    not_a_resident: "Not a resident / outside party",
    search_census_ph: "Type a name to search Census…",
    full_name_ph: "Full name",
    complainant_address: "Complainant Address",
    name_of_respondent: "Name of Respondent",
    respondent_address: "Respondent Address",
    nature_of_case: "Nature of Case",
    nature_of_case_ph: "e.g. Pag-aaway / Alitan sa Hangganan",
    type: "Type",
    criminal: "Criminal",
    civil: "Civil",
    pending: "Pending",
    save_entry: "Save Entry",
    blotter_record_details: "Blotter Record Details",
    blotter_rule_note_1: "Either the complainant or the respondent can be marked 'Not a resident' if they're from outside the barangay.",
    blotter_rule_note_2: "But not both, since at least one party must be a registered Census resident.",

    // Incident Modal
    new_incident_report: "New Incident Report",
    edit_incident_report: "Edit Incident Report",
    save_report: "Save Report",
    report_no: "Report No.",
    date_reported: "Date Reported",
    time_reported: "Time Reported",
    location_detail: "Location Detail",
    location_detail_ph: "e.g. Pandi Encampment One, Ph1 Blk24 Lot 4 Residence 1…",
    zone_mismatch_title: "Zone & Location Mismatch Detected",
    zone_mismatch_desc: "The entered location matches another zone.",
    switch_zone: "Switch Zone",
    geocoded_pin_boundary: "Geocoded Pin & Boundary",
    unverified_location: "Unverified Location",
    geocode_location: "Geocode Location",
    toggle_mini_map: "Toggle Mini-Map",
    wide_view: "Wide View",
    category: "Category",
    priority_level: "Priority Level",
    high: "High",
    medium: "Medium",
    low: "Low",
    description: "Description",
    description_ph: "Detailed description of the incident…",
    reporter_name: "Reporter Name",
    non_resident_reporter: "Non-Resident Reporter",
    reporter_address: "Reporter Address (Municipality / Location)",
    reporter_address_ph: "Outside Barangay / specify municipality or address",
    responding_officer: "Responding Officer",
    responding_officer_ph: "e.g. PO1 Cruz",
    elevate_to_blotter: "Elevate to Blotter",
    already_elevated: "Already Elevated",
    incident_report_details: "Incident Report Details",
    view_in_heatmap: "View in Heatmap",
    elevate_confirm_title: "Elevate Incident to Official Blotter?",
    elevate_confirm_body: "This action cannot be undone or reverted. Elevating this report will permanently lock this incident report and create an official Blotter Case for Lupon conciliation.",
    proceed_to_blotter_form: "Proceed to Blotter Form",

    // Certificate Modals (Clearance, Residency, Non-Residency, Indigency)
    issue_clearance_title: "Issue Barangay Clearance",
    issue_residency_title: "Issue Certificate of Residency",
    issue_non_residency_title: "Issue Certificate of Non-Residency",
    issue_indigency_title: "Issue Certificate of Indigency",
    resident_label: "Resident",
    search_resident_ph: "Type a name to search...",
    full_name: "Full Name",
    age: "Age",
    purpose_of_clearance: "Purpose of Clearance",
    purpose_of_certificate: "Purpose of Certificate",
    or_number: "O.R. Number",
    amount_paid: "Amount Paid (₱)",
    duration_of_residency: "Duration of Residency",
    years: "Years",
    months: "Months",
    previous_home_address: "Previous / Former Home Address in this Barangay",
    requested_by_purpose: "Requested By / Purpose",
    issue_preview: "Issue & Preview",
    derogatory_alert: "Derogatory Alert",
    applicant_active_blotter: "Applicant has an active blotter record",

    // Certificate Modals additions
    census_inheritance_help: "A certificate can only be issued to someone already recorded in Census. Name, age, civil status, and address are inherited from that record.",
    indigency_blotter_warning: "This resident is listed as a Respondent in active or unresolved blotter case(s). A Certificate of Indigency cannot be released until all respondent cases are resolved.",
    indigency_note: "Certifying indigency is the responsibility of the Punong Barangay. Ensure the applicant's financial status has been verified before issuance.",
    note_label: "Note:",
    select_placeholder: "-Select-",

    // Settlement Modals
    new_settlement_title: "New Settlement Record",
    edit_settlement_title: "Edit Settlement Record",
    link_blotter_case: "Link to Blotter Case",
    search_blotter_ph: "Type docket no. or name to search Blotter…",
    search_docket_complainant_hint: "(Search docket no. or complainant)",
    auto_generated: "Auto-generated",
    auto_filled_blotter: "Auto-filled from Blotter",
    optional_notes: "Optional notes",
    blottercast_system_label: "BlotterCast Barangay System",
    case_no: "Case No.",
    case_title: "Case Title",
    date_initial_confrontation: "Date of Initial Confrontation",
    action_taken: "Action Taken",
    date_of_settlement: "Date of Settlement or Award",
    date_of_execution: "Date of Execution",
    officer_in_charge: "Officer-in-Charge / Conciliator",
    officer_ph: "e.g. Punong Barangay / Pangkat Chairman",
    agreement_terms: "Main Point of Agreement / Settlement Terms",
    agreement_terms_ph: "Key terms and conditions of the settlement agreement…",
    status_compliance: "Status of Compliance / Resolution",
    remarks: "Remarks",
    save_record: "Save Record",
    settlement_hearing_details: "Settlement Hearing Details",

    // User Modals
    add_new_user_title: "Add New User",
    edit_user_title: "Edit User",
    personal_info_cap: "PERSONAL INFORMATION",
    roles_cap: "ROLES",
    security_cap: "SECURITY",
    assign_user_role: "ASSIGN USER ROLE",
    assigned_roles: "ASSIGNED ROLES",
    security_credentials: "SECURITY & CREDENTIALS",
    read_only: "(Read-Only)",
    username: "Username",
    email: "Email",
    contact_no: "Contact No.",
    temporary_password: "Temporary Password",
    temp_password_hint: "This temporary password will be emailed directly to the user. The recipient must update their credentials in Settings upon initial login.",
    e_signature: "E-Signature",
    e_sig_hint: "(used on printed Barangay Clearance & Certificate of Indigency)",
    no_sig_uploaded: "No signature uploaded",
    upload_signature: "Upload Signature",
    remove_sig: "Remove",
    sig_format_hint: "PNG with transparent background recommended, max 2MB.",
    del_user_warning_box: "Warning: This action cannot be undone. All personal data, activity records, and authentication credentials linked to this user will be permanently purged from the database.",
    type_to_proceed: "Type DELETE to proceed:",
    copy_clipboard: "Copy to Clipboard",
    regenerate_password: "Regenerate Password",
    save_user: "Save User",
    permanently_delete_user: "Permanently Delete User",
    destructive_removal: "Destructive Account Removal",
    type_delete_confirm: "TYPE DELETE TO CONFIRM",

    // Reports Modal & Page Controls
    generate_report_title: "Generate Report",
    date_from: "Date From",
    date_to: "Date To",
    zone_filter: "Zone Filter",
    all_zones: "All Zones",
    export_format: "Export Format",
    pdf_document: "PDF Document",
    preview: "Preview",
    generate: "Generate",
    scheduled_reports_title: "Scheduled Reports",
    recent_generated_reports_title: "Recent Generated Reports",
    badge_pdf_only: "PDF Only",
    report_card_incident_summary_title: "Incident Summary Report",
    report_card_incident_summary_desc: "All incidents in a selected date range with category and status breakdown.",
    report_card_predictive_risk_title: "Predictive Risk Assessment",
    report_card_predictive_risk_desc: "Zone-level risk forecast with patrol deployment recommendations.",
    report_card_patrol_deployment_title: "Patrol Deployment Plan",
    report_card_patrol_deployment_desc: "Recommended patrol schedules by zone, time, and risk level.",
    report_card_trend_analysis_title: "Trend Analysis Report",
    report_card_trend_analysis_desc: "Historical patterns, seasonal trends, and category comparisons.",
    report_card_settlement_compliance_title: "Settlement Compliance Report",
    report_card_settlement_compliance_desc: "Status of all active settlement agreements and compliance tracking.",
    report_card_comparative_period_title: "Comparative Period Report",
    report_card_comparative_period_desc: "Side-by-side comparison of two date ranges (e.g. Q1 vs Q2).",
    th_report: "Report",
    th_frequency: "Frequency",
    th_next_run: "Next Run",
    th_recipients: "Recipients",
    th_format: "Format",
    th_enabled: "Enabled",
    th_report_name: "Report Name",
    th_generated_by: "Generated By",
    th_date: "Date",
    th_period: "Period",
    th_actions: "Actions",
    all_statuses: "All Statuses",
    view_archived: "View Archived",
    view_active: "View Active",
    prev_label: "‹ Prev",
    next_label: "Next ›",
    action: "Action",
    actions: "Actions",
    th_timestamp: "Timestamp",
    th_user: "User",
    th_module: "Module",
    th_details: "Details",
    created_action: "CREATED",
    deleted_action: "DELETED",
    updated_action: "UPDATED",
    login_action: "LOGIN",

    // Dashboard & Global Headers
    search_records_placeholder: "Search records (Case ID, name, date)…",
    search_users_placeholder: "Search users…",
    welcome_overview: "Welcome back! Here's today's overview.",

    // Card Metrics & Sub-labels
    total_blotters: "Total Blotters",
    blotter_entries_on_file: "blotter entries on file",
    incident_reports: "Incident Reports",
    new_this_week: "New this week",
    pending_settlement: "Pending Settlement",
    awaiting_settlement: "awaiting settlement",
    awaiting_settlement_cap: "Awaiting settlement",
    resolved_cases: "Resolved Cases",
    resolved_lowercase: "resolved",
    risk_forecast: "RISK FORECAST",
    risk_rankings_title: "View This Week's Zone Risk Rankings",
    risk_hotspots_desc: "Model-predicted hotspots by zone →",

    // Quick Actions & Section Headers
    manage_blotter_records: "Manage all barangay blotter records",
    recent_blotter_entries: "Recent Blotter Entries",
    resolution_rate: "Resolution Rate",
    view_all_arrow: "View All →",
    quick_actions: "Quick Actions",
    quick_blotter_records: "Blotter Records",
    quick_new_incident: "New Incident Report",
    quick_monitor_settlement: "Monitor Settlement",
    quick_generate_report: "Generate Report",
    quick_import_census: "Import Census CSV",
    quick_users_roles: "Users & Roles",

    // Role Permission Matrix
    role_permission_matrix: "Role Permission Matrix",
    th_permission: "Permission",
    role_col_admin: "SYSTEM ADMIN",
    role_col_captain: "BARANGAY CAPTAIN",
    role_col_officer: "DESK OFFICER",
    role_col_encoder: "DATA ENCODER",
    perm_view_all_records: "View All Records",
    perm_add_blotter_entry: "Add Blotter Entry",
    perm_edit_any_record: "Edit Any Record",
    perm_delete_records: "Delete Records",
    perm_archive_records: "Archive Records",
    perm_generate_reports: "Generate Reports",
    perm_view_analytics: "View Analytics",
    perm_manage_users: "Manage Users",
    perm_retrain_ml_model: "Retrain ML Model",
    perm_import_csv_excel: "Import CSV/Excel",
    perm_system_settings: "System Settings",

    // Badges & Headings
    protected: "Protected",
    system_users: "System Users",

    // Barangay Census
    barangay_census: "Barangay Census",
    census_description: "Official list of registered residents of Barangay Mapulang Lupa",
    add_resident: "+ Add Resident",
    total_residents: "Total Residents",
    registered_in_barangay: "registered in barangay",
    total_households: "Total Households",
    indexed_residences: "indexed residences",
    registered_voters: "Registered Voters",
    active_precinct_voters: "active precinct voters",
    senior_citizens: "Senior Citizens",
    senior_care_sub: "60+ years & special care",
    resident_records: "Resident Records",
    search_name_address_placeholder: "Search name, address…",

    // Incident Reports
    incident_description: "Log and track all reported incidents in the barangay",
    total_reports: "Total Reports",
    incident_logs_on_record: "incident logs on record",
    high_priority: "High Priority",
    urgent_attention_required: "urgent attention required",
    under_investigation: "Under Investigation",
    in_progress_by_officers: "in progress by officers",
    referred_status: "Referred",
    referred_to_blotter_lupon: "referred to blotter & lupon",
    search_incident_placeholder: "Search report no., location, reporter…",

    // Settlement / Compliance Monitoring
    settlement_monitoring_title: "Monitoring of Compliance to Settlement or Award",
    settlement_monitoring_desc: "Track and manage settlement agreements and compliance status",
    total_cases: "Total Cases",
    status_pending: "Pending",
    status_complied: "Complied",
    status_not_complied: "Not Complied",
    add_settlement_record: "+ Add Settlement Record",
    settlement_records: "Settlement Records",
    search_settlement_placeholder: "Search case no., title…",

    // Barangay Clearance
    barangay_clearance: "Barangay Clearance",
    clearance_description: "Issue and manage barangay clearance certificates",
    issue_new_clearance: "+ Issue New Clearance",
    issued_this_month: "Issued This Month",
    total_this_year: "Total This Year",
    revenue_fees: "Revenue (Fees)",
    issuance_log: "Issuance Log",
    certificate_preview: "Certificate Preview",
    print: "Print",
    search_clearance_placeholder: "Search…",

    // Other Certificates
    certificate_of_residency: "Certificate of Residency",
    residency_description: "Issue and manage certificates of residency",
    issue_new_certificate: "+ Issue New Certificate",
    search_residency_placeholder: "Search…",
    certificate_of_non_residency: "Certificate of Non-Residency",
    non_residency_description: "Issue and manage certificates of non-residency",
    search_non_residency_placeholder: "Search…",
    certificate_of_indigency: "Certificate of Indigency",
    indigency_description: "Issue certificates for financially indigent residents",
    issue_certificate: "+ Issue Certificate",
    common_purpose: "Common Purpose",
    search_indigency_placeholder: "Search…",

    // Heat Map
    incident_heat_map: "Incident Heat Map",
    heatmap_subtitle: "Map boundary overlay of Mapulang Lupa, Pandi, Bulacan",
    period_all_time: "All Time",
    period_this_month: "This Month",
    period_this_week: "This Week",
    show_incident_markers: "Show Incident Markers",
    mapulang_lupa_heat_map: "Mapulang Lupa Heat Map",
    visual_density_desc: "Visual density of reported incidents across Barangay Mapulang Lupa zones",
    zone_density_label: "Zone Density:",
    density_low: "Low",
    density_medium: "Medium",
    density_elevated: "Elevated",
    density_high: "High",
    badge_barangay: "Barangay:",
    badge_municipality: "Municipality:",
    badge_source: "Source:",
    badge_boundary_file: "Boundary file:",
    summary: "Summary",
    visible_incidents: "Visible Incidents",
    top_category: "Top Category",
    category_breakdown: "Category Breakdown",
    incident_location_summary: "Incident Location Summary",
    incident_location_summary_desc: "Only incidents inside the loaded barangay boundary are displayed on the map canvas",
    search_heatmap_placeholder: "Search by ID, location, category, or reporter...",
    all_zones: "All Zones (7 Zones)",
    all_categories: "All Categories",

    notifications: "Notifications",
    mark_all_read: "Mark all read",
    loading_notifications: "Loading notifications…",
    no_notifications: "No notifications yet.",
    notif_error: "Could not load notifications.",

    // Pagination
    showing_zero_incidents: "Showing 0 to 0 of 0 incidents",

    // Trends & Comparative Analytics
    trends_comparative_analytics: "Trends & Comparative Analytics",
    trends_subtitle: "Incident-to-blotter elevation, Lupon settlement rates, and spatial performance",
    total_incidents_metric: "Total Incidents",
    peak_month: "Peak Month",
    highest_incident_volume: "Highest incident volume",
    all_field_incident_logs: "All field incident logs",
    settlement_rate: "Settlement Rate",
    amicably_resolved_cases: "Amicably resolved cases",
    elevated_to_blotter: "Elevated to Blotter",
    official_docketed_cases: "Official docketed cases",
    monthly_comparative_pipeline: "Monthly Comparative Pipeline",
    monthly_pipeline_desc: "Field Incidents vs. Elevated Blotter Cases vs. Resolved",
    elevated_blotters: "Elevated Blotters",
    category_severity: "Category Severity",
    category_distribution: "Incidents & Elevation Distribution",
    zonal_matrix_title: "Zonal Elevation & Settlement Matrix",
    zonal_matrix_subtitle: "Administrative Zone 1 to Zone 7 comparative performance",
    official_admin_zones: "7 Official Administrative Zones",
    th_zone_substation: "ZONE / SUBSTATION",
    th_total_incidents: "TOTAL INCIDENTS",
    th_elevated_to_blotter: "ELEVATED TO BLOTTER",
    th_elevation_rate: "ELEVATION RATE",
    th_resolved_cases: "RESOLVED CASES",
    th_status_col: "STATUS",
    incidents_by_day_of_week: "Incidents by Day of Week",
    weekly_occurrence_distribution: "Weekly occurrence distribution",
    top_incident_categories: "Top Incident Categories",
    ranked_by_volume: "Ranked by volume",
    stable_control: "STABLE CONTROL",
    high_elevation: "HIGH ELEVATION",

    // Predictive Insights
    predictive_insights: "Predictive Insights",
    predictive_insights_desc: "ML-based incident risk forecasting by zone, time, and category",
    loading_latest_insights: "Loading latest insights...",
    retrain_model_btn: "Retrain Model",
    incident_occurrence_task: "INCIDENT OCCURRENCE",
    incident_type_task: "INCIDENT TYPE",
    hotspot_risk_task: "HOTSPOT RISK",
    accuracy_metric: "Accuracy",
    f1_score_metric: "F1 Score",
    forecast_expected_incidents: "7-Day Forecast — Expected Incidents",
    high_risk_zones: "High Risk Zones",
    moderate_risk_zones: "Moderate Risk Zones",
    low_risk_zones: "Low Risk Zones",
    all_zones_1_7: "All Zones (1 - 7)",
    next_7_days: "Next 7 Days",
    next_14_days: "Next 14 Days",
    patrol_recommendations: "Patrol Recommendations",
    category_forecast_by_zone: "Category Forecast by Zone",
    category_forecast_desc: "Expected incidents per day, broken down by category, for the selected zone",
    predicted_risk_by_zone: "Predicted Incident Risk by Zone",
    th_pred_zone: "SONA",
    th_pred_hotspot: "PROBABILIDAD NG HOTSPOT",
    th_pred_expected: "EXPECTED INCIDENTS (7D)",
    th_pred_risk: "ANTAS NG PANGANIB",
    th_pred_top_cat: "INAASAHANG PANGUNAHING KATEGORYA",
    th_pred_peak_time: "ORAS NG PINAKAMATAAS NA INSIDENTE",
    th_pred_trend: "14-DAY TREND",

    // System & Audit Settings
    manage_personnel_accounts: "Manage personnel accounts, roles, and access permissions",
    recent_audit_log: "Recent Audit Log",
    generate_reports_subtitle: "Generate, schedule, and download formatted reports",

    // [DATA MANAGEMENT & EXPORT]
    data_management: "Data Management",
    data_management_desc: "All records are stored in the PostgreSQL blottercast database. Records added on the Blotter and Incident pages automatically feed the Heat Map, Trends, and the Python ML Predictions module.",
    reset_demo_dataset: "Reset Demo Dataset",
    export_records_json: "Export Records (JSON)",

    // [ALERTS & NOTIFICATIONS]
    trigger_alert_risk_desc: "Trigger alert when predicted risk exceeds this value.",
    alert_spike_desc: "Alert when new incidents exceed this count in 24 hours.",
    in_app_notifications: "In-App Notifications",
    show_alerts_desc: "Show alerts in the notification center",
    model_retraining_alerts: "Model Retraining Alerts",
    notify_retrain_desc: "Notify when ML model retraining completes",

    // [SECURITY & PASSWORD RULES]
    password_must_contain: "PASSWORD MUST CONTAIN:",
    rule_len: "At least 6 characters long",
    rule_upper: "At least 1 uppercase letter (A–Z)",
    rule_lower: "At least 1 lowercase letter (a–z)",
    rule_num: "At least 1 number (0–9)",
    rule_special: "At least 1 special character (e.g., !@#$%^&*)",
    security_tip: "Security Tip",
    security_tip_desc: "NEVER REUSE PASSWORDS ACROSS MULTIPLE SYSTEMS",

    // [DISPLAY & AUTHENTICATION SETTINGS]
    display_preferences: "Display Preferences",
    system_time_format: "System Time Format",
    time_format_12h: "12-Hour (hh:mm A) (e.g. 01:45 PM)",
    security_and_authentication: "Security & Authentication",
    admin_master_control: "Admin Master Control",
    enforce_2fa_all_accounts: "Enforce 2FA for All Accounts",
    require_2fa_desc: "Require Two-Factor Authentication across all roles during login.",
    session_inactivity_auto_logout: "Session Inactivity Auto-Logout (2 Hours)",
    auto_logout_desc: "Automatically logs out inactive users after 120 minutes of inactivity.",
    policy_thresholds_password_rules: "Policy Thresholds & Password Rules",
    inactivity_timeout_duration: "Inactivity Timeout Duration (minutes)",
    default_timeout_desc: "Default: 120 minutes (2 hours).",
    max_failed_logins: "Max Failed Login Attempts",
    min_password_length: "Minimum Password Length",
    password_expiry_days: "Password Expiry (days)",
    data_privacy: "Data Privacy",
    audit_trail_logging: "Audit Trail Logging",
    log_data_changes_desc: "Log all data changes, logins, and report exports",
    data_subject_rights_module: "Data Subject Rights Module",
    data_subject_rights_desc: "Allow data access/correction requests from data subjects",

    // [BACKUP & RECOVERY]
    automated_backup: "Automated Backup",
    backup_frequency: "Backup Frequency",
    backup_time: "Backup Time",
    backup_destination: "Backup Destination",
    retain_backups_days: "Retain Backups For (days)",
    backups_scheduled_desc: "Backups are scheduled and executed autonomously by the backend server worker in Asia/Manila standard time (UTC+8).",
    perform_backup_now: "Perform Backup Now",
    recovery_objectives: "Recovery Objectives",
    recovery_time_objective: "Recovery Time Objective (RTO)",
    rto_desc: "Maximum acceptable downtime after failure.",
    recovery_point_objective: "Recovery Point Objective (RPO)",
    rpo_desc: "Maximum acceptable data loss window.",
    backup_history: "Backup History",

    // [MODALS & DIALOGS]
    log_out: "Log Out",
    confirm_logout_message: "Are you sure you want to log out?"
  },
  tl: {
    // Common Actions
    cancel: "Kanselahin",
    import_data: "Mag-import",
    export_excel: "I-export sa Excel",
    download: "I-download",
    view_edit: "Tignan at Baguhin",
    delete: "Burahin",
    close: "Isara",
    save: "I-save",
    save_changes: "I-save ang mga Pagbabago",
    confirm: "Kumpirmahin",
    submit: "Isumite",
    permanent_delete: "Permanenteng Burahin",
    back: "Bumalik",
    next: "Susunod",
    clear: "Linisin",
    reset: "I-reset",
    filter: "Salain",
    replace: "Palitan",
    browse_files: "Mag-browse ng mga file",
    browse_files_cap: "Mag-browse ng mga File",
    upload_import: "I-upload at I-import",
    processing: "Pinoproseso...",
    please_wait: "Mangyaring maghintay...",
    done: "Tapos na",

    // Modal Headers & Labels
    import_resident_title: "Mag-import ng Datos ng Residente",
    export_blotter_title: "I-export ang Tala ng Blotter",
    period_label: "Panahon",
    year_label: "Taon",
    month_label: "Buwan",

    // Dropdown Options
    period_all: "Lahat ng Tala",
    period_year: "Tiyak na Taon",
    period_month: "Tiyak na Buwan",

    month_jan: "Enero",
    month_feb: "Pebreo",
    month_mar: "Marso",
    month_apr: "Abril",
    month_may: "Mayo",
    month_jun: "Hunyo",
    month_jul: "Hulyo",
    month_aug: "Agosto",
    month_sep: "Setyembre",
    month_oct: "Oktubre",
    month_nov: "Nobyembre",
    month_dec: "Disyembre",

    months: {
      jan: "Enero",
      feb: "Pebreo",
      mar: "Marso",
      apr: "Abril",
      may: "Mayo",
      jun: "Hunyo",
      jul: "Hulyo",
      aug: "Agosto",
      sep: "Setyembre",
      oct: "Oktubre",
      nov: "Nobyembre",
      dec: "Disyembre"
    },

    // Census Import Modal
    import_resident_title: "Mag-import ng Datos ng Residente",
    drag_drop_text: "I-drag at I-drop ang CSV o Excel file (.xlsx, .xls) dito o I-click para mag-upload",
    supported_files_census: "Suportadong mga uri: CSV, Excel (.xlsx, .xls)",
    download_resident_template: "I-download ang Resident Census Template (.csv)",
    selected_file: "Napiling File",
    file_ready_import: "Handa na ang file para sa pag-import",

    // Resident Modal (Census)
    add_resident_title: "Magdagdag ng Residente",
    edit_resident_title: "I-edit ang Residente",
    save_resident: "I-save ang Residente",
    resident_no: "Blg. ng Residente",
    resident_no_ph: "Awtomatikong bubuuin sa pag-save",
    last_name: "Apelyido",
    last_name_ph: "Apelyido",
    first_name: "Pangalan",
    first_name_ph: "Pangalan",
    middle_name: "Gitnang Pangalan",
    middle_name_ph: "Gitnang pangalan (opsyonal)",
    dob: "Araw ng Kapanganakan",
    sex: "Kasarian",
    select_sex: "-Pumili-",
    male: "Lalaki",
    female: "Babae",
    civil_status: "Katayuang Sibil",
    select_civil_status: "-Pumili-",
    single: "Walang Asawa",
    married: "May Asawa",
    widowed: "Balo",
    separated: "Hiwalay",
    nationality: "Nasyonalidad",
    zone: "Sona / Purok",
    select_zone: "-Pumili-",
    address: "Tirahan / Kalye",
    address_ph: "Blk, Lot, Kalye",
    household_no: "Blg. ng Sambahayan",
    household_no_ph: "HH-001",
    contact_no: "Numero ng Telepono",
    voter_status: "Katayuan sa Pagboto",
    registered_voter: "Rehistradong Botante",
    not_registered: "Hindi Rehistrado",
    deactivated: "Hindi Aktibo (Deactivated)",
    occupation: "Trabaho / Propesyon",
    occupation_ph: "hal. Magsasaka, Guro",
    status: "Katayuan",
    active: "Aktibo",
    deceased: "Yumao",
    transferred: "Lumipat",
    resident_profile_details: "Mga Detalye ng Profile ng Residente",
    deceased_hint: "Ang Katayuan sa Pagboto ay awtomatikong itinatakda sa Deactivated para sa mga yumaong residente.",

    // Blotter Import Modal
    import_blotter_title: "Mag-import ng Datos ng Blotter",
    import_type: "Uri ng Pag-import",
    blotter_entry_record: "Rekord ng Blotter Entry",
    blotter_entry_record_desc: "Nag-i-import ng tala ng mga kaso at awtomatikong lumilikha ng mga ulat ng insidente na may coordinate para sa Heatmap at Prediction.",
    blotter_record: "Rekord ng Blotter",
    blotter_record_desc: "Nag-a-update ng progreso ng kaso at nag-uugnay ng mga tala sa Settlement Monitor.",
    csv_templates: "Mga CSV Template:",
    blotter_entry_csv: "Blotter Entry (.csv)",
    blotter_record_csv: "Blotter Record (.csv)",
    click_choose_drag_drop: "I-click para pumili ng file o i-drag at i-drop",
    supports_xlsx_csv: "Suportado ang .xlsx at .csv (Hanggang 10MB)",

    // Blotter Entry Modal
    new_blotter_entry: "Bagong Rekord ng Blotter",
    edit_blotter_entry: "I-edit ang Rekord ng Blotter",
    docket_no: "Blg. ng Docket",
    date_filed: "Petsa ng Paghahain",
    name_of_complainant: "Pangalan ng Nagrereklamo",
    not_a_resident: "Hindi residente / taga-labas",
    search_census_ph: "Mag-type ng pangalan para hanapin sa Census…",
    full_name_ph: "Buong pangalan",
    complainant_address: "Tirahan ng Nagrereklamo",
    name_of_respondent: "Pangalan ng Inirereklamo",
    respondent_address: "Tirahan ng Inirereklamo",
    nature_of_case: "Uri ng Kaso",
    nature_of_case_ph: "hal. Pananakit / Alitan sa Hangganan",
    type: "Uri",
    criminal: "Kriminal",
    civil: "Sibil",
    pending: "Nakabinbin",
    save_entry: "I-save ang Rekord",
    blotter_record_details: "Mga Detalye ng Rekord ng Blotter",
    blotter_rule_note_1: "Maaaring markahan ang nagrereklamo o inirereklamo bilang 'Hindi residente' kung sila ay taga-labas ng barangay.",
    blotter_rule_note_2: "Ngunit hindi pareho, dahil hindi bababa sa isang partido ang dapat rehistradong residente sa Census.",

    // Incident Modal
    new_incident_report: "Bagong Ulat ng Insidente",
    edit_incident_report: "I-edit ang Ulat ng Insidente",
    save_report: "I-save ang Ulat",
    report_no: "Blg. ng Ulat",
    date_reported: "Petsa ng Pag-uulat",
    time_reported: "Oras ng Pag-uulat",
    location_detail: "Detalye ng Lokasyon",
    location_detail_ph: "hal. Pandi Encampment One, Ph1 Blk24 Lot 4 Residence 1…",
    zone_mismatch_title: "May Hindi Pagtutugma sa Sona at Lokasyon",
    zone_mismatch_desc: "Ang inilagay na lokasyon ay tumutugma sa ibang sona.",
    switch_zone: "Lumipat sa Sona",
    geocoded_pin_boundary: "Geocoded na Pin at Hangganan",
    unverified_location: "Hindi pa Beripikadong Lokasyon",
    geocode_location: "Geocode ang Lokasyon",
    toggle_mini_map: "Ipakita/Itago ang Mini-Map",
    wide_view: "Malapad na View",
    category: "Kategorya",
    priority_level: "Lebel ng Prayoridad",
    high: "Mataas",
    medium: "Katamtaman",
    low: "Mababa",
    description: "Paglalarawan",
    description_ph: "Detalyadong paglalarawan ng insidente…",
    reporter_name: "Pangalan ng Nag-ulat",
    non_resident_reporter: "Hindi Residente na Nag-ulat",
    reporter_address: "Tirahan ng Nag-ulat (Munisipalidad / Lokasyon)",
    reporter_address_ph: "Labas ng Barangay / tukuyin ang munisipalidad o tirahan",
    responding_officer: "Rumespondeng Opisyal",
    responding_officer_ph: "hal. PO1 Cruz",
    elevate_to_blotter: "Iakyat sa Blotter",
    already_elevated: "Naiakyat Na",
    incident_report_details: "Mga Detalye ng Ulat ng Insidente",
    view_in_heatmap: "Tingnan sa Heatmap",
    elevate_confirm_title: "Iakyat ang Insidente sa Opisyal na Blotter?",
    elevate_confirm_body: "Ang aksyong ito ay hindi na maaaring bawiin o ipagpaliban. Ang pag-aakyat ng ulat na ito ay permanenteng magla-lock sa ulat ng insidente at lilikha ng opisyal na kaso sa Blotter para sa pamamagitan ng Lupon.",
    proceed_to_blotter_form: "Tumuloy sa Form ng Blotter",

    // Certificate Modals (Clearance, Residency, Non-Residency, Indigency)
    issue_clearance_title: "Mag-isyu ng Barangay Clearance",
    issue_residency_title: "Mag-isyu ng Katunayan ng Paninirahan (Residency)",
    issue_non_residency_title: "Mag-isyu ng Katunayan ng Hindi Paninirahan (Non-Residency)",
    issue_indigency_title: "Mag-isyu ng Katunayan ng Kawalan ng Sapat na Kita (Indigency)",
    resident_label: "Residente",
    search_resident_ph: "Mag-type ng pangalan para maghanap...",
    full_name: "Buong Pangalan",
    age: "Edad",
    purpose_of_clearance: "Layunin ng Clearance",
    purpose_of_certificate: "Layunin ng Sertipiko",
    or_number: "Blg. ng O.R.",
    amount_paid: "Halagang Binayaran (₱)",
    duration_of_residency: "Tagal ng Paninirahan",
    years: "Taon",
    months: "Buwan",
    previous_home_address: "Dating Tirahan sa Barangay na Ito",
    requested_by_purpose: "Hiningi Ni / Layunin",
    issue_preview: "I-isyu at I-preview",
    derogatory_alert: "Babala sa Rekord (Derogatory Alert)",
    applicant_active_blotter: "Ang aplikante ay may aktibong rekord sa blotter",

    // Certificate Modals additions
    census_inheritance_help: "Maaari lamang mag-isyu ng sertipiko sa taong nakatala na sa Census. Ang pangalan, edad, katayuang sibil, at tirahan ay awtomatikong magmumula sa talaang iyon.",
    indigency_blotter_warning: "Ang residenteng ito ay nakatala bilang Respondent sa aktibo o hindi pa nareresolbang kaso sa blotter. Hindi maaaring ibigay ang Certificate of Indigency hangga't hindi nareresolba ang lahat ng kaso.",
    indigency_note: "Ang pagpapatunay ng kahirapan (indigency) ay responsibilidad ng Punong Barangay. Siguraduhing napatunayan ang estado sa pananalapi ng aplikante bago mag-isyu.",
    note_label: "Paunawa:",
    select_placeholder: "-Pumili-",

    // Settlement Modals
    new_settlement_title: "Bagong Rekord ng Pag-aayos",
    edit_settlement_title: "I-edit ang Rekord ng Pag-aayos",
    link_blotter_case: "Iugnay sa Kaso ng Blotter",
    search_blotter_ph: "Mag-type ng docket no. o pangalan para hanapin sa Blotter…",
    search_docket_complainant_hint: "(Maghanap ng docket no. o nagrereklamo)",
    auto_generated: "Awtomatikong bubuuin",
    auto_filled_blotter: "Awtomatikong kinuha sa Blotter",
    optional_notes: "Opsyonal na mga tala",
    blottercast_system_label: "BlotterCast Sistemang Pambarangay",
    case_no: "Blg. ng Kaso",
    case_title: "Pamagat ng Kaso",
    date_initial_confrontation: "Petsa ng Unang Pagtutuos",
    action_taken: "Hakbang na Isinagawa",
    date_of_settlement: "Petsa ng Pagkakasundo o Gawad",
    date_of_execution: "Petsa ng Pagpapatupad",
    officer_in_charge: "Namumunong Opisyal / Tagapamagitan",
    officer_ph: "hal. Punong Barangay / Tagapangulo ng Pangkat",
    agreement_terms: "Pangunahing Kasunduan / Tuntunin ng Pag-aayos",
    agreement_terms_ph: "Pangunahing mga tuntunin at kundisyon ng kasunduan sa pag-aayos…",
    status_compliance: "Katayuan ng Pagsunod / Resolusyon",
    remarks: "Mga Tala / Puna",
    save_record: "I-save ang Rekord",
    settlement_hearing_details: "Mga Detalye ng Pagdinig sa Pag-aayos",

    // User Modals
    add_new_user_title: "Magdagdag ng Bagong Gumagamit",
    edit_user_title: "I-edit ang Gumagamit",
    personal_info_cap: "PERSONAL NA IMPORMASYON",
    roles_cap: "MGA GAMPANIN",
    security_cap: "SEGURIDAD",
    assign_user_role: "ITALAGA ANG GAMPANIN NG GUMAGAMIT",
    assigned_roles: "MGA NAKATALAGANG GAMPANIN",
    security_credentials: "SEGURIDAD AT MGA KREDENSYAL",
    read_only: "(Babasahin Lamang)",
    username: "Pangalan ng Gumagamit (Username)",
    email: "Email",
    contact_no: "Numero ng Telepono",
    temporary_password: "Pansamantalang Password",
    temp_password_hint: "Ang pansamantalang password na ito ay ipapadala sa email ng gumagamit. Kailangang i-update ng tatanggap ang kanilang kredensyal sa Settings sa unang pag-login.",
    e_signature: "Elektronikong Lagda (E-Signature)",
    e_sig_hint: "(ginagamit sa nakalimbag na Barangay Clearance at Certificate of Indigency)",
    no_sig_uploaded: "Walang nai-upload na lagda",
    upload_signature: "Mag-upload ng Lagda",
    remove_sig: "Alisin",
    sig_format_hint: "Inirerekomenda ang PNG na may transparent background, hanggang 2MB.",
    del_user_warning_box: "Babala: Ang aksyong ito ay hindi na mababawi. Ang lahat ng personal na datos, talaan ng aktibidad, at kredensyal ng pagpapatunay na nauugnay sa gumagamit na ito ay permanenteng buburahin sa database.",
    type_to_proceed: "I-type ang DELETE para magpatuloy:",
    copy_clipboard: "Kopyahin sa Clipboard",
    regenerate_password: "Bumuo Muli ng Password",
    save_user: "I-save ang Gumagamit",
    permanently_delete_user: "Permanenteng Burahin ang Gumagamit",
    destructive_removal: "Mapangwasak na Pag-alis ng Account",
    type_delete_confirm: "I-TYPE ANG DELETE PARA KUMFIRMAHIN",

    // Reports Modal & Page Controls
    generate_report_title: "Gumawa ng Ulat",
    date_from: "Mula sa Petsa",
    date_to: "Hanggang sa Petsa",
    zone_filter: "Salain ayon sa Sona",
    all_zones: "Lahat ng Sona",
    export_format: "Format ng Pag-export",
    pdf_document: "Dokumentong PDF",
    preview: "Silipin",
    generate: "Bumuo",
    scheduled_reports_title: "Naka-iskedyul na mga Ulat",
    recent_generated_reports_title: "Kamakailang Nabuo na mga Ulat",
    badge_pdf_only: "PDF LAMANG",
    report_card_incident_summary_title: "Ulat sa Buod ng Insidente",
    report_card_incident_summary_desc: "Lahat ng insidente sa napiling saklaw ng petsa na may breakdown ng kategorya at katayuan.",
    report_card_predictive_risk_title: "Pagtatasa ng Inaasahang Panganib",
    report_card_predictive_risk_desc: "Pagtataya ng panganib sa antas ng sona na may mga rekomendasyon sa pagpapakalat ng patrolya.",
    report_card_patrol_deployment_title: "Plano ng Pagpapakalat ng Patrolya",
    report_card_patrol_deployment_desc: "Inirerekomendang mga iskedyul ng patrolya ayon sa sona, oras, at antas ng panganib.",
    report_card_trend_analysis_title: "Ulat sa Pagsusuri ng Trend",
    report_card_trend_analysis_desc: "Mga historikal na pattern, pana-panahong trend, at paghahambing ng kategorya.",
    report_card_settlement_compliance_title: "Ulat sa Pagtupad sa Kasunduan",
    report_card_settlement_compliance_desc: "Katayuan ng lahat ng aktibong kasunduan sa settlement at pagsubaybay sa pagsunod.",
    report_card_comparative_period_title: "Ulat sa Paghahambing ng Panahon",
    report_card_comparative_period_desc: "Paghahambing ng dalawang saklaw ng petsa (hal. Q1 laban sa Q2).",
    th_report: "Ulat",
    th_frequency: "Dalas",
    th_next_run: "Susunod na Pagsasagawa",
    th_recipients: "Mga Tagatanggap",
    th_format: "Format",
    th_enabled: "Pinagana",
    th_report_name: "Pangalan ng Ulat",
    th_generated_by: "Binuo Ni",
    th_date: "Petsa",
    th_period: "Panahon",
    th_actions: "Mga Aksyon",
    all_statuses: "Lahat ng Status",
    view_archived: "Tignan ang Naka-arkibo",
    view_active: "Tignan ang Aktibo",
    prev_label: "‹ Nakalipas",
    next_label: "Susunod ›",
    action: "KILOS",
    actions: "Mga Aksyon",
    th_timestamp: "Petsa at Oras",
    th_user: "Gumagamit",
    th_module: "Modyul",
    th_details: "Mga Detalye",
    created_action: "GINAWA",
    deleted_action: "BINURA",
    updated_action: "INUPDATE",
    login_action: "NAG-LOGIN",

    // Dashboard & Global Headers
    search_records_placeholder: "Maghanap ng tala (Case ID, pangalan, petsa...)",
    search_users_placeholder: "Maghanap ng guma-gamit...",
    welcome_overview: "Maligayang pagbabalik! Narito ang buod ngayong araw.",

    // Card Metrics & Sub-labels
    total_blotters: "Kabuuan ng Blotter",
    blotter_entries_on_file: "mga tala ng blotter sa file",
    incident_reports: "Mga Ulat ng Insidente",
    new_this_week: "Bago ngayong linggo",
    pending_settlement: "Nakahimlay sa Pag-aayos",
    awaiting_settlement: "naghihintay ng pag-aayos",
    awaiting_settlement_cap: "Naghihintay ng pag-aayos",
    resolved_cases: "Mga Resolbadong Kaso",
    resolved_lowercase: "resolbado",
    risk_forecast: "PREDIKSYON NG PANGANIB",
    risk_rankings_title: "Tignan ang Antas ng Panganib sa Bawat Zone Ngayong Linggo",
    risk_hotspots_desc: "Mga inaasahang hotspot ayon sa zone →",

    // Quick Actions & Section Headers
    manage_blotter_records: "Pamahalaan ang lahat ng tala ng blotter sa barangay",
    recent_blotter_entries: "Mga Huling Tala ng Blotter",
    resolution_rate: "Antas ng Pagresolba",
    view_all_arrow: "Tignan Lahat →",
    quick_actions: "Mabilis na Aksyon",
    quick_blotter_records: "Mga Tala ng Blotter",
    quick_new_incident: "Bagong Ulat ng Insidente",
    quick_monitor_settlement: "Subaybayan ang Pag-aayos",
    quick_generate_report: "Gumawa ng Ulat",
    quick_import_census: "Mag-import ng Census CSV",
    quick_users_roles: "Mga Gumagamit at Tungkulin",

    // Role Permission Matrix
    role_permission_matrix: "Talahanayan ng Pahintulot ng Tungkulin",
    th_permission: "Pahintulot",
    role_col_admin: "TAGAPAMAHALA NG SISTEMA",
    role_col_captain: "PUNONG BARANGAY",
    role_col_officer: "DESK OFFICER",
    role_col_encoder: "DATA ENCODER",
    perm_view_all_records: "Tignan ang Lahat ng Tala",
    perm_add_blotter_entry: "Magdagdag ng Entry sa Blotter",
    perm_edit_any_record: "Baguhin ang Anumang Tala",
    perm_delete_records: "Burahin ang mga Tala",
    perm_archive_records: "I-arkibo ang mga Tala",
    perm_generate_reports: "Gumawa ng mga Ulat",
    perm_view_analytics: "Tignan ang Analytics",
    perm_manage_users: "Pamahalaan ang mga Gumagamit",
    perm_retrain_ml_model: "I-retrain ang Modelong ML",
    perm_import_csv_excel: "Mag-import ng CSV/Excel",
    perm_system_settings: "Mga Setting ng Sistema",

    // Badges & Headings
    protected: "Protektado",
    system_users: "Mga Gumagamit ng Sistema",

    // Barangay Census
    barangay_census: "Sensus ng Barangay",
    census_description: "Opisyal na talaan ng mga nakatatalang residente ng Barangay Mapulang Lupa",
    add_resident: "+ Magdagdag ng Residente",
    total_residents: "Kabuuan ng Residente",
    registered_in_barangay: "nakatala sa barangay",
    total_households: "Kabuuan ng Kaya-bahayan",
    indexed_residences: "nakatalang mga tahanan",
    registered_voters: "Rehistradong Botante",
    active_precinct_voters: "mga aktibong botante sa presinto",
    senior_citizens: "Mga Senior Citizen",
    senior_care_sub: "60+ taong gulang at nangangailangan ng tanging pangangalaga",
    resident_records: "Mga Tala ng Residente",
    search_name_address_placeholder: "Maghanap ng pangalan, tirahan...",

    // Incident Reports
    incident_description: "I-tala at subaybayan ang lahat ng inulat na insidente sa barangay",
    total_reports: "Kabuuan ng Ulat",
    incident_logs_on_record: "mga tala ng insidente sa rekord",
    high_priority: "Mataas na Priyoridad",
    urgent_attention_required: "kailangang aksyunan agad",
    under_investigation: "Kasalukuyang Inimbestigahan",
    in_progress_by_officers: "inaaksyunan ng mga opisyal",
    referred_status: "Isinangguni / Naireselba",
    referred_to_blotter_lupon: "isinangguni sa blotter at lupon",
    search_incident_placeholder: "Maghanap ng no. ng ulat, lokasyon, nag-ulat...",

    // Settlement / Compliance Monitoring
    settlement_monitoring_title: "Pagsubaybay sa Pagtupad sa Pag-aayos o Gawad",
    settlement_monitoring_desc: "Subaybayan at pamahalaan ang mga kasunduan sa pag-aayos at katayuan ng pagtupad",
    total_cases: "Kabuuan ng Kaso",
    status_pending: "Naghihintay",
    status_complied: "Nakatupad",
    status_not_complied: "Hindi Nakatupad",
    add_settlement_record: "+ Magdagdag ng Tala ng Pag-aayos",
    settlement_records: "Mga Tala ng Pag-aayos",
    search_settlement_placeholder: "Maghanap ng no. ng kaso, pamagat...",

    // Barangay Clearance
    barangay_clearance: "Barangay Clearance",
    clearance_description: "Mag-isyu at pamahalaan ang mga sertipiko ng barangay clearance",
    issue_new_clearance: "+ Mag-isyu ng Bagong Clearance",
    issued_this_month: "Nai-isyu Ngayong Buwan",
    total_this_year: "Kabuuan Ngayong Taon",
    revenue_fees: "Kikita / Halaga (Bayad)",
    issuance_log: "Talaan ng Pag-iisyu",
    certificate_preview: "Pasilip sa Sertipiko",
    print: "I-print",
    search_clearance_placeholder: "Maghanap…",

    // Other Certificates
    certificate_of_residency: "Katibayan ng Paninirahan",
    residency_description: "Mag-isyu at pamahalaan ang mga katibayan ng paninirahan",
    issue_new_certificate: "+ Mag-isyu ng Bagong Sertipiko",
    search_residency_placeholder: "Maghanap…",
    certificate_of_non_residency: "Katibayan ng Di-Paninirahan",
    non_residency_description: "Mag-isyu at pamahalaan ang mga katibayan ng di-paninirahan",
    search_non_residency_placeholder: "Maghanap…",
    certificate_of_indigency: "Katibayan ng Kawalan ng Sapat na Kita",
    indigency_description: "Mag-isyu ng mga katibayan para sa kapus-palad na mga residente",
    issue_certificate: "+ Mag-isyu ng Sertipiko",
    common_purpose: "Karaniwang Layunin",
    search_indigency_placeholder: "Maghanap…",

    // Heat Map
    incident_heat_map: "Mapa ng Insidente",
    heatmap_subtitle: "Overlay ng hangganan ng mapa ng Mapulang Lupa, Pandi, Bulacan",
    period_all_time: "Lahat ng Panahon",
    period_this_month: "Ngayong Buwan",
    period_this_week: "Ngayong Linggo",
    show_incident_markers: "Ipakita ang mga Marker ng Insidente",
    mapulang_lupa_heat_map: "Heat Map ng Mapulang Lupa",
    visual_density_desc: "Bísuwal na densidad ng mga inulat na insidente sa mga zone ng Barangay Mapulang Lupa",
    zone_density_label: "Densidad ng Zone:",
    density_low: "Mababa",
    density_medium: "Katamtaman",
    density_elevated: "Mataas-taas",
    density_high: "Mataas",
    badge_barangay: "Barangay:",
    badge_municipality: "Bayan:",
    badge_source: "Pinagmulan:",
    badge_boundary_file: "File ng Hangganan:",
    summary: "Buod",
    visible_incidents: "Nakikitang mga Insidente",
    top_category: "Nangungunang Kategorya",
    category_breakdown: "Paghahati ng Kategorya",
    incident_location_summary: "Buod ng Lokasyon ng Insidente",
    incident_location_summary_desc: "Tanging ang mga insidente sa loob ng hangganan ng barangay ang ipinapakita sa mapa",
    search_heatmap_placeholder: "Maghanap gamit ang ID, lokasyon, kategorya, o nag-ulat...",
    all_zones: "Lahat ng Zone (7 Zones)",
    all_categories: "Lahat ng Kategorya",

    notifications: "Mga Abiso",
    mark_all_read: "Markahan lahat na nabasa",
    loading_notifications: "Kinakarga ang mga abiso…",
    no_notifications: "Wala pang mga abiso.",
    notif_error: "Hindi maikarga ang mga abiso.",

    // Pagination
    showing_zero_incidents: "Ipinapakita ang 0 hanggang 0 sa 0 na insidente",

    // Trends & Comparative Analytics
    trends_comparative_analytics: "Mga Trend at Paghahambing ng Analitika",
    trends_subtitle: "Pagtataas mula insidente patungong blotter, antas ng pag-aayos sa Lupon, at pagganap ng bawat lugar",
    total_incidents_metric: "Kabuuan ng mga Insidente",
    peak_month: "Buwan na may Pinakamataas na Bilang",
    highest_incident_volume: "May pinakamataas na bilang ng insidente",
    all_field_incident_logs: "Lahat ng tala ng insidente sa larangan",
    settlement_rate: "Antas ng Pagkakasundo / Pag-aayos",
    amicably_resolved_cases: "Mapayapang naresolbang mga kaso",
    elevated_to_blotter: "Iniakyat sa Blotter",
    official_docketed_cases: "Opisyal na naitalang mga kaso",
    monthly_comparative_pipeline: "Paghahambing ng Daloy Kada Buwan",
    monthly_pipeline_desc: "Mga Insidente sa Larangan vs. Iniakyat sa Blotter vs. Naresolba",
    elevated_blotters: "Iniakyat sa Blotter",
    category_severity: "Antas ng Lahi/Kategorya ng Insidente",
    category_distribution: "Pamamahagi ng mga Insidente at Pag-aakyat ng Kaso",
    zonal_matrix_title: "Matris ng Pag-aakyat at Pagkakasundo Bawat Sona",
    zonal_matrix_subtitle: "Paghahambing ng pagganap ng Sona 1 hanggang Sona 7",
    official_admin_zones: "7 Opisyal na Sonang Pampangasiwaan",
    th_zone_substation: "SONA / SUBSTATION",
    th_total_incidents: "KABUAN NG INSIDENTE",
    th_elevated_to_blotter: "INIAKYAT SA BLOTTER",
    th_elevation_rate: "ANTAS NG PAG-AAKYAT SA BLOTTER",
    th_resolved_cases: "NARESOLBANG MGA KASO",
    th_status_col: "KALAGAYAN / STATUS",
    incidents_by_day_of_week: "Mga Insidente Ayon sa Araw ng Linggo",
    weekly_occurrence_distribution: "Pamamahagi ng paglitaw kada linggo",
    top_incident_categories: "Mga Nangungunang Kategorya ng Insidente",
    ranked_by_volume: "PinaSunod-sunod ayon sa dami",
    stable_control: "MAAYOS NA KONTROL",
    high_elevation: "MATAAS NA PAG-AAKYAT",

    // Predictive Insights
    predictive_insights: "Mga Pahiwatig at Hula ng AI",
    predictive_insights_desc: "Paghula ng panganib ng insidente gamit ang Machine Learning batay sa sona, oras, at kategorya",
    loading_latest_insights: "Ikinakarga ang pinakabagong pahiwatig...",
    retrain_model_btn: "Muling Sanayin ang Modelo (Retrain)",
    incident_occurrence_task: "Pagkakaroon ng Insidente",
    incident_type_task: "Uri ng Insidente",
    hotspot_risk_task: "Panganib sa Hotspot",
    accuracy_metric: "Katumpakan",
    f1_score_metric: "F1 Score",
    forecast_expected_incidents: "Hula para sa 7 Araw — Inaasahang mga Insidente",
    high_risk_zones: "Mga Sonang Mataas ang Panganib",
    moderate_risk_zones: "Mga Sonang Katamtaman ang Panganib",
    low_risk_zones: "Mga Sonang Mababa ang Panganib",
    all_zones_1_7: "Lahat ng Sona (1 - 7)",
    next_7_days: "Susunod na 7 Araw",
    next_14_days: "Susunod na 14 Araw",
    patrol_recommendations: "Mga Inirerekomendang Pagpapatrolya",
    category_forecast_by_zone: "Hula ng Kategorya Bawat Sona",
    category_forecast_desc: "Inaasahang insidente bawat araw, na nakahimay ayon sa kategorya, para sa napiling sona",
    predicted_risk_by_zone: "Inaasahang Panganib ng Insidente Bawat Sona",
    th_pred_zone: "SONA",
    th_pred_hotspot: "PROBABILIDAD NG HOTSPOT",
    th_pred_expected: "INAASAHANG MGA INSIDENTE (7 ARAW)",
    th_pred_risk: "ANTAS NG PANGANIB",
    th_pred_top_cat: "INAASAHANG PANGUNAHING KATEGORYA",
    th_pred_peak_time: "ORAS NG PINAKAMATAAS NA INSIDENTE",
    th_pred_trend: "TREND SA LOOB NG 14 ARAW",

    // System & Audit Settings
    manage_personnel_accounts: "Pamahalaan ang mga account ng tauhan, papel (roles), at pahintulot sa pag-access",
    recent_audit_log: "Kamakailang Talaan ng Pagsusuri (Audit Log)",
    generate_reports_subtitle: "Gumawa, mag-iskedyul, at mag-download ng mga naka-pormat na ulat",

    // [DATA MANAGEMENT & EXPORT]
    data_management: "Pamamahala ng Data",
    data_management_desc: "Ang lahat ng tala ay nakaimbak sa PostgreSQL blottercast database. Ang mga talang idinadagdag sa mga pahina ng Blotter at Incident ay awtomatikong nagpapakain sa Heat Map, Trends, at Python ML Predictions module.",
    reset_demo_dataset: "I-reset ang Sample na Data",
    export_records_json: "I-export ang mga Tala (JSON)",

    // [ALERTS & NOTIFICATIONS]
    trigger_alert_risk_desc: "Magpadala ng babala kapag ang inaasahang panganib ay lumampas sa halagang ito.",
    alert_spike_desc: "Magpadala ng babala kapag ang mga bagong insidente ay lumampas sa bilang na ito sa loob ng 24 oras.",
    in_app_notifications: "Mga Notification sa App",
    show_alerts_desc: "Ipakita ang mga babala sa notification center",
    model_retraining_alerts: "Mga Babala sa Muling Pagsasanay ng Modelo",
    notify_retrain_desc: "Magbigay-alam kapag natapos ang muling pagsasanay ng ML model",

    // [SECURITY & PASSWORD RULES]
    password_must_contain: "ANG PASSWORD AY DAPAT NAGLALAMAN NG:",
    rule_len: "Hindi bababa sa 6 na character",
    rule_upper: "Hindi bababa sa 1 malaking titik (A–Z)",
    rule_lower: "Hindi bababa sa 1 maliit na titik (a–z)",
    rule_num: "Hindi bababa sa 1 numero (0–9)",
    rule_special: "Hindi bababa sa 1 espesyal na karakter (hal. !@#$%^&*)",
    security_tip: "Tip sa Seguridad",
    security_tip_desc: "HUWAG KAILANMAN GAMITIN ANG PAREHONG PASSWORD SA IBANG SYSTEM",

    // [DISPLAY & AUTHENTICATION SETTINGS]
    display_preferences: "Mga Kagustuhan sa Display",
    system_time_format: "Format ng Oras ng System",
    time_format_12h: "12-Oras (hh:mm A) (hal. 01:45 PM)",
    security_and_authentication: "Seguridad at Pagpapatunay",
    admin_master_control: "Pangunahing Kontrol ng Admin",
    enforce_2fa_all_accounts: "Ipatupad ang 2FA sa Lahat ng Account",
    require_2fa_desc: "Hilingin ang Two-Factor Authentication sa lahat ng papel sa pag-login.",
    session_inactivity_auto_logout: "Awtomatikong Pag-logout kapag Walang Gawain (2 Oras)",
    auto_logout_desc: "Awtomatikong nilog-out ang mga user na walang activity pagkaraan ng 120 minuto.",
    policy_thresholds_password_rules: "Mga Patakaran at Tuntunin sa Password",
    inactivity_timeout_duration: "Tagal bago i-Logout kapag walang Gawain (minuto)",
    default_timeout_desc: "Default: 120 minuto (2 oras).",
    max_failed_logins: "Pinakamataas na Subok ng Maling Login",
    min_password_length: "Pinakamaikling Haba ng Password",
    password_expiry_days: "Pagpasa ng Password (araw)",
    data_privacy: "Privacy ng Data",
    audit_trail_logging: "Pagtatala ng Audit Trail",
    log_data_changes_desc: "Itala ang lahat ng pagbabago sa data, pag-login, at pag-export ng ulat",
    data_subject_rights_module: "Module para sa Karapatan sa Data Privacy",
    data_subject_rights_desc: "Payagan ang kahilingan sa pag-access o pagwawasto ng data mula sa mga indibidwal",

    // [BACKUP & RECOVERY]
    automated_backup: "Awtomatikong Backup",
    backup_frequency: "Dalas ng Backup",
    backup_time: "Oras ng Backup",
    backup_destination: "Pupuntahan ng Backup",
    retain_backups_days: "Itabi ang Backup ng (mga araw)",
    backups_scheduled_desc: "Ang mga backup ay naka-iskedyul at awtomatikong isinasagawa ng backend server worker batay sa Asia/Manila standard time (UTC+8).",
    perform_backup_now: "Magsagawa ng Backup Ngayon",
    recovery_objectives: "Mga Layunin sa Pagbawi (Recovery)",
    recovery_time_objective: "Target na Oras ng Pagbawi (RTO)",
    rto_desc: "Pinakamatagal na katanggap-tanggap na pagtigil ng system pagkatapos ng pagkasira.",
    recovery_point_objective: "Target na Halaga ng Nawalang Data (RPO)",
    rpo_desc: "Pinakamataas na katanggap-tanggap na saklaw ng nawalang data.",
    backup_history: "Kasaysayan ng Backup",

    // [MODALS & DIALOGS]
    log_out: "Mag-log Out",
    confirm_logout_message: "Sigurado ka bang gusto mong mag-log out?"
  }
};

function bcGetLanguage() {
  let lang = localStorage.getItem('app_language');
  if (lang) {
    if (lang.toLowerCase() === 'tl' || lang.toLowerCase().startsWith('fil') || lang.toLowerCase().startsWith('tag')) {
      return 'Filipino';
    }
    return 'English';
  }
  lang = localStorage.getItem('bc_language');
  if (!lang) {
    try {
      const cfg = JSON.parse(localStorage.getItem('barangayConfig') || '{}');
      lang = cfg.default_language;
    } catch (_) {}
  }
  if (lang && (lang.toLowerCase().startsWith('fil') || lang.toLowerCase().startsWith('tag') || lang.toLowerCase() === 'tl')) {
    return 'Filipino';
  }
  return 'English';
}

function bcSetLanguage(lang) {
  const normalized = (String(lang || '')).toLowerCase().startsWith('fil') || (String(lang || '')).toLowerCase().startsWith('tag') || (String(lang || '')).toLowerCase() === 'tl' ? 'Filipino' : 'English';
  const appLang = normalized === 'Filipino' ? 'tl' : 'en';
  localStorage.setItem('bc_language', normalized);
  localStorage.setItem('app_language', appLang);
  try {
    const raw = localStorage.getItem('barangayConfig');
    const cfg = raw ? JSON.parse(raw) : {};
    cfg.default_language = normalized;
    localStorage.setItem('barangayConfig', JSON.stringify(cfg));
  } catch (_) {}
  bcApplyLanguage(normalized);
  applyLanguageTranslation(appLang);
  window.dispatchEvent(new CustomEvent('bc-language-changed', { detail: { language: normalized, app_language: appLang } }));
}

function bcT(text, fallback) {
  const currentLang = bcGetLanguage();
  if (currentLang === 'Filipino' && BC_TRANSLATIONS.fil[text]) {
    return BC_TRANSLATIONS.fil[text];
  }
  return fallback || text;
}

function applyLanguageTranslation(lang) {
  let targetLang = lang;
  if (!targetLang) {
    targetLang = localStorage.getItem('app_language');
  }
  if (!targetLang) {
    const bc = localStorage.getItem('bc_language') || (typeof bcGetLanguage === 'function' ? bcGetLanguage() : 'English');
    targetLang = (bc.toLowerCase().startsWith('fil') || bc.toLowerCase().startsWith('tag') || bc.toLowerCase() === 'tl') ? 'tl' : 'en';
  }
  targetLang = (targetLang.toLowerCase().startsWith('fil') || targetLang.toLowerCase().startsWith('tag') || targetLang.toLowerCase() === 'tl') ? 'tl' : 'en';

  if (!window.i18n || !window.i18n[targetLang]) return;
  const dict = window.i18n[targetLang];

  // 1. Elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key && dict[key] !== undefined) {
      if (key === 'showing_zero_incidents') {
        const curText = el.textContent.trim();
        const numMatch = curText.match(/(\d+)\s+(?:to|hanggang)\s+(\d+)\s+(?:of|sa)\s+(\d+)/i);
        if (numMatch && Number(numMatch[3]) > 0) {
          const from = numMatch[1];
          const to = numMatch[2];
          const total = numMatch[3];
          el.textContent = targetLang === 'tl'
            ? `Ipinapakita ang ${from} hanggang ${to} sa ${total} na insidente`
            : `Showing ${from} to ${to} of ${total} incident${total !== '1' ? 's' : ''}`;
          return;
        }
      }
      const textSpan = el.querySelector('span:not([data-icon])');
      const icon = el.querySelector('svg, [data-icon], i');
      if (textSpan && (el.tagName === 'BUTTON' || el.tagName === 'A')) {
        textSpan.textContent = dict[key];
      } else if (icon && el.childNodes.length > 1) {
        let textFound = false;
        el.childNodes.forEach(node => {
          if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim().length > 0) {
            node.nodeValue = ' ' + dict[key];
            textFound = true;
          }
        });
        if (!textFound) {
          el.appendChild(document.createTextNode(' ' + dict[key]));
        }
      } else {
        el.textContent = dict[key];
      }
    }
  });

  // 2. Elements with data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (key && dict[key] !== undefined) {
      el.placeholder = dict[key];
    }
  });

  // 3. Elements with data-i18n-title
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    if (key && dict[key] !== undefined) {
      el.title = dict[key];
    }
  });
}

function isProperNounOrName(text) {
  if (!text || typeof text !== 'string') return false;
  const t = text.trim();
  if (!t) return false;

  // System brand name
  if (t === 'BlotterCast' || t.includes('BlotterCast')) return true;

  // Recipient accounts / usernames (e.g., kapitan, admin)
  if (/^(kapitan|admin)(,\s*(kapitan|admin))*$/i.test(t)) return true;
  if (t.toLowerCase() === 'kapitan' || t.toLowerCase() === 'admin' || t.toLowerCase() === 'kapitan, admin' || t.toLowerCase() === 'admin, kapitan') return true;

  // Zone or Purok names (e.g., Zone 1, Zone 2, Purok 1, etc.)
  if (/^Zone\s+\d+$/i.test(t) || /^Purok\s+\d+$/i.test(t)) return true;

  // House / Street address patterns
  if (/^(Blk|Lot|Phase|Ph\d)\s+/i.test(t)) return true;

  // Check against stored barangay configuration
  try {
    const raw = localStorage.getItem('barangayConfig');
    if (raw) {
      const cfg = JSON.parse(raw);
      if (cfg.barangay_name && t.toLowerCase() === cfg.barangay_name.trim().toLowerCase()) return true;
      if (cfg.captain_name && t.toLowerCase() === cfg.captain_name.trim().toLowerCase()) return true;
      if (cfg.municipality && t.toLowerCase() === cfg.municipality.trim().toLowerCase()) return true;
      if (cfg.province && t.toLowerCase() === cfg.province.trim().toLowerCase()) return true;
    }
  } catch (_) {}

  return false;
}
window.isProperNounOrName = isProperNounOrName;

function bcTranslateAuditAction(action) {
  if (!action) return '';
  const isTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  const act = String(action).trim();
  const actUpper = act.toUpperCase();

  if (isTl) {
    if (actUpper === 'CREATED') return 'GINAWA';
    if (actUpper === 'DELETED') return 'BINURA';
    if (actUpper === 'UPDATED') return 'INUPDATE';
    if (actUpper === 'LOGIN') return 'NAG-LOGIN';
    if (actUpper === 'LOGOUT') return 'NAG-LOGOUT';
    if (actUpper === 'BATCH_ARCHIVE' || actUpper === 'ARCHIVED') return 'INARKIBO';
    if (actUpper === 'BATCH_RESTORE' || actUpper === 'RESTORED') return 'IBINALIK';
    if (actUpper === 'BATCH_PERMANENT_DELETE' || actUpper === 'PERMANENT_DELETE') return 'BINURA';
    if (typeof bcT === 'function') return bcT(act, actUpper);
    return actUpper;
  }
  return act;
}
window.bcTranslateAuditAction = bcTranslateAuditAction;

function bcTranslateAuditDetails(details) {
  if (!details) return '';
  const isTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  const str = String(details).trim();
  if (!isTl) return str;

  // 1. "Account created: {user}" -> "Nakalikha ng account: {user}"
  let m = str.match(/^Account\s+created:\s*(.+)$/i);
  if (m) {
    return `Nakalikha ng account: ${m[1]}`;
  }

  // 2. "Account removed: {user}" -> "Nabura ang account: {user}"
  m = str.match(/^Account\s+(?:removed|deleted):\s*(.+)$/i);
  if (m) {
    return `Nabura ang account: ${m[1]}`;
  }

  // "Account updated: {user}" -> "Na-update ang account: {user}"
  m = str.match(/^Account\s+updated:\s*(.+)$/i);
  if (m) {
    return `Na-update ang account: ${m[1]}`;
  }

  // 3. "Successful login (Master 2FA Switch OFF)" -> "Matagumpay na pag-login (Naka-OFF ang Master 2FA)"
  m = str.match(/^Successful\s+login\s*\(Master\s+2FA\s+Switch\s+(OFF|ON)\)$/i);
  if (m) {
    return `Matagumpay na pag-login (Naka-${m[1].toUpperCase()} ang Master 2FA)`;
  }

  // 4. "Updated their own account details" -> "Inupdate ang sariling detalye ng account"
  if (/^Updated\s+their\s+own\s+account\s+details$/i.test(str)) {
    return "Inupdate ang sariling detalye ng account";
  }

  // 5. "System settings saved" -> "Naisave ang mga setting ng sistema"
  if (/^System\s+settings\s+saved$/i.test(str)) {
    return "Naisave ang mga setting ng sistema";
  }

  // Additional common system audit strings:
  if (/^Barangay\s+general\s+settings\s+updated$/i.test(str)) {
    return "Na-update ang mga pangkalahatang setting ng barangay";
  }
  if (/^Security\s+and\s+authentication\s+settings\s+updated$/i.test(str)) {
    return "Na-update ang mga setting ng seguridad at pagpapatunay";
  }
  if (/^User\s+logged\s+out$/i.test(str)) {
    return "Nag-log out ang gumagamit";
  }
  if (/^Password\s+changed$/i.test(str)) {
    return "Napalitan ang password";
  }
  if (/^Profile\s+photo\s+uploaded$/i.test(str)) {
    return "Na-upload ang larawan sa profile";
  }
  if (/^Profile\s+photo\s+removed$/i.test(str)) {
    return "Naalis ang larawan sa profile";
  }

  return str;
}
window.bcTranslateAuditDetails = bcTranslateAuditDetails;

function bcFormatThisWeekCount(count) {
  const isTl = (localStorage.getItem('app_language') || '').toLowerCase() === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  return isTl ? `↑ ${count} ngayong linggo` : `↑ ${count} this week`;
}
window.bcFormatThisWeekCount = bcFormatThisWeekCount;

function bcFormatResolutionRate(rate) {
  const isTl = (localStorage.getItem('app_language') || '').toLowerCase() === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  return isTl ? `${rate}% antas ng pagresolba` : `${rate}% resolution rate`;
}
window.bcFormatResolutionRate = bcFormatResolutionRate;

function bcFormatDateLocale(date) {
  const isTl = (localStorage.getItem('app_language') || '').toLowerCase() === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  const d = date instanceof Date ? date : new Date(date || Date.now());
  return d.toLocaleDateString(isTl ? 'tl-PH' : 'en-PH', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}
window.bcFormatDateLocale = bcFormatDateLocale;

function bcFormatUserGreeting(firstName) {
  const isTl = (localStorage.getItem('app_language') || '').toLowerCase() === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  if (firstName) {
    return isTl ? `Maligayang pagbabalik, ${firstName}. Narito ang buod ngayong araw.` : `Welcome back, ${firstName}. Here's today's overview.`;
  }
  return isTl ? "Maligayang pagbabalik! Narito ang buod ngayong araw." : "Welcome back! Here's today's overview.";
}
window.bcFormatUserGreeting = bcFormatUserGreeting;

function bcApplyLanguage(lang) {
  const normalized = (String(lang || '')).toLowerCase().startsWith('fil') || (String(lang || '')).toLowerCase().startsWith('tag') || (String(lang || '')).toLowerCase() === 'tl' ? 'Filipino' : 'English';
  const isFil = normalized === 'Filipino';
  document.documentElement.lang = isFil ? 'fil' : 'en';

  const dict = BC_TRANSLATIONS.fil || {};
  const getTrans = (orig) => {
    if (!orig) return orig;
    const trimmed = orig.trim();
    return dict[trimmed] || dict[trimmed.toLowerCase()] || dict[trimmed.toUpperCase()] || orig;
  };

  // 1. Sidebar Navigation links: replace text node, keep svg icon
  document.querySelectorAll('aside nav a.nav-link').forEach(link => {
    let textNode = null;
    for (let node of link.childNodes) {
      if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()) {
        textNode = node;
        break;
      }
    }
    if (!textNode) return;
    if (!link.dataset.bcOrigNav) {
      link.dataset.bcOrigNav = textNode.nodeValue.trim();
    }
    const orig = link.dataset.bcOrigNav;
    const translated = isFil ? getTrans(orig) : orig;
    textNode.nodeValue = ' ' + translated;
  });

  // 2. Sidebar Section Labels
  document.querySelectorAll('.nav-section-label').forEach(el => {
    if (!el.dataset.bcOrigText) el.dataset.bcOrigText = el.textContent.trim();
    const orig = el.dataset.bcOrigText;
    el.textContent = isFil ? getTrans(orig) : orig;
  });

  // 3. Settings Tabs
  document.querySelectorAll('.settings-tab').forEach(btn => {
    let textNode = null;
    for (let node of btn.childNodes) {
      if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()) {
        textNode = node;
        break;
      }
    }
    if (textNode) {
      if (!btn.dataset.bcOrigTab) btn.dataset.bcOrigTab = textNode.nodeValue.trim();
      const orig = btn.dataset.bcOrigTab;
      textNode.nodeValue = ' ' + (isFil ? getTrans(orig) : orig);
    }
  });

  // 4. Form Labels
  document.querySelectorAll('label.form-label, label').forEach(label => {
    if (label.closest('.sidebar-header') || label.hasAttribute('data-no-translate')) return;
    let textNode = null;
    for (let node of label.childNodes) {
      if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()) {
        textNode = node;
        break;
      }
    }
    if (textNode) {
      if (!label.dataset.bcOrigLabel) label.dataset.bcOrigLabel = textNode.nodeValue.trim();
      const orig = label.dataset.bcOrigLabel;
      if (!isProperNounOrName(orig)) {
        const trans = isFil ? getTrans(orig) : orig;
        textNode.nodeValue = trans + (textNode.nodeValue.endsWith(' ') ? ' ' : '');
      }
    }
  });

  // 5. Headings and Page Subtitles
  document.querySelectorAll('h1, h2, h3, h4, .page-header p, .modal-box h2, .modal-box h3').forEach(el => {
    if (el.closest('.sidebar-header') || el.classList.contains('sidebar-brand-title') || el.classList.contains('sidebar-brand-subtitle')) return;
    const t = el.textContent.trim();
    if (!el.dataset.bcOrigHeading) {
      el.dataset.bcOrigHeading = t;
    }
    const orig = el.dataset.bcOrigHeading;
    if (!isProperNounOrName(orig)) {
      if (isFil && (dict[orig] || getTrans(orig) !== orig)) {
        el.textContent = getTrans(orig);
      } else if (!isFil && el.dataset.bcOrigHeading) {
        el.textContent = el.dataset.bcOrigHeading;
      }
    }
  });

  // 6. Action buttons & button titles
  document.querySelectorAll('button, a.btn, a.btn-primary, a.btn-secondary, button[onclick*="save"], button[onclick*="Save"]').forEach(btn => {
    if (btn.closest('.sidebar-header') || btn.classList.contains('sidebar-brand-title')) return;

    // Check title attribute (e.g. View Details, Edit, Delete, Archive, Restore)
    if (btn.title) {
      if (!btn.dataset.bcOrigTitle) btn.dataset.bcOrigTitle = btn.title.trim();
      const origTitle = btn.dataset.bcOrigTitle;
      if (!isProperNounOrName(origTitle)) {
        btn.title = isFil ? getTrans(origTitle) : origTitle;
      }
    }

    if (btn.hasAttribute('data-i18n')) return;

    const textSpan = btn.querySelector('span:not([data-icon]):not([class*="icon"]):not(.badge)');
    if (textSpan && textSpan.textContent.trim()) {
      if (!textSpan.dataset.bcOrigText) textSpan.dataset.bcOrigText = textSpan.textContent.trim();
      const orig = textSpan.dataset.bcOrigText;
      if (!isProperNounOrName(orig)) {
        textSpan.textContent = isFil ? getTrans(orig) : orig;
      }
    } else {
      let textNode = null;
      for (let node of btn.childNodes) {
        if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()) {
          textNode = node;
          break;
        }
      }
      if (textNode) {
        if (!btn.dataset.bcOrigBtn) btn.dataset.bcOrigBtn = textNode.nodeValue.trim();
        const orig = btn.dataset.bcOrigBtn;
        if (!isProperNounOrName(orig)) {
          const trans = isFil ? getTrans(orig) : orig;
          textNode.nodeValue = ' ' + trans;
        }
      }
    }
  });

  // 7. Table column headers (th)
  document.querySelectorAll('table th').forEach(th => {
    let textNode = null;
    for (let node of th.childNodes) {
      if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()) {
        textNode = node;
        break;
      }
    }
    if (textNode) {
      if (!th.dataset.bcOrigTh) th.dataset.bcOrigTh = textNode.nodeValue.trim();
      const orig = th.dataset.bcOrigTh;
      if (!isProperNounOrName(orig)) {
        textNode.nodeValue = isFil ? getTrans(orig) : orig;
      }
    } else if (th.textContent.trim()) {
      if (!th.dataset.bcOrigTh) th.dataset.bcOrigTh = th.textContent.trim();
      const orig = th.dataset.bcOrigTh;
      if (!isProperNounOrName(orig)) {
        th.textContent = isFil ? getTrans(orig) : orig;
      }
    }
  });

  // 8. Status Badges (.badge, [class*="badge"], .status-badge)
  document.querySelectorAll('.badge, span[class*="badge"], .status-badge').forEach(badge => {
    if (badge.hasAttribute('data-no-translate') || badge.closest('.sidebar-header')) return;
    let textNode = null;
    for (let node of badge.childNodes) {
      if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()) {
        textNode = node;
        break;
      }
    }
    if (textNode) {
      if (!badge.dataset.bcOrigBadge) badge.dataset.bcOrigBadge = textNode.nodeValue.trim();
      const orig = badge.dataset.bcOrigBadge;
      if (!isProperNounOrName(orig)) {
        textNode.nodeValue = isFil ? getTrans(orig) : orig;
      }
    } else if (badge.textContent.trim()) {
      if (!badge.dataset.bcOrigBadge) badge.dataset.bcOrigBadge = badge.textContent.trim();
      const orig = badge.dataset.bcOrigBadge;
      if (!isProperNounOrName(orig)) {
        badge.textContent = isFil ? getTrans(orig) : orig;
      }
    }
  });

  // 9. Drop-down option lists (select option)
  document.querySelectorAll('select').forEach(sel => {
    const selId = (sel.id || '').toLowerCase();
    const selName = (sel.name || '').toLowerCase();
    // Exclude selects for resident names, user accounts, and officials
    if (selId.includes('resident') && !selId.includes('status') && !selId.includes('sex') && !selId.includes('civil')) return;
    if (selId.includes('official') || selId.includes('officer') || selId.includes('user') || selId.includes('captain')) return;
    if (selName.includes('resident') || selName.includes('official') || selName.includes('user')) return;

    sel.querySelectorAll('option').forEach(opt => {
      const t = opt.textContent.trim();
      if (!t) return;
      if (!opt.dataset.bcOrigOpt) opt.dataset.bcOrigOpt = t;
      const orig = opt.dataset.bcOrigOpt;
      if (isProperNounOrName(orig)) return; // Strictly exclude proper nouns like Zone 1, Zone 2...
      const trans = isFil ? getTrans(orig) : orig;
      opt.textContent = trans;
    });
  });

  // 10. Sync select dropdown if on settings page
  const langSelect = document.querySelector('select[data-setting="default_language"]');
  if (langSelect && langSelect.value !== normalized) {
    langSelect.value = normalized;
  }

  // 11. Run modal / data-i18n translations
  applyLanguageTranslation(isFil ? 'tl' : 'en');

  // 12. Dynamic pagination text and record counts across tables
  document.querySelectorAll('[id*="PaginationInfo"], [id*="paginationInfo"], [id*="PagInfo"], [id*="pagInfo"], .pagination-info, [id*="recordCount"], [id*="RecordCount"]').forEach(el => {
    const text = el.textContent.trim();
    if (isFil) {
      const incMatch = text.match(/Showing\s+(\d+)\s+to\s+(\d+)\s+of\s+(\d+)\s+incidents?/i);
      if (incMatch) {
        el.textContent = `Ipinapakita ang ${incMatch[1]} hanggang ${incMatch[2]} sa ${incMatch[3]} na insidente`;
        return;
      }
      const match = text.match(/Showing\s+(\d+)\s*[–\-]\s*(\d+)\s+of\s+(\d+)/i);
      if (match) {
        el.textContent = `Ipinapakita ang ${match[1]}–${match[2]} ng ${match[3]}`;
        return;
      }
      const recMatch = text.match(/^(\d+)\s+records$/i);
      if (recMatch) {
        el.textContent = `${recMatch[1]} mga tala`;
        return;
      }
    } else {
      const incMatch = text.match(/Ipinapakita\s+ang\s+(\d+)\s+hanggang\s+(\d+)\s+sa\s+(\d+)\s+(?:(?:na|\(na\))\s+)?insidente/i);
      if (incMatch) {
        el.textContent = `Showing ${incMatch[1]} to ${incMatch[2]} of ${incMatch[3]} incidents`;
        return;
      }
      const match = text.match(/Ipinapakita\s+ang\s+(\d+)\s*[–\-]\s*(\d+)\s+ng\s+(\d+)/i);
      if (match) {
        el.textContent = `Showing ${match[1]}–${match[2]} of ${match[3]}`;
        return;
      }
      const recMatch = text.match(/^(\d+)\s+mga\s+tala$/i);
      if (recMatch) {
        el.textContent = `${recMatch[1]} records`;
        return;
      }
    }
  });

  // 13. Pagination buttons
  document.querySelectorAll('button.pagination-btn').forEach(btn => {
    const t = btn.textContent.trim();
    if (isFil) {
      if (t === '‹ Prev' || t === '‹ Previous') btn.textContent = '‹ Nakalipas';
      if (t === 'Next ›') btn.textContent = 'Susunod ›';
    } else {
      if (t === '‹ Nakalipas') btn.textContent = '‹ Prev';
      if (t === 'Susunod ›') btn.textContent = 'Next ›';
    }
  });

  // 14. If scheduled reports table is present, re-render to reflect language
  if (typeof renderScheduledReports === 'function') {
    renderScheduledReports();
  }

  // 15. If audit log is present, re-render to reflect language
  if (typeof loadAuditLog === 'function') {
    loadAuditLog(true).catch(() => {});
  }

  // 16. Current date formatting on header
  const curDateEl = document.getElementById('currentDate');
  if (curDateEl) {
    curDateEl.textContent = typeof bcFormatDateLocale === 'function' ? bcFormatDateLocale(new Date()) : new Date().toLocaleDateString(isFil ? 'tl-PH' : 'en-PH', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  }

  // 17. User Greeting
  document.querySelectorAll('[data-user-greeting]').forEach(el => {
    let name = '';
    try {
      const u = JSON.parse(localStorage.getItem('currentUser') || localStorage.getItem('bc_user') || '{}');
      name = u.full_name || u.firstName || u.first_name || '';
    } catch (_) {}
    const firstName = name ? (typeof bcFirstName === 'function' ? bcFirstName(name) : name.split(' ')[0]) : '';
    el.textContent = typeof bcFormatUserGreeting === 'function' ? bcFormatUserGreeting(firstName) : (firstName ? `Welcome back, ${firstName}. Here's today's overview.` : "Welcome back! Here's today's overview.");
  });
  const greetingEl = document.getElementById('dashboardGreeting');
  if (greetingEl) {
    let name = '';
    try {
      const u = JSON.parse(localStorage.getItem('currentUser') || localStorage.getItem('bc_user') || '{}');
      name = u.full_name || u.firstName || u.first_name || '';
    } catch (_) {}
    const firstName = name ? (typeof bcFirstName === 'function' ? bcFirstName(name) : name.split(' ')[0]) : '';
    greetingEl.textContent = typeof bcFormatUserGreeting === 'function' ? bcFormatUserGreeting(firstName) : (firstName ? `Welcome back, ${firstName}. Here's today's overview.` : "Welcome back! Here's today's overview.");
  }

  // 18. Stat cards sub-labels
  const blSub = document.getElementById('statBlottersSub') || document.getElementById('blTotalSub');
  if (blSub) {
    blSub.textContent = isFil ? 'mga tala ng blotter sa file' : 'blotter entries on file';
  }
  const pendSub = document.getElementById('blPendingSub');
  if (pendSub) {
    pendSub.textContent = isFil ? 'naghihintay ng pag-aayos' : 'awaiting settlement';
  }
  const incSub = document.getElementById('statIncidentsSub') || document.getElementById('blOngoingSub');
  if (incSub && incSub.textContent) {
    const numMatch = incSub.textContent.match(/(\d+)/);
    if (numMatch) {
      incSub.textContent = `↑ ${numMatch[1]} ${isFil ? 'ngayong linggo' : 'this week'}`;
    }
  }
  const resSub = document.getElementById('statResolvedSub') || document.getElementById('blResolvedRateSub');
  if (resSub && resSub.textContent) {
    const pctMatch = resSub.textContent.match(/(\d+)%/);
    if (pctMatch) {
      resSub.textContent = `${pctMatch[1]}% ${isFil ? 'antas ng pagresolba' : 'resolution rate'}`;
    }
  }

  // 19. Role permission matrix
  if (typeof renderPermMatrix === 'function') {
    renderPermMatrix();
  }

  // 20. Users table (to update protected badge & statuses)
  if (typeof renderUsers === 'function') {
    renderUsers();
  }
}

let _bcI18nObserver = null;
function bcSetupI18nObserver() {
  if (_bcI18nObserver || typeof MutationObserver === 'undefined') return;
  let timer = null;
  _bcI18nObserver = new MutationObserver((mutations) => {
    let shouldTranslate = false;
    for (const m of mutations) {
      if (m.addedNodes && m.addedNodes.length > 0) {
        shouldTranslate = true;
        break;
      }
    }
    if (shouldTranslate) {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        const cur = bcGetLanguage();
        if (cur === 'Filipino') {
          bcApplyLanguage('Filipino');
        }
        applyLanguageTranslation();
      }, 100);
    }
  });
  if (document.body) {
    _bcI18nObserver.observe(document.body, { childList: true, subtree: true });
  }
}

function bcInitLanguage() {
  const currentLang = bcGetLanguage();
  bcApplyLanguage(currentLang);
  bcSetupI18nObserver();
}

window.BC_TRANSLATIONS = BC_TRANSLATIONS;
window.i18n = i18n;
window.applyLanguageTranslation = applyLanguageTranslation;
window.bcGetLanguage = bcGetLanguage;
window.bcSetLanguage = bcSetLanguage;
window.bcApplyLanguage = bcApplyLanguage;
window.bcInitLanguage = bcInitLanguage;
window.bcT = bcT;

window.addEventListener('storage', (e) => {
  if (e.key === 'bc_language' || e.key === 'app_language') {
    const rawVal = localStorage.getItem('app_language') || localStorage.getItem('bc_language') || e.newValue;
    const isFil = (String(rawVal || '')).toLowerCase().startsWith('fil') || (String(rawVal || '')).toLowerCase().startsWith('tag') || (String(rawVal || '')).toLowerCase() === 'tl';
    bcApplyLanguage(isFil ? 'Filipino' : 'English');
    applyLanguageTranslation(isFil ? 'tl' : 'en');
  }
});

// Live character-stripping filters — remove disallowed characters the
// moment they land in a field (typed, pasted, or autofilled), rather
// than only catching them at submit time. Delegated on `input` at the
// document level so every current and future field marked with one of
// these data attributes is covered without a listener wired up per-page.
//   data-no-numbers → name fields: strip digits (0-9), keep letters/punctuation.
//   data-digits-only → contact number fields: strip everything except
//     digits, so letters AND special characters (+, -, (), spaces, etc.)
//     are blocked as you type. PH mobile numbers are entered as plain
//     digits here (e.g. "09171234567"), so there's nothing legitimate
//     for a contact field to keep besides 0-9.
function bcStripDisallowedChars(el, disallowedRe) {
  const cleaned = el.value.replace(disallowedRe, '');
  if (cleaned !== el.value) {
    const pos = el.selectionStart ? el.selectionStart - (el.value.length - cleaned.length) : cleaned.length;
    el.value = cleaned;
    if (el.setSelectionRange) el.setSelectionRange(pos, pos);
  }
}
document.addEventListener('input', (e) => {
  const el = e.target;
  if (!el.matches) return;
  if (el.matches('[data-no-numbers]')) bcStripDisallowedChars(el, /[0-9]/g);
  else if (el.matches('[data-digits-only]')) bcStripDisallowedChars(el, /[^0-9]/g);
});

// ── Auth guard: redirect to landing page if session is missing ────
// Also enforces role-based page access (permissions.js) and hides
// sidebar links the current role isn't permitted to use.
let _bcAuthGuardRunning = false;

function _handleUnauthenticatedRedirect() {
  // Prevent rendering or interaction on protected views
  try {
    document.querySelectorAll('main, .page-header, .stat-card-grad, .data-table, aside').forEach(el => {
      el.style.pointerEvents = 'none';
    });
  } catch (e) {}
  sessionStorage.setItem('bc_logged_out_modal', '1');
  window.location.replace('index.html?logged_out=1');
}

// ── Non-blocking background pre-warm for ML Prediction service ──
let _bcMLPrewarmed = false;
function bcPrewarmMLService() {
  if (_bcMLPrewarmed || typeof window === 'undefined') return;
  _bcMLPrewarmed = true;
  setTimeout(() => {
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/ml/warmup');
      } else if (window.fetch) {
        fetch('/api/ml/warmup', { method: 'GET', keepalive: true, priority: 'low' }).catch(() => {});
      }
    } catch (_) {}
  }, 1200);
}

// ── Centralized Global State & User Profile Hydration ─────────
function resolveAvatar(url) {
  if (!url || typeof url !== 'string') return null;
  const trimmed = url.trim();
  if (
    !trimmed ||
    trimmed === 'null' ||
    trimmed === 'undefined' ||
    trimmed.startsWith('blob:') ||
    trimmed.includes('uploads/avatars/') ||
    trimmed.startsWith('uploads/') ||
    trimmed.startsWith('/uploads/') ||
    trimmed.includes('default.png') ||
    trimmed.includes('default_avatar') ||
    trimmed.includes('avatar-placeholder')
  ) {
    return null; // Reject legacy broken ephemeral disk paths that trigger 404s
  }
  return trimmed; // Valid Base64 or external CDN link
}
window.resolveAvatar = resolveAvatar;

function hydrateGlobalState() {
  let user = null;
  if (typeof bcGetCachedUser === 'function') {
    user = bcGetCachedUser();
  } else {
    try {
      const raw = localStorage.getItem('bc_cached_user') || 
                  sessionStorage.getItem('bc_cached_user') ||
                  localStorage.getItem('currentUser') ||
                  sessionStorage.getItem('currentUser') ||
                  localStorage.getItem('bc_user') ||
                  sessionStorage.getItem('bc_user');
      user = raw ? JSON.parse(raw) : null;
    } catch (e) {}
  }
  if (!user) return;

  const fullName = user.full_name || user.fullName || user.name || '';
  const role = user.role || '';
  const rawAvatar = user.avatar_url || user.avatarUrl || user.avatar || user.profile_photo_path || '';
  const avatarUrl = resolveAvatar(rawAvatar);

  document.querySelectorAll('[data-user-name]').forEach(el => {
    if (fullName) el.textContent = fullName;
  });
  document.querySelectorAll('[data-user-role]').forEach(el => {
    if (role) el.textContent = role;
  });

  const initials = typeof getInitials === 'function'
    ? getInitials(fullName)
    : (typeof bcInitials === 'function' ? bcInitials(fullName) : '??');

  document.querySelectorAll('[data-user-avatar]').forEach(el => {
    if (avatarUrl) {
      const existingImg = el.querySelector('img');
      if (existingImg && existingImg.getAttribute('src') === avatarUrl) {
        return;
      }
      el.innerHTML = `<img src="${avatarUrl}" alt="${fullName || 'User'}" class="w-full h-full object-cover rounded-full" onload="this.style.display='block';" onerror="this.onerror=null; this.removeAttribute('src'); this.classList.add('hidden'); const p=this.parentElement; if(p){ p.innerHTML=''; p.textContent='${initials}'; }"/>`;
    } else {
      el.innerHTML = '';
      el.textContent = initials;
    }
  });
  document.querySelectorAll('[data-user-greeting]').forEach(el => {
    if (fullName) {
      const firstName = typeof bcFirstName === 'function' ? bcFirstName(fullName) : fullName.split(' ')[0];
      el.textContent = typeof bcFormatUserGreeting === 'function' ? bcFormatUserGreeting(firstName) : `Welcome back, ${firstName}. Here's today's overview.`;
    } else {
      el.textContent = typeof bcFormatUserGreeting === 'function' ? bcFormatUserGreeting() : "Welcome back! Here's today's overview.";
    }
  });
  const greetingEl = document.getElementById('dashboardGreeting');
  if (greetingEl) {
    if (fullName) {
      const firstName = typeof bcFirstName === 'function' ? bcFirstName(fullName) : fullName.split(' ')[0];
      greetingEl.textContent = typeof bcFormatUserGreeting === 'function' ? bcFormatUserGreeting(firstName) : `Welcome back, ${firstName}. Here's today's overview.`;
    } else {
      greetingEl.textContent = typeof bcFormatUserGreeting === 'function' ? bcFormatUserGreeting() : "Welcome back! Here's today's overview.";
    }
  }
  if (role && typeof applyNavPermissions === 'function') {
    applyNavPermissions(role);
  }
}
window.hydrateGlobalState = hydrateGlobalState;
window.bcHydrateCachedSession = hydrateGlobalState;
window.updateUserBadge = hydrateGlobalState;

// Synchronously hydrate on load, DOMContentLoaded, and storage sync
hydrateGlobalState();
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', hydrateGlobalState, { once: true });
}
window.addEventListener('storage', (e) => {
  if (e.key === 'bc_cached_user' || e.key === 'currentUser' || e.key === 'bc_user') {
    hydrateGlobalState();
  }
});

// ── Real-Time Reactive Sync Dispatcher (Debounced) ─────────
let _bcRefreshDebounceTimer = null;
function bcTriggerLiveRefresh(detail = {}) {
  if (_bcRefreshDebounceTimer) {
    clearTimeout(_bcRefreshDebounceTimer);
  }
  _bcRefreshDebounceTimer = setTimeout(() => {
    _bcRefreshDebounceTimer = null;
    _bcExecuteLiveRefresh(detail);
  }, 250);
}

function _bcExecuteLiveRefresh(detail = {}) {
  if (_bcNavigating || window._bcSpaNavActive) return;
  try {
    hydrateGlobalState();
    if (typeof refreshNotifBadge === 'function') refreshNotifBadge();
  } catch (_) {}

  // Identify active page context by inspecting the DOM and re-fetch latest data in-place
  try {
    if (document.getElementById('blotterTableBody')) {
      if (typeof window.loadBlotter === 'function') window.loadBlotter(true);
    } else if (document.getElementById('incidentTableBody')) {
      if (typeof window.loadIncidents === 'function') window.loadIncidents(true);
    } else if (document.getElementById('settlementTableBody')) {
      if (typeof window.loadSettlements === 'function') window.loadSettlements(true);
    } else if (document.getElementById('residentBody')) {
      if (typeof window.loadResidents === 'function') window.loadResidents(true);
    } else if (document.getElementById('clLogBody')) {
      if (typeof window.loadLog === 'function') window.loadLog(true);
    } else if (document.getElementById('residencyLog')) {
      if (typeof window.loadResLog === 'function') window.loadResLog(true);
    } else if (document.getElementById('nonResidencyLog')) {
      if (typeof window.loadNrLog === 'function') window.loadNrLog(true);
    } else if (document.getElementById('indLog')) {
      if (typeof window.loadIndLog === 'function') window.loadIndLog(true);
    } else if (document.getElementById('usersTableBody')) {
      if (typeof window.loadUsers === 'function') window.loadUsers(true);
      if (typeof window.loadAuditLog === 'function') window.loadAuditLog(true);
    } else if (document.getElementById('recentReports')) {
      if (typeof window.loadRecentReports === 'function') window.loadRecentReports(true);
    } else if (document.getElementById('statBlotters') || document.getElementById('dashboardGreeting')) {
      if (typeof window.loadDashboardData === 'function') window.loadDashboardData(true);
    } else if (document.getElementById('kpiTotalIncidents') || document.getElementById('heatmap')) {
      if (typeof window.loadIncidents === 'function') window.loadIncidents(true);
    } else if (document.getElementById('zonalMatrixBody')) {
      if (typeof window.updateCharts === 'function') window.updateCharts(true);
    }
  } catch (err) {
    console.warn('Reactive live refresh notice:', err);
  }
}
window.bcTriggerLiveRefresh = bcTriggerLiveRefresh;

window.addEventListener('bc-data-changed', (e) => {
  hydrateGlobalState();
  bcTriggerLiveRefresh(e.detail || {});
});

window.addEventListener('storage', (e) => {
  if (e.key === 'bc_data_updated') {
    bcTriggerLiveRefresh();
  }
});

// ── In-App Client-Side Routing & Persistent Layout Shell ────
let _bcNavigating = false;
const _bcLoadedScriptSrcs = new Set(
  Array.from(document.querySelectorAll('script[src]')).map(s => s.getAttribute('src')).filter(Boolean)
);

// Global timer and resource trackers for view lifecycles
window._bcActiveTimeouts = window._bcActiveTimeouts || [];
window._bcActiveIntervals = window._bcActiveIntervals || [];
window._bcActiveCharts = window._bcActiveCharts || [];

function _bcGetPageNameFromUrl(url) {
  try {
    const clean = url.split('?')[0].split('#')[0];
    const filename = clean.split('/').pop() || 'dashboard.html';
    return filename.replace('.html', '');
  } catch (e) {
    return 'dashboard';
  }
}

function updateActiveSidebar(targetUrl) {
  const pageName = _bcGetPageNameFromUrl(targetUrl);
  const links = document.querySelectorAll('aside nav .nav-link');
  links.forEach(l => {
    const linkPage = l.getAttribute('data-page') || _bcGetPageNameFromUrl(l.getAttribute('href') || '');
    if (linkPage === pageName) {
      l.classList.add('active');
    } else {
      l.classList.remove('active');
    }
  });
}
const _bcUpdateSidebarActiveLink = updateActiveSidebar;

// ── Global Active View / Sub-Tab Session & URL Synchronizer ────────
function bcGetActiveView(moduleName, defaultView = '') {
  try {
    const hashVal = (window.location.hash || '').replace(/^#/, '').trim();
    if (hashVal) return hashVal;

    const params = new URLSearchParams(window.location.search);
    const queryView = (params.get('view') || params.get('tab') || params.get('sub') || '').trim();
    if (queryView) return queryView;

    const stored = (sessionStorage.getItem('current_active_view_' + moduleName) || '').trim();
    if (stored) return stored;
  } catch (_) {}
  return defaultView;
}

function bcSetActiveView(moduleName, viewId, syncUrl = true) {
  if (!moduleName || !viewId) return;
  try {
    sessionStorage.setItem('current_active_view_' + moduleName, String(viewId));
    if (syncUrl && typeof history !== 'undefined' && history.replaceState) {
      const currentHash = (window.location.hash || '').replace(/^#/, '').trim();
      if (currentHash !== String(viewId)) {
        history.replaceState(null, '', '#' + viewId);
      }
    }
  } catch (_) {}
}

window.bcGetActiveView = bcGetActiveView;
window.bcSetActiveView = bcSetActiveView;

async function _bcLoadScriptOnce(src) {
  if (!src) return;
  if (_bcLoadedScriptSrcs.has(src) || document.querySelector(`script[src="${src}"]`)) {
    _bcLoadedScriptSrcs.add(src);
    return;
  }
  return new Promise((resolve) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = () => {
      _bcLoadedScriptSrcs.add(src);
      resolve();
    };
    s.onerror = () => {
      console.warn('Failed to load script:', src);
      resolve(); // Do not hard break router
    };
    document.head.appendChild(s);
  });
}

function _bcCleanupPreviousView() {
  // 0. Finish any pending dialog promises and close modals
  if (typeof _bcDialogFinish === 'function') _bcDialogFinish(false);
  if (typeof _bcPermDeleteFinish === 'function') _bcPermDeleteFinish(false);

  // Hide batch floating bar and remove legacy selection banner elements
  const batchBar = document.getElementById('bcBatchFloatingBar');
  if (batchBar) batchBar.classList.remove('visible');
  document.querySelectorAll('.bc-selection-banner-wrap').forEach(b => b.remove());

  // 1. Destroy all active Leaflet map instances
  const maps = [
    window.currentMap,
    window.heatmapInstance,
    window.pickerMap,
    window.map,
    window._censusMap
  ];
  maps.forEach(m => {
    if (m && typeof m.remove === 'function') {
      try {
        m.remove();
      } catch (e) {
        console.warn('Map cleanup notice:', e);
      }
    }
  });
  window.currentMap = null;
  window.heatmapInstance = null;
  window.pickerMap = null;
  window.map = null;
  window._censusMap = null;

  // Clear map container identifiers
  document.querySelectorAll('#map, #pickerMapContainer, #censusMap').forEach(el => {
    if (el) el._leaflet_id = null;
  });

  // 2. Disconnect observers
  if (window._heatmapResizeObserver) {
    try { window._heatmapResizeObserver.disconnect(); } catch (_) {}
    window._heatmapResizeObserver = null;
  }

  // 3. Destroy Chart.js instances
  if (window._bcActiveCharts && Array.isArray(window._bcActiveCharts)) {
    window._bcActiveCharts.forEach(c => {
      try { c.destroy(); } catch (_) {}
    });
    window._bcActiveCharts = [];
  }
  document.querySelectorAll('canvas').forEach(canvas => {
    try {
      if (window.Chart && typeof Chart.getChart === 'function') {
        const chartInstance = Chart.getChart(canvas);
        if (chartInstance) chartInstance.destroy();
      }
    } catch (_) {}
  });

  // 4. Clear running intervals and timeouts from previous view
  if (_bcRefreshDebounceTimer) {
    clearTimeout(_bcRefreshDebounceTimer);
    _bcRefreshDebounceTimer = null;
  }
  if (window._bcActiveIntervals && Array.isArray(window._bcActiveIntervals)) {
    window._bcActiveIntervals.forEach(id => clearInterval(id));
    window._bcActiveIntervals = [];
  }
  if (window._bcActiveTimeouts && Array.isArray(window._bcActiveTimeouts)) {
    window._bcActiveTimeouts.forEach(id => clearTimeout(id));
    window._bcActiveTimeouts = [];
  }
}

// ── Route-to-Init Dispatcher ──────────────────────────────
function executeModuleInit(url) {
  const clean = (url || window.location.pathname).split('?')[0].split('#')[0];
  const path = clean.split('/').pop().toLowerCase() || 'dashboard.html';
  const fullPath = '/' + path;

  const initMap = {
    'dashboard.html': () => window.initDashboard?.() || window.loadDashboardData?.(),
    '/dashboard.html': () => window.initDashboard?.() || window.loadDashboardData?.(),
    'blotter.html': () => window.initBlotter?.() || window.loadBlotter?.(),
    '/blotter.html': () => window.initBlotter?.() || window.loadBlotter?.(),
    'incident.html': () => window.initIncidents?.() || window.initIncident?.() || window.loadIncidents?.(),
    '/incident.html': () => window.initIncidents?.() || window.initIncident?.() || window.loadIncidents?.(),
    'incidents.html': () => window.initIncidents?.() || window.initIncident?.() || window.loadIncidents?.(),
    '/incidents.html': () => window.initIncidents?.() || window.initIncident?.() || window.loadIncidents?.(),
    'settlement.html': () => window.initSettlement?.() || window.initSettlements?.() || window.loadSettlements?.(),
    '/settlement.html': () => window.initSettlement?.() || window.initSettlements?.() || window.loadSettlements?.(),
    'census.html': () => window.initCensus?.() || window.loadResidents?.(),
    '/census.html': () => window.initCensus?.() || window.loadResidents?.(),
    'clearance.html': () => window.initClearance?.() || window.loadLog?.(),
    '/clearance.html': () => window.initClearance?.() || window.loadLog?.(),
    'residency.html': () => window.initResidency?.() || window.loadResLog?.(),
    '/residency.html': () => window.initResidency?.() || window.loadResLog?.(),
    'non_residency.html': () => window.initNonResidency?.() || window.loadNrLog?.(),
    '/non_residency.html': () => window.initNonResidency?.() || window.loadNrLog?.(),
    'non-residency.html': () => window.initNonResidency?.() || window.loadNrLog?.(),
    '/non-residency.html': () => window.initNonResidency?.() || window.loadNrLog?.(),
    'indigency.html': () => window.initIndigency?.() || window.loadIndLog?.(),
    '/indigency.html': () => window.initIndigency?.() || window.loadIndLog?.(),
    'heatmap.html': () => window.initHeatmap?.(),
    '/heatmap.html': () => window.initHeatmap?.(),
    'trends.html': () => window.initTrends?.() || window.updateCharts?.(),
    '/trends.html': () => window.initTrends?.() || window.updateCharts?.(),
    'predictions.html': () => window.initPredictions?.(),
    '/predictions.html': () => window.initPredictions?.(),
    'users.html': () => window.initUsers?.() || window.loadUsers?.(),
    '/users.html': () => window.initUsers?.() || window.loadUsers?.(),
    'reports.html': () => window.initReports?.() || window.loadRecentReports?.(),
    '/reports.html': () => window.initReports?.() || window.loadRecentReports?.(),
    'settings.html': () => window.initSettings?.(),
    '/settings.html': () => window.initSettings?.()
  };

  try {
    const fn = initMap[path] || initMap[fullPath];
    if (typeof fn === 'function') {
      const res = fn();
      if (res && typeof res.then === 'function') {
        return res;
      }
    }
  } catch (e) {
    console.error(`Error initializing module for ${path}:`, e);
  }
}
// Provide safe refresh hook if Tailwind Play CDN is loaded
if (typeof window !== 'undefined') {
  if (!window.tailwind) {
    try { window.tailwind = {}; } catch (_) {}
  }
  if (window.tailwind && typeof window.tailwind.refresh !== 'function') {
    window.tailwind.refresh = function () {
      if (document.documentElement) {
        document.documentElement.classList.toggle('tw-rescan');
      }
    };
  }
}

// ── Bulletproof SPA Navigation & Content Swap ──────────────
async function navigateTo(url, pushState = true) {
  if (!url || _bcNavigating) return;

  const cleanUrl = url.split('?')[0].split('#')[0];
  if (cleanUrl.endsWith('login.html') || cleanUrl.endsWith('index.html') || cleanUrl === '/' || cleanUrl === '') {
    window.location.href = url;
    return;
  }

  const currentFull = window.location.pathname.split('/').pop() + window.location.search;
  const targetRel = url.split('/').pop();
  if (currentFull === targetRel && !pushState) return;

  // ── SPA navigation pre-flight ─────────────────────────────
  _bcAuthGuardRunning = false;
  window._bcSpaNavActive = true;

  _bcNavigating = true;
  const contentContainer = document.querySelector('#app-content') || document.querySelector('.ml-64');
  if (!contentContainer) {
    window._bcSpaNavActive = false;
    _bcNavigating = false;
    window.location.href = url;
    return;
  }

  // Show instant lightweight loader inside main container without freezing UI
  contentContainer.classList.add('bc-content-loading');

  try {
    const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const html = await response.text();

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const newMain = doc.querySelector('#app-content') || doc.querySelector('main') || doc.querySelector('.page-content') || doc.querySelector('.ml-64');

    if (doc.title) {
      document.title = doc.title;
    }

    // Teardown previous view resources, maps, charts, timers
    _bcCleanupPreviousView();

    // Dismiss open modals before swapping
    document.querySelectorAll('.modal-overlay.open, .modal-overlay.show, .modal.show, [id$="Modal"].show').forEach(m => {
      m.classList.remove('show');
      m.classList.remove('open');
    });

    // Remove obsolete page-level modals from previous view, preserving global system dialogs
    document.querySelectorAll('body > .modal-overlay:not(#bcDialogOverlay):not(#bcPermDeleteOverlay):not(#bcExportFilterModal):not(#bcBlotterDetailsModal), body > [id$="Modal"]:not(#bcDialogOverlay):not(#bcPermDeleteOverlay):not(#bcExportFilterModal):not(#bcBlotterDetailsModal)').forEach(m => {
      m.remove();
    });

    const newModals = doc.querySelectorAll('body > .modal-overlay:not(#bcDialogOverlay):not(#bcPermDeleteOverlay):not(#bcExportFilterModal):not(#bcBlotterDetailsModal), body > [id$="Modal"]:not(#bcDialogOverlay):not(#bcPermDeleteOverlay):not(#bcExportFilterModal):not(#bcBlotterDetailsModal)');
    newModals.forEach(m => {
      document.body.appendChild(m);
    });

    if (newMain) {
      if (newMain.className) {
        const preservedClasses = ['bc-content-loading', 'bc-content-enter', 'ml-64'];
        const currentFlags = preservedClasses.filter(c => contentContainer.classList.contains(c));
        contentContainer.className = newMain.className;
        if (!contentContainer.classList.contains('ml-64')) {
          contentContainer.classList.add('ml-64');
        }
        currentFlags.forEach(c => contentContainer.classList.add(c));
      }
      contentContainer.innerHTML = newMain.innerHTML;
    } else {
      contentContainer.innerHTML = html;
    }

    // Explicitly trigger Tailwind's class scanner immediately after swapping HTML
    if (window.tailwind && typeof window.tailwind.refresh === 'function') {
      try {
        window.tailwind.refresh();
      } catch (twErr) {
        console.warn('Tailwind refresh error:', twErr);
      }
    }

    contentContainer.classList.remove('bc-content-loading');
    contentContainer.classList.remove('bc-content-enter');
    void contentContainer.offsetWidth; // trigger reflow
    contentContainer.classList.add('bc-content-enter');

    // Update URL history
    if (pushState) {
      window.history.pushState({ url }, '', url);
    }
    window.scrollTo({ top: 0, behavior: 'instant' });

    // Update active sidebar link styling
    updateActiveSidebar(url);

    // Load any page stylesheets (e.g. Leaflet CSS) if not already in document.head
    const linkTags = Array.from(doc.querySelectorAll('link[rel="stylesheet"]'));
    for (const l of linkTags) {
      const href = l.getAttribute('href');
      if (href && !document.querySelector(`link[href="${href}"]`)) {
        try {
          const newLink = document.createElement('link');
          newLink.rel = 'stylesheet';
          newLink.href = href;
          if (l.integrity) newLink.integrity = l.integrity;
          if (l.crossOrigin) newLink.crossOrigin = l.crossOrigin;
          document.head.appendChild(newLink);
        } catch (_) {}
      }
    }

    // Transfer page-specific inline <style> blocks to head if not already present
    const pageStyleTags = Array.from(doc.querySelectorAll('style'));
    for (const st of pageStyleTags) {
      const cssText = (st.textContent || '').trim();
      if (cssText && !document.head.innerHTML.includes(cssText.slice(0, 45))) {
        try {
          const newStyle = document.createElement('style');
          newStyle.textContent = cssText;
          document.head.appendChild(newStyle);
        } catch (_) {}
      }
    }

    // Load external scripts (e.g. Chart.js, Leaflet, public/js/certificates.js, etc.)
    const scriptTags = Array.from(doc.querySelectorAll('script'));
    for (const s of scriptTags) {
      const src = s.getAttribute('src');
      if (src && !src.includes('api.js') && !src.includes('permissions.js') && !src.includes('app.js') && !src.includes('icons.js') && !src.includes('custom-controls.js')) {
        try {
          await _bcLoadScriptOnce(src);
        } catch (scriptLoadErr) {
          console.warn('Script preload warning:', src, scriptLoadErr);
        }
      }
    }

    // Clean up previously injected dynamic page scripts to avoid stale tags
    try {
      document.querySelectorAll('script[data-dynamic-page-script]').forEach(el => el.remove());
    } catch (_) {}

    // Execute inline scripts safely with redeclaration protection.
    // window._bcSpaNavActive=true suppresses the direct initXxx()
    // call at the bottom of every page script (those calls are for
    // direct browser-open only; during SPA nav the router calls
    // executeModuleInit() below once everything is ready).
    for (const s of scriptTags) {
      if (!s.getAttribute('src') && s.textContent.trim()) {
        // Skip the Tailwind config script — re-running it causes
        // Tailwind CDN to fully reinitialize, which briefly strips
        // layout classes (fixed, ml-64, etc.) from the sidebar.
        if (s.textContent.includes('tailwind.config')) continue;

        try {
          const rawScript = s.textContent;
          // Convert const/let → var to avoid SyntaxError on
          // redeclaration across SPA navigations. The replacement
          // must insert a space between 'var' and destructuring
          // brackets so `const{a,b}` → `var {a,b}` (not `vara,b}`).
          const safeScript = rawScript
            .replace(/\b(const|let)\s*\{/g, 'var {')
            .replace(/\b(const|let)\s*\[/g, 'var [')
            .replace(/\b(const|let)\s+([a-zA-Z0-9_$]+)\s*=/g, 'var $2 =')
            .replace(/\bconst\s+/g, 'var ')
            .replace(/\blet\s+/g, 'var ');

          const newScript = document.createElement('script');
          newScript.setAttribute('data-dynamic-page-script', '1');
          newScript.textContent = safeScript;
          try {
            document.body.appendChild(newScript);
          } catch (evalErr) {
            console.warn('View script initialization handled:', evalErr);
          }
          // Remove after a tick — script has already run synchronously
          setTimeout(() => {
            try { newScript.remove(); } catch (_) {}
          }, 0);
        } catch (scriptErr) {
          console.warn('Error preparing page script:', scriptErr);
        }
      }
    }

    // Clear the SPA nav flag now that all page scripts have run.
    window._bcSpaNavActive = false;

    // Re-hydrate session & live permissions
    hydrateGlobalState();

    // Re-render icons & controls
    if (typeof renderIcons === 'function') renderIcons();
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
    if (typeof initCustomSelects === 'function') initCustomSelects();

    // Trigger module lifecycle safely.
    await executeModuleInit(url);

    // Re-hydrate state and controls after async data render
    hydrateGlobalState();
    if (typeof renderIcons === 'function') renderIcons();
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
    if (typeof initCustomSelects === 'function') initCustomSelects();

    // Re-scan Tailwind after dynamic component rendering
    if (window.tailwind && typeof window.tailwind.refresh === 'function') {
      try {
        window.tailwind.refresh();
      } catch (_) {}
    }

    window.dispatchEvent(new CustomEvent('bc:page-loaded', { detail: { url } }));
    if (typeof fitCertificatePreview === 'function') {
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        fitCertificatePreview();
      }, 150);
    }
  } catch (err) {
    console.error('Navigation error:', err);
    contentContainer.innerHTML = `
      <div class="flex flex-col items-center justify-center min-h-[60vh] text-slate-500 p-8">
        <div class="card max-w-md w-full p-8 text-center space-y-4 shadow-lg border border-red-100 bg-white">
          <div class="w-14 h-14 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto text-2xl">
            <span data-icon="warning" data-icon-size="28"></span>
          </div>
          <div>
            <h2 class="font-display text-xl text-forest-800">Failed to Load View</h2>
            <p class="text-sm text-forest-500 mt-1">${err.message || 'An error occurred while loading this page.'}</p>
          </div>
          <div class="flex items-center justify-center gap-3 pt-2">
            <button onclick="navigateTo('${url}', false)" class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm font-medium transition flex items-center gap-2">
              <span data-icon="refresh" data-icon-size="14"></span> Retry
            </button>
            <button onclick="window.location.reload()" class="btn-secondary text-sm">
              Reload Page
            </button>
          </div>
        </div>
      </div>`;
    if (typeof renderIcons === 'function') renderIcons();
  } finally {
    _bcNavigating = false;
    _bcAuthGuardRunning = false;
    window._bcSpaNavActive = false;
    contentContainer.classList.remove('bc-content-loading');
    contentContainer.style.opacity = '1';
    contentContainer.style.pointerEvents = 'auto';
    hydrateGlobalState();
  }
}
const bcNavigate = navigateTo;
window.navigateTo = navigateTo;
window.bcNavigate = navigateTo;
window.updateActiveSidebar = updateActiveSidebar;
window.executeModuleInit = executeModuleInit;

// Intercept in-app link clicks
document.addEventListener('click', (e) => {
  const link = e.target.closest('a');
  if (!link) return;

  const href = link.getAttribute('href');
  if (!href) return;
  if (href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:') || href.startsWith('tel:') || link.target === '_blank') return;
  if (href.startsWith('http://') || href.startsWith('https://')) return;
  if (href === 'login.html' || href.endsWith('/login.html') || href === 'index.html' || href.endsWith('/index.html') || href === '/') return;

  if (href.endsWith('.html') || href.includes('.html?') || href.includes('.html#')) {
    e.preventDefault();
    navigateTo(href, true);
  }
});

// Support browser Back/Forward navigation
window.addEventListener('popstate', () => {
  const currentUrl = window.location.pathname.split('/').pop() + window.location.search;
  navigateTo(currentUrl, false);
});


let _bcAuthGuardPromise = null;

async function requireAuth() {
  // Instant visual hydration before awaiting network
  hydrateGlobalState();

  if (_bcAuthGuardPromise) {
    return _bcAuthGuardPromise;
  }

  _bcAuthGuardPromise = (async () => {
    try {
      const status = await BCApi.me();
      if (!status || !status.authenticated) {
        try {
          localStorage.removeItem('bc_cached_user');
          sessionStorage.removeItem('bc_cached_user');
          localStorage.removeItem('currentUser');
          sessionStorage.removeItem('currentUser');
          localStorage.removeItem('bc_user');
          sessionStorage.removeItem('bc_user');
        } catch (e) {}
        _handleUnauthenticatedRedirect();
        return null;
      }

      // Clean/sanitize user payload and ensure permanent avatar URL format
      const userPayload = Object.assign({}, status.user);
      const rawUserAvatar = userPayload.avatar_url || userPayload.avatar || userPayload.avatarUrl || userPayload.profile_photo_path || '';
      let cleanUserAvatar = null;
      if (typeof rawUserAvatar === 'string') {
        const trimmed = rawUserAvatar.trim();
        if (
          trimmed &&
          trimmed !== 'null' &&
          trimmed !== 'undefined' &&
          !trimmed.startsWith('blob:') &&
          !trimmed.includes('default.png') &&
          !trimmed.includes('default_avatar') &&
          !trimmed.includes('avatar-placeholder')
        ) {
          cleanUserAvatar = trimmed;
        }
      }
      userPayload.avatar_url = cleanUserAvatar;
      userPayload.avatar = cleanUserAvatar;
      userPayload.avatarUrl = cleanUserAvatar;
      userPayload.profile_photo_path = cleanUserAvatar;

      // Persist verified user session across all keys
      try {
        localStorage.setItem('bc_cached_user', JSON.stringify(userPayload));
        sessionStorage.setItem('bc_cached_user', JSON.stringify(userPayload));
        localStorage.setItem('currentUser', JSON.stringify(userPayload));
        sessionStorage.setItem('currentUser', JSON.stringify(userPayload));
        localStorage.setItem('bc_user', JSON.stringify(userPayload));
        sessionStorage.setItem('bc_user', JSON.stringify(userPayload));
        localStorage.setItem('user', JSON.stringify(userPayload));
        sessionStorage.setItem('user', JSON.stringify(userPayload));
      } catch (e) {}

      const role = userPayload.role;
      if (typeof enforcePageAccess === 'function' && !enforcePageAccess(role)) {
        return null; // enforcePageAccess already redirected away
      }
      if (typeof applyNavPermissions === 'function') applyNavPermissions(role);
      bcPrewarmMLService();
      if (typeof applyElementPermissionsLive === 'function') applyElementPermissionsLive(role);

      hydrateGlobalState();
      if (userPayload.mustChangePassword) bcShowForcedPasswordChange();
      bcSyncTimeFormatFromServer().catch(() => {});
      _bcStartIdleTracker();
      return userPayload;
    } catch (e) {
      if (e.message && e.message.includes('Not authenticated')) {
        try {
          localStorage.removeItem('bc_cached_user');
          sessionStorage.removeItem('bc_cached_user');
          localStorage.removeItem('currentUser');
          sessionStorage.removeItem('currentUser');
        } catch (_) {}
        _handleUnauthenticatedRedirect();
        return null;
      }
      const cached = bcGetCachedUser();
      if (cached) {
        hydrateGlobalState();
        return cached;
      }
      _handleUnauthenticatedRedirect();
      return null;
    } finally {
      _bcAuthGuardPromise = null;
    }
  })();

  return _bcAuthGuardPromise;
}

// ── Global Inactivity / Idle Auto-Logout Engine (Dynamic & Background-Safe) ──
let _bcIdleTimeoutMs = 2 * 60 * 60 * 1000; // 120 minutes = 7,200,000 ms default
let _bcIdleEnabled = true;
const BC_IDLE_CHECK_INTERVAL_MS = 5000;       // check every 5 seconds
const BC_ACTIVITY_THROTTLE_MS = 1000;     // write to localStorage at most once per second
let _bcLastThrottleWrite = 0;
let _bcIdleCheckInterval = null;
let _bcIdleListenersAttached = false;

function _bcIsPublicPage() {
  const path = window.location.pathname.toLowerCase();
  return path.endsWith('login.html') || path.endsWith('index.html') || path === '/' || path === '';
}

function _bcRecordActivity() {
  if (!_bcIdleEnabled) return;
  const now = Date.now();
  if (now - _bcLastThrottleWrite > BC_ACTIVITY_THROTTLE_MS) {
    _bcLastThrottleWrite = now;
    try {
      localStorage.setItem('bc_last_active_timestamp', now.toString());
    } catch (e) {}
  }
}

function _bcCheckIdleExpiry() {
  if (_bcIsPublicPage() || !_bcIdleEnabled) return;
  try {
    const raw = localStorage.getItem('bc_last_active_timestamp');
    const lastActive = raw ? Number(raw) : Date.now();
    const elapsed = Date.now() - lastActive;
    if (elapsed >= _bcIdleTimeoutMs) {
      _bcTriggerIdleLogout();
    }
  } catch (e) {}
}

async function _bcTriggerIdleLogout() {
  _bcStopIdleTracker();
  try { await BCApi.logout(); } catch (e) {}
  try {
    localStorage.removeItem('token');
    localStorage.removeItem('bc_last_active_timestamp');
    sessionStorage.setItem('bc_logged_out_modal', '1');
    sessionStorage.setItem('bc_session_expired_reason', `Your session expired due to ${Math.round(_bcIdleTimeoutMs / 60000)} minutes of inactivity.`);
  } catch (e) {}
  window.location.replace('login.html?session_expired=1');
}

function _bcStopIdleTracker() {
  if (_bcIdleCheckInterval) {
    clearInterval(_bcIdleCheckInterval);
    _bcIdleCheckInterval = null;
  }
}

async function _bcStartIdleTracker() {
  if (_bcIsPublicPage()) return;

  // Fetch or sync global security settings
  try {
    const settings = await BCApi.settingsList();
    if (settings) {
      if ('idle_timeout_enabled' in settings) {
        _bcIdleEnabled = settings.idle_timeout_enabled === '1' || settings.idle_timeout_enabled === 'true';
      }
      const dur = Number(settings.idle_timeout_duration_minutes || settings.session_timeout || 120);
      if (dur > 0) {
        _bcIdleTimeoutMs = dur * 60 * 1000;
      }
    }
  } catch (e) {}

  if (!_bcIdleEnabled) {
    _bcStopIdleTracker();
    return;
  }

  _bcRecordActivity();

  if (!_bcIdleCheckInterval) {
    _bcIdleCheckInterval = setInterval(_bcCheckIdleExpiry, BC_IDLE_CHECK_INTERVAL_MS);
  }

  if (!_bcIdleListenersAttached) {
    _bcIdleListenersAttached = true;
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
    events.forEach(evt => {
      window.addEventListener(evt, _bcRecordActivity, { passive: true });
    });

    // Background sync: trigger instant check on tab focus / visibility change
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        _bcCheckIdleExpiry();
      }
    });
    window.addEventListener('focus', () => {
      _bcCheckIdleExpiry();
    });
    // Cross-tab sync: sync activity if updated in another tab
    window.addEventListener('storage', (e) => {
      if (e.key === 'bc_last_active_timestamp') {
        _bcCheckIdleExpiry();
      }
    });
  }
}

function _bcStopIdleTracker() {
  if (_bcIdleCheckInterval) {
    clearInterval(_bcIdleCheckInterval);
    _bcIdleCheckInterval = null;
  }
}

// ── Browser Navigation Guards (Back/Forward Buttons) ────────
// 1. Trap Back button on protected pages so it terminates the session and returns to Landing Page
(function _bcSetupBackNavigationTrap() {
  if (!_bcIsPublicPage()) {
    try {
      if (!history.state || history.state.bcGuard !== 1) {
        history.pushState({ bcGuard: 1 }, '', window.location.href);
      }
    } catch (e) {}
  }
})();

window.addEventListener('popstate', async (event) => {
  if (!_bcIsPublicPage()) {
    _bcStopIdleTracker();
    try { localStorage.removeItem('bc_last_active_timestamp'); } catch (e) {}
    try { await BCApi.logout(); } catch (e) {}
    sessionStorage.setItem('bc_logged_out_modal', '1');
    window.location.replace('index.html?logged_out=1');
  }
});

// 2. BFCache & Forward Navigation Guard
window.addEventListener('pageshow', (event) => {
  if (!_bcIsPublicPage()) {
    _bcCheckIdleExpiry();
    requireAuth();
  }
});

// Extracts the first name from a full name string, e.g. "Freya Lynn Ramos" -> "Freya",
// or falls back gracefully to "User" if missing or empty.
function bcFirstName(fullName) {
  if (!fullName || typeof fullName !== 'string') return 'User';
  const words = fullName.trim().split(/\s+/).filter(Boolean);
  return words[0] || 'User';
}

// Initials shown in the avatar circles (e.g. "Juan Cruz" -> "JC", "Maria Clara Santos" -> "MS", "Admin" -> "AD")
// Multi-word names (2, 3, 4+ words) consistently use the first letter of the FIRST name
// and the first letter of the LAST name. Single-word names use the first 2 letters.
function getInitials(name) {
  if (!name || typeof name !== 'string') return '??';

  // Clean extra spaces and split words
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return '??';

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  // For 2, 3, 4, or more words:
  // Always take the first letter of the FIRST name and the first letter of the LAST name
  const firstInitial = words[0].charAt(0).toUpperCase();
  const lastInitial = words[words.length - 1].charAt(0).toUpperCase();

  return `${firstInitial}${lastInitial}`;
}
window.getInitials = getInitials;

function bcInitials(fullName) {
  return getInitials(fullName);
}
window.bcInitials = bcInitials;

function bcBroadcastUserPresence(status = 'Active', userId = null) {
  let uid = userId;
  if (!uid) {
    try {
      const u = JSON.parse(localStorage.getItem('bc_cached_user') || localStorage.getItem('currentUser') || sessionStorage.getItem('currentUser') || '{}');
      if (u && u.id) uid = Number(u.id);
    } catch (_) {}
  }
  if (!uid) return;

  const payload = { type: 'USER_STATUS_CHANGED', userId: Number(uid), status: status === 'Active' ? 'Active' : 'Inactive', timestamp: Date.now() };

  if (typeof BroadcastChannel !== 'undefined') {
    try {
      if (!window._bcPresenceBroadcastChannel) {
        window._bcPresenceBroadcastChannel = new BroadcastChannel('bc_user_presence_channel');
      }
      window._bcPresenceBroadcastChannel.postMessage(payload);
    } catch (_) {}
  }

  // Cross-tab storage event dispatch fallback
  try {
    localStorage.setItem('bc_presence_event', JSON.stringify(payload));
  } catch (_) {}

  // In-page window event dispatch
  try {
    window.dispatchEvent(new CustomEvent('bc-user-presence-changed', { detail: payload }));
  } catch (_) {}
}

async function doLogout() {
  const isTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  const msg = isTl ? 'Sigurado ka bang gusto mong mag-log out?' : 'Are you sure you want to log out?';
  const title = isTl ? 'Mag-log Out' : 'Log Out';
  const okLabel = isTl ? 'Mag-log Out' : 'Log Out';
  const cancelLabel = isTl ? 'Kanselahin' : 'Cancel';
  if (!(await bcConfirm(msg, { title, okLabel, cancelLabel }))) return;
  return handleLogout();
}

async function handleLogout() {
  _bcStopIdleTracker();

  try {
    bcBroadcastUserPresence('Inactive');
  } catch (_) {}

  try {
    if (window.BCApi?.logout) {
      await window.BCApi.logout();
    }
  } catch (e) {
    console.warn('Logout API error:', e);
  } finally {
    try {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('bc_last_active_timestamp');
      localStorage.removeItem('bc_cached_user');
      localStorage.removeItem('currentUser');
      localStorage.removeItem('bc_user');
      sessionStorage.removeItem('bc_cached_user');
      sessionStorage.removeItem('currentUser');
      sessionStorage.removeItem('bc_user');
      sessionStorage.clear();
    } catch (e) {}

    // Direct hard redirect to bypass conflicting in-flight animations
    window.location.replace('login.html');
  }
}
window.doLogout = doLogout;
window.handleLogout = handleLogout;

// ── Real-Time Presence Heartbeat ────────────────────────────
// Keeps active user presence marked "Active" in real-time.
setInterval(() => {
  if (!document.hidden && !window.location.pathname.endsWith('login.html')) {
    BCApi.heartbeat().then(res => {
      if (res && res.online) {
        bcBroadcastUserPresence('Active');
      }
    }).catch(() => {});
  }
}, 10000);


// ── Field validation helpers ────────────────────────────────
// Small, dependency-free predicates used right before any create/update
// API call, so obviously-invalid input (digits in a name, a malformed
// contact number, a birth date in the future, etc.) never reaches the
// server. Deliberately kept as plain functions rather than a form
// framework — every page already collects its values into a `vals`
// object and checks required fields with a simple `if(...) { await bcAlert(...);
// return; }`, so each validator just slots into that same pattern.

// Letters (including accented ones like Ñ/ñ), spaces, commas (e.g. "LastName, FirstName"),
// hyphens (Dela Cruz-Santos), apostrophes (O'Brien, D'Souza), and periods (Jr., Ma.).
const BC_NAME_RE = new RegExp("^[a-zA-ZÀ-ÿñÑ\\s,.\\'\\-]+$");
function bcIsValidName(str) {
  return BC_NAME_RE.test((str || '').trim());
}

// ── Global Time Format Preference & Formatting Engine ──────────
const BC_SYSTEM_TIMEZONE = 'Asia/Manila';

function bcGetTimeFormat() {
  const saved = localStorage.getItem('bc_time_format') || '12';
  return saved.startsWith('24') ? '24' : '12';
}

function bcSetTimeFormat(fmt, broadcastOnly = false) {
  const normalized = (String(fmt || '12')).startsWith('24') ? '24' : '12';
  localStorage.setItem('bc_time_format', normalized);
  window.dispatchEvent(new CustomEvent('bc-time-format-changed', { detail: { format: normalized } }));
  document.dispatchEvent(new CustomEvent('bc-time-format-changed', { detail: { format: normalized } }));
  if (!broadcastOnly && typeof BCApi !== 'undefined' && BCApi.setTimeFormat) {
    BCApi.setTimeFormat(normalized).catch(() => {});
  }
}

async function bcSyncTimeFormatFromServer() {
  try {
    if (typeof BCApi !== 'undefined' && BCApi.getTimeFormat) {
      const res = await BCApi.getTimeFormat();
      if (res && res.time_format) {
        const serverFmt = res.time_format.startsWith('24') ? '24' : '12';
        const currentFmt = bcGetTimeFormat();
        if (serverFmt !== currentFmt) {
          localStorage.setItem('bc_time_format', serverFmt);
          window.dispatchEvent(new CustomEvent('bc-time-format-changed', { detail: { format: serverFmt } }));
        }
      }
    }
  } catch (e) {}
}

/**
 * Formats a time value (e.g. "13:45", "13:45:00", or a Date/ISO timestamp)
 * into "01:45 PM" (12-hour) or "13:45" (24-hour) based on active preference.
 */
function bcFormatTime(val, formatPref) {
  if (!val) return '';
  const use24 = (formatPref || bcGetTimeFormat()) === '24';
  
  if (typeof val === 'string' && val.includes(':') && !val.includes('T') && !val.includes(' ')) {
    const parts = val.split(':').map(Number);
    const h = parts[0];
    const m = parts[1];
    if (Number.isNaN(h) || Number.isNaN(m)) return val;
    if (use24) {
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    }
    const period = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 === 0 ? 12 : h % 12;
    return `${String(h12).padStart(2, '0')}:${String(m).padStart(2, '0')} ${period}`;
  }

  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    if (use24) {
      return d.toLocaleTimeString('en-PH', {
        hour: '2-digit', minute: '2-digit', hour12: false, timeZone: BC_SYSTEM_TIMEZONE
      });
    }
    return d.toLocaleTimeString('en-PH', {
      hour: '2-digit', minute: '2-digit', hour12: true, timeZone: BC_SYSTEM_TIMEZONE
    });
  } catch (e) {
    return String(val);
  }
}

/**
 * Universal Date+Time Formatter (Asia/Manila, UTC+8).
 * Formats timestamps into:
 *   - 12-Hour: "Aug 23, 2026, 01:36 AM" / "Aug 23, 2026, 01:36 PM"
 *   - 24-Hour: "Aug 23, 2026, 01:36" / "Aug 23, 2026, 13:36"
 */
function bcFormatTimestamp(iso, emptyLabel = 'Never', formatPref) {
  if (!iso) return emptyLabel;
  try {
    let d;
    if (typeof iso === 'string') {
      const s = iso.trim();
      if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?$/.test(s) && !/[zZ+-]\d*$/.test(s)) {
        d = new Date(s.replace(' ', 'T') + 'Z');
      } else {
        d = new Date(s.includes(' ') && !s.includes('T') ? s.replace(' ', 'T') : s);
      }
    } else {
      d = new Date(iso);
    }
    if (isNaN(d.getTime())) {
      d = new Date(iso);
      if (isNaN(d.getTime())) return emptyLabel;
    }
    const use24 = (formatPref || bcGetTimeFormat()) === '24';
    const datePart = d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric', timeZone: BC_SYSTEM_TIMEZONE
    });
    const timePart = d.toLocaleTimeString('en-US', {
      hour: '2-digit', minute: '2-digit', hour12: !use24, timeZone: BC_SYSTEM_TIMEZONE
    });
    return `${datePart}, ${timePart}`;
  } catch (e) {
    return emptyLabel;
  }
}

function bcFormatDateTime(iso, emptyLabel = 'Never', formatPref) {
  return bcFormatTimestamp(iso, emptyLabel, formatPref);
}

function bcFormatDate(iso, emptyLabel = '') {
  if (!iso) return emptyLabel;
  try {
    let d;
    if (typeof iso === 'string') {
      const s = iso.trim();
      if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?$/.test(s) && !/[zZ+-]\d*$/.test(s)) {
        d = new Date(s.replace(' ', 'T') + 'Z');
      } else {
        d = new Date(s.includes(' ') && !s.includes('T') ? s.replace(' ', 'T') : s);
      }
    } else {
      d = new Date(iso);
    }
    if (isNaN(d.getTime())) {
      d = new Date(iso);
      if (isNaN(d.getTime())) return emptyLabel;
    }
    return d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric', timeZone: BC_SYSTEM_TIMEZONE,
    });
  } catch (e) {
    return emptyLabel;
  }
}

function formatSystemDate(dateString) {
  if (!dateString || dateString === 'Never') return 'Never';
  let date;
  if (typeof dateString === 'string') {
    const s = dateString.trim();
    if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?$/.test(s) && !/[zZ+-]\d*$/.test(s)) {
      date = new Date(s.replace(' ', 'T') + 'Z');
    } else {
      date = new Date(s.includes(' ') && !s.includes('T') ? s.replace(' ', 'T') : s);
    }
  } else {
    date = new Date(dateString);
  }
  if (isNaN(date.getTime())) {
    date = new Date(dateString);
    if (isNaN(date.getTime())) return String(dateString);
  }
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Manila',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  }).format(date);
}

window.formatSystemDate = formatSystemDate;
window.bcFormatTimestamp = bcFormatTimestamp;
window.bcFormatDateTime = bcFormatDateTime;
window.bcFormatDate = bcFormatDate;

function bcFormatTime12h(hhmm) {
  return bcFormatTime(hhmm);
}

// Zone is its own field (Incident.zone_id) — it must never be baked into
// the free-text Location detail, or changing the zone dropdown later has
// no way to update text that was already saved into the old zone's
// sentence. bcStripZonePrefix() cleans up rows saved before this was
// fixed; bcFormatIncidentLocation() is the single place "Zone X, detail"
// gets composed for display, always from the record's *current* zone.
function bcStripZonePrefix(location) {
  return (location || '').replace(/^\s*Zone\s*\d+\s*,\s*/i, '').trim();
}
function bcFormatIncidentLocation(zone, location) {
  const detail = bcStripZonePrefix(location);
  return zone ? (detail ? `${zone}, ${detail}` : zone) : detail;
}

function toggleFieldPassword(inputId, btnEl) {
  const input = typeof inputId === 'string' ? document.getElementById(inputId) : inputId;
  const btn = typeof btnEl === 'string' ? document.getElementById(btnEl) : btnEl;
  if (!input) return;

  const showing = input.type === 'text';
  input.type = showing ? 'password' : 'text';

  if (btn) {
    if (typeof iconSvg === 'function') {
      btn.innerHTML = iconSvg(showing ? 'view' : 'viewOff', 18);
    } else {
      btn.innerHTML = `<span data-icon="${showing ? 'view' : 'viewOff'}" data-icon-size="18"></span>`;
      if (typeof renderIcons === 'function') renderIcons();
    }
    btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
    btn.setAttribute('title', showing ? 'Show password' : 'Hide password');
  }
}
window.toggleFieldPassword = toggleFieldPassword;


// Philippine mobile numbers: 09XXXXXXXXX (11 digits starting with 09).
// Paired with data-digits-only above, which strips letters/symbols as
// they're typed, so by the time this runs the only way to fail is
// wrong length or wrong prefix — not stray characters.
function bcIsValidContact(str) {
  const digits = (str || '').trim();
  return /^09\d{9}$/.test(digits);
}

function bcIsValidEmail(str) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((str || '').trim());
}

// True if dateStr (the "YYYY-MM-DD" value an <input type="date"> gives
// you) falls after today, in local time — used to block birth dates,
// filing dates, etc. that shouldn't be set in the future.
function bcIsFutureDate(dateStr) {
  if (!dateStr) return false;
  const d = new Date(dateStr + 'T00:00:00');
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return d.getTime() > today.getTime();
}

// True if dateStr is earlier than minDateStr (both "YYYY-MM-DD") — used
// for simple chronological ordering checks between two date fields on
// the same form (e.g. a settlement date shouldn't precede the
// confrontation date it followed).
function bcIsBeforeDate(dateStr, minDateStr) {
  if (!dateStr || !minDateStr) return false;
  return new Date(dateStr + 'T00:00:00').getTime() < new Date(minDateStr + 'T00:00:00').getTime();
}

// True if the combined date+time (a "YYYY-MM-DD" date input value plus an
// "HH:MM" time input value) falls after the current moment — used where a
// form has both a date AND a time field (e.g. Incident's Date/Time
// Reported), since data-no-future / bcIsFutureDate alone only cap the date
// part and would still let someone pick today's date with a time later
// than right now. If timeStr is empty, only the date is compared (same
// behavior as bcIsFutureDate).
function bcIsFutureDateTime(dateStr, timeStr) {
  if (!dateStr) return false;
  const dt = new Date(`${dateStr}T${timeStr || '00:00'}:00`);
  return dt.getTime() > Date.now();
}

// ── Real-Time Password Strength & Policy Validation ──────────
const PASSWORD_POLICY_ERROR_MSG = "Password does not meet the required security criteria. Please follow the instructions below.";

function bcValidatePasswordPolicy(password) {
  const p = password || '';
  const len = p.length >= 6 && p.length <= 128;
  const upper = /[A-Z]/.test(p);
  const lower = /[a-z]/.test(p);
  const num = /[0-9]/.test(p);
  const rawSpecial = /[^A-Za-z0-9]/.test(p);
  // High-entropy / password manager generated rule (12+ chars with upper, lower, numbers)
  const isHighEntropy = p.length >= 12 && upper && lower && num;
  const special = rawSpecial || isHighEntropy;
  const isValid = len && upper && lower && num && special;
  return { len, upper, lower, num, special, rawSpecial, isHighEntropy, isValid };
}

function bcUpdatePasswordChecklist(password, boxElOrId, isSubmittedAttempt = false) {
  const box = typeof boxElOrId === 'string' ? document.getElementById(boxElOrId) : boxElOrId;
  if (!box) return false;

  const res = bcValidatePasswordPolicy(password);
  const rules = [
    { key: 'len', passed: res.len },
    { key: 'upper', passed: res.upper },
    { key: 'lower', passed: res.lower },
    { key: 'num', passed: res.num },
    { key: 'special', passed: res.special }
  ];

  rules.forEach(({ key, passed }) => {
    const item = box.querySelector(`[data-rule="${key}"]`);
    if (!item) return;
    const icon = item.querySelector('.rule-icon');

    item.classList.remove('valid', 'invalid');

    if (passed) {
      item.classList.add('valid');
      if (icon) icon.textContent = '✓';
    } else {
      if (isSubmittedAttempt && password.length > 0) {
        item.classList.add('invalid');
        if (icon) icon.textContent = '✕';
      } else {
        if (icon) icon.textContent = '✓';
      }
    }
  });

  return res.isValid;
}

function bcCalculatePasswordStrength(password) {
  if (!password || password.length === 0) {
    return { score: 0, label: '', barClass: 'bg-gray-200', textClass: 'text-gray-400' };
  }
  const policy = bcValidatePasswordPolicy(password);

  // Level 3: Strong — High-entropy / 12+ chars with upper, lower, number, OR full policy criteria met
  if ((password.length >= 12 && policy.upper && policy.lower && policy.num) || policy.isValid) {
    return {
      score: 3,
      label: 'Strong',
      barClass: 'bg-emerald-600',
      textClass: 'text-emerald-600'
    };
  }

  const typesCount = (policy.upper ? 1 : 0) + (policy.lower ? 1 : 0) + (policy.num ? 1 : 0) + (policy.rawSpecial ? 1 : 0);

  // Level 2: Weak — at least 6 characters and 2+ character types
  if (password.length >= 6 && typesCount >= 2) {
    return {
      score: 2,
      label: 'Weak',
      barClass: 'bg-amber-500',
      textClass: 'text-amber-500'
    };
  }

  // Level 1: Too Weak — <6 chars or single character type
  return {
    score: 1,
    label: 'Too Weak',
    barClass: 'bg-red-500',
    textClass: 'text-red-500'
  };
}

function bcUpdatePasswordStrength(password, containerElOrId) {
  const container = typeof containerElOrId === 'string'
    ? document.getElementById(containerElOrId)
    : containerElOrId;
  if (!container) return;

  const bar1 = container.querySelector('.strength-bar-1');
  const bar2 = container.querySelector('.strength-bar-2');
  const bar3 = container.querySelector('.strength-bar-3');
  const label = container.querySelector('.strength-label');

  const strength = bcCalculatePasswordStrength(password);

  const colorClasses = ['bg-red-500', 'bg-amber-500', 'bg-emerald-600', 'bg-gray-200'];
  const textClasses = ['text-red-500', 'text-amber-500', 'text-emerald-600', 'text-gray-400'];

  [bar1, bar2, bar3].forEach(b => {
    if (b) b.classList.remove(...colorClasses);
  });
  if (label) {
    label.classList.remove(...textClasses);
  }

  if (strength.score === 0) {
    if (bar1) bar1.classList.add('bg-gray-200');
    if (bar2) bar2.classList.add('bg-gray-200');
    if (bar3) bar3.classList.add('bg-gray-200');
    if (label) {
      label.textContent = '';
      label.classList.add('text-gray-400');
    }
  } else if (strength.score === 1) {
    if (bar1) bar1.classList.add('bg-red-500');
    if (bar2) bar2.classList.add('bg-gray-200');
    if (bar3) bar3.classList.add('bg-gray-200');
    if (label) {
      label.textContent = 'Too Weak';
      label.classList.add('text-red-500');
    }
  } else if (strength.score === 2) {
    if (bar1) bar1.classList.add('bg-amber-500');
    if (bar2) bar2.classList.add('bg-amber-500');
    if (bar3) bar3.classList.add('bg-gray-200');
    if (label) {
      label.textContent = 'Weak';
      label.classList.add('text-amber-500');
    }
  } else if (strength.score === 3) {
    if (bar1) bar1.classList.add('bg-emerald-600');
    if (bar2) bar2.classList.add('bg-emerald-600');
    if (bar3) bar3.classList.add('bg-emerald-600');
    if (label) {
      label.textContent = 'Strong';
      label.classList.add('text-emerald-600');
    }
  }
}

function bcWatchPasswordInput(inputElOrId, strengthWrapId, reqBoxId) {
  const el = typeof inputElOrId === 'string' ? document.getElementById(inputElOrId) : inputElOrId;
  if (!el) return null;
  if (el._bcPwWatcherAttached) return el._bcPwWatcherAttached;

  let lastVal = el.value;

  const update = () => {
    const currentVal = el.value;
    if (currentVal !== lastVal) {
      lastVal = currentVal;
      if (typeof bcUpdatePasswordStrength === 'function') {
        bcUpdatePasswordStrength(currentVal, strengthWrapId);
      }
      if (typeof bcUpdatePasswordChecklist === 'function') {
        bcUpdatePasswordChecklist(currentVal, reqBoxId);
      }
    }
  };

  ['input', 'change', 'keyup', 'paste', 'blur', 'focus', 'propertychange', 'animationstart'].forEach(evt => {
    el.addEventListener(evt, update);
  });

  // Polling watcher for programmatic autofill from browser password managers
  const pollInterval = setInterval(() => {
    if (!document.body.contains(el)) {
      clearInterval(pollInterval);
      return;
    }
    update();
  }, 100);

  el._bcPwWatcherAttached = { update, pollInterval };
  update();
  return el._bcPwWatcherAttached;
}

window.bcValidatePasswordPolicy = bcValidatePasswordPolicy;
window.bcUpdatePasswordChecklist = bcUpdatePasswordChecklist;
window.bcCalculatePasswordStrength = bcCalculatePasswordStrength;
window.bcUpdatePasswordStrength = bcUpdatePasswordStrength;
window.bcWatchPasswordInput = bcWatchPasswordInput;
window.PASSWORD_POLICY_ERROR_MSG = PASSWORD_POLICY_ERROR_MSG;

// ── Forced password change (Security > Password Expiry (days)) ─────
// Built and injected on demand rather than living in every page's HTML,
// since it only needs to exist for the rare case a login comes back
// flagged mustChangePassword. Deliberately has no close/backdrop-dismiss
// path — Password Expiry means the account genuinely can't proceed with
// the old password, so this stays up until a valid change succeeds.
function bcShowForcedPasswordChange() {
  if (document.getElementById('bcForcedPwModal')) return; // already showing
  const overlay = document.createElement('div');
  overlay.id = 'bcForcedPwModal';
  overlay.className = 'modal-overlay open';
  overlay.setAttribute('data-no-dismiss', '');
  overlay.style.zIndex = '9999';
  overlay.innerHTML = `
    <div class="modal-box max-w-md">
      <h2 class="font-display text-xl text-forest-800 mb-1">Password Update Required</h2>
      <p class="text-sm text-forest-500 mb-4">Your password has expired per this system's Security policy. Please set a new one to continue.</p>
      <div class="space-y-3">
        <div><label class="form-label">Current Password</label><input type="password" id="bcPw_current" class="form-input" autocomplete="current-password"/></div>
        <div>
          <label class="form-label">New Password</label>
          <input type="password" id="bcPw_new" class="form-input" autocomplete="new-password" oninput="bcUpdatePasswordStrength(this.value, 'bcPw_strength_wrap'); bcUpdatePasswordChecklist(this.value, 'bcPw_req_box');" onchange="bcUpdatePasswordStrength(this.value, 'bcPw_strength_wrap'); bcUpdatePasswordChecklist(this.value, 'bcPw_req_box');"/>
          <div class="password-strength-container mt-2" id="bcPw_strength_wrap">
            <div class="flex items-center justify-between gap-3">
              <div class="strength-bars flex-1 flex gap-1.5 h-1.5">
                <div class="strength-bar-segment strength-bar-1 flex-1 rounded-full bg-gray-200 transition-colors duration-200"></div>
                <div class="strength-bar-segment strength-bar-2 flex-1 rounded-full bg-gray-200 transition-colors duration-200"></div>
                <div class="strength-bar-segment strength-bar-3 flex-1 rounded-full bg-gray-200 transition-colors duration-200"></div>
              </div>
              <span class="strength-label text-xs font-semibold min-w-[60px] text-right"></span>
            </div>
          </div>
          <div class="password-requirements-box mt-2" id="bcPw_req_box">
            <div class="req-title">
              <span data-i18n="password_must_contain">Password must contain:</span>
            </div>
            <ul class="space-y-1">
              <li class="rule-item" data-rule="len"><span class="rule-icon">•</span><span class="rule-text" data-i18n="rule_len">At least 6 characters long</span></li>
              <li class="rule-item" data-rule="upper"><span class="rule-icon">•</span><span class="rule-text" data-i18n="rule_upper">At least 1 uppercase letter (A–Z)</span></li>
              <li class="rule-item" data-rule="lower"><span class="rule-icon">•</span><span class="rule-text" data-i18n="rule_lower">At least 1 lowercase letter (a–z)</span></li>
              <li class="rule-item" data-rule="num"><span class="rule-icon">•</span><span class="rule-text" data-i18n="rule_num">At least 1 number (0–9)</span></li>
              <li class="rule-item" data-rule="special"><span class="rule-icon">•</span><span class="rule-text" data-i18n="rule_special">At least 1 special character (e.g., !@#$%^&*)</span></li>
            </ul>
          </div>
        </div>
        <div><label class="form-label">Confirm New Password</label><input type="password" id="bcPw_confirm" class="form-input" autocomplete="new-password"/></div>
        <div id="bcPw_error" class="text-red-600 text-xs hidden"></div>
        <div class="flex justify-end pt-2">
          <button id="bcPw_submit" class="btn-primary">Update Password</button>
        </div>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';
  if (typeof applyLanguageTranslation === 'function') applyLanguageTranslation();

  bcWatchPasswordInput('bcPw_new', 'bcPw_strength_wrap', 'bcPw_req_box');

  document.getElementById('bcPw_submit').onclick = async () => {
    const errEl = document.getElementById('bcPw_error');
    errEl.classList.add('hidden');
    const current = document.getElementById('bcPw_current').value;
    const next = document.getElementById('bcPw_new').value;
    const confirm = document.getElementById('bcPw_confirm').value;
    if (!current || !next || !confirm) {
      errEl.textContent = 'Please fill in all three fields.'; errEl.classList.remove('hidden'); return;
    }
    const policy = bcValidatePasswordPolicy(next);
    if (!policy.isValid) {
      errEl.textContent = PASSWORD_POLICY_ERROR_MSG;
      errEl.classList.remove('hidden');
      bcUpdatePasswordChecklist(next, 'bcPw_req_box', true);
      document.getElementById('bcPw_new').focus();
      return;
    }
    if (next !== confirm) {
      errEl.textContent = 'New password and confirmation do not match.'; errEl.classList.remove('hidden'); return;
    }
    try {
      await BCApi.changePassword(current, next);
      document.body.removeChild(overlay);
      document.body.style.overflow = '';
      showToast('Password updated. You\'re all set!');
    } catch (err) {
      errEl.textContent = err.message || 'Failed to change password.';
      errEl.classList.remove('hidden');
      document.getElementById('bcPw_new').value = '';
      document.getElementById('bcPw_confirm').value = '';
      bcUpdatePasswordStrength('', 'bcPw_strength_wrap');
      bcUpdatePasswordChecklist('', 'bcPw_req_box');
      document.getElementById('bcPw_new').focus();
    }
  };
}

// ── Global Account Settings Handlers ───────────────────────
window.saveMyPassword = async function saveMyPassword() {
  const currentEl = document.getElementById('acct_currentPw');
  const nextEl = document.getElementById('acct_newPw');
  const confirmEl = document.getElementById('acct_confirmPw');
  const errEl = document.getElementById('acct_pw_error');
  const btn = document.getElementById('btnChangePassword') || document.querySelector('button[onclick*="saveMyPassword"]');

  if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }
  if (currentEl) currentEl.classList.remove('border-red-500');
  if (nextEl) nextEl.classList.remove('border-red-500');
  if (confirmEl) confirmEl.classList.remove('border-red-500');

  const current = currentEl ? currentEl.value.trim() : '';
  const next = nextEl ? nextEl.value : '';
  const confirm = confirmEl ? confirmEl.value : '';

  if (!current || !next || !confirm) {
    const msg = 'Please fill in all password fields.';
    if (errEl) { errEl.textContent = msg; errEl.classList.remove('hidden'); }
    showToast(msg, 'error');
    if (!current && currentEl) currentEl.focus();
    else if (!next && nextEl) nextEl.focus();
    else if (!confirm && confirmEl) confirmEl.focus();
    return;
  }

  const policy = bcValidatePasswordPolicy(next);
  if (!policy.isValid) {
    if (errEl) { errEl.textContent = PASSWORD_POLICY_ERROR_MSG; errEl.classList.remove('hidden'); }
    if (nextEl) { nextEl.classList.add('border-red-500'); nextEl.focus(); }
    bcUpdatePasswordChecklist(next, 'acct_req_box', true);
    showToast(PASSWORD_POLICY_ERROR_MSG, 'error');
    return;
  }

  if (next !== confirm) {
    const msg = 'New passwords do not match.';
    if (errEl) { errEl.textContent = msg; errEl.classList.remove('hidden'); }
    if (confirmEl) {
      confirmEl.classList.add('border-red-500');
      confirmEl.focus();
    }
    showToast(msg, 'error');
    return;
  }

  if (current === next) {
    const msg = 'New password cannot be the same as your current password.';
    if (errEl) { errEl.textContent = msg; errEl.classList.remove('hidden'); }
    if (nextEl) {
      nextEl.classList.add('border-red-500');
      nextEl.focus();
    }
    showToast(msg, 'error');
    return;
  }

  if (btn) btn.disabled = true;

  try {
    const res = await BCApi.changePassword(current, next, confirm);
    if (currentEl) currentEl.value = '';
    if (nextEl) nextEl.value = '';
    if (confirmEl) confirmEl.value = '';
    bcUpdatePasswordStrength('', 'acct_strength_wrap');
    bcUpdatePasswordChecklist('', 'acct_req_box');
    if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }
    showToast(res?.message || 'Password changed successfully.', 'success');
  } catch (err) {
    const msg = err.message || (err.error ? err.error : 'Failed to change password.');
    if (errEl) {
      errEl.textContent = msg;
      errEl.classList.remove('hidden');
    }
    if (msg.toLowerCase().includes('current')) {
      if (currentEl) {
        currentEl.classList.add('border-red-500');
        currentEl.focus();
      }
    } else {
      if (nextEl) {
        nextEl.classList.add('border-red-500');
        nextEl.focus();
      }
    }
    showToast(msg, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
};

// ── Smart pagination ────────────────────────────────────────
// Renders Prev / page numbers / Next into `container`. With only a
// handful of pages every number shows; once there are more, it
// collapses everything except the first page, last page, and a small
// window around the current page into "…" — so a table with 28+ pages
// doesn't force the pagination bar to stretch across (or wrap under)
// the whole table. First/last/current-neighbors are always one click
// away either way.
// onPageChange(page) is called with the 1-based page number clicked.
function bcFormatRecordCount(total) {
  const isTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  const count = Number(total) || 0;
  return isTl ? `${count} mga tala` : `${count} records`;
}
window.bcFormatRecordCount = bcFormatRecordCount;

function bcInterpolatePagination(template, vars = {}) {
  const from = vars.from !== undefined ? vars.from : (vars.start !== undefined ? vars.start : 0);
  const to = vars.to !== undefined ? vars.to : (vars.end !== undefined ? vars.end : 0);
  const total = vars.total !== undefined ? vars.total : 0;
  return (template || '')
    .replace(/\{from\}/g, from)
    .replace(/\{to\}/g, to)
    .replace(/\{total\}/g, total);
}
window.bcInterpolatePagination = bcInterpolatePagination;

function bcFormatPaginationInfo(start, end, total, unit = '') {
  let from = start;
  let to = end;
  let tot = total;
  let u = unit;

  if (typeof start === 'object' && start !== null) {
    from = start.from !== undefined ? start.from : (start.start !== undefined ? start.start : 0);
    to = start.to !== undefined ? start.to : (start.end !== undefined ? start.end : 0);
    tot = start.total !== undefined ? start.total : 0;
    u = start.unit || end || '';
  }

  const isTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  const normalizedUnit = (String(u || '')).toLowerCase();
  from = Number(from) || 0;
  to = Number(to) || 0;
  tot = Number(tot) || 0;
  if (tot === 0) {
    from = 0;
    to = 0;
  }

  if (isTl) {
    if (normalizedUnit === 'incidents' || normalizedUnit === 'insidente') {
      return `Ipinapakita ang ${from} hanggang ${to} sa ${tot} na insidente`;
    }
    return `Ipinapakita ang ${from}–${to} ng ${tot}`;
  }
  if (normalizedUnit === 'incidents' || normalizedUnit === 'insidente') {
    if (tot === 0) return 'Showing 0 to 0 of 0 incidents';
    return `Showing ${from} to ${to} of ${tot} incident${tot !== 1 ? 's' : ''}`;
  }
  return `Showing ${from}–${to} of ${tot}`;
}
window.bcFormatPaginationInfo = bcFormatPaginationInfo;

function bcRenderPagination(container, currentPage, totalPages, onPageChange) {
  if (!container) return;
  container.innerHTML = '';
  totalPages = Math.max(1, totalPages);
  currentPage = Math.min(Math.max(1, currentPage), totalPages);

  const isTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  const prevLabel = isTl ? '‹ Nakalipas' : '‹ Prev';
  const nextLabel = isTl ? 'Susunod ›' : 'Next ›';

  const addBtn = (label, opts = {}) => {
    const b = document.createElement('button');
    b.textContent = label;
    b.type = 'button';
    b.className = 'pagination-btn' + (opts.active ? ' active' : '') + (opts.ellipsis ? ' pagination-ellipsis' : '');
    b.disabled = !!opts.disabled || !!opts.ellipsis;
    if (!b.disabled && opts.onClick) b.onclick = opts.onClick;
    container.appendChild(b);
  };

  addBtn(prevLabel, { disabled: currentPage === 1, onClick: () => onPageChange(currentPage - 1) });

  // Always show page 1, the last page, and a window around the current
  // page; everything in between collapses to a single "…".
  const keep = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
  const pages = [...keep].filter(p => p >= 1 && p <= totalPages).sort((a, b) => a - b);

  let last = 0;
  for (const p of pages) {
    if (last && p - last > 1) addBtn('…', { ellipsis: true });
    addBtn(String(p), { active: p === currentPage, onClick: () => onPageChange(p) });
    last = p;
  }

  addBtn(nextLabel, { disabled: currentPage === totalPages, onClick: () => onPageChange(currentPage + 1) });
}
window.bcRenderPagination = bcRenderPagination;

// ── Modal helpers & Lifecycle Teardown ──────────────────────
function dismissModal(modalEl, backdropEl) {
  if (modalEl) {
    modalEl.classList.add('hidden');
    modalEl.classList.remove('flex', 'show', 'active', 'open');
  }
  if (backdropEl) {
    backdropEl.classList.add('hidden');
    backdropEl.classList.remove('open');
    backdropEl.style.pointerEvents = 'none';
    // If dynamically injected, remove from DOM
    if (backdropEl.dataset.dynamic === "true") backdropEl.remove();
  }
  // Restore document body interactivity
  const hasActiveModals = document.querySelectorAll('.modal-form-card:not(.hidden), .confirm-modal-card:not(.hidden), .modal-overlay.open:not(.hidden)').length > 0;
  if (!hasActiveModals) {
    document.body.classList.remove('overflow-hidden', 'modal-open');
    document.body.style.overflow = '';
    document.body.style.pointerEvents = 'auto';
  }
}
window.dismissModal = dismissModal;

function openModal(id) {
  let el = typeof id === 'string' ? document.getElementById(id) : id;
  if (el && el.classList.contains('modal-box') && el.parentElement && el.parentElement.classList.contains('modal-overlay')) {
    el = el.parentElement;
  }
  if (el) {
    const isConfirm = el.id === 'bcDialogOverlay' || el.id === 'bcPermDeleteOverlay' || el.id === 'confirmModal' || el.id.toLowerCase().includes('confirm') || el.classList.contains('bc-confirm-dialog');
    if (isConfirm) {
      if (!document.body.contains(el) || el.parentElement !== document.body) {
        document.body.appendChild(el);
      }
      el.classList.add('confirm-modal-backdrop');
      const box = el.querySelector('.modal-box, .bc-dialog-box');
      if (box) {
        box.classList.add('confirm-modal-card');
        box.classList.remove('hidden');
      }
    } else {
      el.classList.add('modal-form-backdrop');
      const box = el.querySelector('.modal-box, .bc-dialog-box');
      if (box) {
        box.classList.add('modal-form-card');
        box.classList.remove('hidden');
      }
    }

    el.classList.remove('hidden');
    el.classList.add('open');
    el.style.pointerEvents = 'all';
    document.body.classList.add('overflow-hidden', 'modal-open');
    document.body.style.overflow = 'hidden';
    document.body.style.pointerEvents = 'auto';

    // Scope 2: Enforce hidden initial state on modal initialization
    const dropdowns = el.querySelectorAll('[id$="Suggestions"], #residentDropdownList, .search-results-dropdown');
    dropdowns.forEach(dd => {
      dd.classList.add('hidden');
      dd.innerHTML = '';
    });

    if (typeof applyLanguageTranslation === 'function') {
      applyLanguageTranslation();
    }

    if (typeof fitCertificatePreview === 'function') {
      setTimeout(fitCertificatePreview, 50);
      setTimeout(fitCertificatePreview, 150);
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        fitCertificatePreview();
      }, 300);
    }
  }
}

function closeModal(id) {
  let el = typeof id === 'string' ? document.getElementById(id) : id;
  if (el && el.classList.contains('modal-box') && el.parentElement && el.parentElement.classList.contains('modal-overlay')) {
    el = el.parentElement;
  }
  if (el) {
    const card = el.querySelector('.modal-box, .bc-dialog-box, .modal-form-card, .confirm-modal-card');
    dismissModal(card || el, el);
    if (typeof fitCertificatePreview === 'function') {
      setTimeout(fitCertificatePreview, 50);
      setTimeout(fitCertificatePreview, 150);
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        fitCertificatePreview();
      }, 300);
    }
  }
}

/**
 * Standardize dropdown reset across all forms and modals.
 * Resets all <select> elements in a given form or container to their default placeholder (<option value="">-Select-</option>).
 * @param {string|HTMLElement} target - form or modal element or its id
 */
function resetFormDropdowns(target) {
  const container = typeof target === 'string' ? (document.getElementById(target) || document.getElementById('indFormModal') || document.getElementById('indigencyFormModal')) : target;
  if (!container) return;
  const selects = container.querySelectorAll('select');
  selects.forEach(select => {
    const emptyOpt = select.querySelector('option[value=""]');
    if (emptyOpt) {
      select.value = '';
    } else if (select.options.length > 0) {
      select.selectedIndex = 0;
    }
    select.dispatchEvent(new Event('change', { bubbles: true }));
  });

  // Clear existing autocomplete dropdown options during form reset so no stale records persist
  const dropdowns = container.querySelectorAll('[id$="Suggestions"], #residentDropdownList, .search-results-dropdown');
  dropdowns.forEach(dd => {
    dd.classList.add('hidden');
    dd.innerHTML = '';
  });
}

document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay') && !e.target.hasAttribute('data-no-dismiss')) {
    closeModal(e.target);
  }
});

// Global Escape Key Listener for Modals & Overlays
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    // 1. Dismiss open autocomplete dropdowns first
    let dropdownClosed = false;
    if (typeof _bcResidentPickers !== 'undefined') {
      Object.keys(_bcResidentPickers).forEach(id => {
        const p = _bcResidentPickers[id];
        if (!p) return;
        const curList = document.getElementById(p.listId);
        if (curList && !curList.classList.contains('hidden')) {
          curList.classList.add('hidden');
          curList.innerHTML = '';
          const curIn = document.getElementById(id);
          const parentSec = curIn ? curIn.closest('#if_guardianSection, #if_involvedPartiesSection') : null;
          if (parentSec) parentSec.style.removeProperty('z-index');
          dropdownClosed = true;
        }
      });
    }
    const genericDropdowns = document.querySelectorAll('.search-results-dropdown:not(.hidden), #residentDropdownList:not(.hidden)');
    genericDropdowns.forEach(dd => {
      dd.classList.add('hidden');
      dd.innerHTML = '';
      dropdownClosed = true;
    });
    if (dropdownClosed) return;

    // 2. Dismiss confirm / alert dialogs if active
    if (typeof _bcPermDeleteEl !== 'undefined' && _bcPermDeleteEl && _bcPermDeleteEl.classList.contains('open')) {
      _bcPermDeleteFinish(false);
      return;
    }
    if (typeof _bcDialogEl !== 'undefined' && _bcDialogEl && _bcDialogEl.classList.contains('open')) {
      _bcDialogFinish(false);
      return;
    }

    // 3. Otherwise dismiss topmost open modal
    const openOverlays = Array.from(document.querySelectorAll('.modal-overlay.open:not([data-no-dismiss]), .confirm-modal-backdrop.open'));
    if (openOverlays.length > 0) {
      const topOverlay = openOverlays[openOverlays.length - 1];
      closeModal(topOverlay);
    }
  }
});

// ── Toast System with Linear Countdown Progress Bar ────────
let _toastTimer = null;
let _toastRemainingTime = 0;
let _toastStartTime = 0;
let _toastDuration = 3500;

function showToast(msg, type = 'success', duration = 3500) {
  if (typeof bcT === 'function' && typeof msg === 'string') {
    msg = bcT(msg);
  }
  let t = document.getElementById('globalToast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'globalToast';
    document.body.appendChild(t);
  }

  // Clear existing timer if toast is already active
  if (_toastTimer) {
    clearTimeout(_toastTimer);
    _toastTimer = null;
  }

  _toastDuration = duration || 3500;
  _toastRemainingTime = _toastDuration;

  // Icon per type: success → check, warning → alert-triangle, error → x, info → info
  const iconName = type === 'error' ? 'x' : type === 'warning' ? 'alert-triangle' : type === 'info' ? 'info' : 'check';
  const typeClass = type === 'error' ? 'error' : type === 'warning' ? 'warning' : type === 'info' ? 'info' : 'success';

  t.className = `toast ${typeClass}`;
  t.innerHTML = `
    <div class="flex items-center gap-2.5 flex-1 min-w-0 pr-1">
      <span data-icon="${iconName}" data-icon-size="16"></span>
      <span class="leading-snug">${msg}</span>
    </div>
    <div class="toast-progress-track">
      <div class="toast-progress-bar" style="animation: toastProgress ${_toastDuration}ms linear forwards;"></div>
    </div>
  `;

  if (window.lucide) lucide.createIcons({ nodes: [t] });

  // Force DOM reflow to restart CSS animation cleanly
  const progressBar = t.querySelector('.toast-progress-bar');
  if (progressBar) {
    progressBar.style.animation = 'none';
    void progressBar.offsetWidth; // trigger reflow
    progressBar.style.animation = `toastProgress ${_toastDuration}ms linear forwards`;
  }

  t.classList.add('show');
  _toastStartTime = Date.now();

  const dismissToast = () => {
    t.classList.remove('show');
    if (_toastTimer) {
      clearTimeout(_toastTimer);
      _toastTimer = null;
    }
  };

  _toastTimer = setTimeout(dismissToast, _toastDuration);

  // Hover Interactions: pause countdown on mouseenter, resume on mouseleave
  t.onmouseenter = () => {
    if (_toastTimer) {
      clearTimeout(_toastTimer);
      _toastTimer = null;
      _toastRemainingTime -= (Date.now() - _toastStartTime);
      if (_toastRemainingTime < 200) _toastRemainingTime = 200;
    }
  };

  t.onmouseleave = () => {
    if (t.classList.contains('show') && !_toastTimer) {
      _toastStartTime = Date.now();
      _toastTimer = setTimeout(dismissToast, _toastRemainingTime);
    }
  };

  // Synced cleanup on animationend
  if (progressBar) {
    progressBar.onanimationend = () => {
      if (!t.matches(':hover')) {
        dismissToast();
      }
    };
  }
}

// Expose programmatic toast dismissal
window.toast = {
  dismiss: () => {
    const t = document.getElementById('globalToast');
    if (t) {
      t.classList.remove('show');
      t.remove();
    }
    if (_toastTimer) {
      clearTimeout(_toastTimer);
      _toastTimer = null;
    }
  }
};

/**
 * Hard removal of toast notifications and dynamic alerts before browser print
 */
function executePrint() {
  // 1. Immediately dismiss via library API if available
  if (window.toast && typeof window.toast.dismiss === 'function') {
    window.toast.dismiss();
  }

  // 2. Fallback: Forcefully remove all toast and alert nodes from document.body
  const toastSelectors = [
    '.toast',
    '.toast-container',
    '[role="alert"]',
    '[role="status"]',
    '#toast-container',
    '#globalToast',
    '.toaster',
    '.sonner-toaster',
    '.hot-toast',
    '.chakra-portal',
    '.swal2-container'
  ];
  
  document.querySelectorAll(toastSelectors.join(',')).forEach(el => el.remove());

  // 3. Small microtask delay to let the layout recalculate before opening print dialog
  setTimeout(() => {
    window.print();
  }, 50);
}
window.executePrint = executePrint;

// Auto-purge toasts before any print event as an additional global safeguard
window.addEventListener('beforeprint', () => {
  if (window.toast && typeof window.toast.dismiss === 'function') {
    window.toast.dismiss();
  }
  const toastSelectors = [
    '.toast',
    '.toast-container',
    '[role="alert"]',
    '[role="status"]',
    '#toast-container',
    '#globalToast',
    '.toaster',
    '.sonner-toaster',
    '.hot-toast',
    '.chakra-portal',
    '.swal2-container'
  ];
  document.querySelectorAll(toastSelectors.join(',')).forEach(el => el.remove());
});

// ── Custom alert/confirm dialogs — drop-in async replacements for the
// native window.alert() / window.confirm(), styled to match the rest of
// the app instead of the browser's own popup. Built once, lazily, and
// reused for every call (same pattern as showToast above).
//   await bcAlert('message');
//   await bcAlert('message', { title: 'Heads up', okLabel: 'Got it' });
//   if (await bcConfirm('message')) { ... }
//   if (await bcConfirm('Delete this?', { danger: true, okLabel: 'Delete' })) { ... }
let _bcDialogEl = null;
let _bcDialogResolve = null;

function _bcEnsureDialog() {
  if (_bcDialogEl && document.body.contains(_bcDialogEl) && _bcDialogEl.parentElement === document.body) return _bcDialogEl;

  let el = document.getElementById('bcDialogOverlay');
  if (el) {
    if (el.parentElement !== document.body) document.body.appendChild(el);
    el.classList.add('confirm-modal-backdrop');
    const box = el.querySelector('.bc-dialog-box');
    if (box) box.classList.add('confirm-modal-card');
    _bcDialogEl = el;
    return el;
  }

  el = document.createElement('div');
  el.id = 'bcDialogOverlay';
  el.className = 'modal-overlay confirm-modal-backdrop';
  el.setAttribute('data-no-dismiss', ''); // clicking the backdrop shouldn't silently dismiss it
  el.innerHTML = `
    <div class="bc-dialog-box confirm-modal-card">
      <div class="bc-dialog-header">
        <span id="bcDialogIcon" class="bc-dialog-icon" data-icon="info" data-icon-size="18"></span>
        <h3 id="bcDialogTitle" class="bc-dialog-title"></h3>
      </div>
      <p id="bcDialogMessage" class="bc-dialog-message"></p>
      <div class="bc-dialog-actions">
        <button id="bcDialogCancelBtn" type="button" class="btn-secondary"></button>
        <button id="bcDialogOkBtn" type="button" class="btn-primary"></button>
      </div>
    </div>`;
  document.body.appendChild(el);
  _bcDialogEl = el;
  document.getElementById('bcDialogOkBtn').addEventListener('click', () => _bcDialogFinish(true));
  document.getElementById('bcDialogCancelBtn').addEventListener('click', () => _bcDialogFinish(false));
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') _bcDialogFinish(false);
  });
  return el;
}

function _bcDialogFinish(result) {
  if (_bcDialogEl) {
    dismissModal(_bcDialogEl.querySelector('.bc-dialog-box'), _bcDialogEl);
  }
  const resolve = _bcDialogResolve;
  _bcDialogResolve = null;
  if (resolve) resolve(result);
}

function _bcOpenDialog({ title, message, isConfirm, okLabel, cancelLabel, danger }) {
  // If there was an unresolved dialog promise, unlock it immediately
  if (_bcDialogResolve) {
    const prevResolve = _bcDialogResolve;
    _bcDialogResolve = null;
    try { prevResolve(false); } catch (_) {}
  }

  const el = _bcEnsureDialog();
  if (el.parentElement !== document.body) document.body.appendChild(el);
  el.classList.add('confirm-modal-backdrop');
  const box = el.querySelector('.bc-dialog-box');
  if (box) {
    box.classList.add('confirm-modal-card');
    box.classList.remove('hidden');
  }

  const titleEl = document.getElementById('bcDialogTitle');
  titleEl.textContent = title;
  if (danger) {
    titleEl.classList.add('danger');
    titleEl.style.color = '#9f1239';
  } else {
    titleEl.classList.remove('danger');
    titleEl.style.color = '#111827';
  }

  document.getElementById('bcDialogMessage').textContent = message;
  const cancelBtn = document.getElementById('bcDialogCancelBtn');
  const okBtn = document.getElementById('bcDialogOkBtn');
  const isDialogTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  cancelBtn.style.display = isConfirm ? '' : 'none';
  cancelBtn.textContent = cancelLabel || (isDialogTl ? 'Kanselahin' : 'Cancel');
  cancelBtn.className = 'bg-[#eaf6ee] text-emerald-900 border border-emerald-200 px-6 py-2.5 rounded-xl font-medium hover:bg-emerald-100 transition-colors text-sm cursor-pointer';

  okBtn.textContent = okLabel || (isConfirm ? (isDialogTl ? 'Kumpirmahin' : 'Confirm') : 'OK');
  if (danger) {
    okBtn.className = 'bg-rose-600 text-white hover:bg-rose-700 shadow-sm transition-all cursor-pointer border border-rose-700 px-6 py-2.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2';
  } else {
    okBtn.className = 'bg-[#1b4332] hover:bg-[#143326] text-white px-6 py-2.5 rounded-xl font-medium text-sm transition-colors shadow-sm flex items-center justify-center gap-2 cursor-pointer';
  }

  const icon = document.getElementById('bcDialogIcon');
  icon.dataset.icon = danger ? 'warning' : 'info';
  icon.innerHTML = '';
  delete icon.dataset.iconRendered;
  icon.className = 'bc-dialog-icon' + (danger ? ' danger' : '');
  if (typeof renderIcons === 'function') renderIcons(el);

  el.classList.remove('hidden');
  el.classList.add('open');
  el.style.pointerEvents = 'all';
  document.body.classList.add('overflow-hidden', 'modal-open');
  document.body.style.overflow = 'hidden';
  document.body.style.pointerEvents = 'auto';
  setTimeout(() => (danger && isConfirm ? cancelBtn : okBtn).focus(), 50);
  return new Promise(resolve => { _bcDialogResolve = resolve; });
}

/** Drop-in async replacement for window.alert(). Always resolves (no return value needed). */
function bcAlert(message, opts = {}) {
  const isTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  return _bcOpenDialog({ title: opts.title || (isTl ? 'Paunawa' : 'Notice'), message, isConfirm: false, okLabel: opts.okLabel, danger: opts.danger });
}

/** Drop-in async replacement for window.confirm() — resolves to true (OK/Confirm) or false (Cancel/Esc). */
function bcConfirm(message, opts = {}) {
  const isTl = (localStorage.getItem('app_language') || 'en') === 'tl' || (localStorage.getItem('preferred_language') || 'en') === 'tl' || document.documentElement.lang === 'tl' || (typeof bcGetLanguage === 'function' && bcGetLanguage() === 'Filipino');
  return _bcOpenDialog({
    title: opts.title || (isTl ? 'Mangyaring Kumpirmahin' : 'Please Confirm'), message, isConfirm: true,
    okLabel: opts.okLabel, cancelLabel: opts.cancelLabel, danger: opts.danger,
  });
}

// ── Double-confirmation dialog for irreversible Permanent Deletion ──
let _bcPermDeleteEl = null;
let _bcPermDeleteResolve = null;

function _bcEnsurePermDeleteDialog() {
  if (_bcPermDeleteEl && document.body.contains(_bcPermDeleteEl) && _bcPermDeleteEl.parentElement === document.body) return _bcPermDeleteEl;

  let el = document.getElementById('bcPermDeleteOverlay');
  if (el) {
    if (el.parentElement !== document.body) document.body.appendChild(el);
    el.classList.add('confirm-modal-backdrop');
    const box = el.querySelector('.modal-box');
    if (box) box.classList.add('confirm-modal-card');
    _bcPermDeleteEl = el;
    return el;
  }

  el = document.createElement('div');
  el.id = 'bcPermDeleteOverlay';
  el.className = 'modal-overlay confirm-modal-backdrop';
  el.setAttribute('data-no-dismiss', '');
  el.innerHTML = `
    <div class="modal-box confirm-modal-card max-w-lg p-6 md:p-7 bg-white rounded-2xl shadow-2xl border border-rose-100" style="max-width: 520px; width: 92vw;">
      <!-- Modal Header -->
      <div class="flex items-start justify-between gap-4 mb-4">
        <div class="flex items-center gap-3.5">
          <div class="w-11 h-11 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-rose-600"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </div>
          <div>
            <h2 id="bcPermDeleteTitle" class="font-display text-xl font-bold text-[#9f1239] leading-tight" style="font-family: 'DM Serif Display', serif; color: #9f1239; font-size: 1.25rem; font-weight: 700; margin: 0;">Permanently Delete Record</h2>
            <p id="bcPermDeleteSubtitle" class="text-xs text-rose-600 font-medium mt-0.5" style="font-size: 0.75rem; color: #e11d48; margin-top: 2px;">Destructive Record Removal</p>
          </div>
        </div>
        <button id="bcPermDeleteCloseXBtn" type="button" class="modal-close-btn text-gray-400 hover:text-gray-700 p-1.5 rounded-lg transition-colors cursor-pointer" aria-label="Close modal">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>

      <!-- Dynamic Target Description -->
      <p id="bcPermDeleteMessage" class="text-sm text-forest-800 leading-relaxed" style="font-family: 'DM Sans', sans-serif; font-size: 0.875rem; color: #1e3a29; line-height: 1.6; margin-bottom: 0.75rem;"></p>

      <!-- Red Warning Callout Box -->
      <div class="bg-rose-50 border border-rose-200 rounded-xl p-4 my-4" style="background-color: #fff1f2; border: 1px solid #fecdd3; border-radius: 0.75rem; padding: 1rem; margin: 1rem 0;">
        <p class="text-xs text-rose-700 leading-relaxed" style="font-size: 0.75rem; color: #be123c; line-height: 1.5; margin: 0;">
          <strong class="text-rose-800 font-bold" style="color: #9f1239; font-weight: 700;">Warning:</strong> This action cannot be undone. All personal data, activity records, and authentication credentials linked to this record will be permanently purged from the database.
        </p>
      </div>

      <!-- Type-to-Confirm Input & Validation -->
      <div class="space-y-1.5 mb-6" style="margin-bottom: 1.5rem;">
        <label for="bcPermDeleteInput" class="block text-xs font-semibold text-forest-800" style="display: block; font-size: 0.75rem; font-weight: 600; color: #1e3a29; margin-bottom: 0.375rem;">
          Type <span class="bg-rose-100 text-rose-700 font-mono font-bold text-xs px-2 py-0.5 rounded" style="background: #ffe4e6; color: #be123c; font-family: monospace; font-weight: 700; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px;">DELETE</span> to proceed:
        </label>
        <input
          id="bcPermDeleteInput"
          type="text"
          class="w-full focus:ring-2 focus:ring-emerald-600 focus:border-emerald-600 border-2 border-emerald-600/70 rounded-xl px-4 py-2.5 font-mono text-sm tracking-wider uppercase bg-white text-forest-900 placeholder:text-gray-400 focus:outline-none transition-all"
          style="width: 100%; border: 2px solid rgba(5, 150, 105, 0.7); border-radius: 0.75rem; padding: 0.625rem 1rem; font-family: monospace; font-size: 0.875rem; letter-spacing: 0.05em; text-transform: uppercase; background: #fff; color: #1e3a29; outline: none; box-sizing: border-box;"
          placeholder="TYPE DELETE TO CONFIRM"
          autocomplete="off"
          spellcheck="false"
        />
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center justify-end gap-3 pt-2" style="display: flex; align-items: center; justify-content: flex-end; gap: 0.75rem; padding-top: 0.5rem;">
        <button
          id="bcPermDeleteCancelBtn"
          type="button"
          class="bg-[#eaf6ee] text-emerald-900 border border-emerald-200 px-6 py-2.5 rounded-xl font-medium hover:bg-emerald-100 transition-colors text-sm cursor-pointer"
          style="background: #eaf6ee; color: #064e3b; border: 1px solid #a7f3d0; padding: 0.625rem 1.5rem; border-radius: 0.75rem; font-weight: 500; font-size: 0.875rem; cursor: pointer;"
        >
          Cancel
        </button>
        <button
          id="bcPermDeleteOkBtn"
          type="button"
          disabled
          class="bg-rose-50 text-rose-300 cursor-not-allowed opacity-70 border border-rose-200 px-6 py-2.5 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2 select-none"
          style="background: #fff1f2; color: #fda4af; border: 1px solid #fecdd3; padding: 0.625rem 1.5rem; border-radius: 0.75rem; font-weight: 600; font-size: 0.875rem; opacity: 0.7; cursor: not-allowed; transition: all 0.15s;"
        >
          Permanent Delete
        </button>
      </div>
    </div>`;
  document.body.appendChild(el);
  _bcPermDeleteEl = el;

  const input = document.getElementById('bcPermDeleteInput');
  const okBtn = document.getElementById('bcPermDeleteOkBtn');
  const cancelBtn = document.getElementById('bcPermDeleteCancelBtn');
  const closeXBtn = document.getElementById('bcPermDeleteCloseXBtn');

  input.addEventListener('input', () => {
    const isMatch = input.value.trim().toUpperCase() === 'DELETE';
    okBtn.disabled = !isMatch;
    if (isMatch) {
      okBtn.className = "bg-rose-600 text-white hover:bg-rose-700 shadow-sm transition-all cursor-pointer border border-rose-700 px-6 py-2.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2";
      okBtn.style.background = '#e11d48';
      okBtn.style.color = '#fff';
      okBtn.style.borderColor = '#be123c';
      okBtn.style.opacity = '1';
      okBtn.style.cursor = 'pointer';
    } else {
      okBtn.className = "bg-rose-50 text-rose-300 cursor-not-allowed opacity-70 border border-rose-200 px-6 py-2.5 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2 select-none";
      okBtn.style.background = '#fff1f2';
      okBtn.style.color = '#fda4af';
      okBtn.style.borderColor = '#fecdd3';
      okBtn.style.opacity = '0.7';
      okBtn.style.cursor = 'not-allowed';
    }
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !okBtn.disabled) {
      _bcPermDeleteFinish(true);
    }
  });

  okBtn.addEventListener('click', () => {
    if (!okBtn.disabled) _bcPermDeleteFinish(true);
  });

  cancelBtn.addEventListener('click', () => _bcPermDeleteFinish(false));
  if (closeXBtn) closeXBtn.addEventListener('click', () => _bcPermDeleteFinish(false));

  el.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') _bcPermDeleteFinish(false);
  });

  return el;
}

function _bcPermDeleteFinish(result) {
  if (_bcPermDeleteEl) {
    dismissModal(_bcPermDeleteEl.querySelector('.modal-box'), _bcPermDeleteEl);
  }
  const resolve = _bcPermDeleteResolve;
  _bcPermDeleteResolve = null;
  if (resolve) resolve(result);
}

/**
 * Enterprise double-confirmation modal requiring typing "DELETE" to permanently purge a record.
 * @param {string} message - Descriptive warning text
 * @param {Object} opts - { title, recordName, subtitle }
 * @returns {Promise<boolean>}
 */
function bcConfirmPermanentDelete(message, opts = {}) {
  // If there was an unresolved delete promise, unlock it immediately
  if (_bcPermDeleteResolve) {
    const prevResolve = _bcPermDeleteResolve;
    _bcPermDeleteResolve = null;
    try { prevResolve(false); } catch (_) {}
  }

  const el = _bcEnsurePermDeleteDialog();
  if (el.parentElement !== document.body) document.body.appendChild(el);
  el.classList.add('confirm-modal-backdrop');
  const box = el.querySelector('.modal-box');
  if (box) {
    box.classList.add('confirm-modal-card');
    box.classList.remove('hidden');
  }

  document.getElementById('bcPermDeleteTitle').textContent = opts.title || 'Permanently Delete Record';
  const subEl = document.getElementById('bcPermDeleteSubtitle');
  if (subEl) {
    subEl.textContent = opts.subtitle || 'Destructive Record Removal';
  }

  const msgEl = document.getElementById('bcPermDeleteMessage');
  if (typeof message === 'string' && (message.includes('<') || message.includes('"'))) {
    let formatted = message;
    if (!formatted.includes('<span') && !formatted.includes('<strong')) {
      formatted = formatted
        .replace(/"([^"]+)"/g, '<strong class="font-bold text-forest-900" style="color: #0a2414; font-weight: 700;">"$1"</strong>')
        .replace(/(\([^)]+\))/g, '<span class="font-mono font-semibold text-rose-700" style="color: #be123c; font-family: monospace; font-weight: 600;">$1</span>')
        .replace(/\b(IRREVERSIBLE)\b/gi, '<strong class="text-rose-700 font-semibold" style="color: #be123c; font-weight: 600;">$1</strong>');
    }
    msgEl.innerHTML = formatted;
  } else {
    msgEl.textContent = message || 'Are you sure you want to permanently delete this record?';
  }

  const input = document.getElementById('bcPermDeleteInput');
  const okBtn = document.getElementById('bcPermDeleteOkBtn');
  input.value = '';
  okBtn.disabled = true;
  okBtn.className = "bg-rose-50 text-rose-300 cursor-not-allowed opacity-70 border border-rose-200 px-6 py-2.5 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2 select-none";
  okBtn.style.background = '#fff1f2';
  okBtn.style.color = '#fda4af';
  okBtn.style.borderColor = '#fecdd3';
  okBtn.style.opacity = '0.7';
  okBtn.style.cursor = 'not-allowed';

  el.classList.remove('hidden');
  el.classList.add('open');
  el.style.pointerEvents = 'all';
  document.body.classList.add('overflow-hidden', 'modal-open');
  document.body.style.overflow = 'hidden';
  document.body.style.pointerEvents = 'auto';
  setTimeout(() => input.focus(), 60);

  return new Promise(resolve => { _bcPermDeleteResolve = resolve; });
}

// ── Report Preview & Tab Management Helpers (Method A) ──
if (typeof window !== 'undefined' && typeof window.BC_REPORT_FAVICON === 'undefined') {
  window.BC_REPORT_FAVICON = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%231e3a2b'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM14 9V3.5L18.5 8H14z'/></svg>";
}

function openReportPrintTab(htmlContent, reportTitle = 'Settlement Compliance Report', autoPrint = false) {
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    if (typeof showToast === 'function') {
      showToast('Please allow popups to preview report.', 'error');
    }
    return null;
  }

  const faviconUrl = (typeof window !== 'undefined' && window.BC_REPORT_FAVICON)
    ? window.BC_REPORT_FAVICON
    : "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%231e3a2b'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM14 9V3.5L18.5 8H14z'/></svg>";

  printWindow.document.write(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>${reportTitle}</title>
      <!-- Sets the PDF / App Icon in browser tab -->
      <link rel="icon" type="image/svg+xml" href="${faviconUrl}">
      <style>
        /* Report base styling */
        @page { size: letter portrait; margin: 0.5in; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          padding: 24px;
          color: #1e293b;
          background: #ffffff;
        }
        .header {
          text-align: center;
          border-bottom: 2px solid #0f172a;
          padding-bottom: 12px;
          margin-bottom: 18px;
        }
        .header h2 {
          margin: 0 0 4px;
          font-size: 18px;
          color: #1e3a2b;
          text-transform: uppercase;
          letter-spacing: 0.04em;
        }
        .header p {
          margin: 0;
          font-size: 13px;
          color: #64748b;
        }
        
        /* Enforce responsive, non-overlapping table cells */
        table.report-table {
          width: 100% !important;
          table-layout: fixed !important; /* Critical to respect defined cell widths */
          border-collapse: collapse !important;
          font-size: 11px;
          margin-top: 12px;
        }

        table.report-table th,
        table.report-table td {
          white-space: normal !important; /* Disables nowrap */
          word-wrap: break-word !important;
          overflow-wrap: break-word !important;
          word-break: break-word !important;
          vertical-align: top !important;
          padding: 6px 8px !important;
        }

        table.report-table th {
          background: #1e3a2b !important;
          color: #ffffff !important;
          font-weight: 600;
          border: 1px solid #1e3a2b;
          text-align: left;
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
        }

        table.report-table td {
          border: 1px solid #cbd5e1;
          color: #1e293b;
        }

        table.report-table tbody tr:nth-child(even) {
          background: #f0f9f2 !important;
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
        }

        .footer { margin-top: 24px; font-size: 11px; color: #94a3b8; text-align: right; }
        @media print {
          body { padding: 0; }
          @page { margin: 1.5cm; }
          table.report-table {
            width: 100% !important;
            table-layout: fixed !important;
            border-collapse: collapse !important;
          }
          table.report-table th,
          table.report-table td {
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            word-break: break-word !important;
            vertical-align: top !important;
            padding: 6px 8px !important;
          }
          table.report-table th {
            background-color: #1e3a2b !important;
            color: #ffffff !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          table.report-table tbody tr:nth-child(even) {
            background-color: #f0f9f2 !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
        }
      </style>
    </head>
    <body>
      ${htmlContent}
      ${autoPrint ? '<script>window.onload = function() { window.print(); };</script>' : ''}
    </body>
    </html>
  `);

  printWindow.document.close();
  printWindow.document.title = reportTitle; // Guarantees title reflects on tab bar
  return printWindow;
}
if (typeof window !== 'undefined') {
  if (typeof window.BC_REPORT_FAVICON === 'undefined') {
    window.BC_REPORT_FAVICON = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%231e3a2b'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM14 9V3.5L18.5 8H14z'/></svg>";
  }
  window.openReportPrintTab = openReportPrintTab;
}

// ── Reusable Batch Action Manager for Records Tables ──
class BcBatchManager {
  constructor(opts) {
    this.opts = Object.assign({
      entityName: 'record',
      entityPlural: 'records',
      apiType: 'incidents',
      selectAllId: 'selectAllCheckbox',
      getPageItems: () => [],
      getAllItems: () => [],
      isArchivedView: () => false,
      onRefresh: async () => {},
    }, opts);

    this.selectedIds = new Set();
    this._barEl = null;
    this._ensureToolbar();
    this._initTouchLongPress();
  }

  _ensureToolbar() {
    let el = document.getElementById('bcBatchFloatingBar');
    if (!el) {
      el = document.createElement('div');
      el.id = 'bcBatchFloatingBar';
      el.className = 'bc-batch-bar';
      document.body.appendChild(el);
    }
    this._barEl = el;
  }

  _initTouchLongPress() {
    let touchTimer = null;
    let startX = 0;
    let startY = 0;
    let targetRow = null;

    document.addEventListener('touchstart', (e) => {
      const tr = e.target.closest('tr[data-id]');
      if (!tr || e.target.closest('button, a, input, select, textarea, .row-actions, .bc-batch-bar')) return;
      
      targetRow = tr;
      startX = e.touches[0]?.clientX || 0;
      startY = e.touches[0]?.clientY || 0;

      touchTimer = setTimeout(() => {
        const rowId = targetRow?.getAttribute('data-id');
        if (rowId) {
          if (navigator.vibrate) {
            try { navigator.vibrate(40); } catch (_) {}
          }
          this.toggle(rowId, !this.has(rowId));
        }
        touchTimer = null;
      }, 500);
    }, { passive: true });

    const clearTouch = () => {
      if (touchTimer) {
        clearTimeout(touchTimer);
        touchTimer = null;
      }
      targetRow = null;
    };

    document.addEventListener('touchmove', (e) => {
      if (!touchTimer) return;
      const curX = e.touches[0]?.clientX || 0;
      const curY = e.touches[0]?.clientY || 0;
      if (Math.abs(curX - startX) > 10 || Math.abs(curY - startY) > 10) {
        clearTouch();
      }
    }, { passive: true });

    document.addEventListener('touchend', clearTouch, { passive: true });
    document.addEventListener('touchcancel', clearTouch, { passive: true });
  }

  has(id) {
    return this.selectedIds.has(Number(id));
  }

  toggle(id, checked) {
    const numId = Number(id);
    if (checked) {
      this.selectedIds.add(numId);
    } else {
      this.selectedIds.delete(numId);
    }

    // Immediate visual DOM feedback
    const tr = document.querySelector(`tr[data-id="${numId}"]`);
    if (tr) {
      tr.classList.toggle('row-selected', checked);
      const cb = tr.querySelector('input[type="checkbox"]');
      if (cb && cb.checked !== checked) cb.checked = checked;
    }

    this.updateUI();
  }

  toggleSelectAll(checked, items) {
    const targetItems = items || this.opts.getPageItems() || [];
    targetItems.forEach(item => {
      const numId = Number(item.id);
      if (checked) {
        this.selectedIds.add(numId);
      } else {
        this.selectedIds.delete(numId);
      }

      // Immediate visual row update
      const tr = document.querySelector(`tr[data-id="${numId}"]`);
      if (tr) {
        tr.classList.toggle('row-selected', checked);
        const cb = tr.querySelector('input[type="checkbox"]');
        if (cb && cb.checked !== checked) cb.checked = checked;
      }
    });
    this.updateUI();
  }

  selectAllAcrossFiltered() {
    const all = this.opts.getAllItems() || [];
    all.forEach(item => this.selectedIds.add(Number(item.id)));

    // Highlight all visible page rows
    const pageItems = this.opts.getPageItems() || [];
    pageItems.forEach(item => {
      const tr = document.querySelector(`tr[data-id="${item.id}"]`);
      if (tr) {
        tr.classList.add('row-selected');
        const cb = tr.querySelector('input[type="checkbox"]');
        if (cb) cb.checked = true;
      }
    });

    this.updateUI();
  }

  clearSelection() {
    this.selectedIds.clear();

    // Clear highlights and checkboxes on visible rows
    const pageItems = this.opts.getPageItems() || [];
    pageItems.forEach(item => {
      const tr = document.querySelector(`tr[data-id="${item.id}"]`);
      if (tr) {
        tr.classList.remove('row-selected');
        const cb = tr.querySelector('input[type="checkbox"]');
        if (cb) cb.checked = false;
      }
    });

    this.updateUI();
  }

  updateUI() {
    const pageItems = this.opts.getPageItems() || [];
    const allItems = this.opts.getAllItems() || [];
    const pageCount = pageItems.length;
    const allCount = allItems.length;
    const selectedOnPage = pageItems.filter(item => this.selectedIds.has(Number(item.id))).length;
    const totalSelected = this.selectedIds.size;

    // Clean up any legacy top selection banners
    document.querySelectorAll('.bc-selection-banner-wrap').forEach(b => b.remove());

    // 1. Sync Selection Mode on Table Elements
    const tables = document.querySelectorAll('table.data-table');
    tables.forEach(tbl => {
      if (totalSelected > 0) {
        tbl.classList.add('selection-mode-active');
      } else {
        tbl.classList.remove('selection-mode-active');
      }
    });

    // 2. Sync header select all checkbox state (checked / indeterminate / unchecked)
    const selectAllCb = document.getElementById(this.opts.selectAllId);
    if (selectAllCb) {
      if (pageCount > 0 && selectedOnPage === pageCount) {
        selectAllCb.checked = true;
        selectAllCb.indeterminate = false;
      } else if (selectedOnPage > 0) {
        selectAllCb.checked = false;
        selectAllCb.indeterminate = true;
      } else {
        selectAllCb.checked = false;
        selectAllCb.indeterminate = false;
      }
    }

    // 3. Render Floating Bottom Action Pill / Toolbar
    if (totalSelected === 0) {
      if (this._barEl) this._barEl.classList.remove('visible');
      return;
    }

    const isArchived = this.opts.isArchivedView();
    const entityLabel = totalSelected === 1 ? this.opts.entityName : this.opts.entityPlural;
    const activeRole = (typeof CURRENT_ROLE !== 'undefined' && CURRENT_ROLE) || (window.CURRENT_USER && window.CURRENT_USER.role);
    const canDelete = (typeof roleCan === 'function') ? roleCan(activeRole, 'delete_records') : (activeRole === 'System Admin');
    const canArchive = (typeof roleCan === 'function') ? roleCan(activeRole, 'archive_records') : true;

    const isAllGlobalSelected = totalSelected >= allCount && allCount > 0;
    const canSelectAllGlobal = !isAllGlobalSelected && allCount > totalSelected;

    this._barEl.innerHTML = `
      <div class="bc-batch-count">
        <span class="bc-batch-count-badge">${totalSelected}</span>
        <span class="bc-batch-count-label">
          ${isAllGlobalSelected ? `All <strong>${allCount}</strong> ${this.opts.entityPlural} selected` : `<strong>${totalSelected}</strong> ${entityLabel} selected`}
        </span>
        ${canSelectAllGlobal ? `
          <button id="bcBatchSelectAllGlobalBtn" type="button" class="bc-batch-btn select-all" title="Select all ${allCount} ${this.opts.entityPlural} across all pages">
            Select all ${allCount} across all pages
          </button>
        ` : ''}
      </div>
      <div class="bc-batch-actions">
        ${isArchived ? `
          <button id="bcBatchRestoreBtn" type="button" class="bc-batch-btn restore" title="Restore Selected">
            ${typeof iconSvg === 'function' ? iconSvg('refresh', 14) : ''} Restore Selected (${totalSelected})
          </button>
          ${canDelete ? `
          <button id="bcBatchPermDeleteBtn" type="button" class="bc-batch-btn danger" title="Permanently Delete Selected">
            ${typeof iconSvg === 'function' ? iconSvg('trash', 14) : ''} Permanently Delete Selected (${totalSelected})
          </button>
          ` : ''}
        ` : canArchive ? `
          <button id="bcBatchArchiveBtn" type="button" class="bc-batch-btn archive" title="Archive Selected">
            ${typeof iconSvg === 'function' ? iconSvg('archive', 14) : ''} Archive Selected (${totalSelected})
          </button>
        ` : ''}
        <button id="bcBatchDeselectBtn" type="button" class="bc-batch-btn ghost" title="Clear selection">
          Deselect All
        </button>
      </div>
    `;

    document.getElementById('bcBatchSelectAllGlobalBtn')?.addEventListener('click', () => this.selectAllAcrossFiltered());
    document.getElementById('bcBatchDeselectBtn')?.addEventListener('click', () => this.clearSelection());

    if (isArchived) {
      document.getElementById('bcBatchRestoreBtn')?.addEventListener('click', () => this.executeBatchRestore());
      if (canDelete) {
        document.getElementById('bcBatchPermDeleteBtn')?.addEventListener('click', () => this.executeBatchPermanentDelete());
      }
    } else {
      if (canArchive) {
        document.getElementById('bcBatchArchiveBtn')?.addEventListener('click', () => this.executeBatchArchive());
      }
    }

    this._barEl.classList.add('visible');
  }

  getSelectedItems() {
    const all = this.opts.getAllItems() || [];
    return all.filter(item => this.selectedIds.has(Number(item.id)));
  }

  exportSelectedCsv() {
    const items = this.getSelectedItems();
    if (!items.length) {
      showToast('No records selected for export.', 'error');
      return;
    }

    let csvContent = '\uFEFF'; // UTF-8 BOM for Excel
    const escapeCsv = (val) => {
      if (val === null || val === undefined) return '""';
      const str = String(val).replace(/"/g, '""');
      return `"${str}"`;
    };

    if (this.opts.apiType === 'census') {
      const headers = ['RESIDENT NO.', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'DATE OF BIRTH', 'AGE', 'SEX', 'CIVIL STATUS', 'NATIONALITY', 'ZONE', 'ADDRESS', 'HOUSEHOLD NO.', 'VOTER STATUS', 'STATUS'];
      csvContent += headers.map(escapeCsv).join(',') + '\n';
      items.forEach(r => {
        csvContent += [
          r.resNo || '', r.lastName || '', r.firstName || '', r.midName || '', r.dob || '', r.age ?? '',
          r.sex || '', r.civil || '', r.nationality || '', r.zone || '', r.address || '', r.household || '',
          r.voter || '', r.status || ''
        ].map(escapeCsv).join(',') + '\n';
      });
    } else if (this.opts.apiType === 'incidents') {
      const headers = ['REPORT NO.', 'DATE REPORTED', 'TIME REPORTED', 'ZONE', 'LOCATION', 'CATEGORY', 'DESCRIPTION', 'REPORTER', 'OFFICER', 'PRIORITY', 'STATUS'];
      csvContent += headers.map(escapeCsv).join(',') + '\n';
      items.forEach(r => {
        csvContent += [
          r.reportNo || '', r.dateReported || '', r.timeReported || '', r.zone || '', r.location || '',
          r.category || '', r.description || '', r.reporter || '', r.officer || '', r.priority || '', r.status || ''
        ].map(escapeCsv).join(',') + '\n';
      });
    } else if (this.opts.apiType === 'blotter') {
      const headers = [
        'DOCKET NO.',
        'DATE FILED',
        'COMPLAINANT',
        'COMPLAINANT ADDRESS',
        'RESPONDENT',
        'RESPONDENT ADDRESS',
        'NATURE OF CASE',
        'CASE TYPE',
        'STATUS'
      ];
      csvContent += headers.map(escapeCsv).join(',') + '\n';
      items.forEach(r => {
        csvContent += [
          r.docketNo || '', r.dateFiled || '', r.complainant || '', r.complainantAddr || '',
          r.respondent || '', r.respondentAddr || '', r.nature || '', r.type || '', r.status || ''
        ].map(escapeCsv).join(',') + '\n';
      });
    } else if (this.opts.apiType === 'settlements') {
      const headers = ['CASE NO.', 'CASE TITLE', 'COMPLAINT NATURE', 'DATE FILED', 'ACTION TAKEN / SCHEDULE', 'STATUS'];
      csvContent += headers.map(escapeCsv).join(',') + '\n';
      items.forEach(r => {
        csvContent += [
          r.caseNo || '', r.caseTitle || '', r.nature || r.complaintTitle || '', r.dateFiled || '',
          r.actionTaken || '', r.status || ''
        ].map(escapeCsv).join(',') + '\n';
      });
    } else {
      const keys = Object.keys(items[0] || {});
      csvContent += keys.map(escapeCsv).join(',') + '\n';
      items.forEach(item => {
        csvContent += keys.map(k => escapeCsv(item[k])).join(',') + '\n';
      });
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `BlotterCast_${this.opts.entityPlural}_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Exported ${items.length} ${this.opts.entityPlural} to CSV successfully.`);
  }

  batchPrintSelected() {
    const items = this.getSelectedItems();
    if (!items.length) {
      showToast('No records selected for printing.', 'error');
      return;
    }

    let tableRowsHtml = '';
    let tableHeadersHtml = '';

    if (this.opts.apiType === 'census') {
      tableHeadersHtml = `
        <tr>
          <th style="width: 5%;">#</th>
          <th style="width: 13%;">Resident No.</th>
          <th style="width: 18%;">Full Name</th>
          <th style="width: 10%;">Birth Date</th>
          <th style="width: 6%;">Age</th>
          <th style="width: 6%;">Sex</th>
          <th style="width: 7%;">Civil</th>
          <th style="width: 8%;">Zone</th>
          <th style="width: 17%;">Address</th>
          <th style="width: 10%;">Status</th>
        </tr>
      `;
      tableRowsHtml = items.map((r, i) => `
        <tr>
          <td>${i + 1}</td>
          <td>${r.resNo || '—'}</td>
          <td><strong>${r.lastName || ''}, ${r.firstName || ''}</strong></td>
          <td>${r.dob || '—'}</td>
          <td>${r.age ?? '—'}</td>
          <td>${r.sex || '—'}</td>
          <td>${r.civil || '—'}</td>
          <td>${r.zone || '—'}</td>
          <td>${r.address || '—'}</td>
          <td>${r.status || '—'}</td>
        </tr>
      `).join('');
    } else if (this.opts.apiType === 'incidents') {
      tableHeadersHtml = `
        <tr>
          <th style="width: 15%;">Report No.</th>
          <th style="width: 15%;">Date &amp; Time</th>
          <th style="width: 18%;">Location</th>
          <th style="width: 20%;">Category</th>
          <th style="width: 18%;">Reporter</th>
          <th style="width: 14%;">Status</th>
        </tr>
      `;
      tableRowsHtml = items.map((r, i) => `
        <tr>
          <td><strong>${r.reportNo || '—'}</strong></td>
          <td>${r.dateReported || '—'} ${r.timeReported || ''}</td>
          <td>${r.zone || ''} ${r.location || ''}</td>
          <td>${r.category || '—'}</td>
          <td>${r.reporter || '—'}</td>
          <td>${r.status || '—'}</td>
        </tr>
      `).join('');
    } else if (this.opts.apiType === 'blotter') {
      tableHeadersHtml = `
        <tr>
          <th style="width: 15%;">Docket No.</th>
          <th style="width: 13%;">Date Filed</th>
          <th style="width: 20%;">Complainant</th>
          <th style="width: 20%;">Respondent</th>
          <th style="width: 18%;">Nature</th>
          <th style="width: 14%;">Status</th>
        </tr>
      `;
      tableRowsHtml = items.map((r, i) => `
        <tr>
          <td><strong>${r.docketNo || '—'}</strong></td>
          <td>${r.dateFiled || '—'}</td>
          <td>${r.complainant || '—'}</td>
          <td>${r.respondent || '—'}</td>
          <td>${r.nature || '—'}</td>
          <td>${r.status || '—'}</td>
        </tr>
      `).join('');
    } else if (this.opts.apiType === 'settlements') {
      tableHeadersHtml = `
        <tr>
          <th class="w-[15%]" style="width: 15%;">Case No.</th>
          <th class="w-[35%]" style="width: 35%;">Case Title</th>
          <th class="w-[18%]" style="width: 18%;">Nature</th>
          <th class="w-[17%]" style="width: 17%;">Date Filed</th>
          <th class="w-[15%]" style="width: 15%;">Status</th>
        </tr>
      `;
      tableRowsHtml = items.map((r, i) => `
        <tr>
          <td><strong>${r.caseNo || '—'}</strong></td>
          <td>${r.caseTitle || r.title || '—'}</td>
          <td>${r.nature || r.complaintTitle || '—'}</td>
          <td>${r.dateFiled || '—'}</td>
          <td>${r.status || '—'}</td>
        </tr>
      `).join('');
    } else {
      tableHeadersHtml = `
        <tr>
          <th class="w-[15%]" style="width: 15%;">Case No.</th>
          <th class="w-[35%]" style="width: 35%;">Case Title</th>
          <th class="w-[18%]" style="width: 18%;">Nature</th>
          <th class="w-[17%]" style="width: 17%;">Date Filed</th>
          <th class="w-[15%]" style="width: 15%;">Status</th>
        </tr>
      `;
      tableRowsHtml = items.map((r, i) => `
        <tr>
          <td><strong>${r.caseNo || '—'}</strong></td>
          <td>${r.caseTitle || r.title || '—'}</td>
          <td>${r.nature || r.complaintTitle || '—'}</td>
          <td>${r.dateFiled || '—'}</td>
          <td>${r.status || '—'}</td>
        </tr>
      `).join('');
    }

    const dateStr = new Date().toISOString().slice(0, 10);
    let entityType = 'Report';
    if (this.opts.apiType === 'settlements') entityType = 'Settlement_Compliance_Report';
    else if (this.opts.apiType === 'blotter') entityType = 'Blotter_Report';
    else if (this.opts.apiType === 'incidents') entityType = 'Incident_Summary_Report';
    else if (this.opts.apiType === 'census') entityType = 'Census_Registry_Report';
    else if (this.opts.entityPlural) entityType = `${this.opts.entityPlural}_Report`;

    const reportTitle = `${entityType}_${dateStr}`;
    const displayHeading = `Barangay Mapulang Lupa — Selected ${this.opts.entityPlural.toUpperCase()}`;

    const reportHtml = `
      <div class="header">
        <h2>Republic of the Philippines • City of Valenzuela</h2>
        <p><strong>BARANGAY MAPULANG LUPA</strong> • BlotterCast Official Records System</p>
        <p style="margin-top: 4px; font-weight: bold; color: #1e3a2b;">${displayHeading} (${items.length} records printed on ${new Date().toLocaleDateString()})</p>
      </div>
      <table class="report-table">
        <thead>
          ${tableHeadersHtml}
        </thead>
        <tbody>
          ${tableRowsHtml}
        </tbody>
      </table>
      <div class="footer">
        Printed via BlotterCast System • ${new Date().toLocaleString()}
      </div>
    `;

    openReportPrintTab(reportHtml, reportTitle, true);
  }

  async batchUpdateIncidentStatus() {
    const items = this.getSelectedItems();
    if (!items.length) return;

    const newStatus = prompt(
      `Update Status for ${items.length} selected incident(s):\nEnter one of: Ongoing, Under Investigation, Resolved, Closed, Elevated to Blotter`,
      'Resolved'
    );
    if (!newStatus || !newStatus.trim()) return;

    const targetStatus = newStatus.trim();
    let updatedCount = 0;
    for (const item of items) {
      try {
        await BCApi.update('incidents', item.id, { status: targetStatus });
        updatedCount++;
      } catch (err) {
        console.warn(`Failed to update incident ${item.id}:`, err);
      }
    }

    showToast(`Updated status to "${targetStatus}" for ${updatedCount} incident(s).`);
    this.clearSelection();
    await this.opts.onRefresh();
  }

  async batchUpdateBlotterStatus() {
    const items = this.getSelectedItems();
    if (!items.length) return;

    const newStatus = prompt(
      `Update Status for ${items.length} selected blotter record(s):\nEnter one of: Ongoing, Under Mediation, Hearing Scheduled, Resolved, Settled, Dismissed, CFA Issued`,
      'Resolved'
    );
    if (!newStatus || !newStatus.trim()) return;

    const targetStatus = newStatus.trim();
    let updatedCount = 0;
    for (const item of items) {
      try {
        await BCApi.update('blotter', item.id, { status: targetStatus });
        updatedCount++;
      } catch (err) {
        console.warn(`Failed to update blotter ${item.id}:`, err);
      }
    }

    showToast(`Updated status to "${targetStatus}" for ${updatedCount} blotter record(s).`);
    this.clearSelection();
    await this.opts.onRefresh();
  }

  async batchRescheduleSettlement() {
    const items = this.getSelectedItems();
    if (!items.length) return;

    const newDate = prompt(
      `Batch Reschedule Hearing for ${items.length} selected case(s):\nEnter new hearing date (YYYY-MM-DD) or schedule note:`,
      new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10)
    );
    if (!newDate || !newDate.trim()) return;

    const scheduleVal = newDate.trim();
    let updatedCount = 0;
    for (const item of items) {
      try {
        await BCApi.update('settlements', item.id, { actionTaken: `Hearing scheduled for ${scheduleVal}` });
        updatedCount++;
      } catch (err) {
        console.warn(`Failed to reschedule settlement ${item.id}:`, err);
      }
    }

    showToast(`Rescheduled hearing for ${updatedCount} case(s).`);
    this.clearSelection();
    await this.opts.onRefresh();
  }

  async executeBatchArchive() {
    const ids = Array.from(this.selectedIds);
    if (!ids.length) return;
    const count = ids.length;
    const label = count === 1 ? this.opts.entityName : this.opts.entityPlural;
    const cascadeNote = ['incidents', 'blotter', 'settlements'].includes(this.opts.apiType)
      ? ' Any connected Incident Reports, Blotter Records, and Settlement Cases will also be automatically archived.'
      : '';

    const confirmed = await bcConfirm(
      `Archive ${count} selected ${label}? They will be moved to the archive view and can be restored later.${cascadeNote}`,
      { title: `Batch Archive ${this.opts.entityPlural.toUpperCase()}`, danger: true, okLabel: `Archive Selected (${count})` }
    );
    if (!confirmed) return;

    try {
      await BCApi.batchArchive(this.opts.apiType, ids);
      showToast(`${count} ${label} archived successfully.`);
    } catch (err) {
      showToast(err.message || 'Failed to archive records', 'error');
    } finally {
      this.clearSelection();
      try {
        await this.opts.onRefresh();
      } catch (rErr) {
        console.warn('Post-archive refresh error:', rErr);
      }
    }
  }

  async executeBatchRestore() {
    const ids = Array.from(this.selectedIds);
    if (!ids.length) return;
    const count = ids.length;
    const label = count === 1 ? this.opts.entityName : this.opts.entityPlural;
    const cascadeNote = ['incidents', 'blotter', 'settlements'].includes(this.opts.apiType)
      ? ' Any connected Incident Reports, Blotter Records, and Settlement Cases will also be automatically restored.'
      : '';

    const confirmed = await bcConfirm(
      `Restore ${count} selected ${label} back to the active list?${cascadeNote}`,
      { title: `Batch Restore ${this.opts.entityPlural.toUpperCase()}`, okLabel: `Restore Selected (${count})` }
    );
    if (!confirmed) return;

    try {
      await BCApi.batchRestore(this.opts.apiType, ids);
      showToast(`${count} ${label} restored to active list.`);
    } catch (err) {
      showToast(err.message || 'Failed to restore records', 'error');
    } finally {
      this.clearSelection();
      try {
        await this.opts.onRefresh();
      } catch (rErr) {
        console.warn('Post-restore refresh error:', rErr);
      }
    }
  }

  async executeBatchPermanentDelete() {
    const activeRole = (typeof CURRENT_ROLE !== 'undefined' && CURRENT_ROLE) || (window.CURRENT_USER && window.CURRENT_USER.role);
    const canDelete = (typeof roleCan === 'function') ? roleCan(activeRole, 'delete_records') : (activeRole === 'System Admin');
    if (!canDelete) {
      bcAlert('Access Denied: Only System Administrators are authorized to permanently delete records.', { title: 'Access Denied', danger: true });
      return;
    }

    const ids = Array.from(this.selectedIds);
    if (!ids.length) return;
    const count = ids.length;
    const label = count === 1 ? this.opts.entityName : this.opts.entityPlural;
    const cascadeNote = ['incidents', 'blotter', 'settlements'].includes(this.opts.apiType)
      ? ' All connected Incident Reports, Blotter Records, Settlement Cases, and notifications will also be permanently purged.'
      : '';

    const confirmed = await bcConfirmPermanentDelete(
      `Are you sure you want to permanently delete ${count} selected ${label}? This action is IRREVERSIBLE and will hard-delete matching data from the database.${cascadeNote}`,
      { title: `Batch Permanent Delete (${count} ${label})` }
    );
    if (!confirmed) return;

    try {
      await BCApi.batchPermanentDelete(this.opts.apiType, ids);
      showToast(`${count} ${label} permanently deleted.`);
    } catch (err) {
      showToast(err.message || 'Failed to delete records', 'error');
    } finally {
      this.clearSelection();
      try {
        await this.opts.onRefresh();
      } catch (rErr) {
        console.warn('Post-delete refresh error:', rErr);
      }
    }
  }
}
window.BcBatchManager = BcBatchManager;

// ── Sidebar shared HTML builder (call once per page) ───────
function buildSidebar(activePage) {
  const pages = [
    { href:'dashboard.html',  icon:'dashboard', label:'Dashboard',          group:'main' },
    { href:'blotter.html',    icon:'blotter', label:'Blotter Records',     group:'main' },
    { href:'incident.html',   icon:'incident', label:'Incident Reports',    group:'main' },
    { href:'settlement.html', icon:'settlement', label:'Settlement Monitor',  group:'main' },
    { href:'heatmap.html',    icon:'heatmap', label:'Heat Map',            group:'analytics' },
    { href:'trends.html',     icon:'trends', label:'Trends',              group:'analytics' },
    { href:'predictions.html',icon:'predictions', label:'Predictions',         group:'analytics' },
    { href:'users.html',      icon:'users', label:'Users & Roles',       group:'system' },
    { href:'reports.html',    icon:'reports', label:'Reports',             group:'system' },
    { href:'settings.html',   icon:'settings', label:'Settings',            group:'system' },
  ];
  const groupLabels = { main:'Main Menu', analytics:'Analytics', system:'System' };
  let lastGroup = null, html = '';
  pages.forEach(p => {
    if (p.group !== lastGroup) {
      html += `<p class="text-forest-400 text-xs font-semibold uppercase tracking-widest px-3 py-2 ${lastGroup ? 'mt-4':''}">
                 ${groupLabels[p.group]}</p>`;
      lastGroup = p.group;
    }
    html += `<a href="${p.href}" class="nav-link${p.href === activePage ? ' active':''}">
               <span class="nav-icon" data-icon="${p.icon}">${typeof iconSvg === 'function' ? iconSvg(p.icon) : ''}</span> ${p.label}</a>`;
  });
  return html;
}

// ── Shared export-filter modal (year/month picker before an .xlsx download) ──
// Call openExportFilter(exportUrl, title) from any page; injects a small modal
// into the DOM on first use so pages don't need to duplicate the markup.
let _exportFilterUrl = '';
function _ensureExportFilterModal() {
  if (document.getElementById('bcExportFilterModal')) return;
  const el = document.createElement('div');
  el.innerHTML = `
    <div class="modal-overlay" id="bcExportFilterModal">
      <div class="modal-box" style="width:420px">
        <div class="flex items-center justify-between mb-5">
          <h2 class="font-display text-lg text-forest-800" id="bcExportFilterTitle" data-i18n="export_blotter_title">Export Blotter Records</h2>
          <button onclick="closeModal('bcExportFilterModal')" class="modal-close-btn"><span data-icon="x" data-icon-size="18"></span></button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="form-label" data-i18n="period_label">Period</label>
            <select id="bcExportPeriod" class="form-input" onchange="_updateExportFilterFields()">
              <option value="all" data-i18n="period_all">All Records</option>
              <option value="year" data-i18n="period_year">Specific Year</option>
              <option value="month" data-i18n="period_month">Specific Month</option>
            </select>
          </div>
          <div id="bcExportYearWrap" class="hidden">
            <label class="form-label" data-i18n="year_label">Year</label>
            <select id="bcExportYear" class="form-input"></select>
          </div>
          <div id="bcExportMonthWrap" class="hidden">
            <label class="form-label" data-i18n="month_label">Month</label>
            <select id="bcExportMonth" class="form-input">
              <option value="1" data-i18n="month_jan">January</option><option value="2" data-i18n="month_feb">February</option><option value="3" data-i18n="month_mar">March</option>
              <option value="4" data-i18n="month_apr">April</option><option value="5" data-i18n="month_may">May</option><option value="6" data-i18n="month_jun">June</option>
              <option value="7" data-i18n="month_jul">July</option><option value="8" data-i18n="month_aug">August</option><option value="9" data-i18n="month_sep">September</option>
              <option value="10" data-i18n="month_oct">October</option><option value="11" data-i18n="month_nov">November</option><option value="12" data-i18n="month_dec">December</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-5">
          <button type="button" onclick="closeModal('bcExportFilterModal')" class="btn-secondary" data-i18n="cancel">Cancel</button>
          <button type="button" onclick="_confirmExportFilter()" class="btn-primary flex items-center gap-2">
            <span data-icon="download" data-icon-size="16"></span> <span data-i18n="download">Download</span>
          </button>
        </div>
      </div>
    </div>`;
  document.body.appendChild(el.firstElementChild);
  const yearSel = document.getElementById('bcExportYear');
  const thisYear = new Date().getFullYear();
  for (let y = thisYear; y >= thisYear - 5; y--) {
    const opt = document.createElement('option');
    opt.value = y; opt.textContent = y;
    yearSel.appendChild(opt);
  }
}
function _updateExportFilterFields() {
  const period = document.getElementById('bcExportPeriod').value;
  document.getElementById('bcExportYearWrap').classList.toggle('hidden', period === 'all');
  document.getElementById('bcExportMonthWrap').classList.toggle('hidden', period !== 'month');
}
function openExportFilter(exportUrl, title) {
  _ensureExportFilterModal();
  _exportFilterUrl = exportUrl;
  const titleEl = document.getElementById('bcExportFilterTitle');
  if (title) {
    if (title === 'Export Blotter Records') {
      titleEl.setAttribute('data-i18n', 'export_blotter_title');
    } else {
      titleEl.removeAttribute('data-i18n');
      titleEl.textContent = typeof bcT === 'function' ? bcT(title, title) : title;
    }
  } else {
    titleEl.setAttribute('data-i18n', 'export_blotter_title');
  }
  document.getElementById('bcExportPeriod').value = 'all';
  _updateExportFilterFields();
  if (typeof applyLanguageTranslation === 'function') {
    applyLanguageTranslation();
  }
  if (typeof bcApplyLanguage === 'function') {
    bcApplyLanguage(typeof bcGetLanguage === 'function' ? bcGetLanguage() : 'English');
  }
  openModal('bcExportFilterModal');
}
function _confirmExportFilter() {
  const period = document.getElementById('bcExportPeriod').value;
  let url = _exportFilterUrl;
  if (period === 'year') {
    url += (url.includes('?') ? '&' : '?') + 'year=' + document.getElementById('bcExportYear').value;
  } else if (period === 'month') {
    url += (url.includes('?') ? '&' : '?') + 'year=' + document.getElementById('bcExportYear').value
         + '&month=' + document.getElementById('bcExportMonth').value;
  }
  window.location.href = url;
  closeModal('bcExportFilterModal');
}

// ── Shared Blotter Details Modal (used in Certificate Issuance, Blotter, Settlements) ──
let _cachedBlotterRecords = null;
let _cachedBlotterTimestamp = 0;

function _escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function _ensureBlotterDetailsModal() {
  let modal = document.getElementById('bcBlotterDetailsModal');
  if (modal) {
    if (!document.body.contains(modal)) document.body.appendChild(modal);
    return modal;
  }
  const el = document.createElement('div');
  el.className = 'modal-overlay';
  el.id = 'bcBlotterDetailsModal';
  el.style.zIndex = '1060';
  el.innerHTML = `
    <div class="modal-box max-w-xl" style="max-height: 90vh; overflow-y: auto;">
      <div class="flex items-center justify-between pb-4 mb-4 border-b border-emerald-100/70">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl border border-amber-300 bg-amber-50 flex items-center justify-center text-amber-700 flex-shrink-0">
            <span data-icon="blotter" data-icon-size="18"></span>
          </div>
          <div>
            <h2 class="font-display text-lg sm:text-xl text-forest-800 font-bold leading-tight">Blotter Record Details</h2>
            <p class="text-xs text-emerald-700 font-medium mt-0.5" id="bcBlotterModalSubtitle">Official Barangay Docket Record</p>
          </div>
        </div>
        <button type="button" onclick="closeModal('bcBlotterDetailsModal')" class="modal-close-btn text-gray-400 hover:text-gray-700 transition-colors" title="Close"><span data-icon="x" data-icon-size="18"></span></button>
      </div>
      <div id="bcBlotterDetailsContent" class="space-y-3">
        <div class="py-8 text-center text-forest-400">Loading blotter details…</div>
      </div>
      <div class="mt-6 pt-4 border-t border-emerald-100/70 flex items-center justify-between">
        <span class="text-emerald-700 text-sm font-medium">BlotterCast Barangay System</span>
        <button type="button" onclick="closeModal('bcBlotterDetailsModal')" class="bg-[#eaf6ee] text-emerald-900 border border-emerald-200 px-6 py-2 rounded-xl font-medium hover:bg-emerald-100 transition-colors text-sm">Close</button>
      </div>
    </div>`;
  document.body.appendChild(el);
  if (window.renderIcons) window.renderIcons(el);
  return el;
}

async function openBlotterDetailsModal(docketNoOrIdOrCaseData) {
  const modal = _ensureBlotterDetailsModal();
  const contentEl = document.getElementById('bcBlotterDetailsContent');
  const subtitleEl = document.getElementById('bcBlotterModalSubtitle');
  if (!docketNoOrIdOrCaseData) return;

  let targetDocket = '';
  let targetId = null;
  let initialData = null;

  if (typeof docketNoOrIdOrCaseData === 'object' && docketNoOrIdOrCaseData !== null) {
    initialData = { ...docketNoOrIdOrCaseData };
    targetDocket = initialData.docket_no || initialData.docketNo || '';
    targetId = initialData.id || initialData.blotter_id || initialData.blotterId || null;
  } else {
    const rawVal = String(docketNoOrIdOrCaseData).trim();
    try {
      targetDocket = decodeURIComponent(rawVal);
    } catch (_) {
      targetDocket = rawVal;
    }
    if (/^\d+$/.test(targetDocket)) {
      targetId = Number(targetDocket);
    }
  }

  function renderDetails(r) {
    if (!r) {
      contentEl.innerHTML = `
        <div class="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
          <strong>Record Not Found:</strong> Could not retrieve full details for blotter entry <em>${_escapeHtml(targetDocket || String(targetId || ''))}</em>.
        </div>`;
      return;
    }

    const docketNo = r.docket_no || r.docketNo || targetDocket || '—';
    const dateFiled = r.date_filed || r.dateFiled || r.date || '—';
    const complainant = r.complainant || '—';
    const complainantAddr = r.complainant_addr || r.complainantAddr || '—';
    const respondent = r.respondent || '—';
    const respondentAddr = r.respondent_addr || r.respondentAddr || '—';
    const nature = r.nature || '—';
    const rawType = (r.case_type || r.type || 'CRIM').toUpperCase();
    const typeLabel = rawType === 'CRIM' ? 'Criminal' : (rawType === 'CIVIL' ? 'Civil' : rawType);
    const typeBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">${_escapeHtml(typeLabel)}</span>`;
    const status = r.status || 'Ongoing';
    const statusBadge = (status === 'Resolved' || status === 'Settled' || status === 'Complied' || status === 'Closed')
      ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">${_escapeHtml(status)}</span>`
      : `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-700 border border-rose-200">${_escapeHtml(status)}</span>`;

    if (subtitleEl) subtitleEl.textContent = `Docket: ${docketNo}`;

    const rows = [
      ['DOCKET NO.', `<span class="font-bold font-mono text-gray-900">${_escapeHtml(docketNo)}</span>`],
      ['DATE FILED', `<span class="text-gray-900 font-semibold text-sm">${_escapeHtml(dateFiled)}</span>`],
      ['CASE TYPE', typeBadge],
      ['NATURE OF CASE', `<span class="text-gray-900 font-semibold text-sm">${_escapeHtml(nature)}</span>`],
      ['STATUS', statusBadge],
      ['COMPLAINANT', `<div class="text-gray-900 font-semibold text-sm">${_escapeHtml(complainant)}</div>${complainantAddr ? `<div class="text-emerald-700/80 text-xs mt-0.5 font-medium">${_escapeHtml(complainantAddr)}</div>` : ''}`],
      ['RESPONDENT', `<div class="text-gray-900 font-semibold text-sm">${_escapeHtml(respondent)}</div>${respondentAddr ? `<div class="text-emerald-700/80 text-xs mt-0.5 font-medium">${_escapeHtml(respondentAddr)}${r.zone || r.zone_id ? ` &bull; ${_escapeHtml(r.zone || r.zone_id)}` : ''}</div>` : ''}`],
    ];

    if (r.settlement_status || r.settlementStatus) {
      rows.push(['SETTLEMENT STATUS', `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">${_escapeHtml(r.settlement_status || r.settlementStatus)}</span>`]);
    }
    if (r.hold_reason) {
      rows.push(['HOLD REASON', `<span class="text-amber-800 text-xs font-medium">${_escapeHtml(r.hold_reason)}</span>`]);
    }

    contentEl.innerHTML = `
      <div class="bg-[#f4faf6] rounded-2xl border border-emerald-100/60 p-6 space-y-1 shadow-sm">
        ${rows.map(([k, v]) => `
          <div class="flex flex-col sm:flex-row sm:items-start gap-1.5 sm:gap-4 py-3.5 border-b border-emerald-100/70 last:border-0">
            <span class="w-44 sm:w-48 text-xs font-bold tracking-wider text-emerald-800 uppercase flex-shrink-0 pt-0.5">${k}</span>
            <div class="flex-1 text-sm">${v}</div>
          </div>
        `).join('')}
      </div>
    `;
    if (window.renderIcons) window.renderIcons(contentEl);
  }

  if (initialData && (initialData.complainant || initialData.respondent)) {
    renderDetails(initialData);
  } else {
    contentEl.innerHTML = `<div class="py-8 text-center text-forest-500 text-xs"><span class="inline-block animate-spin mr-2" data-icon="spinner" data-icon-size="14">${typeof iconSvg === 'function' ? iconSvg('spinner', 14) : ''}</span> Loading blotter case details…</div>`;
  }

  openModal('bcBlotterDetailsModal');

  try {
    const now = Date.now();
    let records = _cachedBlotterRecords;
    if (!records || (now - _cachedBlotterTimestamp > 60000)) {
      records = await BCApi.list('blotter');
      if (Array.isArray(records)) {
        _cachedBlotterRecords = records;
        _cachedBlotterTimestamp = now;
      }
    }

    if (Array.isArray(records)) {
      const match = records.find(x =>
        (targetId && Number(x.id) === Number(targetId)) ||
        (targetDocket && String(x.docket_no || x.docketNo || '').toLowerCase() === targetDocket.toLowerCase())
      );
      if (match) {
        renderDetails({ ...(initialData || {}), ...match });
      } else if (!initialData) {
        renderDetails(null);
      }
    }
  } catch (err) {
    console.error('Error fetching full blotter record:', err);
    if (!initialData) {
      renderDetails(null);
    }
  }
}

window.openBlotterDetailsModal = openBlotterDetailsModal;
window.handleOpenBlotterDetails = openBlotterDetailsModal;
window.openBlotterModal = openBlotterDetailsModal;
window.showBlotterDetailsModal = openBlotterDetailsModal;

function getStatusBadge(status) {
  const s = String(status || '').toUpperCase().trim();
  switch (s) {
    case 'UNDER INVESTIGATION':
      return 'bg-amber-100 text-amber-800 border border-amber-300';
    case 'ELEVATED':
    case 'ELEVATED TO BLOTTER':
      // Enforce consistent soft red styling
      return 'bg-red-100 text-red-700 border border-red-200';
    case 'SETTLED':
    case 'RESOLVED':
      return 'bg-emerald-100 text-emerald-800 border border-emerald-300';
    default:
      return 'bg-gray-100 text-gray-700 border border-gray-200';
  }
}
window.getStatusBadge = getStatusBadge;

// ── Notification bell (real, system-generated alerts) ──────
// Only does anything on pages that actually have #notifPanel in the DOM
// (currently the Dashboard); harmless no-op calls elsewhere.
const NOTIF_TYPE_CONFIG = {
  incident_crud: { icon: 'incident', color: '#16a34a', badge: 'INCIDENT', badge_tl: 'INSIDENTE', bg: '#f0fdf4' },
  incident_elevated: { icon: 'blotter', color: '#ea580c', badge: 'ELEVATED TO BLOTTER', badge_tl: 'NAITAAS SA BLOTTER', bg: '#fff7ed' },
  settlement_updated: { icon: 'settlement', color: '#0284c7', badge: 'SETTLEMENT', badge_tl: 'PAG-AAYOS', bg: '#f0f9ff' },
  settlement_created: { icon: 'settlement', color: '#0284c7', badge: 'SETTLEMENT', badge_tl: 'PAG-AAYOS', bg: '#f0f9ff' },
  new_incident: { icon: 'warning', color: '#dc2626', badge: 'HIGH PRIORITY', badge_tl: 'MATAAS NA PRIYORIDAD', bg: '#fef2f2' },
  heatmap_hotspot: { icon: 'heatmap', color: '#d97706', badge: 'GEOSPATIAL', badge_tl: 'HEOGRAPIKO', bg: '#fffbeb' },
  heatmap_alert: { icon: 'heatmap', color: '#d97706', badge: 'GEOSPATIAL', badge_tl: 'HEOGRAPIKO', bg: '#fffbeb' },
  predictive_risk: { icon: 'predictions', color: '#7c3aed', badge: 'PREDICTIVE ML', badge_tl: 'PREDIKSYON ML', bg: '#f5f3ff' },
  prediction_alert: { icon: 'predictions', color: '#7c3aed', badge: 'PREDICTION ALERT', badge_tl: 'BABALA SA PREDIKSYON', bg: '#f5f3ff' },
  high_risk_zone: { icon: 'predictions', color: '#7c3aed', badge: 'PREDICTIVE ML', badge_tl: 'PREDIKSYON ML', bg: '#f5f3ff' },
  trend_spike: { icon: 'trends', color: '#2563eb', badge: 'TREND SURGE', badge_tl: 'PAGTAAS NG TREND', bg: '#eff6ff' },
  trend_alert: { icon: 'trends', color: '#2563eb', badge: 'TREND ALERT', badge_tl: 'BABALA SA TREND', bg: '#eff6ff' },
  settlement_overdue: { icon: 'clock', color: '#d97706', badge: 'SETTLEMENT', badge_tl: 'PAG-AAYOS', bg: '#fffbeb' },
};

function timeAgo(dateStr) {
  const isFil = typeof bcGetLanguage === 'function' && (bcGetLanguage().toLowerCase().startsWith('fil') || bcGetLanguage().toLowerCase().startsWith('tag') || bcGetLanguage().toLowerCase() === 'tl');
  if (!dateStr) return isFil ? 'ngayon lang' : 'just now';
  let parsed;
  if (typeof dateStr === 'string') {
    const s = dateStr.trim();
    if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?$/.test(s) && !/[zZ+-]\d*$/.test(s)) {
      parsed = new Date(s.replace(' ', 'T') + 'Z');
    } else {
      parsed = new Date(s.replace(' ', 'T'));
    }
  } else {
    parsed = new Date(dateStr);
  }
  const seconds = Math.floor((Date.now() - parsed) / 1000);
  if (isNaN(seconds) || seconds < 60) return isFil ? 'ngayon lang' : 'just now';
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return isFil ? `${mins}m nakalipas` : `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return isFil ? `${hours}h nakalipas` : `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return isFil ? `${days}d nakalipas` : `${days}d ago`;
}

const ANALYTICS_NOTIF_TYPES = [
  'heatmap_alert',
  'heatmap_hotspot',
  'trend_alert',
  'trend_spike',
  'prediction_alert',
  'predictive_risk',
  'high_risk_zone',
  'analytics',
];

function isCurrentUserEncoder() {
  try {
    const u = (typeof bcGetCachedUser === 'function' ? bcGetCachedUser() : null) ||
              JSON.parse(localStorage.getItem('currentUser') || sessionStorage.getItem('currentUser') || localStorage.getItem('bc_cached_user') || '{}');
    const roleName = (u?.role?.name || u?.role || '').toLowerCase();
    return roleName.includes('encoder');
  } catch (e) {
    return false;
  }
}

let _notifAlertsInitialized = false;
const _seenNotifAlertIds = new Set();

async function refreshNotifBadge() {
  const badge = document.getElementById('notifBadge');
  try {
    const res = await BCApi.notifUnreadCount();
    const count = res?.count || 0;
    if (badge) badge.classList.toggle('hidden', count === 0);

    // Live alert dispatch for reactive prediction, trend, and heat map alerts
    if (count > 0 && typeof BCApi.notifList === 'function') {
      const recentNotifs = await BCApi.notifList(5);
      if (Array.isArray(recentNotifs)) {
        if (!_notifAlertsInitialized) {
          recentNotifs.forEach(n => _seenNotifAlertIds.add(n.id));
          _notifAlertsInitialized = true;
        } else {
          for (const n of recentNotifs) {
            // Guard: Drop analytics alerts immediately for Data Encoders
            if (isCurrentUserEncoder() && ANALYTICS_NOTIF_TYPES.includes(n.type)) {
              continue;
            }
            if (!_seenNotifAlertIds.has(n.id) && !n.is_read) {
              _seenNotifAlertIds.add(n.id);
              if (ANALYTICS_NOTIF_TYPES.includes(n.type)) {
                if (typeof showToast === 'function') {
                  showToast({
                    message: `${n.title}: ${n.body}`,
                    type: n.severity === 'critical' ? 'error' : 'warning',
                    duration: 6000
                  });
                }
              }
            }
          }
        }
      }
    }
  } catch (e) { /* not fatal — badge just stays as-is */ }
}

// Auto-poll notifications every 30 seconds on active tabs
setInterval(() => {
  if (!document.hidden) refreshNotifBadge();
}, 30000);

function resolveNotifLink(n) {
  let link = n.link || '#';
  if (link !== '#' && (link.includes('highlight=') || link.includes('?id='))) {
    return link;
  }

  // Extract key code (e.g. INC-2026-0064, BLT-2026-0012, STL-2026-0001, etc.) from title/body
  const codeMatch = (n.title + ' ' + (n.body || '')).match(/(INC-\d{4}-\d{2,6}|BLT-\d{4}-\d{2,6}|STL-\d{4}-\d{2,6}|RES-\d{4}-\d{2,6})/i);
  const code = codeMatch ? codeMatch[1] : (n.ref_id || '');

  // Extract Zone if mentioned in title or body (e.g. Zone 1, Zone 2, etc.)
  const zoneMatch = (n.title + ' ' + (n.body || '')).match(/(Zone\s*[1-7])/i);
  const zoneName = zoneMatch ? zoneMatch[1].replace(/Zone\s*/i, 'Zone ') : (n.zone || '');

  const isGeospatial = (
    (n.type && (n.type.includes('heat') || n.type.includes('hotspot') || n.type.includes('spatial') || n.type.includes('geo') || n.type.includes('zone'))) ||
    link.includes('heatmap.html')
  );

  if (isGeospatial) {
    const params = [];
    if (zoneName) params.push(`zone=${encodeURIComponent(zoneName)}`);
    if (code) params.push(`incidentId=${encodeURIComponent(code)}`);
    params.push('highlight=true');
    return `heatmap.html?${params.join('&')}`;
  }

  if (link === '#' || !link) {
    if (n.type === 'prediction_alert' || n.type === 'predictive_risk' || (n.type && (n.type.includes('predict') || n.type.includes('risk')))) link = 'predictions.html';
    else if (n.type === 'trend_alert' || n.type === 'trend_spike' || (n.type && n.type.includes('trend'))) link = 'trends.html';
    else if (n.type === 'heatmap_hotspot' || n.type === 'heatmap_alert' || (n.type && n.type.includes('heatmap'))) link = 'heatmap.html';
    else if (n.ref_table === 'incidents' || (n.type && n.type.includes('incident'))) link = 'incident.html';
    else if (n.ref_table === 'blotter' || (n.type && n.type.includes('blotter'))) link = 'blotter.html';
    else if (n.ref_table === 'settlements' || (n.type && n.type.includes('settlement'))) link = 'settlement.html';
    else link = 'dashboard.html';
  }

  if (code && !link.includes('highlight=')) {
    const sep = link.includes('?') ? '&' : '?';
    link = `${link}${sep}highlight=${encodeURIComponent(code)}`;
  }
  return link;
}

async function handleNotifClick(e, id, targetUrl) {
  e.preventDefault();
  try {
    await BCApi.notifMarkRead(id);
    refreshNotifBadge();
  } catch (err) {}
  if (targetUrl && targetUrl !== '#') {
    window.location.href = targetUrl;
  }
}

async function toggleNotifPanel() {
  const panel = document.getElementById('notifPanel');
  if (!panel) return;
  const opening = panel.classList.contains('hidden');
  panel.classList.toggle('hidden');
  if (!opening) return;

  const isFil = typeof bcGetLanguage === 'function' && (bcGetLanguage().toLowerCase().startsWith('fil') || bcGetLanguage().toLowerCase().startsWith('tag') || bcGetLanguage().toLowerCase() === 'tl');
  const list = document.getElementById('notifList');
  list.innerHTML = `<div class="px-4 py-6 text-center text-forest-400 text-sm">${isFil ? 'Kinakarga ang mga abiso…' : 'Loading notifications…'}</div>`;
  try {
    const rawItems = await BCApi.notifList(25);
    const items = (isCurrentUserEncoder() && Array.isArray(rawItems))
      ? rawItems.filter(n => !ANALYTICS_NOTIF_TYPES.includes(n.type))
      : rawItems;
    if (!items || items.length === 0) {
      list.innerHTML = `<div class="px-4 py-8 text-center text-forest-400 text-sm">${isFil ? 'Wala pang mga abiso.' : 'No notifications yet.'}</div>`;
    } else {
      list.innerHTML = items.map(n => {
        const cfg = NOTIF_TYPE_CONFIG[n.type] || { icon: 'bell', color: '#23703c', badge: 'ALERT', badge_tl: 'ALERTO', bg: '#f0f9f2' };
        const badgeLabel = (isFil && cfg.badge_tl) ? cfg.badge_tl : cfg.badge;
        const destLink = resolveNotifLink(n);
        return `
          <a href="${destLink}" onclick="handleNotifClick(event, ${n.id}, '${destLink}')"
             class="flex gap-3 px-4 py-3.5 border-b border-forest-50 hover:bg-forest-50/80 transition-colors ${n.is_read == 0 ? 'bg-forest-50/40' : ''}">
            <div style="background:${cfg.bg}; color:${cfg.color};" class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm border border-black/5">
              <span data-icon="${cfg.icon}" data-icon-size="16"></span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-0.5">
                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider" style="background:${cfg.bg}; color:${cfg.color};">${badgeLabel}</span>
                <span class="text-[11px] text-forest-400 font-medium">${timeAgo(n.created_at)}</span>
              </div>
              <span class="block text-sm font-semibold text-forest-800 leading-snug">${n.title}</span>
              <span class="block text-xs text-forest-600 mt-1 line-clamp-2 leading-relaxed">${n.body}</span>
            </div>
            ${n.is_read == 0 ? '<span class="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0 mt-2"></span>' : ''}
          </a>`;
      }).join('');
    }
  } catch (e) {
    list.innerHTML = `<div class="px-4 py-6 text-center text-red-500 text-sm">${isFil ? 'Hindi maikarga ang mga abiso.' : 'Could not load notifications.'}</div>`;
  }
  refreshNotifBadge();
}

async function markNotifRead(id) {
  try { await BCApi.notifMarkRead(id); refreshNotifBadge(); } catch (e) {}
}

async function markAllNotifsRead() {
  try {
    await BCApi.notifMarkAllRead();
    const panel = document.getElementById('notifPanel');
    if (panel && !panel.classList.contains('hidden')) {
      panel.classList.add('hidden');
      await toggleNotifPanel();
    }
    refreshNotifBadge();
  } catch (e) {}
}

document.addEventListener('click', (e) => {
  const panel = document.getElementById('notifPanel');
  if (!panel || panel.classList.contains('hidden')) return;
  if (!e.target.closest('#notifPanel') && !e.target.closest('[onclick="toggleNotifPanel()"]')) {
    panel.classList.add('hidden');
  }
});

/**
 * Universal table row deep-link highlighter.
 * Searches for 'docket', 'openCase', 'highlight', or 'id' in URL search params.
 * If found, locates the target record in the dataset, switches pagination to the matching page,
 * smoothly scrolls to the row, triggers the pulsing emerald highlight animation, and cleans up the URL.
 * 
 * @param {Object} opts
 * @param {Array} opts.items - complete dataset or filtered items array
 * @param {Function} [opts.matcher] - (item, query) => boolean
 * @param {number} [opts.pageSize] - rows per page (e.g. 6 or 8)
 * @param {Function} [opts.setPage] - (pageNum) => void
 * @param {Function} [opts.render] - () => void
 * @param {string} [opts.rowSelector] - CSS selector pattern
 */
function bcCheckUrlHighlight({ items, matcher, pageSize, setPage, render, rowSelector } = {}) {
  const urlParams = new URLSearchParams(window.location.search);
  const target = (urlParams.get('docket') || urlParams.get('openCase') || urlParams.get('case') || urlParams.get('highlight') || urlParams.get('id') || urlParams.get('search') || '').trim();
  if (!target || !items || !items.length) return false;

  const targetLower = target.toLowerCase();
  const index = items.findIndex(item => {
    if (matcher) return matcher(item, target);
    return (
      (item.id != null && String(item.id) === target) ||
      (item.reportNo && item.reportNo.toLowerCase() === targetLower) ||
      (item.report_no && item.report_no.toLowerCase() === targetLower) ||
      (item.docketNo && item.docketNo.toLowerCase() === targetLower) ||
      (item.docket_no && item.docket_no.toLowerCase() === targetLower) ||
      (item.caseNo && item.caseNo.toLowerCase() === targetLower) ||
      (item.case_no && item.case_no.toLowerCase() === targetLower) ||
      (item.resNo && item.resNo.toLowerCase() === targetLower) ||
      (item.residentNo && item.residentNo.toLowerCase() === targetLower) ||
      (item.resident_no && item.resident_no.toLowerCase() === targetLower) ||
      (item.username && item.username.toLowerCase() === targetLower)
    );
  });

  if (index === -1) return false;

  if (pageSize && setPage) {
    const pageNum = Math.floor(index / pageSize) + 1;
    setPage(pageNum);
    if (render) render();
  }

  // Allow DOM to settle, then scroll and animate
  setTimeout(() => {
    let row = null;
    if (rowSelector) {
      row = document.querySelector(rowSelector.replace(/%s/g, CSS.escape(target)));
    }
    if (!row) {
      row = document.querySelector(`tr[data-id="${CSS.escape(target)}"], tr[data-key="${CSS.escape(target)}"], tr[data-report-no="${CSS.escape(target)}"], tr[data-docket-no="${CSS.escape(target)}"], tr[data-case-no="${CSS.escape(target)}"]`);
    }
    if (!row) {
      // Fallback: search row text in data-table tbody
      const allRows = document.querySelectorAll('.data-table tbody tr');
      for (const r of allRows) {
        if (r.textContent.toLowerCase().includes(targetLower)) {
          row = r;
          break;
        }
      }
    }

    if (row) {
      row.scrollIntoView({ behavior: 'smooth', block: 'center' });
      row.classList.add('bc-row-highlight');
      setTimeout(() => {
        row.classList.remove('bc-row-highlight');
      }, 3500);

      // Clean up URL query parameters without reloading
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.delete('docket');
      newUrl.searchParams.delete('openCase');
      newUrl.searchParams.delete('case');
      newUrl.searchParams.delete('highlight');
      newUrl.searchParams.delete('id');
      newUrl.searchParams.delete('search');
      window.history.replaceState({}, document.title, newUrl.pathname + (newUrl.searchParams.toString() ? '?' + newUrl.searchParams.toString() : ''));
    }
  }, 120);

  return true;
}

// ── Resident search-picker (replaces the old <select> dropdown) ────
// Shared by Clearance, Certificate of Residency, and Certificate of
// Indigency — a text input that filters as you type and shows name,
// age, address, and household number in each suggestion, instead of
// a plain dropdown of names. Call bcInitResidentPicker() once per page
// after residentOptions has been loaded.
const _bcResidentPickers = {}; // keyed by input id, holds { options, hiddenId, listId, onPick, validate }

// Backward compatibility shim for legacy prefixed IDs if referenced
if (typeof Document !== 'undefined' && Document.prototype.getElementById) {
  const _nativeGetElementById = Document.prototype.getElementById;
  Document.prototype.getElementById = function(id) {
    const el = _nativeGetElementById.call(this, id);
    if (!el && this === document) {
      if (id === 'cl_residentSearch' || id === 'rs_residentSearch' || id === 'if_residentSearch') {
        return _nativeGetElementById.call(this, 'residentSearch');
      }
      if (id === 'cl_residentSuggestions' || id === 'rs_residentSuggestions' || id === 'if_residentSuggestions') {
        return _nativeGetElementById.call(this, 'residentResultsMenu') || _nativeGetElementById.call(this, 'residentDropdownList');
      }
      if (id === 'residentDropdownList') {
        return _nativeGetElementById.call(this, 'residentResultsMenu');
      }
      if (id === 'residentResultsMenu') {
        return _nativeGetElementById.call(this, 'residentDropdownList');
      }
    }
    return el;
  };
}

function renderResidentResults(results) {
  const dropdown = document.getElementById('residentDropdownList');
  if (!dropdown) return;

  if (!results || results.length === 0) {
    dropdown.innerHTML = '<div class="p-3 text-xs text-[#52796f] text-center">No active residents found</div>';
    dropdown.classList.remove('hidden');
    return;
  }

  // Populate items (skipping deceased)
  const activeResults = results.filter(r => {
    const statusValue = String(r.status || r.resident_status || r.census_status || '').toLowerCase().trim();
    const isDeceased = statusValue === 'deceased' || r.is_deceased == 1 || r.is_deceased === true || (typeof window.bcIsResidentDeceased === 'function' && window.bcIsResidentDeceased(r));
    return !isDeceased;
  });

  if (activeResults.length === 0) {
    dropdown.innerHTML = '<div class="p-3 text-xs text-[#52796f] text-center">No active residents found</div>';
    dropdown.classList.remove('hidden');
    return;
  }

  dropdown.innerHTML = activeResults.map(r => `
    <div class="resident-item p-2 hover:bg-[#edf5f0] cursor-pointer text-sm text-[#1e3a2b]" data-id="${r.id}">
      ${r.full_name || (r.last_name + ', ' + r.first_name)}
    </div>
  `).join('');

  dropdown.classList.remove('hidden');

  dropdown.querySelectorAll('.resident-item').forEach(el => {
    el.addEventListener('mousedown', (e) => {
      e.stopPropagation();
      e.preventDefault();
    });
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      const resId = Number(el.dataset.id);
      if (typeof selectResident === 'function') {
        selectResident(resId);
      } else if (typeof bcResidentPickerChoose === 'function') {
        const activeInput = document.getElementById('residentSearch') || document.querySelector('[id$="residentSearch"]');
        const activeId = activeInput ? activeInput.id : 'residentSearch';
        bcResidentPickerChoose(activeId, resId);
      }
    });
  });
}
window.renderResidentResults = renderResidentResults;

function selectResident(residentId) {
  const activeInput = document.getElementById('residentSearch') || document.querySelector('[id$="residentSearch"]');
  const activeId = activeInput ? activeInput.id : 'residentSearch';
  if (typeof bcResidentPickerChoose === 'function') {
    bcResidentPickerChoose(activeId, residentId);
  }
}
window.selectResident = selectResident;

function filterResidents(val) {
  const query = String(val || '').trim().toLowerCase();
  const dropdown = document.getElementById('residentDropdownList');
  if (!dropdown) return;

  if (query.length === 0) {
    dropdown.classList.add('hidden');
    dropdown.innerHTML = '';
    return;
  }

  let options = [];
  const searchInput = document.getElementById('residentSearch') || document.querySelector('[id$="residentSearch"]');
  const activeId = searchInput ? searchInput.id : 'residentSearch';
  const picker = _bcResidentPickers[activeId] || _bcResidentPickers['residentSearch'] || _bcResidentPickers['cl_residentSearch'] || _bcResidentPickers['rs_residentSearch'] || _bcResidentPickers['if_residentSearch'];

  if (picker && Array.isArray(picker.options) && picker.options.length > 0) {
    options = picker.options;
  } else if (typeof residentOptions !== 'undefined' && Array.isArray(residentOptions) && residentOptions.length > 0) {
    options = residentOptions;
  } else if (typeof resResidentOptions !== 'undefined' && Array.isArray(resResidentOptions) && resResidentOptions.length > 0) {
    options = resResidentOptions;
  } else if (typeof indResidentOptions !== 'undefined' && Array.isArray(indResidentOptions) && indResidentOptions.length > 0) {
    options = indResidentOptions;
  }

  const normalized = options.map(r => {
    const lastName = r.lastName || r.last_name || '';
    const firstName = r.firstName || r.first_name || '';
    const middleName = r.middleName || r.middle_name || '';
    const fullName = r.full_name || `${lastName}, ${firstName}${middleName ? ' ' + middleName : ''}`.trim();
    return {
      ...r,
      last_name: lastName,
      first_name: firstName,
      middle_name: middleName,
      lastName,
      firstName,
      middleName,
      full_name: fullName,
    };
  });

  const matches = normalized.filter(r => {
    // Exclude deceased residents
    const statusValue = String(r.status || r.resident_status || r.census_status || '').toLowerCase().trim();
    const isDeceased = statusValue === 'deceased' || r.is_deceased == 1 || r.is_deceased === true || (typeof window.bcIsResidentDeceased === 'function' && window.bcIsResidentDeceased(r));
    if (isDeceased) return false;

    const target = `${r.last_name} ${r.first_name} ${r.middle_name} ${r.full_name}`.toLowerCase();
    return target.includes(query);
  }).slice(0, 20);

  renderResidentResults(matches);
}
window.filterResidents = filterResidents;

function bcInitResidentPicker(inputId, hiddenId, listId, options, onPick, validate) {
  _bcResidentPickers[inputId] = { options, hiddenId, listId, onPick, validate };
  if (inputId === 'residentSearch') {
    _bcResidentPickers['cl_residentSearch'] = _bcResidentPickers[inputId];
    _bcResidentPickers['rs_residentSearch'] = _bcResidentPickers[inputId];
    _bcResidentPickers['if_residentSearch'] = _bcResidentPickers[inputId];
  }

  const input = document.getElementById(inputId);
  if (!input) return;

  const list = document.getElementById(listId);
  if (list) {
    list.classList.add('hidden');
    list.innerHTML = '';
  }

  if (!input.dataset.bcPickerBound) {
    input.dataset.bcPickerBound = '1';

    // Refactored Search Input Listeners:
    // Open ONLY if the user has already entered text
    input.addEventListener('focus', () => {
      if (input.value.trim().length > 0) {
        if (listId === 'residentDropdownList' || inputId === 'residentSearch') {
          filterResidents(input.value.trim());
        } else {
          _bcFilterResidents(inputId);
        }
      }
    });

    input.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      if (val.length > 0) {
        if (listId === 'residentDropdownList' || inputId === 'residentSearch') {
          filterResidents(val);
        } else {
          _bcFilterResidents(inputId);
        }
      } else {
        const curList = document.getElementById(listId) || document.getElementById('residentDropdownList');
        const dropdown = curList;
        if (dropdown) {
          dropdown.classList.add('hidden');
          dropdown.innerHTML = '';
        }
        const parentSec = input.closest('#if_guardianSection, #if_involvedPartiesSection');
        if (parentSec) parentSec.style.removeProperty('z-index');
      }
    });

    input.addEventListener('click', (e) => {
      e.stopPropagation();
      if (input.value.trim().length > 0) {
        if (listId === 'residentDropdownList' || inputId === 'residentSearch') {
          filterResidents(input.value.trim());
        } else {
          _bcFilterResidents(inputId);
        }
      }
    });
  }

  if (list && !list.dataset.bcListBound) {
    list.dataset.bcListBound = '1';
    list.addEventListener('mousedown', (e) => e.stopPropagation());
    list.addEventListener('click', (e) => e.stopPropagation());
  }

  // Requirement 3: searchInput input listener
  const searchInput = document.getElementById('residentSearch');
  if (searchInput && !searchInput.dataset.bcResidentSearchBound) {
    searchInput.dataset.bcResidentSearchBound = '1';
    searchInput.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      if (val.length > 0) {
        filterResidents(val);
      } else {
        const dropdown = document.getElementById('residentDropdownList');
        if (dropdown) dropdown.classList.add('hidden');
      }
    });
  }

  if (!window._bcResidentPickerDocClickBound) {
    window._bcResidentPickerDocClickBound = true;
    document.addEventListener('click', (e) => {
      Object.keys(_bcResidentPickers).forEach(id => {
        const p = _bcResidentPickers[id];
        if (!p) return;
        const curInput = document.getElementById(id);
        const curList = document.getElementById(p.listId);
        if (!curList || curList.classList.contains('hidden')) return;
        if ((!curInput || !curInput.contains(e.target)) && (!curList.contains(e.target))) {
          curList.classList.add('hidden');
          curList.innerHTML = '';
          const parentSec = curInput ? curInput.closest('#if_guardianSection, #if_involvedPartiesSection') : null;
          if (parentSec) parentSec.style.removeProperty('z-index');
        }
      });

      // Also dismiss generic resident search dropdown if present
      const genericInput = document.getElementById('residentSearch');
      const genericDropdown = document.getElementById('residentDropdownList') || document.querySelector('.search-results-dropdown');
      if (genericDropdown && !genericDropdown.classList.contains('hidden')) {
        if ((!genericInput || !genericInput.contains(e.target)) && !genericDropdown.contains(e.target)) {
          genericDropdown.classList.add('hidden');
          genericDropdown.innerHTML = '';
        }
      }
    });
  }
}

function bcResidentPickerSetOptions(inputId, options) {
  if (_bcResidentPickers[inputId]) _bcResidentPickers[inputId].options = options;
  if (inputId === 'residentSearch') {
    if (_bcResidentPickers['cl_residentSearch']) _bcResidentPickers['cl_residentSearch'].options = options;
    if (_bcResidentPickers['rs_residentSearch']) _bcResidentPickers['rs_residentSearch'].options = options;
    if (_bcResidentPickers['if_residentSearch']) _bcResidentPickers['if_residentSearch'].options = options;
  }
}

window.bcIsResidentDeceased = function(r) {
  if (!r) return false;
  const status = String(r.status || '').trim().toUpperCase();
  const vital = String(r.vital_status || r.vitalStatus || '').trim().toUpperCase();
  if (status === 'DECEASED' || status === 'DEAD' || vital === 'DECEASED' || vital === 'DEAD') return true;
  const isDead = r.is_deceased !== undefined ? r.is_deceased : r.isDeceased;
  if (isDead === true || String(isDead).trim().toLowerCase() === 'true' || String(isDead).trim() === '1') return true;
  return false;
};

function _bcFilterResidents(inputId) {
  const picker = _bcResidentPickers[inputId] || _bcResidentPickers['residentSearch'];
  if (!picker) return;
  const input = document.getElementById(inputId) || document.getElementById('residentSearch');
  if (!input) return;
  const list = document.getElementById(picker.listId) || document.getElementById('residentDropdownList');
  if (!list) return;
  const q = input.value.trim().toLowerCase();

  // Guard: NEVER open or populate dropdown on empty query (prevents premature autocomplete expansion on modal open / focus)
  if (q.length === 0) {
    list.classList.add('hidden');
    list.innerHTML = '';
    const parentSec = input.closest('#if_guardianSection, #if_involvedPartiesSection');
    if (parentSec) parentSec.style.removeProperty('z-index');
    return;
  }

  if (list.id === 'residentDropdownList' || inputId === 'residentSearch') {
    filterResidents(q);
    return;
  }

  const isCertPicker = ['residentSearch', 'cl_residentSearch', 'rs_residentSearch', 'if_residentSearch', 'nr_residentSearch'].includes(inputId) ||
                       inputId.startsWith('cl_') || inputId.startsWith('rs_') || inputId.startsWith('ind_') || inputId === 'if_residentSearch' ||
                       window.location.pathname.includes('clearance') || window.location.pathname.includes('residency') || window.location.pathname.includes('indigency');

  let rawOptions = picker.options || [];
  if (isCertPicker) {
    rawOptions = rawOptions.filter(resident => {
      const statusValue = String(resident.status || resident.resident_status || resident.census_status || '').toLowerCase().trim();
      const isDeceased = statusValue === 'deceased' || resident.is_deceased == 1 || resident.is_deceased === true || (typeof window.bcIsResidentDeceased === 'function' && window.bcIsResidentDeceased(resident));
      return !isDeceased;
    });
  }

  const matches = q === ''
    ? rawOptions.slice(0, 20)
    : rawOptions.filter(r => `${r.lastName || r.last_name} ${r.firstName || r.first_name} ${r.middleName || r.middle_name || ''}`.toLowerCase().includes(q)).slice(0, 20);

  if (matches.length === 0) {
    list.innerHTML = `<div class="px-3 py-3 text-sm text-forest-400">${q ? 'No matching residents.' : 'No residents recorded yet.'}</div>`;
  } else {
    const isRespondent = inputId.toLowerCase().includes('respondent');
    const items = matches.map(resident => {
      // Check if resident is deceased
      const statusValue = String(resident.status || resident.resident_status || resident.census_status || '').toLowerCase().trim();
      const isDeceased = statusValue === 'deceased' || resident.is_deceased == 1 || resident.is_deceased === true;

      // Skip deceased residents entirely so they do not render
      if (isDeceased) {
        return; // (or continue; if inside a for-loop)
      }

      const deceasedMsg = isRespondent
        ? 'Deceased residents cannot be recorded as respondents.'
        : 'Deceased residents cannot be filed as complainants/reporters.';
      const deadIneligible = (typeof window.bcIsResidentDeceased === 'function' && window.bcIsResidentDeceased(resident));
      const resLastName = resident.lastName || resident.last_name || '';
      const resFirstName = resident.firstName || resident.first_name || '';
      const resMiddleName = resident.middleName || resident.middle_name || '';
      return `
      <button type="button" class="w-full text-left px-3 py-2 border-b border-forest-50 last:border-0 ${deadIneligible ? 'bg-gray-50/80 cursor-not-allowed opacity-75' : 'hover:bg-forest-50 cursor-pointer'}"
              onmousedown="event.stopPropagation(); event.preventDefault();"
              onclick="${deadIneligible ? `showToast('${deceasedMsg}', 'error');` : `bcResidentPickerChoose('${inputId}', ${resident.id})`}">
        <div class="flex items-center justify-between gap-2">
          <div class="text-sm font-semibold ${deadIneligible ? 'text-gray-500 line-through' : 'text-forest-800'}">
            ${resLastName}, ${resFirstName} ${resMiddleName}
          </div>
          ${deadIneligible ? `<span class="inline-flex items-center px-1.5 py-0.5 text-[10px] font-bold text-rose-700 bg-rose-100 border border-rose-200 rounded">Deceased - Ineligible</span>` : ''}
        </div>
        <div class="text-xs text-forest-500">${resident.age ?? '—'} yrs old &middot; ${resident.address || '—'} &middot; Household ${resident.householdNo || resident.household_no || '—'}</div>
      </button>`;
    }).filter(Boolean);

    if (items.length === 0) {
      list.innerHTML = `<div class="px-3 py-3 text-sm text-forest-400">${q ? 'No matching residents.' : 'No residents recorded yet.'}</div>`;
    } else {
      list.innerHTML = items.join('');
    }
  }
  list.classList.remove('hidden');
  list.style.position = 'absolute';
  list.style.zIndex = '99999';
  const parentSec = input.closest('#if_guardianSection, #if_involvedPartiesSection');
  if (parentSec) {
    parentSec.style.setProperty('z-index', '9999', 'important');
    parentSec.style.setProperty('overflow', 'visible', 'important');
  }
}

function bcResidentPickerChoose(inputId, residentId) {
  let targetId = inputId;
  if (!_bcResidentPickers[targetId]) {
    if (document.getElementById('residentSearch')) targetId = 'residentSearch';
    else if (document.getElementById(inputId)) targetId = inputId;
  }
  const picker = _bcResidentPickers[targetId] || _bcResidentPickers[inputId] || _bcResidentPickers['residentSearch'];
  if (!picker) return;
  const r = (picker.options || []).find(x => x.id === residentId);
  if (!r) return;

  const statusValue = String(r.status || r.resident_status || r.census_status || '').toLowerCase().trim();
  const isDeceased = statusValue === 'deceased' || r.is_deceased == 1 || r.is_deceased === true || (typeof window.bcIsResidentDeceased === 'function' && window.bcIsResidentDeceased(r));
  if (isDeceased) {
    const isRespondent = inputId.toLowerCase().includes('respondent');
    const isCertPicker = ['residentSearch', 'cl_residentSearch', 'rs_residentSearch', 'if_residentSearch', 'nr_residentSearch'].includes(inputId) ||
                         inputId.startsWith('cl_') || inputId.startsWith('rs_') || inputId.startsWith('ind_') || inputId === 'if_residentSearch' ||
                         window.location.pathname.includes('clearance') || window.location.pathname.includes('residency') || window.location.pathname.includes('indigency');
    const msg = isCertPicker
      ? 'A certificate cannot be issued for a deceased resident.'
      : (isRespondent
          ? 'Deceased residents cannot be recorded as respondents.'
          : 'Deceased residents cannot be filed as complainants/reporters.');
    showToast(msg, 'error');
    const list = document.getElementById(picker.listId) || document.getElementById('residentDropdownList');
    if (list) list.classList.add('hidden');
    const curIn = document.getElementById(inputId) || document.getElementById(targetId);
    const parentSec = curIn ? curIn.closest('#if_guardianSection, #if_involvedPartiesSection') : null;
    if (parentSec) parentSec.style.removeProperty('z-index');
    return;
  }

  if (picker.validate) {
    const reason = picker.validate(r);
    if (reason) {
      showToast(reason, 'error');
      const list = document.getElementById(picker.listId) || document.getElementById('residentDropdownList');
      if (list) list.classList.add('hidden');
      const curIn = document.getElementById(inputId) || document.getElementById(targetId);
      const parentSec = curIn ? curIn.closest('#if_guardianSection, #if_involvedPartiesSection') : null;
      if (parentSec) parentSec.style.removeProperty('z-index');
      return;
    }
  }
  const input = document.getElementById(inputId) || document.getElementById(targetId);
  const resLast = r.lastName || r.last_name || '';
  const resFirst = r.firstName || r.first_name || '';
  const resMiddle = r.middleName || r.middle_name || '';
  if (input) input.value = `${resLast}, ${resFirst} ${resMiddle}`.trim();
  const hidden = document.getElementById(picker.hiddenId);
  if (hidden) hidden.value = String(residentId);
  const list = document.getElementById(picker.listId) || document.getElementById('residentDropdownList');
  if (list) {
    list.classList.add('hidden');
    list.innerHTML = '';
  }
  const parentSec = input ? input.closest('#if_guardianSection, #if_involvedPartiesSection') : null;
  if (parentSec) parentSec.style.removeProperty('z-index');
  if (typeof picker.onPick === 'function') picker.onPick(r);
}

function bcResidentPickerClear(inputId) {
  let targetId = inputId;
  if (!_bcResidentPickers[targetId]) {
    if (document.getElementById('residentSearch')) targetId = 'residentSearch';
    else if (document.getElementById(inputId)) targetId = inputId;
  }
  const picker = _bcResidentPickers[targetId] || _bcResidentPickers[inputId] || _bcResidentPickers['residentSearch'];
  const input = document.getElementById(inputId) || document.getElementById(targetId) || document.getElementById('residentSearch');
  if (input) input.value = '';
  if (picker) {
    const hidden = document.getElementById(picker.hiddenId);
    if (hidden) hidden.value = '';
    const list = document.getElementById(picker.listId);
    if (list) {
      list.classList.add('hidden');
      list.innerHTML = '';
    }
    if (typeof picker.onPick === 'function') picker.onPick(null);
  }
  const dropdown = document.getElementById('residentDropdownList');
  if (dropdown) {
    dropdown.classList.add('hidden');
    dropdown.innerHTML = '';
  }
  const parentSec = input ? input.closest('#if_guardianSection, #if_involvedPartiesSection') : null;
  if (parentSec) parentSec.style.removeProperty('z-index');
}

// ============================================================
// SKELETON LOADING & STATE MANAGEMENT SUITE (Zero-CLS)
// ============================================================

/**
 * Generates an accessible, zero-CLS table skeleton matching active table columns.
 * @param {Object} options Configuration options
 * @param {number} options.rows Number of skeleton rows to render (default 5)
 * @param {string|number|Array} options.template 'incident', 'blotter', 'settlement', 'dashboard', or column count
 */
function bcGetTableSkeletonHtml(options = {}) {
  const rows = options.rows || 5;
  const tpl = options.template || 'incident';

  let colDefs = [];
  if (Array.isArray(options.cols)) {
    colDefs = options.cols;
  } else if (tpl === 'incident') {
    colDefs = [
      { type: 'checkbox', width: '40px' },
      { type: 'pill', width: 'w-24' },   // Report No
      { type: 'pill', width: 'w-20' },   // Date
      { type: 'pill', width: 'w-16' },   // Time
      { type: 'pill', width: 'w-36' },   // Zone & Location
      { type: 'pill', width: 'w-28' },   // Category
      { type: 'pill', width: 'w-44' },   // Description
      { type: 'pill', width: 'w-28' },   // Reporter
      { type: 'pill', width: 'w-24' },   // Officer
      { type: 'badge', width: 'w-16' },  // Priority
      { type: 'badge', width: 'w-24' },  // Status
      { type: 'actions', count: 3 }      // Actions
    ];
  } else if (tpl === 'blotter') {
    colDefs = [
      { type: 'checkbox', width: '40px' },
      { type: 'pill', width: 'w-28' },   // Docket No
      { type: 'pill', width: 'w-24' },   // Date Filed
      { type: 'pill', width: 'w-32' },   // Complainant
      { type: 'pill', width: 'w-32' },   // Respondent
      { type: 'pill', width: 'w-28' },   // Nature / Type
      { type: 'badge', width: 'w-24' },  // Status
      { type: 'actions', count: 3 }      // Actions
    ];
  } else if (tpl === 'settlement') {
    colDefs = [
      { type: 'checkbox', width: '40px' },
      { type: 'pill', width: 'w-24' },   // Case No
      { type: 'pill', width: 'w-36' },   // Title / Parties
      { type: 'pill', width: 'w-28' },   // Nature
      { type: 'pill', width: 'w-20' },   // Confrontation Date
      { type: 'pill', width: 'w-20' },   // Settlement Date
      { type: 'badge', width: 'w-24' },  // Status
      { type: 'actions', count: 2 }      // Actions
    ];
  } else if (tpl === 'dashboard') {
    colDefs = [
      { type: 'pill', width: 'w-28' },   // Docket No
      { type: 'pill', width: 'w-36' },   // Complainant
      { type: 'pill', width: 'w-28' },   // Nature
      { type: 'badge', width: 'w-20' },  // Status
    ];
  } else if (tpl === 'census') {
    colDefs = [
      { type: 'checkbox', width: '44px' },
      { type: 'pill', width: 'w-24' },   // Resident No
      { type: 'pill', width: 'w-36' },   // Full Name
      { type: 'pill', width: 'w-20' },   // DOB
      { type: 'pill', width: 'w-16' },   // Age
      { type: 'badge', width: 'w-16' },  // Sex
      { type: 'pill', width: 'w-20' },   // Civil Status
      { type: 'pill', width: 'w-20' },   // Zone / Purok
      { type: 'pill', width: 'w-44' },   // Address
      { type: 'pill', width: 'w-20' },   // Household No
      { type: 'badge', width: 'w-16' },  // Status
      { type: 'actions', count: 2 }      // Actions
    ];
  } else if (tpl === 'clearance' || tpl === 'residency' || tpl === 'non_residency' || tpl === 'indigency') {
    colDefs = [
      { type: 'pill', width: 'w-28' },   // Control/Cert No
      { type: 'pill', width: 'w-36' },   // Resident Name
      { type: 'pill', width: 'w-28' },   // Purpose
      { type: 'pill', width: 'w-24' },   // Date Issued
      { type: 'pill', width: 'w-28' },   // Issued By
      { type: 'badge', width: 'w-20' },  // Status
      { type: 'actions', count: 2 }      // Actions
    ];
  } else if (tpl === 'users') {
    colDefs = [
      { type: 'pill', width: 'w-36' },   // User / Name
      { type: 'pill', width: 'w-40' },   // Email
      { type: 'badge', width: 'w-24' },  // Role
      { type: 'badge', width: 'w-16' },  // Status
      { type: 'pill', width: 'w-28' },   // Last Active
      { type: 'actions', count: 2 }      // Actions
    ];
  } else {
    const colCount = typeof options.cols === 'number' ? options.cols : 6;
    colDefs = Array.from({ length: colCount }, (_, i) => ({
      type: i === 0 ? 'pill' : (i === colCount - 1 ? 'actions' : 'pill'),
      width: 'w-28'
    }));
  }

  let html = '';
  for (let r = 0; r < rows; r++) {
    // Stagger widths slightly for organic look
    const stagger = (r % 3 === 0) ? 'max-w-[85%]' : (r % 3 === 1 ? 'max-w-[70%]' : 'max-w-[95%]');
    html += '<tr class="bc-skeleton-row animate-pulse">';
    colDefs.forEach((col, idx) => {
      if (col.type === 'checkbox') {
        html += `<td style="width: 40px; text-align: center;"><div class="w-4 h-4 rounded bg-slate-200 mx-auto"></div></td>`;
      } else if (col.type === 'badge') {
        html += `<td><div class="h-6 ${col.width || 'w-20'} rounded-full bg-slate-200"></div></td>`;
      } else if (col.type === 'actions') {
        const count = col.count || 2;
        html += `<td><div class="flex items-center gap-1.5 justify-end">`;
        for (let a = 0; a < count; a++) {
          html += `<div class="w-7 h-7 rounded-lg bg-slate-200"></div>`;
        }
        html += `</div></td>`;
      } else {
        html += `<td><div class="h-3.5 ${col.width || 'w-28'} ${stagger} rounded bg-slate-200"></div></td>`;
      }
    });
    html += '</tr>';
  }
  return html;
}

/**
 * Renders table skeleton directly into a tbody element.
 */
function bcRenderTableSkeleton(tbodyId, options = {}) {
  const el = typeof tbodyId === 'string' ? document.getElementById(tbodyId) : tbodyId;
  if (!el) return;
  el.innerHTML = bcGetTableSkeletonHtml(options);
}

/**
 * Manages loading pulse indicators on KPI metric stat cards.
 * @param {Array<string>|string} targetIds Element IDs of stat number displays
 * @param {boolean} isLoading True to show skeleton pulse, false to restore
 * @param {string} placeholder Optional placeholder value if restoring without data
 */
function bcSetStatsLoading(targetIds, isLoading = true, placeholder = '—') {
  const ids = Array.isArray(targetIds) ? targetIds : [targetIds];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (isLoading) {
      el.innerHTML = '<span class="inline-block h-8 w-20 bg-white/25 rounded-md animate-pulse align-middle"></span>';
    } else if (el.innerHTML.includes('animate-pulse')) {
      el.textContent = placeholder;
    }
  });
}

/**
 * Generates an accessible 4-card metric skeleton grid.
 */
function bcGetMetricsSkeletonHtml(count = 4) {
  let html = `<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-${count} gap-4 mb-6">`;
  for (let i = 0; i < count; i++) {
    html += `
      <div class="bc-skeleton-card">
        <div class="flex items-center justify-between mb-3">
          <div class="h-4 w-28 bg-slate-200 rounded"></div>
          <div class="w-9 h-9 rounded-xl bg-slate-200"></div>
        </div>
        <div class="h-8 w-20 bg-slate-200 rounded mb-2"></div>
        <div class="h-3 w-32 bg-slate-100 rounded"></div>
      </div>`;
  }
  html += `</div>`;
  return html;
}

/**
 * Renders chart & analytics bounding box skeleton.
 */
function bcGetChartSkeletonHtml(type = 'donut') {
  if (type === 'donut') {
    return `
      <div class="flex flex-col items-center justify-center p-6 space-y-4 animate-pulse">
        <div class="w-32 h-32 rounded-full border-8 border-slate-200 bg-slate-50 flex items-center justify-center">
          <div class="h-6 w-12 bg-slate-200 rounded"></div>
        </div>
        <div class="w-full space-y-2 pt-2">
          <div class="h-4 bg-slate-200 rounded w-3/4 mx-auto"></div>
          <div class="h-3 bg-slate-100 rounded w-1/2 mx-auto"></div>
        </div>
      </div>`;
  }
  return `
    <div class="h-64 rounded-2xl bg-slate-100 border border-slate-200 p-6 flex flex-col justify-between animate-pulse">
      <div class="flex items-center justify-between">
        <div class="h-5 w-40 bg-slate-200 rounded"></div>
        <div class="h-4 w-24 bg-slate-200 rounded"></div>
      </div>
      <div class="h-36 bg-slate-200/60 rounded-xl flex items-center justify-center">
        <span class="text-xs text-slate-400 font-medium">Loading visualization…</span>
      </div>
    </div>`;
}

/**
 * Renders an empty state placeholder row in a table with contextual title, subtitle, and optional action.
 */
function bcSetTableEmpty(tbodyId, message = "There's no records found.", icon = 'inbox', colSpan = 12, subtitle = '', actionBtnHtml = '') {
  const el = typeof tbodyId === 'string' ? document.getElementById(tbodyId) : tbodyId;
  if (!el) return;
  el.innerHTML = `
    <tr class="empty-state-row row-no-hover">
      <td colspan="${colSpan}" class="py-12 text-center text-forest-500 border-none bg-transparent">
        <div class="bc-empty-state max-w-lg mx-auto flex flex-col items-center justify-center">
          <div class="bc-empty-state-icon mb-3 w-12 h-12 rounded-full bg-forest-50 border border-forest-100 flex items-center justify-center text-forest-600 shadow-sm">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
            </svg>
          </div>
          <strong class="font-semibold text-forest-800 text-sm block leading-relaxed">${message}</strong>
          ${subtitle ? `<span class="text-xs text-forest-400 mt-1 block">${subtitle}</span>` : ''}
          ${actionBtnHtml ? `<div class="mt-3.5 flex items-center justify-center gap-2">${actionBtnHtml}</div>` : ''}
        </div>
      </td>
    </tr>`;
  if (typeof renderIcons === 'function') {
    try { renderIcons(el); } catch (_) {}
  }
}

/**
 * Renders an error state placeholder row with a retry button in a table.
 */
function bcSetTableError(tbodyId, errorMessage = 'Failed to load records from server.', retryFnStr = '', colSpan = 12) {
  const el = typeof tbodyId === 'string' ? document.getElementById(tbodyId) : tbodyId;
  if (!el) return;
  el.innerHTML = `
    <tr class="error-state-row row-no-hover">
      <td colspan="${colSpan}" class="py-12 text-center text-rose-600 border-none bg-transparent">
        <div class="bc-error-state">
          <div class="bc-error-state-icon">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <strong class="font-semibold text-rose-900 text-sm block">${errorMessage}</strong>
          ${retryFnStr ? `<button type="button" onclick="${retryFnStr}" class="mt-3 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shadow-sm transition pointer-events-auto">Retry Loading</button>` : ''}
        </div>
      </td>
    </tr>`;
}


