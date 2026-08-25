/**
 * backend/controllers/importController.js
 * Comprehensive Import Controller for BlotterCast
 * Handles Route 1: Blotter Entry Record (Dual Insert to Incident + Blotter)
 * Handles Route 2: Blotter Record (Lookup & Upsert to Settlement Monitor)
 */

const fs = require('fs');
const path = require('path');
const xlsx = require('xlsx');
const { Pool } = require('pg');
const { getJitteredZoneCoordinates, extractZoneFromText } = require('../config/zones');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

/**
 * Normalizes raw and Tagalog nature terms to standard categories
 */
function normalizeNatureCategory(natureText = '') {
  const t = String(natureText).toLowerCase();
  if (/pag-aaway|suntukan|sakitan|pananakit|assault|physical|bugbog/i.test(t)) return 'Physical Assault';
  if (/nakawan|pagnanakaw|theft|robbery|hold-up|snatching|kupit/i.test(t)) return 'Theft';
  if (/alitan|awayan|kapitbahay|neighborhood\s*dispute|boundary\s*dispute/i.test(t)) return 'Neighborhood Dispute';
  if (/domestic|mag-asawa|pamilya|family\s*dispute|marital/i.test(t)) return 'Domestic Dispute';
  if (/paninira|vandalism|damage\s*to\s*property|sirang\s*gamit/i.test(t)) return 'Vandalism';
  if (/trespass|trespassing|pagpasok\s*nang\s*walang\s*paalam/i.test(t)) return 'Trespassing';
  if (/droga|drug|shabu|marijuana/i.test(t)) return 'Drug-Related Activity';
  if (/ingay|scandal|public\s*disturbance|kaguluhan|lasing/i.test(t)) return 'Public Disturbance';
  return 'Other';
}

/**
 * Normalizes settlement status strings
 */
function normalizeSettlementStatus(statusRaw = '') {
  const s = String(statusRaw).toUpperCase();
  if (s.includes('CFA') || s.includes('CERTIFICATE TO FILE') || s.includes('COURT')) return 'CFA Issued';
  if (s.includes('SETTLED') || s.includes('COMPLIED') || s.includes('RESOLVED')) return 'Settled';
  if (s.includes('NOT COMPLIED') || s.includes('FAILED')) return 'Not Complied';
  return 'Ongoing';
}

/**
 * Parses flexible dates into YYYY-MM-DD
 */
function parseFlexibleDate(dateVal) {
  if (!dateVal) return new Date().toISOString().slice(0, 10);
  if (typeof dateVal === 'number') {
    const excelEpoch = new Date(1899, 11, 30);
    return new Date(excelEpoch.getTime() + dateVal * 86400000).toISOString().slice(0, 10);
  }
  const d = new Date(String(dateVal).trim());
  return !isNaN(d.getTime()) ? d.toISOString().slice(0, 10) : new Date().toISOString().slice(0, 10);
}

/**
 * Reads tabular data from uploaded CSV or Excel sheet
 */
function readSheetRows(filePath) {
  const workbook = xlsx.readFile(filePath, { cellDates: false });
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  return xlsx.utils.sheet_to_json(worksheet, { header: 1, defval: '' });
}

/**
 * ROUTE 1: POST /api/import/blotter-entry
 * Blotter Entry Record: Dual Insert Transaction
 * 1. Insert into incident_reports (status: 'ELEVATED', zone centroid + jitter coordinates, normalized category)
 * 2. Insert into blotter_records (binds incident_id, stores docket_no, complainant, respondent)
 */
