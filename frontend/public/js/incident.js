/**
 * frontend/public/js/incident.js
 * Incident Reports module helper & "View in Heatmap" redirection handler
 */

let currentViewingIncident = null;

/**
 * Attaches or triggers the "View in Heatmap" action for the currently viewed incident.
 *
 * @param {Object} [incident] - Incident data object (defaults to currentViewingIncident)
 */
function openIncidentInHeatmap(incident) {
  const inc = incident || currentViewingIncident;
  if (!inc) return;

  const incidentId = inc.id || inc.report_no || inc.reportNo || '';
  const zone = inc.zone || inc.zone_id || '';
  const lat = inc.lat != null ? inc.lat : (inc.latitude != null ? inc.latitude : '');
  const lng = inc.lng != null ? inc.lng : (inc.longitude != null ? inc.longitude : '');

  const params = new URLSearchParams();
  if (incidentId) params.set('incidentId', incidentId);
  if (zone) params.set('zone', zone);
  if (lat) params.set('lat', lat);
  if (lng) params.set('lng', lng);
  params.set('focus', 'marker');
  params.set('highlight', 'true');

  window.location.href = `/heatmap.html?${params.toString()}`;
}

/**
 * Initializes the "View in Heatmap" button listener on DOM ready
 */
function initIncidentHeatmapShortcut() {
  const btn = document.getElementById('viewInHeatmapBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      openIncidentInHeatmap();
    });
  }
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initIncidentHeatmapShortcut);
  } else {
    initIncidentHeatmapShortcut();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { openIncidentInHeatmap, initIncidentHeatmapShortcut };
}
