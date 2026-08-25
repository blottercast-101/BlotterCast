/**
 * backend/controllers/importController.js
 * Clean ETL Import Controller with Legacy Column Mapping & Standard Fallbacks
 */

const { Pool } = require('pg');
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

// Official Barangay Mapulang Lupa Zone Centroid Fallbacks
const ZONE_CENTROIDS = {
  'Zone 1': { lat: 14.8812, lng: 120.9634 },
  'Zone 2': { lat: 14.8825, lng: 120.9648 },
  'Zone 3': { lat: 14.8841, lng: 120.9659 },
  'Zone 4': { lat: 14.8853, lng: 120.9672 },
  'Zone 5': { lat: 14.8867, lng: 120.9685 },
  'Zone 6': { lat: 14.8880, lng: 120.9698 },
  'Zone 7': { lat: 14.8894, lng: 120.9710 },
};

/**
 * Maps raw legacy nature text to standardized incident category
 */
function mapLegacyCategory(natureText = '') {
  const t = String(natureText).toLowerCase();
  if (/assault|physical|injury|pananakit|suntukan/i.test(t)) return 'Physical Assault';
  if (/theft|robbery|nakaw|pagnanakaw|hold-up/i.test(t)) return 'Theft';
  if (/dispute|domestic|away|mag-asawa|family/i.test(t)) return 'Domestic Dispute';
  if (/vandalism|damage|paninira/i.test(t)) return 'Vandalism';
  if (/trespass|trespassing|pagpasok/i.test(t)) return 'Trespassing';
  if (/drug|droga|shabu/i.test(t)) return 'Drug-Related Activity';
  if (/disturbance|public|ingay|kaguluhan/i.test(t)) return 'Public Disturbance';
  return 'Other';
}

/**
 * ETL Legacy Import Function: maps legacy CSV/Excel columns into
 * blotter_records and linked incident_reports with standard fallbacks.
 */
async function importLegacyBlotterRow(client, rawRow, index = 0) {
  const {
    caseNo,
    caseTitle,
    complaintTitle,
    natureOfCase,
    dateFiled,
    complainantName,
    respondentName,
    zone = 'Zone 1',
  } = rawRow;

  // 1. Resolve Complainant & Respondent
  const complainant = (complainantName || caseTitle?.split(/vs\.?/i)[0] || 'Legacy Walk-In').trim();
  const respondent = (respondentName || caseTitle?.split(/vs\.?/i)[1] || 'Unspecified Party').trim();
  const nature = (natureOfCase || complaintTitle || 'Legacy Blotter Case Record').trim();
  const category = mapLegacyCategory(nature);

  // 2. Resolve Centroid Coordinates
  const centroid = ZONE_CENTROIDS[zone] || ZONE_CENTROIDS['Zone 1'];

  // 3. Sequential Key Minting
  const docketNo = `BLT-${new Date().getFullYear()}-${String(index + 1).padStart(4, '0')}`;
  const reportNo = `INC-${new Date().getFullYear()}-${String(index + 1).padStart(4, '0')}`;

  // 4. Create Linked Incident Report (with standard fallback defaults)
  const incRes = await client.query(
    `INSERT INTO incidents (
       report_no, incident_date, time_reported, hour, zone_id, location,
       lat, lng, category, description, reporter, is_non_resident,
       officer, priority, status, is_blotter, blotter_docket_no, created_at
     ) VALUES (
       $1, COALESCE($2, CURRENT_DATE), '12:00:00', 12, $3, $4,
       $5, $6, $7, $8, $9, $10,
       $11, $12, $13, $14, $15, NOW()
     ) RETURNING id`,
    [
      reportNo,
      dateFiled || new Date().toISOString().slice(0, 10),
      zone,
      'Barangay Mapulang Lupa (Legacy Record)',
      centroid.lat,
      centroid.lng,
      category,
      nature,
      complainant,
      false, // Census resident / walk-in default
      'PO1 Legacy / Desk Officer',
      'Medium',
      'Elevated to Blotter',
      true,
      docketNo,
    ]
  );

  const incidentId = incRes.rows[0].id;

  // 5. Create Official Blotter Record (linked to incidentId)
  const blotterRes = await client.query(
    `INSERT INTO blotter_records (
       docket_no, date_filed, complainant, respondent, nature,
       case_type, status, zone_id, source_incident_id, created_at
     ) VALUES (
       $1, COALESCE($2, CURRENT_DATE), $3, $4, $5,
       $6, $7, $8, $9, NOW()
     ) RETURNING id`,
    [
      docketNo,
      dateFiled || new Date().toISOString().slice(0, 10),
      complainant,
      respondent,
      nature,
      /criminal/i.test(nature) ? 'CRIM' : 'CIVIL',
      'Ongoing',
      zone,
      incidentId,
    ]
  );

  return {
    blotterId: blotterRes.rows[0].id,
    incidentId,
    docketNo,
    reportNo,
  };
}

module.exports = {
  importLegacyBlotterRow,
  mapLegacyCategory,
  ZONE_CENTROIDS,
};
