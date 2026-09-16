/**
 * BlotterCast Authentication Helper Script
 * Centralized error clearing, auth view transitions, and validation state.
 */

function clearAuthErrors() {
  const errorBanner = document.getElementById('loginErrorAlert') || document.querySelector('.auth-error-banner');
  if (errorBanner) {
    errorBanner.classList.remove('show');
    errorBanner.classList.add('hidden');
    errorBanner.style.display = 'none';
    errorBanner.textContent = '';
  }
}
window.clearAuthErrors = clearAuthErrors;

function initAuthErrorListeners() {
  // 1. Forgot password links
  const forgotLink = document.getElementById('forgotPasswordLink') || document.getElementById('forgotLink');
  if (forgotLink) {
    forgotLink.addEventListener('click', clearAuthErrors);
  }

  // 2. Back to sign in links
  document.querySelectorAll('a[onclick*="backToLogin"], button[onclick*="backToLogin"]').forEach(el => {
    el.addEventListener('click', clearAuthErrors);
  });

  // 3. Username and password input/focus events
  ['username', 'password'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      ['input', 'focus'].forEach(evt => {
        el.addEventListener(evt, () => {
          clearAuthErrors();
          el.classList.remove('error');
          const errEl = document.getElementById(id + 'Error');
          if (errEl) errEl.classList.remove('show');
        });
      });
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAuthErrorListeners);
} else {
  initAuthErrorListeners();
}
