/**
 * frontend/public/js/incident.js
 * Incident Reports module helper, Geocoding, Jurisdiction Validation & "View in Heatmap" redirection
 */

// Pre-loaded Mapulang Lupa boundary polygon vertices [lat, lng]
const MAPULANG_LUPA_BOUNDARY = [
  [14.882500, 120.953500],
  [14.884500, 120.953500],
  [14.887500, 120.955500],
  [14.889500, 120.957000],
  [14.891800, 120.958500],
  [14.892500, 120.959200],
  [14.891500, 120.963500],
  [14.890000, 120.966000],
  [14.888500, 120.967500],
  [14.887500, 120.970000],
  [14.886800, 120.971500],
  [14.885800, 120.973000],
  [14.885200, 120.977500],
  [14.884500, 120.980500],
  [14.882500, 120.981000],
  [14.881000, 120.979000],
  [14.879500, 120.978500],
  [14.877800, 120.977200],
  [14.876500, 120.976800],
  [14.874000, 120.976000],
  [14.872500, 120.975200],
  [14.871500, 120.973500],
  [14.872000, 120.970000],
  [14.873200, 120.967000],
  [14.874500, 120.965000],
  [14.873800, 120.964000],
  [14.874500, 120.961000],
  [14.876000, 120.958000],
  [14.877000, 120.955500],
  [14.878000, 120.954000],
  [14.879500, 120.953500],
  [14.880500, 120.953000],
  [14.881500, 120.952500],
  [14.882500, 120.953500]
];

let currentViewingIncident = null;
let cachedBoundaryGeojson = null;

/**
 * Ray-casting point-in-polygon algorithm
 * @param {number[]} point - [lat, lng]
 * @param {number[][]} vs - Array of [lat, lng] vertices
 * @returns {boolean}
 */
