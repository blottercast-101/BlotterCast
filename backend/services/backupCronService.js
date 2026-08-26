/**
 * backend/services/backupCronService.js
 * Background Cron Scheduler for BlotterCast Automated Database Backups
 */

const cron = require('node-cron');
const backupService = require('./backupService');

let scheduledBackupTask = null;
let currentScheduleConfig = {
  timeString: '02:00',
  frequency: 'Daily',
  isEnabled: true,
  cronExpression: '0 2 * * *',
  lastStarted: null,
};

/**
 * Converts frequency string and time (e.g. "23:00" or "02:00") into Cron expression
 * @param {string} frequency - 'Daily', 'Every 12 hours', 'Weekly', 'Monthly'
 * @param {string} timeStr - 'HH:MM' in 24h format
 * @returns {string}
 */
function buildCronExpression(frequency = 'Daily', timeStr = '02:00') {
  let [hours, minutes] = [2, 0];
  try {
    const parts = String(timeStr).trim().split(':');
    hours = parseInt(parts[0], 10);
    minutes = parseInt(parts[1], 10) || 0;
  } catch (_) {
    hours = 2;
    minutes = 0;
  }

  hours = Math.max(0, Math.min(23, isNaN(hours) ? 2 : hours));
  minutes = Math.max(0, Math.min(59, isNaN(minutes) ? 0 : minutes));

  switch (frequency) {
    case 'Every 12 hours': {
      const secondHour = (hours + 12) % 24;
      const sortedHours = [hours, secondHour].sort((a, b) => a - b);
      return `${minutes} ${sortedHours.join(',')} * * *`;
    }
    case 'Weekly':
      return `${minutes} ${hours} * * 0`; // Sunday
    case 'Monthly':
      return `${minutes} ${hours} 1 * *`; // 1st day of month
    case 'Daily':
    default:
      return `${minutes} ${hours} * * *`;
  }
}

/**
 * Initializes or restarts the background cron scheduler strictly based on the configured time string.
 *
 * @param {string} timeString - Scheduled time (e.g., "23:00")
 * @param {boolean} isEnabled - Whether automated backup is active
 * @param {string} frequency - 'Daily', 'Every 12 hours', 'Weekly', 'Monthly'
 */
function initBackupScheduler(timeString = '02:00', isEnabled = true, frequency = 'Daily') {
  if (scheduledBackupTask) {
    scheduledBackupTask.stop();
    scheduledBackupTask = null;
  }

  currentScheduleConfig = {
    timeString,
    frequency,
    isEnabled: Boolean(isEnabled),
    cronExpression: buildCronExpression(frequency, timeString),
    lastStarted: new Date().toISOString(),
  };

  if (!isEnabled) {
    console.log('[CRON] Automated backup is disabled in settings. Scheduler paused.');
    return currentScheduleConfig;
  }

  const cronExpression = buildCronExpression(frequency, timeString);
  console.log(`[CRON] Initializing automated backup scheduler: "${cronExpression}" (Timezone: Asia/Manila, Scheduled Time: ${timeString})`);

  scheduledBackupTask = cron.schedule(
    cronExpression,
    async () => {
      console.log(`[CRON] Running scheduled automated backup at ${timeString} (Timezone: Asia/Manila)`);
      try {
        const result = await backupService.runAutomatedBackup('system (automatic)');
        console.log('[CRON] Automated backup completed successfully:', result);
      } catch (err) {
        console.error('[CRON] Automated backup execution failed:', err);
      }
    },
    {
      scheduled: true,
      timezone: 'Asia/Manila',
    }
  );

  return currentScheduleConfig;
}

/**
 * Reads the latest settings from the database and updates the active cron task
 */
async function rescheduleBackupJob() {
  try {
    const res = await backupService.pool.query(`
      SELECT setting_key, setting_value 
      FROM system_settings 
      WHERE setting_key IN ('backup_frequency', 'backup_time', 'retain_backups_days', 'auto_backup_enabled')
    `);

    const map = {};
    (res.rows || []).forEach(r => { map[r.setting_key] = r.setting_value; });

    const frequency = map.backup_frequency || 'Daily';
    const timeString = map.backup_time || '02:00';
    const isEnabled = map.auto_backup_enabled !== '0' && map.auto_backup_enabled !== 'false';

    return initBackupScheduler(timeString, isEnabled, frequency);
  } catch (err) {
    console.error('[CRON] Failed to query database settings for scheduler:', err);
    return initBackupScheduler('02:00', true, 'Daily');
  }
}

/**
 * Returns read-only scheduler telemetry
 */
function getSchedulerStatus() {
  return {
    ...currentScheduleConfig,
    active: Boolean(scheduledBackupTask),
    timezone: 'Asia/Manila',
  };
}

module.exports = {
  buildCronExpression,
  initBackupScheduler,
  rescheduleBackupJob,
  getSchedulerStatus,
};
