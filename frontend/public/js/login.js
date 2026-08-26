/**
 * frontend/public/js/login.js
 * Authentication & Redirect Animation Handler for BlotterCast Login
 */

/**
 * Triggers the smooth SVG checkmark animation and displays the "Welcome back!" redirect overlay.
 *
 * @param {Object|string} userOrName - User object or display string
 * @param {string} [customSubtitle] - Optional custom redirect message
 */
function showSuccessRedirect(userOrName, customSubtitle) {
  const roleEl = document.getElementById('redirectRole');
  const subtitleEl = document.getElementById('redirectSubtitle');
  const overlay = document.getElementById('successOverlay');
  const msgEl = document.getElementById('successMsg');
  const checkmarkPath = document.querySelector('.checkmark-path');
  const circlePop = document.querySelector('.success-circle-pop');

  const nameOrRole = (typeof userOrName === 'object' && userOrName !== null)
    ? (userOrName.full_name || userOrName.role || userOrName.username || 'System Administrator')
    : (userOrName || 'System Administrator');

  if (roleEl) {
    roleEl.textContent = nameOrRole;
  }

  if (customSubtitle && subtitleEl) {
    subtitleEl.innerHTML = `<span>${customSubtitle}</span>`;
  } else if (subtitleEl) {
    subtitleEl.innerHTML = `
      <span>Signed in as <strong id="redirectRole" class="font-semibold text-emerald-900">${nameOrRole}</strong></span>
      <span class="inline-block">— Redirecting</span>
      <span class="inline-flex gap-0.5">
        <span class="animate-bounce delay-100">.</span>
        <span class="animate-bounce delay-200">.</span>
        <span class="animate-bounce delay-300">.</span>
      </span>`;
  }

  if (msgEl) {
    msgEl.textContent = customSubtitle || `Signed in as ${nameOrRole} — Redirecting…`;
  }

  // Trigger SVG checkmark draw-in and badge pop animation
  if (checkmarkPath) {
    checkmarkPath.style.animation = 'none';
    void checkmarkPath.offsetWidth;
    checkmarkPath.style.animation = '';
  }
  if (circlePop) {
    circlePop.style.animation = 'none';
    void circlePop.offsetWidth;
    circlePop.style.animation = '';
  }

  if (overlay) {
    overlay.classList.add('show');
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { showSuccessRedirect };
}