function isPointInPolygon(point, vs) {
  const x = point[0], y = point[1];
  let inside = false;
  for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
    const xi = vs[i][0], yi = vs[i][1];
    const xj = vs[j][0], yj = vs[j][1];
    const intersect = ((yi > y) !== (yj > y)) &&
                      (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

/**
 * Validates whether a coordinate point falls inside Barangay Mapulang Lupa jurisdiction.
 * Updates the UI status badges, error banners, and save button enablement state.
 *
 * @param {number|string} lat - Latitude
 * @param {number|string} lng - Longitude
 * @returns {{ inBounds: boolean, lat: number, lng: number }}
 */
function validateJurisdiction(lat, lng) {
  const numLat = parseFloat(lat);
  const numLng = parseFloat(lng);

  if (isNaN(numLat) || isNaN(numLng) || (numLat === 0 && numLng === 0)) {
    updateJurisdictionUI(false, null, null, 'Unverified Location');
    return { inBounds: false, lat: 0, lng: 0 };
  }

  // 1. Ray-casting verification using predefined vertices
  let inBounds = isPointInPolygon([numLat, numLng], MAPULANG_LUPA_BOUNDARY);

  // 2. Turf GeoJSON validation fallback if boundary is loaded
  if (!inBounds && cachedBoundaryGeojson && typeof turf !== 'undefined') {
    try {
      const pt = turf.point([numLng, numLat]);
      if (turf.booleanPointInPolygon(pt, cachedBoundaryGeojson)) {
        inBounds = true;
      }
    } catch (e) {}
  }

  updateJurisdictionUI(inBounds, numLat, numLng);
  return { inBounds, lat: numLat, lng: numLng };
}

/**
 * Single-source updater for jurisdiction UI elements
 */
function updateJurisdictionUI(inBounds, lat, lng, customMsg = null) {
  const badge = document.getElementById('if_geoBadge');
  const wideGeoBadge = document.getElementById('wideGeoBadge');
  const preview = document.getElementById('if_coordsPreview');
  const wideCoordsPreview = document.getElementById('wideCoordsPreview');
  const boundaryBanner = document.getElementById('if_boundaryErrorBanner');
  const saveBtn = document.getElementById('btnSaveIncident');

  if (lat == null || lng == null) {
    const cls = 'text-[11px] font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200';
    if (badge) { badge.className = cls; badge.textContent = customMsg || '⚪ Unverified Location'; }
    if (wideGeoBadge) { wideGeoBadge.className = cls; wideGeoBadge.textContent = customMsg || '⚪ Unverified Location'; }
    if (preview) preview.textContent = 'Lat: --, Lng: --';
    if (wideCoordsPreview) wideCoordsPreview.textContent = 'Lat: --, Lng: --';
    if (boundaryBanner) boundaryBanner.classList.add('hidden');
    if (saveBtn) { saveBtn.classList.add('opacity-75'); saveBtn.title = 'Location must be verified within Barangay boundary before saving.'; }
    return;
  }

  const coordsStr = `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`;
  if (preview) preview.textContent = coordsStr;
  if (wideCoordsPreview) wideCoordsPreview.textContent = coordsStr;

  if (inBounds) {
    const cls = 'text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200';
    if (badge) { badge.className = cls; badge.textContent = '✓ Inside Boundary'; }
    if (wideGeoBadge) { wideGeoBadge.className = cls; wideGeoBadge.textContent = '✓ Inside Boundary'; }
    if (boundaryBanner) boundaryBanner.classList.add('hidden');
    if (saveBtn) { saveBtn.classList.remove('opacity-75'); saveBtn.removeAttribute('title'); }
  } else {
    const cls = 'text-[11px] font-semibold px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200';
    if (badge) { badge.className = cls; badge.textContent = '⚠️ Outside Boundary / Non-Jurisdiction'; }
    if (wideGeoBadge) { wideGeoBadge.className = cls; wideGeoBadge.textContent = '⚠️ Outside Boundary'; }
    if (boundaryBanner) boundaryBanner.classList.remove('hidden');
    if (saveBtn) { saveBtn.classList.add('opacity-75'); saveBtn.title = 'Location is outside Barangay jurisdiction.'; }
  }
}

/**
 * Handles address geocoding with strict asynchronous sequence to eliminate race conditions
 */
async function handleGeocodeLocation() {
  const locInput = document.getElementById('if_location');
  const zoneInput = document.getElementById('if_zone');
  const loc = locInput ? locInput.value.trim() : '';
  const zone = zoneInput ? zoneInput.value : '';

  if (!loc && !zone) {
    if (typeof showToast === 'function') showToast('Please type a location or select a zone first.', 'error');
    return;
  }

  const btn = document.getElementById('btnGeocode');
  if (btn) btn.innerHTML = '<span data-icon="loader" class="animate-spin" data-icon-size="12"></span> Locating…';

  try {
    // 1. Fetch geocoding response
    const res = await fetch(`/api/records.php?type=geocode&q=${encodeURIComponent(loc)}&zone=${encodeURIComponent(zone)}`, { credentials: 'same-origin' });
    const data = await res.json();

    if (data && data.ok && data.lat && data.lng) {
      const lat = parseFloat(data.lat);
      const lng = parseFloat(data.lng);

      // 2. Update coordinates on Leaflet mini-map & input fields FIRST
      if (typeof setPickerCoordinates === 'function') {
        if (typeof showPickerMap === 'function') showPickerMap();
        setPickerCoordinates(lat, lng, true);
      } else {
        const latInput = document.getElementById('if_lat');
        const lngInput = document.getElementById('if_lng');
        if (latInput) latInput.value = lat.toFixed(6);
        if (lngInput) lngInput.value = lng.toFixed(6);
      }

      // 3. Validate jurisdiction AFTER coordinates are assigned
      const result = validateJurisdiction(lat, lng);

      // 4. Feedback toast notification
      if (typeof showToast === 'function') {
        if (result.inBounds) {
          showToast(`Located: ${data.display_name || loc}`, 'success');
        } else {
          showToast('Location is outside Barangay Mapulang Lupa. Incident cannot be filed outside barangay jurisdiction.', 'error');
        }
      }
    } else {
      updateJurisdictionUI(false, null, null, '❌ Invalid Location');
      if (typeof showToast === 'function') {
        showToast(data?.message || 'Location could not be geocoded within Barangay Mapulang Lupa boundary.', 'error');
      }
    }
  } catch (err) {
    console.error('Geocoding error:', err);
    if (typeof showToast === 'function') showToast('Geocoding request failed.', 'error');
  } finally {
    if (btn) btn.innerHTML = '<span data-icon="search" data-icon-size="12"></span> Geocode Location';
    if (window.lucide && typeof lucide.createIcons === 'function') lucide.createIcons();
  }
}

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
  module.exports = {
    MAPULANG_LUPA_BOUNDARY,
    isPointInPolygon,
    validateJurisdiction,
    handleGeocodeLocation,
    openIncidentInHeatmap,
    initIncidentHeatmapShortcut
  };
}
