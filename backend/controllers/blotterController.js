/**
 * backend/controllers/blotterController.js
 * Single Source of Truth (SSOT) Blotter Controller for BlotterCast
 */

const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

/**
 * PUT /api/blotter/:id
 * Updates an official blotter entry and automatically synchronizes
 * shared fields to the linked incident report record within a SQL transaction.
 */
async function updateBlotter(req, res) {
  const client = await pool.connect();
  try {
    const blotterId = parseInt(req.params.id, 10);
    const {
      dateFiled,
      complainant,
      complainantId,
      complainantAddr,
      respondent,
      respondentId,
      respondentAddr,
      nature,
      type,
      status,
      zone,
      incidentTime,
    } = req.body;

    // Begin SQL Transaction
    await client.query('BEGIN');

    // 1. Fetch current blotter entry to check if linked to an incident report
    const existingRes = await client.query(
      'SELECT id, source_incident_id FROM blotter_records WHERE id = $1',
      [blotterId]
    );

    if (existingRes.rows.length === 0) {
      await client.query('ROLLBACK');
      return res.status(404).json({ ok: false, error: 'Blotter record not found' });
    }

    const blotterRecord = existingRes.rows[0];

    // 2. Update the official Blotter record
    await client.query(
      `UPDATE blotter_records
       SET date_filed = COALESCE($1, date_filed),
           complainant = COALESCE($2, complainant),
           complainant_id = $3,
           complainant_addr = COALESCE($4, complainant_addr),
           respondent = COALESCE($5, respondent),
           respondent_id = $6,
           respondent_addr = COALESCE($7, respondent_addr),
           nature = COALESCE($8, nature),
           case_type = COALESCE($9, case_type),
           status = COALESCE($10, status),
           zone_id = COALESCE($11, zone_id)
       WHERE id = $12`,
      [
        dateFiled,
        complainant,
        complainantId || null,
        complainantAddr,
        respondent,
        respondentId || null,
        respondentAddr,
        nature,
        type || 'CRIM',
        status || 'Pending',
        zone || null,
        blotterId,
      ]
    );

    // 3. Single Source of Truth (SSOT): propagate shared fields to linked Incident Report
    if (blotterRecord.source_incident_id) {
      await client.query(
        `UPDATE incidents
         SET incident_date = COALESCE($1, incident_date),
             description = COALESCE($2, description),
             category = COALESCE($3, category),
             zone_id = COALESCE($4, zone_id),
             updated_at = NOW()
         WHERE id = $5`,
        [
          dateFiled,
          nature,
          type,
          zone,
          blotterRecord.source_incident_id,
        ]
      );
    }

    // Commit Transaction
    await client.query('COMMIT');

    return res.status(200).json({
      ok: true,
      message: 'Blotter entry updated and linked incident synchronized.',
    });
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('[blotterController] Update error:', err);
    return res.status(500).json({ ok: false, error: err.message });
  } finally {
    client.release();
  }
}

module.exports = {
  updateBlotter,
};
