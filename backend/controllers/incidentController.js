/**
 * backend/controllers/incidentController.js
 * Incident Controller with Elevated Status Guard for BlotterCast
 */

const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

/**
 * PUT /api/incidents/:id
 * Updates an incident report. Rejects edits with 403 Forbidden if the
 * record has already been elevated to an official Blotter case.
 */
async function updateIncident(req, res) {
  try {
    const incidentId = parseInt(req.params.id, 10);
    const {
      date,
      timeReported,
      location,
      category,
      priority,
      description,
      reporter,
      isNonResident,
      reporterResidentId,
      reporterAddress,
      officer,
      status,
      zone,
      lat,
      lng,
    } = req.body;

    // 1. Fetch current incident record
    const checkRes = await pool.query(
      'SELECT id, report_no, is_blotter, blotter_docket_no, status FROM incidents WHERE id = $1',
      [incidentId]
    );

    if (checkRes.rows.length === 0) {
      return res.status(404).json({ ok: false, error: 'Incident report not found' });
    }

    const incident = checkRes.rows[0];

    // 2. Guard: Reject updates if elevated to Blotter
    if (incident.is_blotter || incident.status === 'Elevated to Blotter' || incident.status === 'ELEVATED') {
      return res.status(403).json({
        ok: false,
        error: `Record is an official Blotter case (${incident.blotter_docket_no || 'Elevated'}). Edits must be made directly in the Blotter Records module.`,
      });
    }

    // 3. Update Incident Record
    await pool.query(
      `UPDATE incidents
       SET incident_date = COALESCE($1, incident_date),
           time_reported = COALESCE($2, time_reported),
           location = COALESCE($3, location),
           category = COALESCE($4, category),
           priority = COALESCE($5, priority),
           description = COALESCE($6, description),
           reporter = COALESCE($7, reporter),
           is_non_resident = COALESCE($8, is_non_resident),
           reporter_resident_id = $9,
           reporter_address = COALESCE($10, reporter_address),
           officer = COALESCE($11, officer),
           status = COALESCE($12, status),
           zone_id = COALESCE($13, zone_id),
           lat = COALESCE($14, lat),
           lng = COALESCE($15, lng),
           updated_at = NOW()
       WHERE id = $16`,
      [
        date,
        timeReported,
        location,
        category,
        priority,
        description,
        reporter,
        Boolean(isNonResident),
        isNonResident ? null : (reporterResidentId || null),
        reporterAddress,
        officer,
        status,
        zone,
        lat || null,
        lng || null,
        incidentId,
      ]
    );

    return res.status(200).json({
      ok: true,
      message: 'Incident report updated successfully.',
    });
  } catch (err) {
    console.error('[incidentController] Update error:', err);
    return res.status(500).json({ ok: false, error: err.message });
  }
}

module.exports = {
  updateIncident,
};
