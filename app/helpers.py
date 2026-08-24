import random
from datetime import date, datetime, time

from .extensions import db
from .models import Zone, CensusRecord


def next_seq_no(model, column_name: str, prefix: str, digits: int = 3) -> str:
    """Next sequential number for the year, e.g. next_seq_no(Incident, 'report_no',
    'INC', 4) -> 'INC-2026-0007'. Based on the highest existing number for the
    prefix+year (not a row count), then guarded against collisions."""
    year = datetime.utcnow().year
    like = f"{prefix}-{year}-%"
    column = getattr(model, column_name)
    row = (
        model.query.filter(column.like(like))
        .order_by(column.desc())
        .first()
    )
    n = 1
    if row:
        existing = getattr(row, column_name)
        n = int(existing.split("-")[-1]) + 1

    while True:
        candidate = f"{prefix}-{year}-{n:0{digits}d}"
        exists = model.query.filter(column == candidate).first()
        if not exists:
            return candidate
        n += 1


def next_ctrl_no(model, prefix: str) -> str:
    return next_seq_no(model, "ctrl_no", prefix, digits=3)


def next_or_no() -> str:
    """OR number is shared across the three fee-based document tables (they draw
    from the same treasurer's receipt booklet)."""
    from .models import BarangayClearance, BarangayResidency, BarangayNonResidency

    or_tables = [BarangayClearance, BarangayResidency, BarangayNonResidency]
    year = datetime.utcnow().year
    like = f"OR-{year}-%"
    n = 1
    for model in or_tables:
        row = model.query.filter(model.or_no.like(like)).order_by(model.or_no.desc()).first()
        if row and row.or_no:
            candidate_n = int(row.or_no.split("-")[-1]) + 1
            n = max(n, candidate_n)

    while True:
        candidate = f"OR-{year}-{n:03d}"
        taken = any(model.query.filter(model.or_no == candidate).first() for model in or_tables)
        if not taken:
            return candidate
        n += 1


ZONE_LANDMARK_DEFINITIONS = {
    "Zone 1": {
        "name": "Residence 3",
        "aliases": ["residence 3", "residences 3", "pandi residences 3", "pandi residence 3", "res 3", "res3"],
        "latitude": 14.883760,
        "longitude": 120.968420,
    },
    "Zone 2": {
        "name": "Residence 1",
        "aliases": ["residence 1", "residences 1", "pandi residences 1", "pandi residence 1", "res 1", "res1", "pasong kalabaw", "kalabaw st"],
        "latitude": 14.882000,
        "longitude": 120.958000,
    },
    "Zone 3": {
        "name": "Pandi Village 2 (Atlantica)",
        "aliases": ["pandi village 2", "pandi village", "atlantica", "pv2", "pv 2"],
        "latitude": 14.879000,
        "longitude": 120.972000,
    },
    "Zone 4": {
        "name": "Mitay 1",
        "aliases": ["mitay 1", "mitay", "sitio mitay", "pandi village 1"],
        "latitude": 14.887500,
        "longitude": 120.962000,
    },
    "Zone 5": {
        "name": "Sitio Gubat",
        "aliases": ["sitio gubat", "gubat", "purok gubat", "barangay center", "mapulang lupa center"],
        "latitude": 14.882500,
        "longitude": 120.964500,
    },
    "Zone 6": {
        "name": "Bangko St.",
        "aliases": ["bangko st", "bangko street", "bangko"],
        "latitude": 14.877500,
        "longitude": 120.966500,
    },
    "Zone 7": {
        "name": "Barangka St.",
        "aliases": ["barangka st", "barangka street", "barangka", "pandi-angat road", "pandi angat"],
        "latitude": 14.878500,
        "longitude": 120.959500,
    },
}


def resolve_coordinates_by_zone_and_text(zone_id: str, location_detail: str) -> tuple[float | None, float | None]:
    """Resolves geographic coordinates when an address includes block/lot or phase details
    along with a recognized zone landmark name or alias (e.g. 'Ph1 Blk24 Lot 4 Residence 1')."""
    if not zone_id or not location_detail:
        return None, None

    normalized = str(location_detail).lower().strip()
    zone_info = ZONE_LANDMARK_DEFINITIONS.get(zone_id)
    if not zone_info:
        return None, None

    if zone_info["name"].lower() in normalized:
        return zone_info["latitude"], zone_info["longitude"]

    for alias in zone_info.get("aliases", []):
        if alias.lower() in normalized:
            return zone_info["latitude"], zone_info["longitude"]

    return None, None


def zone_coords(zone_id: str):
    """Returns the exact geographic coordinates tied to the specified zone."""
    zone = Zone.query.get(zone_id)
    if not zone:
        return 14.883, 120.965  # barangay centroid fallback
    return round(float(zone.lat), 6), round(float(zone.lng), 6)


def compute_age(dob) -> int | None:
    """Age in whole years as of today, from a date (or ISO string). None if
    dob is empty or in the future."""
    if not dob:
        return None
    if isinstance(dob, str):
        try:
            dob = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            return None
    today = date.today()
    if dob > today:
        return None
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return years


def is_name_a_census_resident(name: str) -> bool:
    name = (name or "").strip()
    if not name:
        return False
    name_lower = name.lower()
    residents = CensusRecord.query.with_entities(CensusRecord.last_name, CensusRecord.first_name).all()
    return any(r.last_name.lower() in name_lower and r.first_name.lower() in name_lower for r in residents)


def find_census_resident_id_by_name(name: str) -> int | None:
    """Same tolerant match as is_name_a_census_resident(), but returns the resident's
    id only when there's exactly one match — ambiguous matches are left unlinked."""
    name = (name or "").strip()
    if not name:
        return None
    name_lower = name.lower()
    residents = CensusRecord.query.with_entities(
        CensusRecord.id, CensusRecord.last_name, CensusRecord.first_name
    ).all()
    matches = [
        r.id for r in residents
        if r.last_name.lower() in name_lower and r.first_name.lower() in name_lower
    ]
    return matches[0] if len(matches) == 1 else None


def parse_date(value):
    """Accepts a 'YYYY-MM-DD' string, a date/datetime, or None/'' -> date|None.
    SQLite (unlike MySQL/Postgres) requires real Python date objects, not strings."""
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value):
    """Accepts 'HH:MM', 'HH:MM:SS', 'hh:mm AM/PM', a datetime.time object, or None/'' -> time|None."""
    if value in (None, ""):
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        v = value.strip()
        for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p", "%I:%M%p", "%I:%M:%S%p"):
            try:
                return datetime.strptime(v, fmt).time()
            except ValueError:
                pass
    return None


def full_name_of(resident: CensusRecord) -> str:
    return f"{resident.last_name}, {resident.first_name} {resident.middle_name or ''}".strip()
