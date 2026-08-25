"""One-off: seed enough incident history so ml/service.py has >=60 rows
and enough lag/rolling history (30-day warmup per zone) to actually train
and produce a hotspot forecast."""
import random
from datetime import date, timedelta, time as dtime

from app import create_app
from app.extensions import db
from app.models import Incident

random.seed(42)

CATEGORIES = ['Physical Assault', 'Theft', 'Domestic Dispute', 'Vandalism',
              'Trespassing', 'Drug-Related Activity', 'Public Disturbance', 'Other']
ZONES = [f"Zone {i}" for i in range(1, 8)]
ZONE_WEIGHTS = [0.22, 0.13, 0.20, 0.08, 0.12, 0.07, 0.18]

app = create_app()
with app.app_context():
    start = date.today() - timedelta(days=150)
    n = 0
    seq = 1
    for d_off in range(150):
        d = start + timedelta(days=d_off)
        # a handful of incidents most days, skewed by zone weight
        for _ in range(random.choices([0, 1, 2, 3], weights=[15, 45, 30, 10])[0]):
            zone = random.choices(ZONES, weights=ZONE_WEIGHTS)[0]
            hour = random.choices(range(24), weights=[1]*6 + [2]*6 + [3]*6 + [4]*6)[0]
            cat = random.choices(CATEGORIES, weights=[15, 20, 15, 10, 10, 8, 15, 7])[0]
            inc = Incident(
                report_no=f"INC-SEED-{seq:05d}",
                incident_date=d,
                time_reported=dtime(hour=hour, minute=0),
                hour=hour,
                zone_id=zone,
                location="Synthetic seed data",
                category=cat,
                description="Synthetic seed record for ML training test",
                reporter="Seed Script",
                officer="admin",
                priority=random.choice(["Low", "Medium", "High"]),
                status=random.choice(["Resolved", "Under Investigation", "Filed"]),
            )
            db.session.add(inc)
            seq += 1
            n += 1
    db.session.commit()
    print(f"Inserted {n} synthetic incidents across {len(ZONES)} zones over 150 days.")
