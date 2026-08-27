"""
BlotterCast Database Seeder CLI Entrypoint
Delegates directly to app.seed.seed_data / app.seed.run
Run with:  python seed.py [--reset]
"""
import sys
from app.seed import run

if __name__ == "__main__":
    force_reset = any(arg in sys.argv for arg in ["--reset", "--force", "-f"])
    run(force_reset=force_reset)
