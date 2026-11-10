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

# ----------------------------------------------------------------------------- themes
# Three looks. Series hues keep their meaning (raw blue, DWT orange, MODWT green) in every theme;
# only the shade changes so each stays readable on its background.
SANS = "'Inter','Segoe UI',system-ui,sans-serif"
THEMES = {
    "Midnight": dict(dark=True, bg="#121826", panel="#1B2438", panel2="#222D45", border="#2F3C57", text="#E9EEF7",
                     muted="#A3AEC2", accent="#3DDCB0", accent_ink="#0B1A16", head_bg="#0E1422", head_text="#E9EEF7",
                     hero="linear-gradient(135deg,#1B2438 0%,#17324A 100%)", font=SANS, hfont=SANS,
                     RAW="#6AA8F0", DWT="#F5A04A", MODWT="#3DDCB0", PAPER="#F47C70", GREY="#8E9AB0", ACTUAL="#B9C2D3",
                     DIST=("#7DB4EA", "#F47C70", "#86DB92")),
    "Daylight": dict(dark=False, bg="#F4F7FB", panel="#FFFFFF", panel2="#EEF2F8", border="#D6DEEA", text="#18202E",
                     muted="#5A6679", accent="#0E8F6D", accent_ink="#FFFFFF", head_bg="#FFFFFF", head_text="#18202E",
                     hero="linear-gradient(135deg,#FFFFFF 0%,#E4F1FA 100%)", font=SANS, hfont=SANS,
                     RAW="#2A68B5", DWT="#D2690F", MODWT="#0B8A67", PAPER="#D13F3F", GREY="#6B7587", ACTUAL="#7C879A",
                     DIST=("#2A68B5", "#D13F3F", "#2E9B55")),
    "Executive": dict(dark=False, bg="#F6F1E7", panel="#FFFCF5", panel2="#EFE7D6", border="#D9CDB4", text="#1C2A3E",
                      muted="#5F6B7C", accent="#1F4E79", accent_ink="#FFFFFF", head_bg="#FFFCF5", head_text="#1C2A3E",
                      hero="linear-gradient(120deg,#1C2A3E 0%,#2A4466 100%)", font=SANS,
                      hfont="Georgia,'Times New Roman',serif", hero_text="#F6F1E7",
                      RAW="#1F5C9E", DWT="#C2610A", MODWT="#12795C", PAPER="#B83A36", GREY="#6A7384", ACTUAL="#7A8497",
                      DIST=("#1F5C9E", "#B83A36", "#3C8A4F")),
}
THEME_NAMES = list(THEMES)
RAW = DWT = MODWT = PAPER = GREY = ACTUAL = GRID = BG = PANEL = TEXT = ""
PIPE_COLOURS = {}
DIST_COLOURS = {}
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


def theme() -> dict:
    try:
        return THEMES[st.session_state.get("theme_name", "Midnight")]
    except Exception:  # noqa: BLE001  (outside a Streamlit session)
        return THEMES["Midnight"]


def apply_theme(name: str) -> dict:
    """Point the module palette (C.RAW, C.TEXT, ...) at the chosen theme; views read these at call time."""
    t = THEMES[name]
    g = globals()
    for k in ("RAW", "DWT", "MODWT", "PAPER", "GREY", "ACTUAL"):
        g[k] = t[k]
    g["BG"], g["PANEL"], g["TEXT"], g["GRID"] = t["bg"], t["panel"], t["text"], t["border"]
    PIPE_COLOURS.update(raw=t["RAW"], dwt=t["DWT"], modwt=t["MODWT"])
    DIST_COLOURS.update(gaussian=t["DIST"][0], student_t=t["DIST"][1], ged=t["DIST"][2])
    return t


apply_theme("Midnight")