async function importBlotterEntry(req, res) {
  if (!req.file) {
    return res.status(400).json({ ok: false, error: 'No file uploaded.' });
  }

  const filePath = req.file.path;
  const client = await pool.connect();
  let importedCount = 0;
  let skippedCount = 0;

  try {
    const rawRows = readSheetRows(filePath);
    if (!rawRows || rawRows.length < 2) {
      return res.status(400).json({ ok: false, error: 'Sheet contains no data rows.' });
    }

    let headerIdx = rawRows.findIndex(row => {
      const s = row.map(c => String(c).toUpperCase()).join(' ');
      return s.includes('DOCKET') || s.includes('CASE NO') || s.includes('COMPLAINANT');
    });

    const headers = (headerIdx >= 0 ? rawRows[headerIdx] : rawRows[0]).map(h => String(h).trim().toUpperCase());
    const dataRows = rawRows.slice(headerIdx >= 0 ? headerIdx + 1 : 1);

    const getCol = (patterns) => headers.findIndex(h => patterns.some(p => h.includes(p)));
    const colDocket = getCol(['DOCKET', 'CASE NO', 'CASE_NO']);
    const colDate = getCol(['DATE FILED', 'DATE', 'INCIDENT DATE']);
    const colComplainant = getCol(['COMPLAINANT', 'NAME OF COMPLAINANT']);
    const colCompAddr = getCol(['COMPLAINANT ADDRESS', 'COMPLAINANT_ADDR', 'ADDRESS OF COMPLAINANT']);
    const colRespondent = getCol(['RESPONDENT', 'NAME OF RESPONDENT']);
    const colRespAddr = getCol(['RESPONDENT ADDRESS', 'RESPONDENT_ADDR', 'ADDRESS OF RESPONDENT']);
    const colNature = getCol(['NATURE OF CASE', 'NATURE', 'OFFENSE']);
    const colCaseType = getCol(['CRIM/CIVIL', 'CASE TYPE', 'TYPE']);
    const colZone = getCol(['ZONE', 'ZONE/ADDRESS']);

    await client.query('BEGIN');
    const currentYear = new Date().getFullYear();

    for (let i = 0; i < dataRows.length; i++) {
      const row = dataRows[i];
      if (!row || row.every(c => String(c).trim() === '')) {
        skippedCount++;
        continue;
      }

      const complainant = (colComplainant >= 0 ? String(row[colComplainant]).trim() : '') || 'Legacy Walk-In';
      const respondent = (colRespondent >= 0 ? String(row[colRespondent]).trim() : '') || 'Unspecified Respondent';
      const compAddr = colCompAddr >= 0 ? String(row[colCompAddr]).trim() : '';
      const respAddr = colRespAddr >= 0 ? String(row[colRespAddr]).trim() : '';
      const natureRaw = (colNature >= 0 ? String(row[colNature]).trim() : '') || 'Neighborhood Dispute';
      const category = normalizeNatureCategory(natureRaw);
      const incidentDate = parseFlexibleDate(colDate >= 0 ? row[colDate] : null);
      const rawCaseType = colCaseType >= 0 ? String(row[colCaseType]).trim() : '';
      const caseType = /crim/i.test(rawCaseType) ? 'CRIM' : (/civil/i.test(rawCaseType) ? 'CIVIL' : (/criminal/i.test(natureRaw) ? 'CRIM' : 'CIVIL'));

      const rawZoneText = colZone >= 0 ? String(row[colZone]).trim() : `${compAddr} ${respAddr}`;
      const zone = extractZoneFromText(rawZoneText);
      const { lat, lng } = getJitteredZoneCoordinates(zone, 0.0008);

      const seqSuffix = String(i + 1).padStart(4, '0');
      const customDocket = colDocket >= 0 ? String(row[colDocket]).trim() : '';
      const docketNo = customDocket || `BLT-LEGACY-${currentYear}-${seqSuffix}`;
      const reportNo = `INC-LEGACY-${currentYear}-${seqSuffix}`;

      // Step 1: Insert root incident_reports entry (ELEVATED + Geospatial Coordinates)
      const incRes = await client.query(
        `INSERT INTO incidents (
           report_no, incident_date, time_reported, hour, zone_id, location,
           lat, lng, category, description, reporter, reporter_address,
           is_non_resident, officer, priority, status, is_blotter, blotter_docket_no,
           created_at, updated_at
         ) VALUES (
           $1, $2, '19:00:00', 19, $3, $4,
           $5, $6, $7, $8, $9, $10,
           false, 'PO1 Legacy / Desk Officer', 'Medium', 'ELEVATED', true, $11,
           NOW(), NOW()
         ) RETURNING id`,
        [
          reportNo,
          incidentDate,
          zone,
          compAddr || 'Barangay Mapulang Lupa (Legacy Record)',
          lat,
          lng,
          category,
          natureRaw,
          complainant,
          compAddr,
          docketNo,
        ]
      );

      const sourceIncidentId = incRes.rows[0].id;

      // Step 2: Insert linked blotter_records entry
      await client.query(
        `INSERT INTO blotter_records (
           docket_no, date_filed, complainant, complainant_addr,
           respondent, respondent_addr, nature, case_type, status,
           zone_id, source_incident_id, created_at, updated_at
         ) VALUES (
           $1, $2, $3, $4,
           $5, $6, $7, $8, 'Ongoing',
           $9, $10, NOW(), NOW()
         )`,
        [
          docketNo,
          incidentDate,
          complainant,
          compAddr,
          respondent,
          respAddr,
          natureRaw,
          caseType,
          zone,
          sourceIncidentId,
        ]
      );

      importedCount++;
    }

    await client.query('COMMIT');

    return res.status(200).json({
      ok: true,
      importType: 'blotter-entry',
      message: `Successfully imported ${importedCount} Blotter Entry records with linked incident backfills.`,
      imported: importedCount,
      skipped: skippedCount,
    });
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('[importBlotterEntry] Error:', err);
    return res.status(500).json({ ok: false, error: err.message });
  } finally {
    client.release();
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
  }
}

