/**
 * backend/services/backupService.js
 * Standalone Node.js Database Backup and Retention Service for BlotterCast
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { Pool } = require('pg');

const BACKUP_DIR = process.env.BACKUP_DIR || path.join(__dirname, '..', '..', 'backup');
if (!fs.existsSync(BACKUP_DIR)) {
  fs.mkdirSync(BACKUP_DIR, { recursive: true });
}

// Database Connection Pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@127.0.0.1:5432/blottercast',
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

/**
 * Format bytes to readable string (e.g. "285 KB")
 */
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Prune backup files on disk and backup_history records older than retainDays
 */
async function cleanupOldBackups(retainDays = 30) {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - parseInt(retainDays, 10));
  let cleanedCount = 0;

  try {
    // 1. Delete expired records from database
    const deleteRes = await pool.query(
      'DELETE FROM backups WHERE created_at < $1 RETURNING file_name',
      [cutoffDate]
    );
    cleanedCount += (deleteRes.rows || []).length;

    // 2. Delete expired SQL files from disk
    const files = fs.readdirSync(BACKUP_DIR);
    for (const file of files) {
      if (file.startsWith('blottercast-backup-') && file.endsWith('.sql')) {
        const filePath = path.join(BACKUP_DIR, file);
        const stats = fs.statSync(filePath);
        if (stats.mtime < cutoffDate) {
          try {
            fs.unlinkSync(filePath);
            cleanedCount++;
          } catch (_) {}
        }
      }
    }
  } catch (err) {
    console.error('[BackupService] Retention cleanup error:', err.message);
  }

  return cleanedCount;
}

/**
 * Runs automated or manual database backup with SQL schema + data dump
 */
async function runAutomatedBackup(triggeredBy = 'system (automatic)') {
  const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  const fileName = `blottercast-backup-${timestamp}.sql`;
  const filePath = path.join(BACKUP_DIR, fileName);

  try {
    // Query database settings for retention
    const settingRes = await pool.query(
      "SELECT setting_value FROM system_settings WHERE setting_key = 'retain_backups_days'"
    );
    const retainDays = settingRes.rows[0]?.setting_value || 30;

    // Generate Portable SQL Dump
    const tablesRes = await pool.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    `);
    const tables = tablesRes.rows.map(r => r.table_name);

    let sqlDump = `-- BlotterCast Database Backup\n-- Generated: ${new Date().toISOString()}\n\n`;

    for (const table of tables) {
      sqlDump += `-- Table: ${table}\n`;
      const rowsRes = await pool.query(`SELECT * FROM "${table}"`);
      if (rowsRes.rows.length > 0) {
        const columns = Object.keys(rowsRes.rows[0]);
        for (const row of rowsRes.rows) {
          const values = columns.map(c => {
            const v = row[c];
            if (v === null || v === undefined) return 'NULL';
            if (typeof v === 'number') return v;
            return `'${String(v).replace(/'/g, "''")}'`;
          });
          sqlDump += `INSERT INTO "${table}" ("${columns.join('", "')}") VALUES (${values.join(', ')});\n`;
        }
      }
      sqlDump += '\n';
    }

    // Save to disk
    fs.writeFileSync(filePath, sqlDump, 'utf8');
    const stats = fs.statSync(filePath);
    const sizeBytes = stats.size;

    // Log to backups table
    await pool.query(
      `INSERT INTO backups (file_name, size_bytes, status, created_by, created_at)
       VALUES ($1, $2, $3, $4, NOW())`,
      [fileName, sizeBytes, 'Success', triggeredBy]
    );

    // Retention Cleanup
    const cleaned = await cleanupOldBackups(retainDays);

    return {
      success: true,
      file: fileName,
      size: formatBytes(sizeBytes),
      sizeBytes,
      status: 'Success',
      by: triggeredBy,
      cleanedOldBackups: cleaned,
    };
  } catch (err) {
    console.error('[BackupService] Backup failed:', err);
    try {
      await pool.query(
        `INSERT INTO backups (file_name, size_bytes, status, created_by, created_at)
         VALUES ($1, $2, $3, $4, NOW())`,
        [fileName, 0, 'Failed', triggeredBy]
      );
    } catch (_) {}

    return {
      success: false,
      error: err.message,
      status: 'Failed',
    };
  }
}

module.exports = {
  runAutomatedBackup,
  cleanupOldBackups,
  pool,
};
