"""
Forward Geocoding & Boundary Geofencing Engine for Barangay Mapulang Lupa, Pandi, Bulacan.
Combines real-world OpenStreetMap Nominatim forward geocoding bounded by the barangay
viewport with an authentic local landmark gazetteer and strict polygon geofencing.
"""
import json
import os
import re
import urllib.parse
import urllib.request

# Load official Mapulang Lupa polygon boundary
_GEOJSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "mapulang-lupa.geojson")

_POLYGON_COORDS = []
if os.path.exists(_GEOJSON_PATH):
    try:
        with open(_GEOJSON_PATH, "r", encoding="utf-8") as f:
            _geo_data = json.load(f)
            if "geometry" in _geo_data and "coordinates" in _geo_data["geometry"]:
                _POLYGON_COORDS = _geo_data["geometry"]["coordinates"][0]
            elif "coordinates" in _geo_data:
                _POLYGON_COORDS = _geo_data["coordinates"][0]
    except Exception as e:
        print("Warning: Could not load GeoJSON boundary:", e)


def is_point_inside_boundary(lat: float | None, lng: float | None) -> bool:
    """Ray-casting point-in-polygon verification against Mapulang Lupa polygon coordinates [lng, lat]."""
    if lat is None or lng is None:
        return False
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return False

    if not _POLYGON_COORDS:
        # Bounding box fallback if geojson coords not loaded:
        return 14.875 <= lat <= 14.892 and 120.956 <= lng <= 120.972

    inside = False
    n = len(_POLYGON_COORDS)
    for i in range(n):
        j = (i - 1 + n) % n
        xi, yi = _POLYGON_COORDS[i][0], _POLYGON_COORDS[i][1]  # xi = lng, yi = lat
        xj, yj = _POLYGON_COORDS[j][0], _POLYGON_COORDS[j][1]  # xj = lng, yj = lat
        intersect = ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
    return inside


# Authentic local landmark, subdivision, and street gazetteer for Mapulang Lupa
LOCAL_GAZETTEER = [
    {
        "name": "Pandi Residences 1",
        "aliases": ["pandi residences 1", "pandi residence 1", "residence 1", "residences 1", "res 1", "res1"],
        "zone": "Zone 2",
        "lat": 14.881800,
        "lng": 120.960200,
    },
    {
        "name": "Pandi Residences 3",
        "aliases": ["pandi residences 3", "pandi residence 3", "residence 3", "residences 3", "res 3", "res3"],
        "zone": "Zone 1",
        "lat": 14.881000,
        "lng": 120.969500,
    },
    {
        "name": "Pandi Village 2 (Atlantica)",
        "aliases": ["pandi village 2", "pandi village", "atlantica", "pv2", "pv 2"],
        "zone": "Zone 3",
        "lat": 14.879500,
        "lng": 120.966800,
    },
    {
        "name": "Pandi Encampment One",
        "aliases": ["pandi encampment one", "pandi encamp one", "encampment one", "encamp one", "pandi encampment", "encampment"],
        "zone": "Zone 7",
        "lat": 14.885400,
        "lng": 120.961300,
    },
    {
        "name": "Mitay 1",
        "aliases": ["mitay 1", "mitay", "sitio mitay", "mitay uno"],
        "zone": "Zone 4",
        "lat": 14.883500,
        "lng": 120.964800,
    },
    {
        "name": "Sitio Gubat",
        "aliases": ["sitio gubat", "gubat", "purok gubat"],
        "zone": "Zone 5",
        "lat": 14.885800,
        "lng": 120.966500,
    },
    {
        "name": "Bangko St.",
        "aliases": ["bangko st", "bangko street", "bangko", "kalye bangko", "bangko lane"],
        "zone": "Zone 6",
        "lat": 14.884200,
        "lng": 120.962500,
    },
    {
        "name": "Barangka St.",
        "aliases": ["barangka st", "barangka street", "barangka", "kalye barangka"],
        "zone": "Zone 7",
        "lat": 14.885200,
        "lng": 120.964000,
    },
    {
        "name": "Mapulang Lupa Barangay Hall",
        "aliases": ["barangay hall", "brgy hall", "hall", "mapulang lupa hall"],
        "zone": "Zone 1",
        "lat": 14.883600,
        "lng": 120.965500,
    },
    {
        "name": "Mapulang Lupa Elementary School",
        "aliases": ["elementary school", "mapulang lupa elementary", "elem school", "es school"],
        "zone": "Zone 2",
        "lat": 14.880000,
        "lng": 120.963400,
    },
    {
        "name": "Sitio Bata",
        "aliases": ["sitio bata", "bata"],
        "zone": "Zone 3",
        "lat": 14.886300,
        "lng": 120.967900,
    },
    {
        "name": "Silangan Corridor",
        "aliases": ["silangan", "silangan corridor", "pandi-angat road", "pandi angat rd"],
        "zone": "Zone 5",
        "lat": 14.888400,
        "lng": 120.964000,
    },
]


