"""Run every page through streamlit.testing AppTest and report exceptions."""
import os, sys, time
from pathlib import Path
from streamlit.testing.v1 import AppTest
APP = Path(__file__).resolve().parents[1]
pages = ["Overview.py"] + sorted(str(p.relative_to(APP)) for p in (APP / "pages").glob("*.py"))
bad = 0
for p in pages:
    t = time.time()
    at = AppTest.from_file(str(APP / p), default_timeout=300)
    if os.environ.get("DATA_ROOT"):
        at.session_state["data_root"] = os.environ["DATA_ROOT"]
    at.run()
    exc = list(at.exception)
    errs = [e.value for e in at.error]
    print(f"{p}: {'OK' if not exc else 'EXCEPTION'} ({time.time()-t:.1f}s) errors={errs[:2]}")
    for e in exc:
        bad += 1
        print("   ", e.message, "\n", "\n".join(e.stack_trace[-6:]) if e.stack_trace else "")
sys.exit(1 if bad else 0)
