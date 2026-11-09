"""Shared data access, labels, colours and small UI helpers.

Every number shown in the app's prose is read from a file under app/data through
these functions. See NUMBERS.md for the few constants that are written in prose.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

APP = Path(__file__).resolve().parents[1]
DATA = APP / "data"          # shared files (paper/, validation/)
# The final run (data_corrected/) is used whenever it is present.
DEFAULT_RUN = "data_corrected" if (APP / "data_corrected" / "results" / "RUN_ID.txt").exists() else "data"


def available_runs() -> dict:
    """Synced result sets: the final run bundled with the app."""
    out = {}
    for d in ([APP / DEFAULT_RUN] if (APP / DEFAULT_RUN / "results" / "RUN_ID.txt").exists() else [DATA]):
        if (d / "results" / "RUN_ID.txt").exists():
            info = dict(l.split("=", 1) for l in (d / "RUN_INFO.txt").read_text().splitlines() if "=" in l)                 if (d / "RUN_INFO.txt").exists() else {}
            out[d.name] = info.get("label", d.name) + " · run " + (d / "results" / "RUN_ID.txt").read_text().strip()
    return out


def active_root() -> Path:
    try:
        name = st.session_state.get("data_root", DEFAULT_RUN)
    except Exception:  # noqa: BLE001  (outside a Streamlit session)
        name = "data"
    root = APP / name
    return root if root.exists() else DATA


def path(rel: str) -> Path:
    """File in the selected run; falls back to app/data for files shared by all runs (paper/, validation/)."""
    p = active_root() / rel
    return p if p.exists() else DATA / rel

# Colour scheme shared by the report, slides and this application
RAW = "#1F5FA8"
DWT = "#D95F02"
MODWT = "#1B9E77"
PAPER = "#B8322A"
GREY = "#7F7F7F"
ACTUAL = "#9A9A9A"
PIPE_COLOURS = {"raw": RAW, "dwt": DWT, "modwt": MODWT}
DIST_COLOURS = {"gaussian": "#4C78A8", "student_t": "#E45756", "ged": "#54A24B"}
DIST_LABELS = {"gaussian": "Gaussian", "student_t": "Student-t", "ged": "GED"}

DATASETS = ["south_africa", "tunisia", "nigeria", "india_infosys", "usa_ibm", "google_class_a"]
STOCKS = ["india_infosys", "usa_ibm", "google_class_a"]
PERIOD_LABELS = {"validation": "Validation 2010-2011", "test": "Historical test 2012-2014",
                 "later": "Later stock evaluation 2015-2025"}


# ----------------------------------------------------------------------------- files
@st.cache_data(show_spinner=False)
def _read_csv(full: str, **kw) -> pd.DataFrame:
    return pd.read_csv(full, **kw)


def read_csv(rel: str, **kw) -> pd.DataFrame:
    return _read_csv(str(path(rel)), **kw).copy()


def read_text(rel: str) -> str:
    return path(rel).read_text(encoding="utf-8")


def manifest() -> pd.DataFrame:  # noqa: D401
    return read_csv("prices/manifest.csv")


def label(ds: str) -> str:
    m = manifest().set_index("dataset")["label"].to_dict()
    return m.get(ds, ds)


def ds_options(stocks_only: bool = False):
    return STOCKS if stocks_only else DATASETS


def config() -> dict:
    """Parse the R run's config.txt (dput output) for the scalar settings shown in prose."""
    txt = read_text("results/run/config.txt").replace("\n", " ")
    out = {}
    for key in ["mean_window", "max_window", "refit_every", "max_pq", "component_max_pq", "mlp_maxit", "seed"]:
        m = re.search(rf"\b{key} = (\d+)L", txt)
        if m:
            out[key] = int(m.group(1))
    m = re.search(r'criterion = "(\w+)"', txt)
    out["criterion"] = m.group(1) if m else "AIC"
    m = re.search(r"selection_min_coverage = ([\d.]+)", txt)
    out["selection_min_coverage"] = float(m.group(1)) if m else None
    for key in ["training", "validation", "test", "later"]:
        m = re.search(rf'{key} = c\("([\d-]+)",\s*"([\d-]+)"\)', txt)
        if m:
            out[key] = (m.group(1), m.group(2))
    for key in ["mlp_hidden", "mlp_decay", "mlp_seeds"]:
        m = re.search(rf"{key} = c\(([^)]*)\)", txt)
        if m:
            out[key] = [float(v.strip().rstrip("L")) for v in m.group(1).split(",")]
    m = re.search(r'filters = c\(([^)]*)\)', txt)
    out["filters"] = re.findall(r'"(\w+)"', m.group(1)) if m else []
    return out


