/**
 * backend/controllers/certificateController.js
 * Certificate Controller with Hard Guard for Non-Residency Issuance
 * & Strictly Decoupled Settings-Driven Punong Barangay Signatory Data Binding
 */

const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

/**
 * Fetches the active Barangay Leadership (Punong Barangay / Barangay Captain)
 * strictly from the Barangay Information settings database table, decoupled from user sessions.
 * @returns {Promise<Object>}
 */
async function getBarangayLeadershipConfig() {
  try {
    const res = await pool.query(
      `SELECT setting_key, setting_value 
       FROM system_settings 
       WHERE setting_key IN ('barangay_captain', 'punong_barangay', 'captain_name', 'municipality', 'province', 'official_logo_url', 'barangay_name')`
    );
    const map = {};
    res.rows.forEach(r => {
      map[r.setting_key] = r.setting_value;
    });

    const activeCaptainName = map.barangay_captain || map.punong_barangay || map.captain_name || 'Alex Roque Cruz';

    return {
      signatory_captain: activeCaptainName,
      barangay_captain: activeCaptainName,
      punong_barangay: activeCaptainName,
      captain_name: activeCaptainName,
      municipality: map.municipality || 'Pandi, Bulacan',
      province: map.province || 'Bulacan',
      barangay_name: map.barangay_name || 'Barangay Mapulang Lupa',
      official_logo_url: map.official_logo_url || '',
    };
  } catch (e) {
    console.warn('[certificateController] Could not query system_settings for leadership info, using fallback:', e.message);
    return {
      signatory_captain: 'Alex Roque Cruz',
      barangay_captain: 'Alex Roque Cruz',
      punong_barangay: 'Alex Roque Cruz',
      captain_name: 'Alex Roque Cruz',
      municipality: 'Pandi, Bulacan',
      province: 'Bulacan',
      barangay_name: 'Barangay Mapulang Lupa',
      official_logo_url: '',
    };
  }
}

/**
 * POST /api/certificates/generate or POST /api/certificates/non-residency
 * Generates a Certificate of Non-Residency with strict hard guard against active blotters
 * and signatory strictly bound to the Barangay Information settings.
 */
async function generateNonResidencyCertificate(req, res) {
  try {
    const { residentId, previousAddress, purpose, orNo, fee, dateIssued } = req.body;
    const resId = parseInt(residentId, 10);

    if (!resId) {
      return res.status(400).json({ ok: false, error: 'Resident ID is required.' });
    }

    // 1. Verify resident status in Census
    const residentQuery = await pool.query(
      `SELECT id, first_name, last_name, middle_name, status, address
       FROM census_records
       WHERE id = $1`,
      [resId]
    );

    if (residentQuery.rows.length === 0) {
      return res.status(404).json({ ok: false, error: 'Resident record not found in Census.' });
    }

    const resident = residentQuery.rows[0];

    // 2. Strict Hard Guard: Check for any active/unsettled Blotter Records
    const blotterCheckQuery = await pool.query(
      `SELECT id, docket_no, status, nature, complainant, date_filed
       FROM blotter_records
       WHERE (respondent_id = $1 OR (respondent_id IS NULL AND respondent ILIKE $2 AND respondent ILIKE $3))
         AND UPPER(status) NOT IN ('SETTLED', 'RESOLVED', 'DISMISSED', 'COMPLIED')
         AND (archived = FALSE OR archived IS NULL)`,
      [resId, `%${resident.last_name}%`, `%${resident.first_name}%`]
    );

    const pendingCases = blotterCheckQuery.rows;

    if (pendingCases.length > 0) {
      console.warn(`[certificateController] Issuance blocked for resident ID ${resId} due to ${pendingCases.length} pending blotter(s).`);
      return res.status(422).json({
        success: false,
        blocked: true,
        error: 'CERTIFICATE_ISSUANCE_BLOCKED',
        message: 'Cannot issue Certificate of Non-Residency. Resident has active/unsettled blotter cases.',
        pendingCases: pendingCases.map(c => ({
          docketNo: c.docket_no,
          status: c.status,
          nature: c.nature,
          complainant: c.complainant,
          dateFiled: c.date_filed,
        })),
      });
    }

    // 3. Sequential Control Number Minting
    const currentYear = new Date().getFullYear();
    const countRes = await pool.query(
      `SELECT COUNT(*) FROM barangay_non_residency WHERE ctrl_no LIKE $1`,
      [`NR-${currentYear}-%`]
    );
    const seq = parseInt(countRes.rows[0].count, 10) + 1;
    const ctrlNo = `NR-${currentYear}-${String(seq).padStart(4, '0')}`;
    const officialOrNo = orNo || `OR-${currentYear}-${String(seq).padStart(4, '0')}`;
    const fullName = `${resident.last_name}, ${resident.first_name} ${resident.middle_name || ''}`.trim();

    // 4. Fetch official leadership configuration strictly from settings (decoupled from user account)
    const leadershipConfig = await getBarangayLeadershipConfig();

    // 5. Insert Certificate Issuance Record
    const insertRes = await pool.query(
      `INSERT INTO barangay_non_residency (
         resident_id, ctrl_no, full_name, previous_address, purpose,
         or_no, fee, date_issued, issued_by, created_at
       ) VALUES (
         $1, $2, $3, $4, $5,
         $6, $7, COALESCE($8, CURRENT_DATE), $9, NOW()
       ) RETURNING id`,
      [
        resId,
        ctrlNo,
        fullName,
        previousAddress || resident.address,
        purpose || 'General Purpose',
        officialOrNo,
        parseFloat(fee) || 20.00,
        dateIssued || new Date().toISOString().slice(0, 10),
        'Office of the Punong Barangay',
      ]
    );

    return res.status(201).json({
      ok: true,
      success: true,
      data: {
        id: insertRes.rows[0].id,
        ctrlNo,
        orNo: officialOrNo,
        signatory_captain: leadershipConfig.signatory_captain,
        barangay_captain: leadershipConfig.barangay_captain,
        captain_name: leadershipConfig.captain_name,
        punong_barangay: leadershipConfig.punong_barangay,
        barangay_name: leadershipConfig.barangay_name,
        municipality: leadershipConfig.municipality,
        province: leadershipConfig.province,
        official_logo_url: leadershipConfig.official_logo_url,
      },
      message: 'Certificate of Non-Residency issued successfully.',
    });
  } catch (err) {
    console.error('[certificateController] Issuance error:', err);
    return res.status(500).json({ ok: false, error: err.message });
  }
}

