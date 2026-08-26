/**
 * backend/controllers/backupController.js
 * Decoupled Read-Only Status/Settings and Manual/Scheduled Backup Controller for BlotterCast
 */

const { Pool } = require('pg');
const backupService = require('../services/backupService');
const backupCronService = require('../services/backupCronService');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

/**
 * GET /api/backup/settings
 * STRICTLY READ-ONLY: Returns configuration values without executing backups or dumping the database.
 */
async function getBackupSettings(req, res) {
  try {
    const queryRes = await pool.query(
      `SELECT setting_key, setting_value 
       FROM system_settings 
       WHERE setting_key IN ('backup_frequency', 'backup_time', 'retain_backups_days', 'auto_backup_enabled')`
    );

    const map = {};
    (queryRes.rows || []).forEach(r => {
      map[r.setting_key] = r.setting_value;
    });

    const frequency = map.backup_frequency || 'Daily';
    const scheduleTime = map.backup_time || '02:00';
    const retainDays = parseInt(map.retain_backups_days, 10) || 30;
    const isEnabled = map.auto_backup_enabled !== '0' && map.auto_backup_enabled !== 'false';

    return res.status(200).json({
      ok: true,
      success: true,
      data: {
        auto_backup_enabled: isEnabled,
        schedule_time: scheduleTime,
        frequency,
        backup_frequency: frequency,
        backup_time: scheduleTime,
        retain_backups_days: retainDays,
        timezone: 'Asia/Manila',
      }
    });
  } catch (err) {
    console.error('[backupController] Error fetching backup settings:', err);
    return res.status(500).json({
      ok: false,
      success: false,
      error: 'Failed to retrieve backup settings.',
      details: err.message,
    });
  }
}

/**
 * POST /api/backup/settings
 * Updates backup scheduling parameters and restarts background cron scheduler without running a backup.
 */
async function updateBackupSettings(req, res) {
  try {
    const { backup_frequency, backup_time, retain_backups_days, auto_backup_enabled, schedule_time, frequency } = req.body || {};

    const freq = backup_frequency || frequency || 'Daily';
    const timeVal = backup_time || schedule_time || '02:00';
    const retain = retain_backups_days != null ? parseInt(retain_backups_days, 10) : 30;
    const enabled = auto_backup_enabled !== false && auto_backup_enabled !== '0' && auto_backup_enabled !== 'false';

    const updates = {
      backup_frequency: freq,
      backup_time: timeVal,
      retain_backups_days: String(retain),
      auto_backup_enabled: enabled ? '1' : '0',
    };

    for (const [k, v] of Object.entries(updates)) {
      await pool.query(
        `INSERT INTO system_settings (setting_key, setting_value)
         VALUES ($1, $2)
         ON CONFLICT (setting_key)
         DO UPDATE SET setting_value = EXCLUDED.setting_value`,
        [k, String(v)]
      );
    }

    // Reschedule background cron task with new schedule parameters
    const cronStatus = backupCronService.initBackupScheduler(timeVal, enabled, freq);

    return res.status(200).json({
      ok: true,
      success: true,
      message: 'Backup schedule settings updated successfully.',
      data: {
        ...updates,
        cronStatus,
      }
    });
  } catch (err) {
    console.error('[backupController] Error updating backup settings:', err);
    return res.status(500).json({
      ok: false,
      success: false,
      error: 'Failed to update backup settings.',
      details: err.message,
    });
  }
}

/**
 * GET /api/backup/history or GET /api/backup/list
 * STRICTLY READ-ONLY: Returns list of past database backups.
 */
async function getBackupHistory(req, res) {
  try {
    const queryRes = await pool.query(
      `SELECT id, file_name, size_bytes, status, created_by, created_at 
       FROM backups 
       ORDER BY id DESC 
       LIMIT 25`
    );

    return res.status(200).json({
      ok: true,
      success: true,
      data: queryRes.rows || [],
    });
  } catch (err) {
    console.error('[backupController] Error fetching backup history:', err);
    return res.status(500).json({
      ok: false,
      success: false,
      error: 'Failed to retrieve backup history.',
      details: err.message,
    });
  }
}

/**
 * GET /api/backup/status
 * STRICTLY READ-ONLY: Returns background scheduler telemetry without executing a backup.
 */
async function getBackupStatus(req, res) {
  try {
    const status = backupCronService.getSchedulerStatus();
    return res.status(200).json({
      ok: true,
      success: true,
      data: status,
    });
  } catch (err) {
    return res.status(500).json({ ok: false, error: err.message });
  }
}

/**
 * POST /api/backup/manual or POST /api/backup/run
 * Executed STRICTLY when the user manually clicks "Backup Now".
 */
async function runManualBackup(req, res) {
  try {
    const operator = req.user?.username || req.user?.fullName || 'admin';
    const result = await backupService.runAutomatedBackup(operator);

    if (!result || !result.success) {
      return res.status(500).json({
        ok: false,
        success: false,
        error: result?.error || 'Database backup execution failed.',
      });
    }

    return res.status(200).json({
      ok: true,
      success: true,
      message: 'Database backup completed successfully.',
      data: result,
    });
  } catch (err) {
    console.error('[backupController] Manual backup execution failed:', err);
    return res.status(500).json({
      ok: false,
      success: false,
      error: err.message,
    });
  }
}

module.exports = {
  getBackupSettings,
  updateBackupSettings,
  getBackupHistory,
  getBackupStatus,
  runManualBackup,
};
