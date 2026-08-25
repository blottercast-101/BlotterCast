/**
 * backend/controllers/certificateController.js
 * Certificate Controller with Hard Guard for Non-Residency Issuance
 */

const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

/**
 * POST /api/certificates/generate or POST /api/certificates/non-residency
 * Generates a Certificate of Non-Residency with strict hard guard against active blotters.
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
    // Status must NOT be 'SETTLED', 'RESOLVED', 'DISMISSED', or 'COMPLIED'
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

    // 4. Insert Certificate Issuance Record
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
        req.user?.fullName || 'Barangay Staff',
      ]
    );

    return res.status(201).json({
      ok: true,
      success: true,
      id: insertRes.rows[0].id,
      ctrlNo,
      orNo: officialOrNo,
      message: 'Certificate of Non-Residency issued successfully.',
    });
  } catch (err) {
    console.error('[certificateController] Issuance error:', err);
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
  generateNonResidencyCertificate,
  checkResidentBlotterEligibility,
};