def forward_geocode(location_text: str, zone_id: str = None) -> dict | None:
    """Forward geocodes an address string within Barangay Mapulang Lupa, Pandi, Bulacan.
    Returns dict(lat=float, lng=float, display_name=str, source=str) or None."""
    if not location_text:
        return None

    raw_text = str(location_text).strip()
    norm_text = raw_text.lower()

    # Reject obvious mock / test strings
    if len(norm_text) < 4:
        return None
    mock_keywords = ["test", "mock", "sample", "fake", "dummy", "sdada", "asdf", "qwe", "nanaman", "placeholder"]
    if any(kw in norm_text for kw in mock_keywords):
        return None

    # 1. Check local gazetteer for recognized landmarks / streets / subdivisions / encampments
    for entry in LOCAL_GAZETTEER:
        if entry["name"].lower() in norm_text or any(alias in norm_text for alias in entry["aliases"]):
            if is_point_inside_boundary(entry["lat"], entry["lng"]):
                return {
                    "lat": entry["lat"],
                    "lng": entry["lng"],
                    "display_name": f"{entry['name']}, Barangay Mapulang Lupa, Pandi, Bulacan",
                    "source": "local_gazetteer",
                }

    # 2. Query OpenStreetMap Nominatim with bounded viewbox
    # Viewbox coordinates for Mapulang Lupa / Pandi: min_lon, max_lat, max_lon, min_lat
    try:
        clean_loc = re.sub(r'^(zone\s*\d+[\s,:-]*)', '', raw_text, flags=re.IGNORECASE).strip()
        query = f"{clean_loc}, Mapulang Lupa, Pandi, Bulacan, Philippines"
        params = {
            "q": query,
            "format": "json",
            "limit": 3,
            "viewbox": "120.955,14.892,120.975,14.875",
            "bounded": 1,
        }
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "BlotterCast-Mapulang-Lupa/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                for item in data:
                    lat = float(item["lat"])
                    lng = float(item["lon"])
                    if is_point_inside_boundary(lat, lng):
                        return {
                            "lat": round(lat, 6),
                            "lng": round(lng, 6),
                            "display_name": item.get("display_name", clean_loc),
                            "source": "nominatim_geocoder",
                        }
    except Exception as e:
        # Nominatim network or rate limit failure: gracefully fall back
        pass

    # 3. Zone-based fallback if zone is authentic
    from .helpers import ZONE_LANDMARK_DEFINITIONS
    if zone_id and zone_id in ZONE_LANDMARK_DEFINITIONS:
        zinfo = ZONE_LANDMARK_DEFINITIONS[zone_id]
        if is_point_inside_boundary(zinfo["latitude"], zinfo["longitude"]):
            return {
                "lat": zinfo["latitude"],
                "lng": zinfo["longitude"],
                "display_name": f"{zinfo['name']} ({zone_id}), Barangay Mapulang Lupa, Pandi, Bulacan",
                "source": "zone_default",
            }

    return None
