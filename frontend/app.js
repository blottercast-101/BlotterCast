// app.js — shared application logic

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

async function requireAuth() {
  if (_bcAuthGuardRunning) return null;
  _bcAuthGuardRunning = true;
  try {
    const status = await BCApi.me();
    if (!status || !status.authenticated) {
      _handleUnauthenticatedRedirect();
      return null;
    }

    const role = status.user.role;
    if (typeof enforcePageAccess === 'function' && !enforcePageAccess(role)) {
      return null; // enforcePageAccess already redirected away
    }
    if (typeof applyNavPermissions === 'function') applyNavPermissions(role);
    bcPrewarmMLService();
    if (typeof applyElementPermissionsLive === 'function') applyElementPermissionsLive(role);

    const nameEl = document.querySelector('[data-user-name]');
    const roleEl = document.querySelector('[data-user-role]');
    const avatarEl = document.querySelector('[data-user-avatar]');
    const greetingEl = document.querySelector('[data-user-greeting]') || document.getElementById('dashboardGreeting');
    if (nameEl) nameEl.textContent = status.user.full_name;
    if (roleEl) roleEl.textContent = status.user.role;
    if (avatarEl) avatarEl.textContent = bcInitials(status.user.full_name);
    if (greetingEl) {
      const firstName = bcFirstName(status.user.full_name || status.user.firstName || status.user.first_name);
      greetingEl.textContent = `Welcome back, ${firstName}. Here's today's overview.`;
    }
    if (status.user.mustChangePassword) bcShowForcedPasswordChange();
    bcSyncTimeFormatFromServer().catch(() => {});
    _bcStartIdleTracker();
    return status.user;
  } catch (e) {
    _handleUnauthenticatedRedirect();
    return null;
  } finally {
    _bcAuthGuardRunning = false;
  }
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

// Initials shown in the sidebar avatar circle, e.g. "Juan Dela Cruz" -> "JD"
// (first letter of the first two words). Falls back to a single letter for
// one-word names, and "?" if the name is somehow empty.
function bcInitials(fullName) {
  const words = (fullName || '').trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return '?';
  if (words.length === 1) return words[0][0].toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

async function doLogout() {
  if (!(await bcConfirm('Are you sure you want to log out?', { title: 'Log Out', okLabel: 'Log Out' }))) return;
  _bcStopIdleTracker();
  try { localStorage.removeItem('bc_last_active_timestamp'); } catch (e) {}
  try { await BCApi.logout(); } catch (e) {}
  window.location.replace('login.html');
}

// ── Real-Time Presence Heartbeat ────────────────────────────
// Keeps active user presence marked "ACTIVE (Online)" in real-time.
setInterval(() => {
  if (!document.hidden && !window.location.pathname.endsWith('login.html')) {
    BCApi.heartbeat().catch(() => {});
  }
}, 15000);


// ── Field validation helpers ────────────────────────────────
// Small, dependency-free predicates used right before any create/update
// API call, so obviously-invalid input (digits in a name, a malformed
// contact number, a birth date in the future, etc.) never reaches the
// server. Deliberately kept as plain functions rather than a form
// framework — every page already collects its values into a `vals`
// object and checks required fields with a simple `if(...) { await bcAlert(...);
// return; }`, so each validator just slots into that same pattern.

// Letters (including accented ones like Ñ/ñ), spaces, and the
// punctuation that legitimately appears in Filipino names — hyphens
// (Dela Cruz-Santos), apostrophes (O'Brien, D'Souza), and periods
// (Jr., Ma.). No digits or other symbols.
const BC_NAME_RE = /^[A-Za-zÀ-ÖØ-öø-ÿ.'\- ]+$/;
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
 * Universal Date+Time Formatter.
 * Formats timestamps into:
 *   - 12-Hour: "Aug 23, 2026, 01:36 AM" / "Aug 23, 2026, 01:36 PM"
 *   - 24-Hour: "Aug 23, 2026, 01:36" / "Aug 23, 2026, 13:36"
 */
function bcFormatTimestamp(iso, emptyLabel = 'Never', formatPref) {
  if (!iso) return emptyLabel;
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return emptyLabel;
    const use24 = (formatPref || bcGetTimeFormat()) === '24';
    const datePart = d.toLocaleDateString('en-PH', {
      month: 'short', day: 'numeric', year: 'numeric', timeZone: BC_SYSTEM_TIMEZONE
    });
    const timePart = d.toLocaleTimeString('en-PH', {
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
    const d = new Date(iso);
    if (isNaN(d.getTime())) return emptyLabel;
    return d.toLocaleDateString('en-PH', {
      month: 'short', day: 'numeric', year: 'numeric', timeZone: BC_SYSTEM_TIMEZONE,
    });
  } catch (e) {
    return emptyLabel;
  }
}

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

// Every password field in the app gets a Show/Hide eye icon — call this
// once per field, right after the input exists in the DOM. The toggle
// only flips the input's type; it never touches or clears the value, and
// stays put no matter what else on the page the user clicks.
function bcAddPasswordToggle(inputId) {
  const input = document.getElementById(inputId);
  if (!input || input.dataset.pwToggleAdded) return;
  input.dataset.pwToggleAdded = '1';
  input.classList.add('pw-input');

  let wrap = input.parentElement;
  if (!wrap.classList.contains('relative')) {
    wrap = document.createElement('div');
    wrap.className = 'relative';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
  }

  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'pw-toggle';
  btn.setAttribute('aria-label', 'Show password');
  btn.tabIndex = -1;
  btn.innerHTML = '<span data-icon="view" data-icon-size="16"></span>';
  btn.onclick = () => {
    const showing = input.type === 'text';
    input.type = showing ? 'password' : 'text';
    btn.innerHTML = `<span data-icon="${showing ? 'view' : 'viewOff'}" data-icon-size="16"></span>`;
    btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
  };
  wrap.appendChild(btn);
}

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
        <div><label class="form-label">New Password</label><input type="password" id="bcPw_new" class="form-input" autocomplete="new-password"/></div>
        <div><label class="form-label">Confirm New Password</label><input type="password" id="bcPw_confirm" class="form-input" autocomplete="new-password"/></div>
        <div id="bcPw_error" class="text-red-600 text-xs hidden"></div>
        <div class="flex justify-end pt-2">
          <button id="bcPw_submit" class="btn-primary">Update Password</button>
        </div>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

  document.getElementById('bcPw_submit').onclick = async () => {
    const errEl = document.getElementById('bcPw_error');
    errEl.classList.add('hidden');
    const current = document.getElementById('bcPw_current').value;
    const next = document.getElementById('bcPw_new').value;
    const confirm = document.getElementById('bcPw_confirm').value;
    if (!current || !next || !confirm) {
      errEl.textContent = 'Please fill in all three fields.'; errEl.classList.remove('hidden'); return;
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
      document.getElementById('bcPw_new').focus();
    }
  };
}

// ── Smart pagination ────────────────────────────────────────
// Renders Prev / page numbers / Next into `container`. With only a
// handful of pages every number shows; once there are more, it
// collapses everything except the first page, last page, and a small
// window around the current page into "…" — so a table with 28+ pages
// doesn't force the pagination bar to stretch across (or wrap under)
// the whole table. First/last/current-neighbors are always one click
// away either way.
// onPageChange(page) is called with the 1-based page number clicked.
function bcRenderPagination(container, currentPage, totalPages, onPageChange) {
  if (!container) return;
  container.innerHTML = '';
  totalPages = Math.max(1, totalPages);
  currentPage = Math.min(Math.max(1, currentPage), totalPages);

  const addBtn = (label, opts = {}) => {
    const b = document.createElement('button');
    b.textContent = label;
    b.type = 'button';
    b.className = 'pagination-btn' + (opts.active ? ' active' : '') + (opts.ellipsis ? ' pagination-ellipsis' : '');
    b.disabled = !!opts.disabled || !!opts.ellipsis;
    if (!b.disabled && opts.onClick) b.onclick = opts.onClick;
    container.appendChild(b);
  };

  addBtn('‹ Prev', { disabled: currentPage === 1, onClick: () => onPageChange(currentPage - 1) });

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

  addBtn('Next ›', { disabled: currentPage === totalPages, onClick: () => onPageChange(currentPage + 1) });
}

// ── Modal helpers ──────────────────────────────────────────
function openModal(id) {
  const el = document.getElementById(id);
  if (el) { el.classList.add('open'); document.body.style.overflow = 'hidden'; }
}
function closeModal(id) {
  const el = document.getElementById(id);
  if (el) { el.classList.remove('open'); document.body.style.overflow = ''; }
}

/**
 * Standardize dropdown reset across all forms and modals.
 * Resets all <select> elements in a given form or container to their default placeholder (<option value="">-Select-</option>).
 * @param {string|HTMLElement} target - form or modal element or its id
 */
function resetFormDropdowns(target) {
  const container = typeof target === 'string' ? document.getElementById(target) : target;
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
}
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay') && !e.target.hasAttribute('data-no-dismiss')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// ── Toast ──────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  let t = document.getElementById('globalToast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'globalToast';
    t.className = 'toast';
    document.body.appendChild(t);
  }
  // Icon per type: success → check, warning → alert-triangle, error → x
  const iconName = type === 'error' ? 'x' : type === 'warning' ? 'alert-triangle' : 'check';
  // Apply the matching CSS modifier class
  t.className = 'toast' + (type === 'error' ? ' error' : type === 'warning' ? ' warning' : '');
  t.innerHTML = `<span data-icon="${iconName}" data-icon-size="16"></span><span>${msg}</span>`;
  if (window.lucide) lucide.createIcons({ nodes: [t] });
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2800);
}

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
  if (_bcDialogEl) return _bcDialogEl;
  const el = document.createElement('div');
  el.id = 'bcDialogOverlay';
  el.className = 'modal-overlay';
  el.setAttribute('data-no-dismiss', ''); // clicking the backdrop shouldn't silently dismiss it
  el.innerHTML = `
    <div class="bc-dialog-box">
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
    // Enter is intentionally NOT force-bound to "confirm" here — the
    // focused button (see _bcOpenDialog, which focuses Cancel by default
    // for danger actions) already handles Enter/Space natively, so a
    // destructive dialog can't be confirmed by an accidental Enter press.
  });
  return el;
}

function _bcDialogFinish(result) {
  if (!_bcDialogEl || !_bcDialogEl.classList.contains('open')) return;
  _bcDialogEl.classList.remove('open');
  document.body.style.overflow = '';
  const resolve = _bcDialogResolve;
  _bcDialogResolve = null;
  if (resolve) resolve(result);
}

function _bcOpenDialog({ title, message, isConfirm, okLabel, cancelLabel, danger }) {
  const el = _bcEnsureDialog();
  document.getElementById('bcDialogTitle').textContent = title;
  document.getElementById('bcDialogMessage').textContent = message;
  const cancelBtn = document.getElementById('bcDialogCancelBtn');
  const okBtn = document.getElementById('bcDialogOkBtn');
  cancelBtn.style.display = isConfirm ? '' : 'none';
  cancelBtn.textContent = cancelLabel || 'Cancel';
  okBtn.textContent = okLabel || (isConfirm ? 'Confirm' : 'OK');
  okBtn.className = danger ? 'btn-danger' : 'btn-primary';

  // Swap the icon (info for plain alerts, warning for danger confirms) —
  // reset the icon-library's "already rendered" flag first so it actually
  // redraws instead of keeping whatever icon was shown last time.
  const icon = document.getElementById('bcDialogIcon');
  icon.dataset.icon = danger ? 'warning' : 'info';
  icon.innerHTML = '';
  delete icon.dataset.iconRendered;
  icon.className = 'bc-dialog-icon' + (danger ? ' danger' : '');
  if (typeof renderIcons === 'function') renderIcons(el);

  el.classList.add('open');
  document.body.style.overflow = 'hidden';
  // Default focus sits on whichever button is the "safe" choice: Cancel
  // for destructive (danger) confirms, OK otherwise — so a stray Enter
  // press never accidentally triggers a delete.
  setTimeout(() => (danger && isConfirm ? cancelBtn : okBtn).focus(), 50);
  return new Promise(resolve => { _bcDialogResolve = resolve; });
}

/** Drop-in async replacement for window.alert(). Always resolves (no return value needed). */
function bcAlert(message, opts = {}) {
  return _bcOpenDialog({ title: opts.title || 'Notice', message, isConfirm: false, okLabel: opts.okLabel });
}

/** Drop-in async replacement for window.confirm() — resolves to true (OK/Confirm) or false (Cancel/Esc). */
function bcConfirm(message, opts = {}) {
  return _bcOpenDialog({
    title: opts.title || 'Please Confirm', message, isConfirm: true,
    okLabel: opts.okLabel, cancelLabel: opts.cancelLabel, danger: opts.danger,
  });
}

// ── Sidebar shared HTML builder (call once per page) ───────
function buildSidebar(activePage) {
  const pages = [
    { href:'dashboard.html',  icon:'📊', label:'Dashboard',          group:'main' },
    { href:'blotter.html',    icon:'📋', label:'Blotter Records',     group:'main' },
    { href:'incident.html',   icon:'🚨', label:'Incident Reports',    group:'main' },
    { href:'settlement.html', icon:'🤝', label:'Settlement Monitor',  group:'main' },
    { href:'heatmap.html',    icon:'🗺', label:'Heat Map',            group:'analytics' },
    { href:'trends.html',     icon:'📈', label:'Trends',              group:'analytics' },
    { href:'predictions.html',icon:'🤖', label:'Predictions',         group:'analytics' },
    { href:'users.html',      icon:'👥', label:'Users & Roles',       group:'system' },
    { href:'reports.html',    icon:'📄', label:'Reports',             group:'system' },
    { href:'settings.html',   icon:'⚙', label:'Settings',            group:'system' },
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
               <span class="nav-icon">${p.icon}</span> ${p.label}</a>`;
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
          <h2 class="font-display text-lg text-forest-800" id="bcExportFilterTitle">Export to Excel</h2>
          <button onclick="closeModal('bcExportFilterModal')" class="modal-close-btn"><span data-icon="x" data-icon-size="18"></span></button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="form-label">Period</label>
            <select id="bcExportPeriod" class="form-input" onchange="_updateExportFilterFields()">
              <option value="all">All Records</option>
              <option value="year">Specific Year</option>
              <option value="month">Specific Month</option>
            </select>
          </div>
          <div id="bcExportYearWrap" class="hidden">
            <label class="form-label">Year</label>
            <select id="bcExportYear" class="form-input"></select>
          </div>
          <div id="bcExportMonthWrap" class="hidden">
            <label class="form-label">Month</label>
            <select id="bcExportMonth" class="form-input">
              <option value="1">January</option><option value="2">February</option><option value="3">March</option>
              <option value="4">April</option><option value="5">May</option><option value="6">June</option>
              <option value="7">July</option><option value="8">August</option><option value="9">September</option>
              <option value="10">October</option><option value="11">November</option><option value="12">December</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-5">
          <button type="button" onclick="closeModal('bcExportFilterModal')" class="btn-secondary">Cancel</button>
          <button type="button" onclick="_confirmExportFilter()" class="btn-primary flex items-center gap-2">
            <span data-icon="download" data-icon-size="16"></span> Download
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
  document.getElementById('bcExportFilterTitle').textContent = title || 'Export to Excel';
  document.getElementById('bcExportPeriod').value = 'all';
  _updateExportFilterFields();
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

