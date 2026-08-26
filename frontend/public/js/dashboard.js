/**
 * frontend/public/js/dashboard.js
 * Cross-page notification handler and geospatial deep linking for BlotterCast Dashboard
 */

/**
 * Handles clicking a geospatial notification item, redirecting to the heatmap
 * with target zone, incident identifier, and active highlight flag.
 *
 * @param {Object} notif - Notification record from API.
 * @param {string} [notif.zone] - Zone name (e.g., 'Zone 1').
 * @param {string|number} [notif.incidentId] - Incident ID or reference code.
 * @param {string} [notif.title] - Notification title.
 * @param {string} [notif.body] - Notification body.
 */
function handleGeospatialNotificationClick(notif) {
  if (!notif) return;

  // Extract Zone Name
  let zoneName = notif.zone || '';
  if (!zoneName) {
    const zoneMatch = ((notif.title || '') + ' ' + (notif.body || '')).match(/(Zone\s*[1-7])/i);
    if (zoneMatch) zoneName = zoneMatch[1].replace(/Zone\s*/i, 'Zone ');
  }

  // Extract Incident Identifier
  let incidentId = notif.incidentId || notif.ref_id || '';
  if (!incidentId) {
    const codeMatch = ((notif.title || '') + ' ' + (notif.body || '')).match(/(INC-\d{4}-\d{2,6})/i);
    if (codeMatch) incidentId = codeMatch[1];
  }

  // Redirect to heatmap with URL query parameters
  const params = new URLSearchParams();
  if (zoneName) params.set('zone', zoneName);
  if (incidentId) params.set('incidentId', incidentId);
  params.set('highlight', 'true');

  window.location.href = `/heatmap.html?${params.toString()}`;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { handleGeospatialNotificationClick };
}
