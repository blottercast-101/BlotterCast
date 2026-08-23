import React, { useState, useEffect } from 'react';

export default function SystemSettings({ userRole = 'System Admin' }) {
  const [systemPrefs, setSystemPrefs] = useState({
    barangay_name: 'Barangay Mapulang Lupa',
    municipality: 'Pandi, Bulacan',
    region: 'Region III – Central Luzon',
    captain_name: 'Kapitan Jose Reyes',
    date_format: 'MM/DD/YYYY',
    time_format: '12',
    records_per_page: '6',
    default_language: 'English',
  });

  const [securitySettings, setSecuritySettings] = useState({
    is_2fa_globally_enabled: false,
    is_idle_timeout_enabled: false,
    idle_timeout_duration_minutes: 120,
  });

  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true);
        const [prefsRes, secRes] = await Promise.all([
          fetch('/api/settings.php?action=list').then((r) => r.json()).catch(() => ({})),
          fetch('/api/admin/security-settings').then((r) => r.json()).catch(() => ({})),
        ]);

        if (prefsRes && typeof prefsRes === 'object') {
          setSystemPrefs((prev) => ({ ...prev, ...prefsRes }));
        }
        if (secRes && secRes.settings) {
          setSecuritySettings((prev) => ({ ...prev, ...secRes.settings }));
        } else if (secRes && typeof secRes === 'object' && secRes.status === 'success') {
          setSecuritySettings((prev) => ({ ...prev, ...secRes }));
        }
      } catch (err) {
        console.error('Failed to load system settings:', err);
      } finally {
        setLoading(false);
      }
    }

    loadSettings();
  }, []);

  const handleToggleSecurity = async (key, checked) => {
    try {
      const updated = { ...securitySettings, [key]: checked };
      setSecuritySettings(updated);

      const res = await fetch('/api/admin/security-settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: checked }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.error || 'Failed to update security setting');
      }
      setToast({
        type: 'success',
        message: `Master Security setting updated: ${checked ? 'Enabled' : 'Disabled'}`,
      });
    } catch (err) {
      setSecuritySettings((prev) => ({ ...prev, [key]: !checked }));
      setToast({ type: 'error', message: err.message });
    }
  };

  const handlePrefChange = (key, value) => {
    setSystemPrefs((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {toast && (
        <div
          className={`p-4 rounded-xl text-sm font-medium transition-all ${
            toast.type === 'error'
              ? 'bg-red-50 border border-red-200 text-red-700'
              : 'bg-emerald-50 border border-emerald-200 text-emerald-800'
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* System Preferences Card */}
      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <h3 className="text-base font-semibold text-gray-800 mb-4">System Preferences</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
              Date Format
            </label>
            <select
              value={systemPrefs.date_format}
              onChange={(e) => handlePrefChange('date_format', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
              Time Format
            </label>
            <select
              value={systemPrefs.time_format}
              onChange={(e) => handlePrefChange('time_format', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="12">12-Hour (hh:mm A) (e.g. 01:45 PM)</option>
              <option value="24">24-Hour (HH:mm) (e.g. 13:45)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
              Records Per Page
            </label>
            <select
              value={systemPrefs.records_per_page}
              onChange={(e) => handlePrefChange('records_per_page', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="5">5</option>
              <option value="6">6</option>
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1">
              Default Language
            </label>
            <select
              value={systemPrefs.default_language}
              onChange={(e) => handlePrefChange('default_language', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="English">English</option>
              <option value="Filipino">Filipino</option>
            </select>
          </div>
        </div>
      </div>

      {/* Security Settings Section (Admin Master Control) */}
      <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm mt-6">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-base font-semibold text-gray-800">Security &amp; Authentication</h3>
          <span className="px-2 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-800 rounded-full">
            Admin Master Control
          </span>
        </div>

        <div className="space-y-4">
          {/* Master 2FA Switch */}
          <div className="flex items-center justify-between p-4 bg-gray-50/70 rounded-xl border border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-800">Enforce 2FA for All Accounts</p>
              <p className="text-xs text-gray-500">Require Two-Factor Authentication across all roles during login.</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                id="twoFaMasterToggle"
                checked={Boolean(securitySettings.is_2fa_globally_enabled)}
                onChange={(e) => handleToggleSecurity('is_2fa_globally_enabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
            </label>
          </div>

          {/* Master Idle Timeout Switch */}
          <div className="flex items-center justify-between p-4 bg-gray-50/70 rounded-xl border border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-800">Session Inactivity Auto-Logout (2 Hours)</p>
              <p className="text-xs text-gray-500">Automatically logs out inactive users after 120 minutes of inactivity.</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                id="idleTimeoutMasterToggle"
                checked={Boolean(securitySettings.is_idle_timeout_enabled)}
                onChange={(e) => handleToggleSecurity('is_idle_timeout_enabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