// ── Notification bell (real, system-generated alerts) ──────
// Only does anything on pages that actually have #notifPanel in the DOM
// (currently the Dashboard); harmless no-op calls elsewhere.
const NOTIF_TYPE_CONFIG = {
  incident_crud: { icon: 'incident', color: '#16a34a', badge: 'INCIDENT', bg: '#f0fdf4' },
  new_incident: { icon: 'warning', color: '#dc2626', badge: 'HIGH PRIORITY', bg: '#fef2f2' },
  heatmap_hotspot: { icon: 'heatmap', color: '#d97706', badge: 'GEOSPATIAL', bg: '#fffbeb' },
  predictive_risk: { icon: 'predictions', color: '#7c3aed', badge: 'PREDICTIVE ML', bg: '#f5f3ff' },
  high_risk_zone: { icon: 'predictions', color: '#7c3aed', badge: 'PREDICTIVE ML', bg: '#f5f3ff' },
  trend_spike: { icon: 'trends', color: '#2563eb', badge: 'TREND SURGE', bg: '#eff6ff' },
  settlement_overdue: { icon: 'clock', color: '#d97706', badge: 'SETTLEMENT', bg: '#fffbeb' },
};

function timeAgo(dateStr) {
  if (!dateStr) return 'just now';
  const seconds = Math.floor((Date.now() - new Date(dateStr.replace(' ', 'T'))) / 1000);
  if (isNaN(seconds) || seconds < 60) return 'just now';
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

async function refreshNotifBadge() {
  const badge = document.getElementById('notifBadge');
  if (!badge) return;
  try {
    const res = await BCApi.notifUnreadCount();
    const count = res?.count || 0;
    badge.classList.toggle('hidden', count === 0);
  } catch (e) { /* not fatal — badge just stays as-is */ }
}

// Auto-poll notifications every 30 seconds on active tabs
setInterval(() => {
  if (!document.hidden) refreshNotifBadge();
}, 30000);

function resolveNotifLink(n) {
  let link = n.link || '#';
  if (link !== '#') {
    if (link.includes('highlight=') || link.includes('?id=')) return link;
  }
  
  // Extract key code (e.g. INC-2026-0064, BLT-2026-0012, STL-2026-0001, etc.) from title/body
  const codeMatch = (n.title + ' ' + (n.body || '')).match(/(INC-\d{4}-\d{2,6}|BLT-\d{4}-\d{2,6}|STL-\d{4}-\d{2,6}|RES-\d{4}-\d{2,6})/i);
  const code = codeMatch ? codeMatch[1] : (n.ref_id || '');

  if (link === '#' || !link) {
    if (n.ref_table === 'incidents' || (n.type && n.type.includes('incident'))) link = 'incident.html';
    else if (n.ref_table === 'blotter' || (n.type && n.type.includes('blotter'))) link = 'blotter.html';
    else if (n.ref_table === 'settlements' || (n.type && n.type.includes('settlement'))) link = 'settlement.html';
    else if (n.type && n.type.includes('heatmap')) link = 'heatmap.html';
    else if (n.type && (n.type.includes('predict') || n.type.includes('risk'))) link = 'predictions.html';
    else if (n.type && n.type.includes('trend')) link = 'trends.html';
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

  const list = document.getElementById('notifList');
  list.innerHTML = '<div class="px-4 py-6 text-center text-forest-400 text-sm">Loading notifications…</div>';
  try {
    const items = await BCApi.notifList(25);
    if (!items || items.length === 0) {
      list.innerHTML = '<div class="px-4 py-8 text-center text-forest-400 text-sm">No notifications yet.</div>';
    } else {
      list.innerHTML = items.map(n => {
        const cfg = NOTIF_TYPE_CONFIG[n.type] || { icon: 'bell', color: '#23703c', badge: 'ALERT', bg: '#f0f9f2' };
        const destLink = resolveNotifLink(n);
        return `
          <a href="${destLink}" onclick="handleNotifClick(event, ${n.id}, '${destLink}')"
             class="flex gap-3 px-4 py-3.5 border-b border-forest-50 hover:bg-forest-50/80 transition-colors ${n.is_read == 0 ? 'bg-forest-50/40' : ''}">
            <div style="background:${cfg.bg}; color:${cfg.color};" class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm border border-black/5">
              <span data-icon="${cfg.icon}" data-icon-size="16"></span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-0.5">
                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider" style="background:${cfg.bg}; color:${cfg.color};">${cfg.badge}</span>
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
    list.innerHTML = '<div class="px-4 py-6 text-center text-red-500 text-sm">Could not load notifications.</div>';
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
 * Searches for 'highlight' or 'id' in URL search params.
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
  const target = (urlParams.get('highlight') || urlParams.get('id') || urlParams.get('search') || '').trim();
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
const _bcResidentPickers = {}; // keyed by input id, holds { options, hiddenId, onPick }

function bcInitResidentPicker(inputId, hiddenId, listId, options, onPick, validate) {
  _bcResidentPickers[inputId] = { options, hiddenId, listId, onPick, validate };
  const input = document.getElementById(inputId);
  if (!input || input.dataset.bcPickerBound) return;
  input.dataset.bcPickerBound = '1';
  input.addEventListener('input', () => _bcFilterResidents(inputId));
  input.addEventListener('focus', () => _bcFilterResidents(inputId));
  document.addEventListener('click', (e) => {
    if (!e.target.closest('#' + listId) && e.target !== input) {
      const list = document.getElementById(listId);
      if (list) list.classList.add('hidden');
    }
  });
}

function bcResidentPickerSetOptions(inputId, options) {
  if (_bcResidentPickers[inputId]) _bcResidentPickers[inputId].options = options;
}

function _bcFilterResidents(inputId) {
  const picker = _bcResidentPickers[inputId];
  if (!picker) return;
  const input = document.getElementById(inputId);
  const list = document.getElementById(picker.listId);
  const q = input.value.trim().toLowerCase();

  const matches = q === ''
    ? picker.options.slice(0, 20)
    : picker.options.filter(r => `${r.lastName} ${r.firstName} ${r.middleName}`.toLowerCase().includes(q)).slice(0, 20);

  if (matches.length === 0) {
    list.innerHTML = `<div class="px-3 py-3 text-sm text-forest-400">${q ? 'No matching residents.' : 'No residents recorded yet.'}</div>`;
  } else {
    list.innerHTML = matches.map(r => `
      <button type="button" class="w-full text-left px-3 py-2 hover:bg-forest-50 border-b border-forest-50 last:border-0"
              onclick="bcResidentPickerChoose('${inputId}', ${r.id})">
        <div class="text-sm font-semibold text-forest-800">${r.lastName}, ${r.firstName} ${r.middleName || ''}</div>
        <div class="text-xs text-forest-500">${r.age ?? '—'} yrs old &middot; ${r.address || '—'} &middot; Household ${r.householdNo || '—'}</div>
      </button>`).join('');
  }
  list.classList.remove('hidden');
}

function bcResidentPickerChoose(inputId, residentId) {
  const picker = _bcResidentPickers[inputId];
  if (!picker) return;
  const r = picker.options.find(x => x.id === residentId);
  if (!r) return;
  if (picker.validate) {
    const reason = picker.validate(r);
    if (reason) {
      showToast(reason, 'error');
      document.getElementById(picker.listId).classList.add('hidden');
      return;
    }
  }
  document.getElementById(inputId).value = `${r.lastName}, ${r.firstName} ${r.middleName || ''}`.trim();
  document.getElementById(picker.hiddenId).value = String(residentId);
  document.getElementById(picker.listId).classList.add('hidden');
  picker.onPick(r);
}

function bcResidentPickerClear(inputId) {
  const picker = _bcResidentPickers[inputId];
  if (!picker) return;
  document.getElementById(inputId).value = '';
  document.getElementById(picker.hiddenId).value = '';
  const list = document.getElementById(picker.listId);
  if (list) list.classList.add('hidden');
  picker.onPick(null);
}