/**
 * GET /api/certificates/preview or GET /api/certificates/details
 * Returns document preview metadata with dynamically injected Punong Barangay signatory data.
 */
async function getCertificatePreviewDetails(req, res) {
  try {
    const leadershipConfig = await getBarangayLeadershipConfig();
    return res.status(200).json({
      ok: true,
      success: true,
      data: {
        signatory_captain: leadershipConfig.signatory_captain,
        barangay_captain: leadershipConfig.barangay_captain,
        captain_name: leadershipConfig.captain_name,
        punong_barangay: leadershipConfig.punong_barangay,
        barangay_name: leadershipConfig.barangay_name,
        municipality: leadershipConfig.municipality,
        province: leadershipConfig.province,
        official_logo_url: leadershipConfig.official_logo_url,
      }
    });
  } catch (err) {
    return res.status(500).json({ ok: false, error: err.message });
  }
}

/**
 * GET /api/certificates/check-blotter/:residentId
 * Pre-issuance eligibility check
 */
async function checkResidentBlotterEligibility(req, res) {
  try {
    const resId = parseInt(req.params.residentId, 10);
    const residentRes = await pool.query('SELECT first_name, last_name FROM census_records WHERE id = $1', [resId]);
    if (residentRes.rows.length === 0) {
      return res.status(404).json({ ok: false, error: 'Resident not found' });
    }
    const resident = residentRes.rows[0];

    const blotterCheck = await pool.query(
      `SELECT id, docket_no, status, nature, complainant, respondent, date_filed
       FROM blotter_records
       WHERE (respondent_id = $1 OR (respondent_id IS NULL AND respondent ILIKE $2 AND respondent ILIKE $3))
         AND UPPER(status) NOT IN ('SETTLED', 'RESOLVED', 'DISMISSED', 'COMPLIED')
         AND (archived = FALSE OR archived IS NULL)`,
      [resId, `%${resident.last_name}%`, `%${resident.first_name}%`]
    );

    const hasActiveBlotters = blotterCheck.rows.length > 0;
    return res.status(200).json({
      eligible: !hasActiveBlotters,
      blocked: hasActiveBlotters,
      activeCases: blotterCheck.rows,
    });
  } catch (err) {
    return res.status(500).json({ ok: false, error: err.message });
  }
}

module.exports = {
  getBarangayLeadershipConfig,
  generateNonResidencyCertificate,
  getCertificatePreviewDetails,
  checkResidentBlotterEligibility,
};
