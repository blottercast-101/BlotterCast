/**
 * frontend/public/js/heatmap.js
 * Heatmap URL Parameter Listener and Temporary Density-Based Zone Pulsing Handler
 */

/**
 * Calculates the density color matching the zone incident frequency:
 * - High / Critical (>= 5 cases): #EF4444 (Red)
 * - Moderate (3 - 4 cases): #F59E0B (Amber / Yellow)
 * - Low (< 3 cases): #10B981 (Green)
 *
 * @param {string} zoneId - e.g. 'Zone 1'
 * @param {Object.<string, number>} [zoneCounts={}] - Map of incident count per zone
 * @returns {string} Hex color string
 */
function getDensityColor(zoneId, zoneCounts = {}) {
  const count = Number(zoneCounts[zoneId] || 0);
  if (count >= 5) return '#EF4444'; // High / Critical (>= 5 cases)
  if (count >= 3) return '#F59E0B'; // Moderate (3 - 4 cases)
  return '#10B981'; // Low (< 3 cases)
}

/**
 * Parses URL query parameters on page load and triggers focused map fly-to and
 * temporary pulsing highlight on the target zone polygon layer.
 *
 * @param {Object} options
 * @param {L.Map} options.map - Leaflet map instance
 * @param {Object.<string, L.Layer>} options.zonePolygonLayers - Map of Leaflet Polygon layers indexed by zoneId
 * @param {Object.<string, number>} [options.zoneCounts={}] - Map of incident counts per zone
 * @param {Function} [options.focusIncidentFn] - Optional callback to focus incident pin
 */
function initHeatmapDeepLink({ map, zonePolygonLayers = {}, zoneCounts = {}, focusIncidentFn = null } = {}) {
  const params = new URLSearchParams(window.location.search);
  const targetZone = params.get('zone');
  const isHighlight = params.get('highlight') === 'true' || params.has('highlight');
  const incidentIdParam = params.get('incidentId') || (params.get('highlight') !== 'true' ? params.get('highlight') : null);

  if (targetZone && zonePolygonLayers[targetZone]) {
    const targetLayer = zonePolygonLayers[targetZone];
    const baseColor = getDensityColor(targetZone, zoneCounts);

    // Center and fly map view to target zone polygon
    try {
      const bounds = targetLayer.getBounds();
      const center = bounds.getCenter();
      map.flyTo(center, 16, { animate: true, duration: 1.0 });
    } catch (e) {
      if (typeof map.fitBounds === 'function') {
        map.fitBounds(targetLayer.getBounds(), { padding: [30, 30], maxZoom: 16 });
      }
    }

    if (isHighlight) {
      // Add SVG pulsing animation class
      if (targetLayer._path) {
        targetLayer._path.classList.add('zone-pulse-active');
      }

      // Temporary active pulse styling
      targetLayer.setStyle({
        color: baseColor,
        weight: 6,
        fillColor: baseColor,
        fillOpacity: 0.55,
        dashArray: '6, 6'
      });

      if (typeof targetLayer.openTooltip === 'function') {
        targetLayer.openTooltip();
      }

      // Revert to standard density styling after 6 seconds
      setTimeout(() => {
        if (targetLayer._path) {
          targetLayer._path.classList.remove('zone-pulse-active');
        }
        targetLayer.setStyle({
          color: baseColor,
          weight: 3,
          fillColor: baseColor,
          fillOpacity: 0.25,
          dashArray: null
        });
      }, 6000);
    }
  }

  // If incident identifier was provided, focus marker pin
  if (incidentIdParam && typeof focusIncidentFn === 'function') {
    const numericId = parseInt(String(incidentIdParam).replace(/\D/g, ''), 10) || parseInt(incidentIdParam, 10);
    if (numericId) {
      setTimeout(() => focusIncidentFn(numericId), 600);
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { getDensityColor, initHeatmapDeepLink };
}