def css(t: dict) -> str:
    inv = "" if t["dark"] else ("[data-testid='stDataFrame'] {filter: invert(0.9) hue-rotate(180deg)%s;}" % (" sepia(0.3)" if "hero_text" in t else ""))
    ht = t.get("hero_text", t["text"])
    chip_bg = "rgba(255,255,255,0.08)" if "hero_text" in t else t["panel"]
    chip_tx = ht if "hero_text" in t else t["muted"]
    shadow = 0.35 if t["dark"] else 0.08
    return f"""<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{background:{t['bg']};color:{t['text']};font-family:{t['font']}}}
[data-testid="stHeader"] {{background:{t['head_bg']};border-bottom:1px solid {t['border']}}}
[data-testid="stHeader"] a, [data-testid="stHeader"] button, [data-testid="stHeader"] span, [data-testid="stHeader"] p {{color:{t['head_text']}}}
[data-testid="stSidebar"] {{background:{t['panel']};border-right:1px solid {t['border']}}}
.stApp p, .stApp li, .stApp label, .stApp span, .stApp div[data-testid="stMarkdownContainer"], .stApp td, .stApp th {{color:{t['text']}}}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{color:{t['text']};font-family:{t['hfont']};letter-spacing:-0.01em}}
.stApp [data-testid="stCaptionContainer"], .stApp small {{color:{t['muted']}}}
.block-container {{padding-top:4.6rem;max-width:1400px}}
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div, textarea, [data-baseweb="textarea"]
  {{background:{t['panel']} !important;border-color:{t['border']} !important;color:{t['text']} !important}}
input, textarea {{color:{t['text']} !important;-webkit-text-fill-color:{t['text']} !important;background:{t['panel']} !important;caret-color:{t['text']}}}
input::placeholder, textarea::placeholder {{color:{t['muted']} !important;-webkit-text-fill-color:{t['muted']} !important;opacity:1}}
[data-baseweb="input"] *, [data-baseweb="base-input"] *, [data-baseweb="select"] *, [data-testid="stTextInput"] div, [data-testid="stNumberInput"] div, [data-testid="stSelectbox"] div, [data-testid="stMultiSelect"] div[data-baseweb="select"] div
  {{background-color:{t['panel']};color:{t['text']}}}
[data-baseweb="select"], [data-baseweb="select"] > div {{background:{t['panel']} !important;border:1px solid {t['border']} !important;border-radius:8px;box-shadow:none !important}}
[data-testid="stMultiSelect"] div, [data-testid="stSelectbox"] div, [data-testid="stTextInput"] div, [data-testid="stNumberInput"] div, [data-testid="stTextArea"] div, [data-testid="stDateInput"] div {{background-color:{t['panel']} !important;color:{t['text']}}}
[data-baseweb="tag"], [data-baseweb="tag"] * {{background-color:{t['panel2']} !important;color:{t['text']} !important}}
[data-baseweb="select"] svg, [data-testid="stNumberInput"] svg, [data-testid="stTextInput"] svg {{fill:{t['muted']};color:{t['muted']}}}
[data-testid="stNumberInput"] button {{background:{t['panel2']} !important;color:{t['text']} !important;border-color:{t['border']} !important}}
[data-testid="stFileUploaderDropzone"], [data-testid="stCode"], [data-testid="stCode"] pre, [data-testid="stTable"] table, [data-testid="stJson"], [data-testid="stToolbar"], [data-testid="stBottom"] > div
  {{background:{t['panel']} !important;color:{t['text']} !important;border-color:{t['border']} !important}}
[data-baseweb="tooltip"] *, [data-testid="stTooltipContent"], [data-baseweb="popover"] *, [role="listbox"] *, [role="option"] {{background-color:{t['panel']};color:{t['text']}}}
[role="option"]:hover, [role="option"][aria-selected="true"] {{background-color:{t['panel2']} !important}}
[data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"], [data-testid="stSliderThumbValue"] {{color:{t['text']} !important;background:transparent !important}}
[data-testid="stRadio"] label p, [data-testid="stCheckbox"] label p, [data-testid="stWidgetLabel"] p {{color:{t['text']} !important}}
details summary, details summary * {{background:transparent !important;color:{t['text']}}}
[data-baseweb="popover"] > div, [data-baseweb="menu"], ul[role="listbox"] {{background:{t['panel']} !important;color:{t['text']}}}
[data-baseweb="menu"] li:hover, ul[role="listbox"] li:hover {{background:{t['panel2']} !important}}
[data-baseweb="tag"] {{background:{t['panel2']} !important}}
.stButton button, .stDownloadButton button, [data-testid="stPageLink"] a {{background:{t['panel']};color:{t['text']};border:1px solid {t['border']};border-radius:8px}}
.stButton button:hover, .stDownloadButton button:hover {{border-color:{t['accent']};color:{t['accent']}}}
button[data-variant="segmented_control"] {{background:{t['panel']} !important;border:1px solid {t['border']} !important}}
button[data-variant="segmented_control"] p {{color:{t['text']}}}
button[data-variant="segmented_control"][aria-checked="true"] {{background:{t['accent']} !important;border-color:{t['accent']} !important}}
button[data-variant="segmented_control"][aria-checked="true"] p {{color:{t['accent_ink']} !important}}
[data-baseweb="tab-list"] {{border-bottom:1px solid {t['border']}}}
[data-baseweb="tab"] {{color:{t['muted']} !important}}
[data-baseweb="tab"][aria-selected="true"] {{color:{t['accent']} !important}}
[data-baseweb="tab-highlight"] {{background:{t['accent']} !important}}
[data-testid="stExpander"] details {{background:{t['panel']};border:1px solid {t['border']};border-radius:10px}}
[data-testid="stExpander"] summary:hover {{color:{t['accent']}}}
div[data-testid="stMetric"] {{background:{t['panel']};border:1px solid {t['border']};border-radius:10px;padding:10px 14px}}
[data-testid="stAlert"] {{background:{t['panel2']};border:1px solid {t['border']}}}
pre, code {{background:{t['panel2']} !important;color:{t['text']} !important}}
[data-testid="stProgress"] [role="progressbar"] > div > div {{background:{t['accent']} !important}}
{inv}
.pill {{display:inline-block;padding:2px 10px;border-radius:12px;color:#fff !important;font-weight:600;font-size:0.85em;margin-right:4px}}
.note {{border-left:4px solid {t['GREY']};padding:8px 14px;margin:8px 0;background:{t['panel2']};border-radius:6px}}
.paper {{border-left:4px solid {t['PAPER']};padding:8px 14px;margin:8px 0;background:{t['panel2']};border-radius:6px}}
.ours {{border-left:4px solid {t['RAW']};padding:8px 14px;margin:8px 0;background:{t['panel2']};border-radius:6px}}
.howto {{padding:8px 14px;margin:6px 0 14px 0;background:{t['panel']};border:1px solid {t['border']};border-left:4px solid {t['MODWT']};border-radius:6px;font-size:0.95em}}
.hero {{padding:24px 28px;border:1px solid {t['border']};border-radius:14px;background:{t['hero']};margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,{shadow})}}
.hero, .hero p, .hero span, .hero div {{color:{ht}}}
.hero h1 {{margin:0 0 6px 0;color:{ht};font-family:{t['hfont']}}}
.chip {{display:inline-block;padding:2px 10px;border:1px solid {t['border']};border-radius:999px;margin:2px 4px 2px 0;font-size:0.82em;color:{chip_tx};background:{chip_bg}}}
</style>"""


