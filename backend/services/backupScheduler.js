/**
 * backend/services/backupScheduler.js
 * Standalone Node.js Autonomous Cron Worker for BlotterCast
 */

const cron = require('node-cron');
const backupService = require('./backupService');

let currentScheduledTask = null;

/**
 * Converts frequency string and time (e.g. "02:00" or "02:00 AM") into Cron expression
 */
function buildCronExpression(frequency = 'Daily', timeStr = '02:00') {
  let [hours, minutes] = [2, 0];
  try {
    const parts = timeStr.trim().split(':');
    hours = parseInt(parts[0], 10);
    minutes = parseInt(parts[1], 10) || 0;
  } catch (_) {
    hours = 2;
    minutes = 0;
  }

  // Ensure 0-23 and 0-59 bounds
  hours = Math.max(0, Math.min(23, isNaN(hours) ? 2 : hours));
  minutes = Math.max(0, Math.min(59, isNaN(minutes) ? 0 : minutes));

  switch (frequency) {
    case 'Every 12 hours':
      const secondHour = (hours + 12) % 24;
      const sortedHours = [hours, secondHour].sort((a, b) => a - b);
      return `${minutes} ${sortedHours.join(',')} * * *`;
    case 'Weekly':
      return `${minutes} ${hours} * * 0`; // Sunday
    case 'Monthly':
      return `${minutes} ${hours} 1 * *`; // 1st of every month
    case 'Daily':
    default:
      return `${minutes} ${hours} * * *`; // Daily
  }
}

/**
 * Reads scheduling settings from PostgreSQL and (re)instantiates the cron job
 */
async function rescheduleBackupJob() {
  try {
    // 1. Destroy / stop existing active job
    if (currentScheduledTask) {
      currentScheduledTask.stop();
      currentScheduledTask = null;
      console.log('[BackupScheduler] Existing cron job stopped.');
    }

    // 2. Query settings from database
    const res = await backupService.pool.query(`
      SELECT setting_key, setting_value 
      FROM system_settings 
      WHERE setting_key IN ('backup_frequency', 'backup_time', 'retain_backups_days')
    `);

    const settings = {};
    (res.rows || []).forEach(r => { settings[r.setting_key] = r.setting_value; });

    const frequency = settings.backup_frequency || 'Daily';
    const timeStr = settings.backup_time || '02:00';
    const cronExp = buildCronExpression(frequency, timeStr);

    console.log(`[BackupScheduler] Scheduling autonomous backup with expression: "${cronExp}" (Timezone: Asia/Manila)`);

    // 3. Schedule autonomous cron job with Asia/Manila timezone
    currentScheduledTask = cron.schedule(
      cronExp,
      async () => {
        console.log(`[BackupScheduler] Scheduled cron triggered at ${new Date().toISOString()}`);
        const result = await backupService.runAutomatedBackup('system (automatic)');
        console.log(`[BackupScheduler] Backup finished:`, result);
      },
      {
        scheduled: true,
        timezone: 'Asia/Manila',
      }
    );

    return {
      scheduled: true,
      frequency,
      time: timeStr,
      cronExpression: cronExp,
      timezone: 'Asia/Manila',
    };
  } catch (err) {
    console.error('[BackupScheduler] Failed to initialize/reschedule backup cron:', err);
    return { scheduled: false, error: err.message };
  }
}

/**
 * Initializes the scheduler on application bootstrap
 */
async function initBackupScheduler() {
  console.log('[BackupScheduler] Initializing autonomous background backup worker...');
  return rescheduleBackupJob();
}

module.exports = {
  initBackupScheduler,
  rescheduleBackupJob,
};
