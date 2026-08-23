import React, { useState, useEffect } from 'react';

/**
 * SecuritySettings
 * Admin-Only System Security Settings component.
 * Allows System Administrators to configure Global 2FA Enforcement and Global Inactivity Auto-Logout.
 */
export function SecuritySettings({ apiBase = '/api', onSaveSuccess }) {
  const [settings, setSettings] = useState({
    is_2fa_globally_enabled: false,
    is_idle_timeout_enabled: false,
    idle_timeout_duration_minutes: 120,
    lockout_enabled: true,
    max_failed_logins: 5,
    min_password_length: 8,
    password_expiry_days: 90,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Load existing system security settings
  useEffect(() => {
    async function fetchSettings() {
      try {
        setLoading(true);
        const res = await fetch(`${apiBase}/admin/security-settings`, {
          credentials: 'include',
        });
        if (!res.ok) {
          throw new Error('Failed to load admin security settings');
        }
        const data = await res.json();
        setSettings({
          is_2fa_globally_enabled: Boolean(data.is_2fa_globally_enabled ?? data.enforce_2fa_all_users),
          is_idle_timeout_enabled: Boolean(data.is_idle_timeout_enabled ?? data.idle_timeout_enabled),
          idle_timeout_duration_minutes: Number(data.idle_timeout_duration_minutes || 120),
          lockout_enabled: Boolean(data.lockout_enabled),
          max_failed_logins: Number(data.max_failed_logins || 5),
          min_password_length: Number(data.min_password_length || 8),
          password_expiry_days: Number(data.password_expiry_days || 90),
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchSettings();
  }, [apiBase]);

  const handleToggle = (key) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings((prev) => ({ ...prev, [name]: Number(value) }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const res = await fetch(`${apiBase}/admin/security-settings`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(settings),
      });

      const result = await res.json();
      if (!res.ok || !result.ok) {
        throw new Error(result.error || result.message || 'Failed to save security settings');
      }

      setSuccessMessage('System-wide security settings successfully updated and enforced.');
      if (typeof onSaveSuccess === 'function') {
        onSaveSuccess(result.settings);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center text-forest-600">
        <p className="animate-pulse">Loading system security policies...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-forest-100 shadow-sm p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-forest-900 tracking-tight">System-Wide Security Settings</h2>
        <p className="text-sm text-forest-500 mt-1">
          Global policies enforced across all user roles (Admin, Staff, Desk Officers). Strictly restricted to System Administrators.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl bg-green-50 border border-green-200 text-green-800 text-sm font-medium">
          {successMessage}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Global 2FA Policy */}
        <div className="flex items-start justify-between p-4 rounded-xl bg-forest-50/50 border border-forest-100/80">
          <div className="space-y-0.5 max-w-xl">
            <label className="text-sm font-bold text-forest-800 cursor-pointer" htmlFor="toggle-2fa">
              Require 2FA for All Accounts
            </label>
            <p className="text-xs text-forest-500">
              When enabled, all users across all roles must complete Two-Factor Authentication (OTP email verification) during login. When disabled, users log in directly.
            </p>
          </div>
          <button
            type="button"
            id="toggle-2fa"
            onClick={() => handleToggle('is_2fa_globally_enabled')}
            className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors duration-200 ease-in-out ${
              settings.is_2fa_globally_enabled ? 'bg-forest-600 justify-end' : 'bg-gray-300 justify-start'
            }`}
          >
            <span className="w-4 h-4 rounded-full bg-white shadow-sm block" />
          </button>
        </div>

        {/* Global Inactivity Auto-Logout */}
        <div className="flex items-start justify-between p-4 rounded-xl bg-forest-50/50 border border-forest-100/80">
          <div className="space-y-0.5 max-w-xl">
            <label className="text-sm font-bold text-forest-800 cursor-pointer" htmlFor="toggle-idle">
              Session Inactivity Auto-Logout
            </label>
            <p className="text-xs text-forest-500">
              When enabled, automatically logs out inactive users across all roles after the inactivity duration. When disabled, sessions remain active.
            </p>
          </div>
          <button
            type="button"
            id="toggle-idle"
            onClick={() => handleToggle('is_idle_timeout_enabled')}
            className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors duration-200 ease-in-out ${
              settings.is_idle_timeout_enabled ? 'bg-forest-600 justify-end' : 'bg-gray-300 justify-start'
            }`}
          >
            <span className="w-4 h-4 rounded-full bg-white shadow-sm block" />
          </button>
        </div>

        {/* Duration & Threshold Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-xs font-semibold text-forest-700 uppercase tracking-wider mb-1.5">
              Inactivity Timeout Duration (Minutes)
            </label>
            <input
              type="number"
              name="idle_timeout_duration_minutes"
              value={settings.idle_timeout_duration_minutes}
              onChange={handleChange}
              min="5"
              max="1440"
              className="w-full px-3.5 py-2.5 rounded-xl border border-forest-200 focus:outline-none focus:ring-2 focus:ring-forest-500 text-sm bg-white"
            />
            <span className="text-[11px] text-forest-400 mt-1 block">Default: 120 minutes (2 hours).</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-forest-700 uppercase tracking-wider mb-1.5">
              Max Failed Login Attempts
            </label>
            <input
              type="number"
              name="max_failed_logins"
              value={settings.max_failed_logins}
              onChange={handleChange}
              min="1"
              max="20"
              className="w-full px-3.5 py-2.5 rounded-xl border border-forest-200 focus:outline-none focus:ring-2 focus:ring-forest-500 text-sm bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-forest-700 uppercase tracking-wider mb-1.5">
              Minimum Password Length
            </label>
            <input
              type="number"
              name="min_password_length"
              value={settings.min_password_length}
              onChange={handleChange}
              min="6"
              max="32"
              className="w-full px-3.5 py-2.5 rounded-xl border border-forest-200 focus:outline-none focus:ring-2 focus:ring-forest-500 text-sm bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-forest-700 uppercase tracking-wider mb-1.5">
              Password Expiry (Days)
            </label>
            <input
              type="number"
              name="password_expiry_days"
              value={settings.password_expiry_days}
              onChange={handleChange}
              min="0"
              max="365"
              className="w-full px-3.5 py-2.5 rounded-xl border border-forest-200 focus:outline-none focus:ring-2 focus:ring-forest-500 text-sm bg-white"
            />
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end pt-4 border-t border-forest-100">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-forest-600 hover:bg-forest-700 text-white font-semibold text-sm transition-colors shadow-sm disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Security Settings'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default SecuritySettings;
