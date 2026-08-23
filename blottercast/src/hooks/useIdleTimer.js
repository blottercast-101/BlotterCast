import { useEffect, useRef, useCallback } from 'react';

/**
 * useIdleTimer
 * Global React Hook for session inactivity auto-logout.
 *
 * @param {Object} options
 * @param {boolean} options.enabled - Whether idle timeout is enabled in system settings
 * @param {number} options.timeoutMinutes - Idle timeout duration in minutes (default: 120)
 * @param {Function} options.onIdle - Callback invoked when the idle timeout expires
 * @param {number} options.throttleMs - Activity event throttle in milliseconds (default: 1000)
 */
export function useIdleTimer({
  enabled = true,
  timeoutMinutes = 120,
  onIdle,
  throttleMs = 1000,
} = {}) {
  const timeoutMs = (timeoutMinutes || 120) * 60 * 1000;
  const lastActiveRef = useRef(Date.now());
  const timerRef = useRef(null);
  const throttleRef = useRef(0);

  const handleIdle = useCallback(() => {
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('bc_last_active_timestamp');
      sessionStorage.setItem(
        'bc_session_expired_reason',
        `Your session expired due to ${timeoutMinutes} minutes of inactivity.`
      );
    } catch (e) {
      console.warn('Storage clear notice:', e);
    }

    if (typeof onIdle === 'function') {
      onIdle();
    } else {
      window.location.replace('/login?session_expired=1');
    }
  }, [onIdle, timeoutMinutes]);

  const checkIdle = useCallback(() => {
    if (!enabled) return;
    const now = Date.now();
    let lastActive = lastActiveRef.current;
    try {
      const stored = localStorage.getItem('bc_last_active_timestamp');
      if (stored) {
        lastActive = Math.max(lastActive, Number(stored));
      }
    } catch (e) {}

    const elapsed = now - lastActive;
    if (elapsed >= timeoutMs) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      handleIdle();
    }
  }, [enabled, timeoutMs, handleIdle]);

  const recordActivity = useCallback(() => {
    if (!enabled) return;
    const now = Date.now();
    if (now - throttleRef.current > throttleMs) {
      throttleRef.current = now;
      lastActiveRef.current = now;
      try {
        localStorage.setItem('bc_last_active_timestamp', now.toString());
      } catch (e) {}
    }
  }, [enabled, throttleMs]);

  useEffect(() => {
    if (!enabled) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    // Set initial activity timestamp
    recordActivity();

    // Check idle status periodically
    timerRef.current = setInterval(checkIdle, 5000);

    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
    events.forEach((evt) => {
      window.addEventListener(evt, recordActivity, { passive: true });
    });

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        checkIdle();
      }
    };

    const handleFocus = () => {
      checkIdle();
    };

    const handleStorageChange = (e) => {
      if (e.key === 'bc_last_active_timestamp') {
        checkIdle();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    window.addEventListener('storage', handleStorageChange);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      events.forEach((evt) => {
        window.removeEventListener(evt, recordActivity);
      });
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [enabled, checkIdle, recordActivity]);

  return { recordActivity, checkIdle };
}

export default useIdleTimer;
