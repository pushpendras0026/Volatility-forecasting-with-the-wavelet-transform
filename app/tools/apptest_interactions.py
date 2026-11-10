"""Exercise main widget combinations with AppTest (every architecture, lab run, periods, datasets)."""
import sys, time
from pathlib import Path
from streamlit.testing.v1 import AppTest
APP = Path(__file__).resolve().parents[1]
fails = []
def check(at, tag):
    if at.exception:
        fails.append((tag, at.exception[0].message)); print("FAIL", tag, at.exception[0].message)

# Architecture navigator: every family and model
at = AppTest.from_file(str(APP / "views/architecture.py"), default_timeout=300); at.run()
fams = at.selectbox[0].options
n = 0
for i, f in enumerate(fams):
    at.selectbox[0].select_index(i).run(); check(at, f)
    for j, m in enumerate(at.selectbox[1].options):
        at.selectbox[1].select_index(j).run(); check(at, f"{f}/{m}"); n += 1
print("architectures tested:", n)

# Concepts with each dataset
for ds in ["south_africa", "tunisia", "nigeria", "india_infosys", "usa_ibm", "google_class_a"]:
    at = AppTest.from_file(str(APP / "views/concepts.py"), default_timeout=300); at.run()
    at.sidebar.selectbox[0].select_index(["south_africa", "tunisia", "nigeria", "india_infosys", "usa_ibm", "google_class_a"].index(ds)).run(); check(at, f"concepts {ds}")
for ds in ["nigeria", "google_class_a"]:
    at = AppTest.from_file(str(APP / "Overview.py"), default_timeout=300); at.run()
    at.selectbox[0].select_index(["south_africa", "tunisia", "nigeria", "india_infosys", "usa_ibm", "google_class_a"].index(ds)).run(); check(at, f"home {ds}")

# Results explorer: later period, other datasets
at = AppTest.from_file(str(APP / "views/results.py"), default_timeout=300); at.run()
for r in at.radio:
    if "later" in r.options:
        r.set_value("later").run(); check(at, f"results radio {r.label} later")
for s in at.selectbox:
    if "usa_ibm" in s.options:
        s.set_value("usa_ibm").run(); check(at, f"results {s.label} ibm")

# Parameter lab: run a few short configurations
at = AppTest.from_file(str(APP / "views/lab.py"), default_timeout=600); at.run()
for tr, dist in [("raw", "gaussian"), ("modwt", "student_t"), ("dwt", "ged")]:
    t = time.time()
    at.slider[0].set_value(20)
    at.radio[0].set_value(tr); at.radio[1].set_value(dist)
    at.button[0].click().run(); check(at, f"lab {tr} {dist}")
    print(f"lab {tr}/{dist}: {time.time()-t:.1f}s, dataframes={len(at.dataframe)}")
at.selectbox[1].set_value("later"); at.selectbox[0].set_value("usa_ibm"); at.button[0].click().run(); check(at, "lab ibm later")
at.button[1].click().run() if len(at.button) > 1 else None; check(at, "simulator estimate")
print("FAILURES:", len(fails)); sys.exit(1 if fails else 0)
