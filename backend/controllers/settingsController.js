/**
 * backend/controllers/settingsController.js
 * Barangay Information & System Settings Controller for BlotterCast
 */

const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

const GENERAL_SETTING_KEYS = [
  'barangay_name',
  'municipality',
  'province',
  'region',
  'captain_name',
  'punong_barangay',
  'contact_number',
  'contact_no',
  'email',
  'official_logo_url',
];

/**
 * GET /api/settings/general
 * Retrieves the current Barangay Information configuration.
 */
async function getGeneralSettings(req, res) {
  try {
    const result = await pool.query(
      `SELECT setting_key, setting_value FROM system_settings WHERE setting_key = ANY($1::text[])`,
      [GENERAL_SETTING_KEYS]
    );

    const configMap = {};
    result.rows.forEach(row => {
      configMap[row.setting_key] = row.setting_value;
    });

    const bName = configMap.barangay_name || 'Barangay Mapulang Lupa';
    const muni = configMap.municipality || 'Pandi';
    const prov = configMap.province || 'Bulacan';
    const capt = configMap.captain_name || configMap.punong_barangay || 'Kapitan Jose Reyes';
    const contact = configMap.contact_number || configMap.contact_no || '0917-000-0000';
    const email = configMap.email || 'mapulanglupa@pandi.gov.ph';
    const logo = configMap.official_logo_url || '';
    const region = configMap.region || 'Region III – Central Luzon';

    const data = {
      barangay_name: bName,
      municipality: muni,
      province: prov,
      region,
      captain_name: capt,
      punong_barangay: capt,
      contact_number: contact,
      contact_no: contact,
      email,
      official_logo_url: logo,
    };

    return res.status(200).json({
      ok: true,
      success: true,
      data,
    });
  } catch (err) {
    console.error('[settingsController] Error fetching general settings:', err);
    return res.status(500).json({
      ok: false,
      success: false,
      error: 'Failed to retrieve barangay settings.',
      details: err.message,
    });
  }
}

/**
 * POST or PUT /api/settings/general
 * Saves and synchronizes updated Barangay Information.
 */
async function updateGeneralSettings(req, res) {
  const client = await pool.connect();
  try {
    const body = req.body || {};

    if (!body || Object.keys(body).length === 0) {
      return res.status(400).json({
        ok: false,
        success: false,
        error: 'No barangay settings provided for update.',
      });
    }

    await client.query('BEGIN');

    // Normalize and persist each general setting key
    const updates = { ...body };

    // Synchronize aliases
    if (updates.punong_barangay && !updates.captain_name) {
      updates.captain_name = updates.punong_barangay;
    } else if (updates.captain_name && !updates.punong_barangay) {
      updates.punong_barangay = updates.captain_name;
    }

    if (updates.contact_number && !updates.contact_no) {
      updates.contact_no = updates.contact_number;
    } else if (updates.contact_no && !updates.contact_number) {
      updates.contact_number = updates.contact_no;
    }

    for (const [key, value] of Object.entries(updates)) {
      const cleanKey = String(key).replace(/[^a-zA-Z0-9_]/g, '');
      if (!cleanKey) continue;
      const strVal = value != null ? String(value) : '';

      await client.query(
        `INSERT INTO system_settings (setting_key, setting_value)
         VALUES ($1, $2)
         ON CONFLICT (setting_key)
         DO UPDATE SET setting_value = EXCLUDED.setting_value`,
        [cleanKey, strVal]
      );
    }

    await client.query('COMMIT');

    // Fetch refreshed configuration
    const refreshed = await pool.query(
      `SELECT setting_key, setting_value FROM system_settings WHERE setting_key = ANY($1::text[])`,
      [GENERAL_SETTING_KEYS]
    );

    const configMap = {};
    refreshed.rows.forEach(row => {
      configMap[row.setting_key] = row.setting_value;
    });

    const bName = configMap.barangay_name || updates.barangay_name || 'Barangay Mapulang Lupa';
    const muni = configMap.municipality || updates.municipality || 'Pandi';
    const prov = configMap.province || updates.province || 'Bulacan';
    const capt = configMap.captain_name || configMap.punong_barangay || updates.captain_name || 'Kapitan Jose Reyes';
    const contact = configMap.contact_number || configMap.contact_no || updates.contact_number || '0917-000-0000';
    const email = configMap.email || updates.email || 'mapulanglupa@pandi.gov.ph';
    const logo = configMap.official_logo_url || updates.official_logo_url || '';
    const region = configMap.region || updates.region || 'Region III – Central Luzon';

    const data = {
      barangay_name: bName,
      municipality: muni,
      province: prov,
      region,
      captain_name: capt,
      punong_barangay: capt,
      contact_number: contact,
      contact_no: contact,
      email,
      official_logo_url: logo,
    };

    return res.status(200).json({
      ok: true,
      success: true,
      message: 'Barangay information updated successfully.',
      data,
    });
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('[settingsController] Error updating general settings:', err);
    return res.status(500).json({
      ok: false,
      success: false,
      error: 'Failed to update barangay settings.',
      details: err.message,
    });
  } finally {
    client.release();
  }
}

module.exports = {
  GENERAL_SETTING_KEYS,
  getGeneralSettings,
  updateGeneralSettings,
};
