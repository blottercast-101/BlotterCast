/**
 * frontend/public/js/heatmap.js
 * Heatmap Module: URL Parameter Deep-linking, Density Alert Pulsing,
 * Full-Width Toolbar, Real-time Search, and Reactive 7-Zone Filtering
 */

/**
 * Official 7-Zone mapping reference for Barangay Mapulang Lupa, Pandi, Bulacan
 */
const HEATMAP_OFFICIAL_ZONES = [
  { id: 'Zone 1', name: 'Residence 3 (Barangay Hall)', label: 'Zone 1 - Residence 3 (Barangay Hall)' },
  { id: 'Zone 2', name: 'Residence 1', label: 'Zone 2 - Residence 1' },
  { id: 'Zone 3', name: 'Pandi Village 2 (Atlantica)', label: 'Zone 3 - Pandi Village 2 (Atlantica)' },
  { id: 'Zone 4', name: 'Mitay 1', label: 'Zone 4 - Mitay 1' },
  { id: 'Zone 5', name: 'Sitio Gubat', label: 'Zone 5 - Sitio Gubat' },
  { id: 'Zone 6', name: 'Bangko St.', label: 'Zone 6 - Bangko St.' },
  { id: 'Zone 7', name: 'Barangka St.', label: 'Zone 7 - Barangka St.' }
];

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
 * temporary pulsing highlight on the target zone polygon layer or incident marker.
 *
 * @param {Object} options
 * @param {L.Map} options.map - Leaflet map instance
 * @param {Object.<string, L.Layer>} options.zonePolygonLayers - Map of Leaflet Polygon layers indexed by zoneId
 * @param {Object.<string, number>} [options.zoneCounts={}] - Map of incident counts per zone
 * @param {Function} [options.focusIncidentFn] - Optional callback to focus incident pin
 */
function initHeatmapDeepLink({ map, zonePolygonLayers = {}, zoneCounts = {}, focusIncidentFn = null } = {}) {
  const params = new URLSearchParams(window.location.search);
  const focusType = params.get('focus'); // 'marker'
  const targetZone = params.get('zone');
  const isHighlight = params.get('highlight') === 'true' || params.has('highlight');
  const incidentIdParam = params.get('incidentId') || (params.get('highlight') !== 'true' ? params.get('highlight') : null);
  const lat = parseFloat(params.get('lat'));
  const lng = parseFloat(params.get('lng'));

  // 1. Zone Polygon Highlighting & Pulsing
  if (targetZone && zonePolygonLayers[targetZone]) {
    const targetLayer = zonePolygonLayers[targetZone];
    const baseColor = getDensityColor(targetZone, zoneCounts);

    if (focusType !== 'marker' && (!lat || !lng)) {
      try {
        const bounds = targetLayer.getBounds();
        const center = bounds.getCenter();
        map.flyTo(center, 16, { animate: true, duration: 1.0 });
      } catch (e) {
        if (typeof map.fitBounds === 'function') {
          map.fitBounds(targetLayer.getBounds(), { padding: [30, 30], maxZoom: 16 });
        }
      }
    }

    if (isHighlight) {
      if (targetLayer._path) {
        targetLayer._path.classList.add('zone-pulse-active');
      }

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

  // 2. Incident Marker Direct Focus
  const numericId = incidentIdParam
    ? (parseInt(String(incidentIdParam).replace(/\D/g, ''), 10) || parseInt(incidentIdParam, 10))
    : null;

  if (numericId && typeof focusIncidentFn === 'function') {
    setTimeout(() => focusIncidentFn(numericId), 500);
  } else if (focusType === 'marker' && !isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
    map.flyTo([lat, lng], 17.5, { animate: true, duration: 1.2 });
  }
}

/**
 * Filters a list of incident objects based on search query, zone, and category
 * Matches both zone ID and full landmark label.
 *
 * @param {Array<Object>} incidents - Master incident list
 * @param {Object} filters
 * @param {string} [filters.query=''] - Search term
 * @param {string} [filters.zone='ALL'] - Selected zone
 * @param {string} [filters.category='ALL'] - Selected category
 * @returns {Array<Object>}
 */
function filterIncidentList(incidents = [], { query = '', zone = 'ALL', category = 'ALL' } = {}) {
  const q = String(query || '').toLowerCase().trim();
  const z = zone || 'ALL';
  const c = category || 'ALL';

  return incidents.filter(item => {
    if (z !== 'ALL') {
      const zoneKey = String(item.zone || '');
      if (zoneKey !== z && !z.startsWith(zoneKey) && !zoneKey.startsWith(z)) return false;
    }
    if (c !== 'ALL' && item.category !== c) return false;
    if (q) {
      const idStr = String(item.id || '').toLowerCase();
      const repNoStr = String(item.reportNo || item.report_no || '').toLowerCase();
      const locStr = String(item.location || '').toLowerCase();
      const descStr = String(item.description || '').toLowerCase();
      const repStr = String(item.reporter || '').toLowerCase();
      const catStr = String(item.category || '').toLowerCase();
      const zoneStr = String(item.zone || '').toLowerCase();

      const matches = idStr.includes(q) ||
                      repNoStr.includes(q) ||
                      locStr.includes(q) ||
                      descStr.includes(q) ||
                      repStr.includes(q) ||
                      catStr.includes(q) ||
                      zoneStr.includes(q);
      if (!matches) return false;
    }
    return true;
  });
}

/**
 * Returns a paginated slice of an array
 *
 * @param {Array} list - Array of items
 * @param {number} page - Current 1-based page number
 * @param {number} pageSize - Number of items per page
 * @returns {{ slice: Array, totalPages: number, totalItems: number, currentPage: number, startIndex: number, endIndex: number }}
 */
function paginateItems(list = [], page = 1, pageSize = 8) {
  const totalItems = list.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const currentPage = Math.max(1, Math.min(page, totalPages));
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);
  const slice = list.slice(startIndex, endIndex);

  return {
    slice,
    totalPages,
    totalItems,
    currentPage,
    startIndex,
    endIndex
  };
}

/**
 * Initializes reactive filter event bindings for the heatmap toolbar
 *
 * @param {Function} onFilterChange - Callback executed whenever query or dropdown filters update
 */
function initHeatmapToolbarListeners(onFilterChange) {
  if (typeof onFilterChange !== 'function') return;

  const searchInput = document.getElementById('heatmapSearchInput');
  const zoneFilter = document.getElementById('heatmapZoneFilter');
  const categoryFilter = document.getElementById('heatmapCategoryFilter');

  if (searchInput) searchInput.addEventListener('input', () => onFilterChange(true));
  if (zoneFilter) zoneFilter.addEventListener('change', () => onFilterChange(true));
  if (categoryFilter) categoryFilter.addEventListener('change', () => onFilterChange(true));
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    HEATMAP_OFFICIAL_ZONES,
    getDensityColor,
    initHeatmapDeepLink,
    filterIncidentList,
    paginateItems,
    initHeatmapToolbarListeners
  };
}