/**
 * ROUTE 2: POST /api/import/blotter-settlement
 * Blotter Record: Lookup & Upsert into Settlement Monitor
 * 1. Query blotter_records by docket_no
 * 2. Upsert record into settlements referencing blotter_id
 */
async function importBlotterSettlement(req, res) {
  if (!req.file) {
    return res.status(400).json({ ok: false, error: 'No file uploaded.' });
  }

  const filePath = req.file.path;
  const client = await pool.connect();
  let updatedCount = 0;
  let skippedCount = 0;

  try {
    const rawRows = readSheetRows(filePath);
    if (!rawRows || rawRows.length < 2) {
      return res.status(400).json({ ok: false, error: 'Sheet contains no data rows.' });
    }

    let headerIdx = rawRows.findIndex(row => {
      const s = row.map(c => String(c).toUpperCase()).join(' ');
      return s.includes('DOCKET') || s.includes('HEARING') || s.includes('STAGE') || s.includes('SETTLEMENT');
    });

    const headers = (headerIdx >= 0 ? rawRows[headerIdx] : rawRows[0]).map(h => String(h).trim().toUpperCase());
    const dataRows = rawRows.slice(headerIdx >= 0 ? headerIdx + 1 : 1);

    const getCol = (patterns) => headers.findIndex(h => patterns.some(p => h.includes(p)));
    const colDocket = getCol(['DOCKET NO', 'DOCKET', 'CASE NO']);
    const colHearingDate = getCol(['HEARING DATE', 'DATE OF CONFRONTATION', 'CONFRONTATION DATE', 'DATE']);
    const colStage = getCol(['STAGE', 'PATAWAG', 'HEARING STAGE']);
    const colStatus = getCol(['SETTLEMENT STATUS', 'STATUS', 'ACTION TAKEN']);
    const colRemarks = getCol(['REMARKS', 'MAIN POINT', 'AGREEMENT']);

    if (colDocket < 0) {
      return res.status(400).json({ ok: false, error: 'Missing required "DOCKET NO." column header in template.' });
    }

    await client.query('BEGIN');
    const currentYear = new Date().getFullYear();

    for (let i = 0; i < dataRows.length; i++) {
      const row = dataRows[i];
      if (!row || row.every(c => String(c).trim() === '')) {
        skippedCount++;
        continue;
      }

      const docketNo = String(row[colDocket]).trim();
      if (!docketNo) {
        skippedCount++;
        continue;
      }

      // Step 1: Query blotter_records by docket_no
      const blotterRes = await client.query(
        `SELECT id, complainant, respondent, nature, case_type, date_filed FROM blotter_records WHERE docket_no = $1`,
        [docketNo]
      );

      let blotterId = null;
      let complainant = 'Complainant';
      let respondent = 'Respondent';
      let nature = 'Dispute';
      let caseType = 'CIVIL';
      let dateFiled = new Date().toISOString().slice(0, 10);

      if (blotterRes.rows.length > 0) {
        const bRow = blotterRes.rows[0];
        blotterId = bRow.id;
        complainant = bRow.complainant;
        respondent = bRow.respondent;
        nature = bRow.nature;
        caseType = bRow.case_type || 'CIVIL';
        dateFiled = bRow.date_filed;
      } else {
        // Fallback: Create placeholder blotter entry so settlement can link properly
        const insertBlotter = await client.query(
          `INSERT INTO blotter_records (
             docket_no, date_filed, complainant, respondent, nature, case_type, status, zone_id, created_at, updated_at
           ) VALUES ($1, CURRENT_DATE, 'Legacy Complainant', 'Legacy Respondent', 'Legacy Case', 'CIVIL', 'Ongoing', 'Zone 1', NOW(), NOW())
           RETURNING id`,
          [docketNo]
        );
        blotterId = insertBlotter.rows[0].id;
      }

      const hearingDate = parseFlexibleDate(colHearingDate >= 0 ? row[colHearingDate] : null);
      const stage = colStage >= 0 ? String(row[colStage]).trim() : '1st Patawag';
      const rawStatus = colStatus >= 0 ? String(row[colStatus]).trim() : 'Ongoing';
      const settlementStatus = normalizeSettlementStatus(rawStatus);
      const remarks = colRemarks >= 0 ? String(row[colRemarks]).trim() : '';

      // Step 2: Upsert into settlements table
      const stlCaseNo = `STL-${currentYear}-${String(i + 1).padStart(4, '0')}`;
      const existingStl = await client.query(`SELECT id FROM settlements WHERE blotter_id = $1`, [blotterId]);

      if (existingStl.rows.length > 0) {
        await client.query(
          `UPDATE settlements
           SET date_confrontation = $1,
               action_taken = $2,
               main_point = $3,
               status = $4,
               remarks = $5,
               updated_at = NOW()
           WHERE blotter_id = $6`,
          [
            hearingDate,
            stage,
            remarks || `Status: ${settlementStatus}`,
            settlementStatus === 'Settled' ? 'Complied' : 'Pending',
            remarks,
            blotterId,
          ]
        );
      } else {
        await client.query(
          `INSERT INTO settlements (
             blotter_id, case_no, case_title, complaint_title,
             nature, date_filed, date_confrontation, action_taken,
             main_point, status, remarks, created_at
           ) VALUES (
             $1, $2, $3, $4,
             $5, $6, $7, $8,
             $9, $10, $11, NOW()
           )`,
          [
            blotterId,
            stlCaseNo,
            `${complainant} vs ${respondent}`,
            nature,
            caseType === 'CRIM' ? 'Criminal' : 'Civil',
            dateFiled,
            hearingDate,
            stage,
            remarks || `Status: ${settlementStatus}`,
            settlementStatus === 'Settled' ? 'Complied' : 'Pending',
            remarks,
          ]
        );
      }

      // If settled or CFA issued, update blotter record status
      if (settlementStatus === 'Settled') {
        await client.query(`UPDATE blotter_records SET status = 'Resolved', updated_at = NOW() WHERE id = $1`, [blotterId]);
      } else if (settlementStatus === 'CFA Issued') {
        await client.query(`UPDATE blotter_records SET status = 'CFA Issued', updated_at = NOW() WHERE id = $1`, [blotterId]);
      }

      updatedCount++;
    }

    await client.query('COMMIT');

    return res.status(200).json({
      ok: true,
      importType: 'blotter-settlement',
      message: `Successfully processed ${updatedCount} Blotter Settlement records linked to the Settlement Monitor.`,
      updated: updatedCount,
      skipped: skippedCount,
    });
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('[importBlotterSettlement] Error:', err);
    return res.status(500).json({ ok: false, error: err.message });
  } finally {
    client.release();
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
  }
}

module.exports = {
  importBlotterEntry,
  importBlotterSettlement,
  normalizeNatureCategory,
  normalizeSettlementStatus,
};