CLIPS = APP / "media" / "clips"
CLIP_TITLES = {
    "s01": "Calm and storms: volatility clustering", "s02": "Title card",
    "s03": "Returns and the forecasting target", "s04": "Fat tails",
    "s05": "The mean model and the ARCH test", "s06": "GARCH(1,1)",
    "s07": "Wavelets: DWT versus MODWT", "s08": "From wavelet forecasts back to returns",
    "s09": "The paper", "s10": "Our replication design", "s11": "Core results",
    "s12": "Extension 1: heavier tails", "s13": "Extension 1 results",
    "s14": "Extension 2: parallel models and ensembles", "s15": "Extension 3: a small neural network",
    "s16": "Lessons and future work", "s17": "End card",
}


def setup(title: str, icon=None):
    """Page config (once), theme switcher, themed styling and the result-run selector. Safe to call from the router or standalone."""
    try:
        st.set_page_config(page_title=f"{title} | Wavelet GARCH", page_icon=icon, layout="wide")
    except Exception:  # noqa: BLE001  (already set by the router)
        pass
    cur = st.session_state.get("theme_name", "Midnight")
    _, tc = st.columns([5, 3])
    pick = tc.segmented_control("Theme", THEME_NAMES, key="theme_pick", default=cur, label_visibility="collapsed",
                                help="Switch the look of the whole app: Midnight (dark), Daylight (light) or Executive (warm paper).")
    name = pick or cur
    st.session_state["theme_name"] = name
    t = apply_theme(name)
    st.markdown(css(t), unsafe_allow_html=True)
    runs = available_runs()
    with st.sidebar:
        if len(runs) > 1:
            if "data_root" not in st.session_state:
                st.session_state["data_root"] = DEFAULT_RUN
            st.selectbox("Result run", list(runs), format_func=runs.get, key="data_root")
        st.caption("DA-3041 Group 9, IIT Guwahati. Reported results are produced by the R code in this repository "
                   "(run " + read_text("results/RUN_ID.txt").strip() + ").")


