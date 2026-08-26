/**
 * frontend/public/js/heatmap.js
 * Heatmap Module: Dynamic Min-Max Quartile Zone Density Classification,
 * Dynamic Legend UI Range Injection, URL Parameter Deep-linking,
 * Alert Pulsing, Reactive 7-Zone Toolbar Filtering, and Permanent Centroid Labels
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
 * Official permanent zone label dictionary
 */
const OFFICIAL_ZONE_LABELS = {
  'Zone 1': 'Zone 1 - Residence 3',
  'Zone 2': 'Zone 2 - Residence 1',
  'Zone 3': 'Zone 3 - Pandi Village 2',
  'Zone 4': 'Zone 4 - Mitay 1',
  'Zone 5': 'Zone 5 - Sitio Gubat',
  'Zone 6': 'Zone 6 - Bangko St.',
  'Zone 7': 'Zone 7 - Barangka St.'
};

/**
 * Computes dynamic break intervals based on 4 equal steps (Min-Max / Quartiles)
 * from the active dataset's incident frequency across zones.
 *
 * @param {Object.<string, number>} [zoneCounts={}] - Map of incident count per zone
 * @returns {{ lowMax: number, medMax: number, elevMax: number, maxCount: number, minCount: number, step: number }}
 */
function computeDensityBreaks(zoneCounts = {}) {
  const counts = Object.values(zoneCounts || {})
    .map(Number)
    .filter(c => !isNaN(c) && c > 0);

  if (counts.length === 0) {
    return {
      lowMax: 0,
      medMax: 0,
      elevMax: 0,
      maxCount: 0,
      minCount: 0,
      step: 0
    };
  }

  const max = Math.max(...counts);
  const min = Math.min(...counts);
  const step = (max - min) / 4;

  return {
    lowMax: Math.round(min + step),
    medMax: Math.round(min + (step * 2)),
    elevMax: Math.round(min + (step * 3)),
    maxCount: max,
    minCount: min,
    step: step
  };
}

/**
 * Evaluates the dynamic zone classification color based on relative density breaks:
 * - High (Red): #EF4444 - Zone(s) with the highest incident volume (top range)
 * - Elevated (Orange): #F97316 - Upper-middle range nearing the high threshold
 * - Medium (Yellow): #F59E0B - Lower-middle range with moderate incidents
 * - Low (Green): #10B981 - Lowest non-zero range
 * - Zero / Inactive: 'transparent' - Zones with 0 incidents
 *
 * @param {number} count - Incident count for the zone
 * @param {Object} [breaks] - Output from computeDensityBreaks()
 * @returns {string} Hex color string or 'transparent'
 */
function getDynamicZoneColor(count, breaks = null) {
  const n = Number(count || 0);
  if (!n || n <= 0) return 'transparent';
  if (!breaks || breaks.maxCount === 0) return '#10B981';

  if (n > breaks.elevMax) return '#EF4444'; // High (Red) - pinakamarami
  if (n > breaks.medMax)  return '#F97316'; // Elevated (Orange) - malapit sa high
  if (n > breaks.lowMax)  return '#F59E0B'; // Medium (Yellow) - medyo marami
  return '#10B981';                             // Low (Green) - kaunti pa lang
}

/**
 * Calculates the dynamic density color for a specific zone ID.
 *
 * @param {string} zoneId - e.g. 'Zone 1'
 * @param {Object.<string, number>} [zoneCounts={}] - Map of incident count per zone
 * @param {Object} [breaks=null] - Optional precomputed breaks
 * @returns {string} Hex color string
 */
function getDensityColor(zoneId, zoneCounts = {}, breaks = null) {
  const count = Number(zoneCounts[zoneId] || 0);
  const b = breaks || computeDensityBreaks(zoneCounts);
  return getDynamicZoneColor(count, b);
}

/**
 * Dynamically updates the Heat Map Legend labels to display the calculated
 * range intervals based on the current dataset distribution.
 *
 * @param {Object} breaks - Output from computeDensityBreaks()
 */
function updateDynamicLegendUI(breaks) {
  const lowEl = document.getElementById('legendLowText');
  const medEl = document.getElementById('legendMedText');
  const eleEl = document.getElementById('legendEleText');
  const highEl = document.getElementById('legendHighText');

  if (lowEl) lowEl.textContent = 'Low';
  if (medEl) medEl.textContent = 'Medium';
  if (eleEl) eleEl.textContent = 'Elevated';
  if (highEl) highEl.textContent = 'High';
}

/**
 * Leaflet GeoJSON layer feature styling function using dynamic relative breaks.
 *
 * @param {Object} feature - GeoJSON feature object
 * @param {Object.<string, number>} [zoneCounts={}] - Map of incident count per zone
 * @param {Object} [breaks=null] - Precalculated density breaks
 * @returns {Object} Leaflet path style options
 */
function getDynamicZoneStyle(feature, zoneCounts = {}, breaks = null) {
  const zoneName = feature?.properties?.zone || feature?.properties?.zone_name || feature?.properties?.name;
  const count = Number(zoneCounts[zoneName] || 0);
  const calculatedBreaks = breaks || computeDensityBreaks(zoneCounts);
  const fillColor = getDynamicZoneColor(count, calculatedBreaks);
  const isZero = count === 0;

  return {
    fillColor: fillColor === 'transparent' ? '#10B981' : fillColor,
    fillOpacity: isZero ? 0.08 : 0.45,
    color: isZero ? '#94A3B8' : (fillColor === 'transparent' ? '#10B981' : fillColor),
    weight: isZero ? 1.5 : 2,
    dashArray: isZero ? '4, 4' : null,
    opacity: 0.85
  };
}

/**
 * Binds permanent centered zone labels to a Leaflet GeoJSON layer
 *
 * @param {L.GeoJSON} layer - Leaflet GeoJSON layer
 * @param {Object} [labelMap=OFFICIAL_ZONE_LABELS] - Dictionary mapping zone IDs to label strings
 */
function bindPermanentZoneLabels(layer, labelMap = OFFICIAL_ZONE_LABELS) {
  if (!layer || typeof layer.eachLayer !== 'function') return;

  layer.eachLayer((poly) => {
    const zoneId = poly.feature?.properties?.zone;
    const labelText = labelMap[zoneId] || (zoneId ? `${zoneId}` : 'Zone');

    poly.bindTooltip(labelText, {
      permanent: true,
      direction: 'center',
      className: 'zone-map-permanent-label',
      interactive: false
    });
  });
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
        color: baseColor === 'transparent' ? '#10B981' : baseColor,
        weight: 6,
        fillColor: baseColor === 'transparent' ? '#10B981' : baseColor,
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
          color: baseColor === 'transparent' ? '#94A3B8' : baseColor,
          weight: 2,
          fillColor: baseColor === 'transparent' ? '#10B981' : baseColor,
          fillOpacity: baseColor === 'transparent' ? 0.08 : 0.45,
          dashArray: baseColor === 'transparent' ? '4, 4' : null
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
    OFFICIAL_ZONE_LABELS,
    computeDensityBreaks,
    getDynamicZoneColor,
    getDensityColor,
    updateDynamicLegendUI,
    getDynamicZoneStyle,
    bindPermanentZoneLabels,
    initHeatmapDeepLink,
    filterIncidentList,
    paginateItems,
    initHeatmapToolbarListeners
  };
}