def prices(ds: str) -> pd.DataFrame:
    p = read_csv(f"prices/{ds}.csv", parse_dates=["Date"])
    return p


def returns_and_target(ds: str, mean_window: int = 20) -> pd.DataFrame:
    return _returns_and_target(str(path(f"prices/{ds}.csv")), mean_window).copy()


@st.cache_data(show_spinner=False)
def _returns_and_target(price_file: str, mean_window: int) -> pd.DataFrame:
    """Same as R make_targets(): r = diff(log(Price)); y_i = (r_i - mean(r_{i-20..i-1}))^2."""
    p = pd.read_csv(price_file, parse_dates=["Date"])
    r = np.diff(np.log(p["Price"].to_numpy()))
    ma = pd.Series(r).rolling(mean_window).mean().shift(1).to_numpy()
    y = (r - ma) ** 2
    return pd.DataFrame({"Date": p["Date"].iloc[1:].to_numpy(), "r": r, "ma20": ma, "y": y})


def forecasts(ds: str, period: str) -> pd.DataFrame:
    """Saved per-origin R forecasts (slimmed). period: test | later | validation_core."""
    f = {"test": f"forecasts/test_{ds}.csv.gz", "later": f"forecasts/later_{ds}.csv.gz",
         "validation_core": f"forecasts/validation_core_{ds}.csv.gz"}[period]
    return _read_csv(str(path(f)), parse_dates=["target_date"])


def all_scores() -> pd.DataFrame:
    return read_csv("results/tables/all_model_scores.csv")


def model_catalogue() -> pd.DataFrame:
    """One row per model_id with family information (from a frozen registry)."""
    reg = read_csv("results/per_dataset/south_africa/frozen_registry.csv")
    return reg


def valid_mask(df: pd.DataFrame) -> pd.Series:
    """Port of R .valid_forecasts()."""
    ok = np.isfinite(df["actual"]) & np.isfinite(df["prediction"])
    st_ = df["fit_status"].astype(str).str.lower()
    bad = st_.str.contains("failed|failure|error|pending|skipped|timeout|iteration_limit|missing_member", regex=True)
    return ok & ~bad


def matched_scores(fc: pd.DataFrame, models: list[str]) -> tuple[pd.DataFrame, int]:
    """Score models on the dates where all of them produced valid forecasts."""
    sub = fc[fc.model_id.isin(models)].copy()
    sub = sub[valid_mask(sub)]
    dates = None
    for m in models:
        d = set(sub.loc[sub.model_id == m, "target_date"])
        dates = d if dates is None else dates & d
    dates = dates or set()
    sub = sub[sub.target_date.isin(dates)]
    rows = []
    for m in models:
        z = sub[sub.model_id == m]
        if len(z) == 0:
            rows.append(dict(model_id=m, n=0))
            continue
        e = z["actual"] - z["prediction"]
        tv = ((z["actual"] - z["actual"].mean()) ** 2).sum()
        rows.append(dict(model_id=m, n=len(z), MSE=(e ** 2).mean(), RMSE=np.sqrt((e ** 2).mean()),
                         MAE=e.abs().mean(), R2=1 - (e ** 2).sum() / tv if tv > 0 else np.nan))
    return pd.DataFrame(rows), len(dates)