def style_fig(fig, height=None):
    """Plotly look that follows the active theme."""
    t = theme()
    fig.update_layout(template="plotly_dark" if t["dark"] else "plotly_white", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(color=t["text"]), legend=dict(bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(gridcolor=t["border"], zerolinecolor=t["border"])
    fig.update_yaxes(gridcolor=t["border"], zerolinecolor=t["border"])
    if height:
        fig.update_layout(height=height)
    return fig


def show(fig, howto: str | None = None, **kw):
    """Render a Plotly figure with the dark style and an optional 'How to read this' note underneath."""
    kw.setdefault("theme", None)
    st.plotly_chart(style_fig(fig), width="stretch", **kw)
    if howto:
        how_to(howto)


def how_to(text: str):
    st.markdown(f'<div class="howto"><b>How to read this.</b> {text}</div>', unsafe_allow_html=True)


def clip(key: str, caption: str | None = None, expanded: bool = False, label: str | None = None):
    """Embed a short narrated 3Blue1Brown-style lesson clip (with captions) inside an expander."""
    f = CLIPS / f"{key}.mp4"
    if not f.exists():
        return
    vtt = CLIPS / f"{key}.vtt"
    with st.expander(f"Watch: {label or CLIP_TITLES[key]}", expanded=expanded, icon=":material/play_circle:"):
        try:
            st.video(str(f), subtitles=str(vtt) if vtt.exists() else None)
        except TypeError:
            st.video(str(f))
        if caption:
            st.caption(caption)


MICRO = APP / "media" / "micro"
MICRO_TITLES = {
    "proof_target": "Proof: why the target is a noisy proxy",
    "proof_garch_uncond": "Proof: GARCH(1,1) long-run variance and half-life",
    "proof_ll_gaussian": "Proof: Gaussian log-likelihood",
    "effect_gaussian_sigma": "Effect of the variance on the Gaussian likelihood",
    "proof_aic": "Proof idea: AIC and BIC",
    "proof_ll_student_t": "Proof: Student-t log-likelihood",
    "effect_student_nu": "Effect of the degrees of freedom ν",
    "proof_ll_ged": "Proof: GED log-likelihood",
    "effect_ged_shape": "Effect of the GED shape",
    "proof_haar_recon": "Proof: Haar filters, energy and reconstruction",
    "proof_ensemble": "Proof: why an ensemble cannot be worse than its average member",
}


def micro(*keys: str, columns: bool = True):
    """Short narrated derivation clips with burned-in captions. Missing files are skipped quietly."""
    keys = [k for k in keys if (MICRO / f"{k}.mp4").exists()]
    if not keys:
        return
    cols = st.columns(len(keys)) if columns and len(keys) > 1 else [st.container() for _ in keys]
    for col, k in zip(cols, keys):
        with col:
            st.caption(f"**{MICRO_TITLES.get(k, k)}** · narrated, captions on screen")
            st.video(str(MICRO / f"{k}.mp4"), loop=True)


def download(df: pd.DataFrame, name: str, label: str = "Download CSV"):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=name, mime="text/csv",
                       key=f"dl_{name}_{label}")


def pills():
    return (f'<span class="pill" style="background:{RAW}">A: Raw</span>'
            f'<span class="pill" style="background:{DWT}">B: DWT</span>'
            f'<span class="pill" style="background:{MODWT}">C: MODWT</span>')


def note(text: str, kind: str = "note"):
    st.markdown(f'<div class="{kind}">{text}</div>', unsafe_allow_html=True)
