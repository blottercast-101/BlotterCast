import os
import time

os.environ.setdefault("TZ", "Asia/Manila")
if hasattr(time, "tzset"):
    try:
        time.tzset()
    except Exception:
        pass

from app import create_app

app = create_app()

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