# ----------------------------------------------------------------------------- names
FRIENDLY = {
    "naive": "Naive (yesterday's y)", "trailing_mean": "Trailing 20-day mean of y",
    "raw_arima": "Raw ARMA (no GARCH)", "dwt_arima": "DWT ARMA (no GARCH)", "modwt_arima": "MODWT ARMA (no GARCH)",
    "raw_garch": "Raw GARCH", "dwt_garch": "DWT-GARCH", "modwt_garch": "MODWT-GARCH",
    "raw_garch_student_t": "Raw GARCH, Student-t", "dwt_garch_student_t": "DWT-GARCH, Student-t",
    "modwt_garch_student_t": "MODWT-GARCH, Student-t",
    "modwt_garch_structural": "MODWT-GARCH, extra MA lag", "modwt_garch_structural_student_t": "MODWT-GARCH, extra MA lag, Student-t",
    "direct_y_arima": "Direct-target ARMA", "ensemble_base_only": "Base ensemble", "ensemble_all": "Combined ensemble",
    "ensemble_modwt": "MODWT ensemble", "mlp": "MLP seed 101", "mlp_seed202": "MLP seed 202", "mlp_seed303": "MLP seed 303",
}


def friendly(mid: str) -> str:
    if mid in FRIENDLY:
        return FRIENDLY[mid]
    m = re.match(r"mra_(dwt|modwt)_(haar|db4|db6)_(all_arima|mixed)(_j1)?$", mid)
    if m:
        alloc = "all-ARMA" if m.group(3) == "all_arima" else "mixed"
        return f"MRA {m.group(1).upper()} {m.group(2)} J={1 if m.group(4) else 2} {alloc}"
    m = re.match(r"(raw|dwt|modwt)_garch__(gaussian|student_t|ged)$", mid)
    if m:
        return f"{m.group(1).upper() if m.group(1) != 'raw' else 'Raw'} GARCH, {DIST_LABELS[m.group(2)]}"
    return mid


def model_colour(mid: str) -> str:
    if mid.startswith("raw"):
        return RAW
    if mid.startswith("dwt") or mid.startswith("mra_dwt"):
        return DWT
    if mid.startswith("modwt") or mid.startswith("mra_modwt") or mid == "ensemble_modwt":
        return MODWT
    return GREY


# ----------------------------------------------------------------------------- format
def sci(x, digits=3) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:.{digits}g}"


def pct(x, digits=2, sign=True) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    return f"{x:+.{digits}f}%" if sign else f"{x:.{digits}f}%"


def setup(title: str, icon=None):
    st.set_page_config(page_title=f"{title} | Wavelet GARCH", page_icon=icon, layout="wide")
    st.markdown(
        """<style>
        .pill {display:inline-block;padding:2px 10px;border-radius:12px;color:white;font-size:0.85em;margin-right:4px}
        .note {border-left:4px solid #888;padding:6px 12px;margin:8px 0;background:rgba(127,127,127,0.08);border-radius:4px}
        .paper {border-left:4px solid #B8322A;padding:6px 12px;margin:8px 0;background:rgba(184,50,42,0.07);border-radius:4px}
        .ours {border-left:4px solid #1F5FA8;padding:6px 12px;margin:8px 0;background:rgba(31,95,168,0.07);border-radius:4px}
        </style>""",
        unsafe_allow_html=True,
    )
    runs = available_runs()
    with st.sidebar:
        if len(runs) > 1:
            if "data_root" not in st.session_state:
                st.session_state["data_root"] = DEFAULT_RUN
            st.selectbox("Result run", list(runs), format_func=runs.get, key="data_root")
        st.caption("DA-3041 Group 9, IIT Guwahati. Reported results are produced by the R code in this repository "
                   "(run " + read_text("results/RUN_ID.txt").strip() + ").")


def pills():
    return (f'<span class="pill" style="background:{RAW}">A: Raw</span>'
            f'<span class="pill" style="background:{DWT}">B: DWT</span>'
            f'<span class="pill" style="background:{MODWT}">C: MODWT</span>')


def note(text: str, kind: str = "note"):
    st.markdown(f'<div class="{kind}">{text}</div>', unsafe_allow_html=True)
