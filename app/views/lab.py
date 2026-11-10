"""Parameter lab: Python re-implementation of the core pipelines on real data, plus a GARCH simulator."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ on the path when run standalone

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from lib import common as C
from lib import reimpl as R

C.setup("Parameter lab")
cfg = C.config()
st.title("Parameter lab")
st.warning("**This is a Python re-implementation for exploration. The reported results come from the R code** (`R/`). "
           "It follows the R pipeline step by step; its agreement with the saved R forecasts is shown at the bottom of the "
           "first tab and in `VALIDATION.md`.")

tab_run, tab_sim = st.tabs(["Rolling forecasts on real data", "GARCH simulator"])

PERIODS = {"validation": ("validation", "Validation 2010-2011"), "test": ("test", "Historical test 2012-2014"),
           "later": ("later", "Later 2015-2025 (stocks)")}


@st.cache_data(show_spinner=False, max_entries=64)
def run_lab(ds, period, start_offset, n, transform, p, q, dist, window, cadence, root=""):
    D = C.returns_and_target(ds, cfg["mean_window"])
    dates = D.Date.to_numpy()
    lo, hi = cfg[period]
    idx = np.where((D.Date >= lo) & (D.Date <= hi) & np.isfinite(D.y))[0]
    idx = idx[start_offset: start_offset + n]
    res = R.rolling_forecast(dates, D.r.to_numpy(), list(idx), transform, p, q, dist, window, cadence, cfg["mean_window"])
    return pd.DataFrame(res.rows), pd.DataFrame(res.refits)


@st.cache_data(show_spinner=False, max_entries=32)
def aic_order(ds, period, start_offset, transform, window, max_pq):
    D = C.returns_and_target(ds, cfg["mean_window"])
    lo, _ = cfg[period]
    i0 = np.where(D.Date >= lo)[0][start_offset]
    x = R.transform_input(D.r.to_numpy()[:i0][-window:], transform)
    p, q, rows = R.select_arma(x, max_pq)
    return p, q, pd.DataFrame(rows)


with tab_run:
    with st.form("lab"):
        c1, c2, c3, c4 = st.columns(4)
        ds = c1.selectbox("Dataset", C.DATASETS, format_func=C.label)
        period = c2.selectbox("Period", ["test", "validation", "later"], format_func=lambda k: PERIODS[k][1])
        n = c3.slider("Forecast days (test length)", 20, 250, 60, 10,
                      help="Each day needs one Kalman refilter (~0.01 s); each refit one ARMA + GARCH fit (~1 s).")
        start_offset = c4.number_input("Start at day # of the period", 0, 2000, 0, 20)
        c1, c2, c3, c4 = st.columns(4)
        transform = c1.radio("Transform", ["raw", "dwt", "modwt"], format_func=lambda t: {"raw": "A: raw", "dwt": "B: paired DWT",
                                                                                           "modwt": "C: MODWT"}[t])
        dist = c2.radio("Innovation distribution", ["gaussian", "student_t", "ged"], format_func=C.DIST_LABELS.get)
        window = c3.select_slider("Rolling window (returns)", [256, 512, 768, 1024, 1536], value=cfg["max_window"])
        cadence = c4.select_slider("Refit every (days)", [1, 5, 10, 20, 40, 60], value=cfg["refit_every"])
        c1, c2, c3 = st.columns(3)
        order_mode = c1.radio("ARMA order", ["R frozen order (from initial_orders.csv)", "manual", "choose by AIC now (slow, ~16 fits)"])
        mp = c2.number_input("p (manual)", 0, 5, 1)
        mq = c3.number_input("q (manual)", 0, 5, 1)
        go_ = st.form_submit_button("Run rolling forecasts", type="primary")

    if ds not in C.STOCKS and period == "later":
        st.error("The 2015-2025 period exists only for the three stocks.")
        st.stop()
    rid = {"raw": "raw_garch", "dwt": "dwt_garch", "modwt": "modwt_garch"}[transform]
    io = C.read_csv(f"results/per_dataset/{ds}/initial_orders.csv")
    rp, rq = io[(io.model_id == rid) & (io.component == "x")][["p", "q"]].iloc[0].astype(int)
    if order_mode.startswith("R frozen"):
        p, q = rp, rq
    elif order_mode == "manual":
        p, q = int(mp), int(mq)
    else:
        if go_:
            with st.spinner("Fitting 16 ARMA candidates on the window before the first forecast..."):
                p, q, grid = aic_order(ds, period, int(start_offset), transform, window, 3)
            st.session_state["aic"] = (p, q, grid)
        p, q = st.session_state.get("aic", (rp, rq, None))[:2]
    st.caption(f"Using ARMA({p},{q}). The R run froze ARMA({rp},{rq}) for {C.friendly(rid)} on {C.label(ds)}.")

    if go_ or st.session_state.get("lab_ran"):
        st.session_state["lab_ran"] = True
        try:
            with st.spinner("Fitting and forecasting (cached after the first run)..."):
                out, refits = run_lab(ds, period, int(start_offset), int(n), transform, int(p), int(q), dist, int(window), int(cadence), str(C.active_root()))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Run failed: {exc}")
            st.stop()
        if out.empty:
            st.error("No forecast dates in that range. Reduce the start offset.")
            st.stop()
        out["target_date"] = pd.to_datetime(out.target_date)
        # Saved R forecasts for comparison (same dates)
        rmodel = rid + ("_student_t" if dist == "student_t" else "")
        rf = None
        if period in ("test", "later") and dist != "ged":
            fc = C.forecasts(ds, period)
            rf = fc[(fc.model_id == rmodel) & fc.target_date.isin(out.target_date)]
        elif period in ("test", "later") and dist == "ged":
            try:
                g = pd.read_csv(C.path(f"distribution/forecasts/{ds}_{rid}_{period}.csv.gz"), parse_dates=["target_date"])
                rf = g[(g.model_id == rid + "__ged") & g.target_date.isin(out.target_date)]
            except FileNotFoundError:
                rf = None
        same = (p, q) == (rp, rq) and window == cfg["max_window"] and cadence == cfg["refit_every"]
        tm = C.returns_and_target(ds, cfg["mean_window"])
        trailing = tm.y.shift(1).rolling(20).mean()
        tmap = dict(zip(tm.Date, trailing))
        out["trailing_mean"] = out.target_date.map(tmap)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=out.target_date, y=out.actual * 1e4, name="actual y", line=dict(color=C.ACTUAL, width=1)))
        fig.add_trace(go.Scatter(x=out.target_date, y=out.prediction * 1e4, name="Python forecast",
                                 line=dict(color=C.PIPE_COLOURS[transform], width=2)))
        if rf is not None and len(rf):
            fig.add_trace(go.Scatter(x=rf.target_date, y=rf.prediction * 1e4, name=f"saved R: {C.friendly(rf.model_id.iloc[0])}",
                                     line=dict(color=C.TEXT, width=1, dash="dot")))
        rd = out[out.refitted]
        fig.add_trace(go.Scatter(x=rd.target_date, y=np.zeros(len(rd)), mode="markers", name="refit days",
                                 marker=dict(symbol="triangle-up", color=C.PAPER, size=8)))
        fig.update_layout(height=400, yaxis_title="y × 1e4", legend=dict(orientation="h"), margin=dict(l=10, r=10, t=10, b=10))
        C.show(fig, howto='Grey is the actual target; coloured lines are forecasts from this lab (and the saved R forecast when shown). Dots on the baseline mark refit days. The closer a line follows the grey peaks without overshooting, the better the forecast.')

        rows = [dict(forecast=f"Python {transform} ARMA({p},{q})-GARCH(1,1) {C.DIST_LABELS[dist]}", **R.metrics(out.actual, out.prediction)),
                dict(forecast="Trailing 20-day mean of y (baseline)", **R.metrics(out.actual, out.trailing_mean))]
        if rf is not None and len(rf):
            m = out.merge(rf[["target_date", "prediction"]], on="target_date", suffixes=("", "_R"))
            rows.append(dict(forecast=f"Saved R {rf.model_id.iloc[0]} (window {cfg['max_window']}, refit {cfg['refit_every']}, R order)",
                             **R.metrics(m.actual, m.prediction_R)))
        met = pd.DataFrame(rows)
        met["RMSE x1e4"] = met.RMSE * 1e4
        met["MAE x1e4"] = met.MAE * 1e4
        st.dataframe(met[["forecast", "n", "RMSE x1e4", "MAE x1e4", "R2", "MSE"]], hide_index=True, width="stretch")
        if rf is not None and len(rf):
            m = out.merge(rf[["target_date", "prediction"]], on="target_date", suffixes=("", "_R"))
            rel = (m.prediction / m.prediction_R - 1).abs()
            if same:
                st.success(f"Settings match the R run, so the two lines should nearly coincide: median |relative difference| "
                           f"{100 * rel.median():.3f}%, max {100 * rel.max():.2f}%. (R's refit dates can differ by a few days "
                           "because R's schedule continues from the validation period.)")
            else:
                st.info("Your settings differ from the R run (order, window or cadence), so the saved R line is a reference, "
                        "not an expected match.")
        fails = (out.fit_status != "ok").sum()
        if fails:
            st.warning(f"{fails} forecast(s) failed (optimiser did not converge); they are excluded from the metrics, like in R.")
        if len(refits):
            st.markdown("**Fitted GARCH parameters at each refit**")
            rr = refits.copy()
            rr["persistence α+β"] = rr.alpha + rr.beta
            figp = make_subplots(rows=1, cols=2, subplot_titles=("α and β", "persistence α+β"))
            figp.add_trace(go.Scatter(x=rr.target_date, y=rr.alpha, name="α", mode="lines+markers"), 1, 1)
            figp.add_trace(go.Scatter(x=rr.target_date, y=rr.beta, name="β", mode="lines+markers"), 1, 1)
            figp.add_trace(go.Scatter(x=rr.target_date, y=rr["persistence α+β"], name="α+β", mode="lines+markers"), 1, 2)
            figp.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
            C.show(figp, howto='Left: estimated α (reaction to shocks) and β (memory) at each refit. Right: persistence α+β; values near 1 mean volatility shocks fade very slowly.')
            st.dataframe(rr, hide_index=True, width="stretch")
        with st.expander("Per-day output (mean, variance, moving mean, forecast)"):
            st.dataframe(out, hide_index=True, width="stretch")

    st.markdown("---")
    st.markdown("### How close is this Python version to R? (comparison with the saved R forecasts)")
    vs = C.read_csv("validation/validation_summary.csv")
    st.dataframe(vs[["case", "arma", "first_date", "last_date", "n", "refits", "median_abs_rel_diff_pct", "max_abs_rel_diff_pct",
                     "corr", "MSE_diff_pct", "max_abs_alpha_diff", "max_abs_beta_diff"]]
                 .style.format({"median_abs_rel_diff_pct": "{:.3f}", "max_abs_rel_diff_pct": "{:.2f}", "corr": "{:.5f}",
                                "MSE_diff_pct": "{:+.3f}", "max_abs_alpha_diff": "{:.1e}", "max_abs_beta_diff": "{:.1e}"}),
                 hide_index=True, width="stretch")
    raw_med = vs[vs["transform"] == "raw"].median_abs_rel_diff_pct.max()
    st.markdown(f"Raw-return pipelines (Gaussian, Student-t, GED) agree with R to a median of at most **{raw_med:.3f}%** per forecast. "
                "MODWT and paired-DWT agree less closely and not uniformly. A likely reason is a flat ARMA likelihood (the Haar "
                "detail has an MA root at one; DWT has only ~511 points), where statsmodels and R's `arima` can stop at different "
                "coefficients. Generated by "
                "`tools/validate_against_r.py`; see `VALIDATION.md`.")
    vf = pd.read_csv(C.DATA / "validation" / "validation_forecasts.csv.gz", parse_dates=["target_date"])
    case = st.selectbox("Show a validation case", vs.case.tolist())
    z = vf[vf.case == case]
    figv = go.Figure()
    figv.add_trace(go.Scatter(x=z.target_date, y=z.prediction_R * 1e4, name="R (saved)", line=dict(color=C.TEXT)))
    figv.add_trace(go.Scatter(x=z.target_date, y=z.prediction_py * 1e4, name="Python", line=dict(color=C.DWT, dash="dash")))
    figv.update_layout(height=280, yaxis_title="forecast × 1e4", margin=dict(l=10, r=10, t=10, b=10))
    C.show(figv, howto='R (saved, white) against this Python re-implementation (dashed). Where the two overlap, the Python lab reproduces the R result; gaps show the approximation error documented in VALIDATION.md.')

# ============================================================================ simulator
with tab_sim:
    st.markdown("Simulate returns from a GARCH(1,1), then estimate a GARCH(1,1) back from the simulated data with the same "
                "MLE code. This shows clustering, fat tails created by GARCH itself, and how well parameters can be recovered.")
    c1, c2, c3, c4 = st.columns(4)
    om = c1.number_input("ω (× 1e-6)", 0.1, 100.0, 2.0, 0.1) * 1e-6
    al = c2.slider("α", 0.0, 0.4, 0.09, 0.01)
    be = c3.slider("β", 0.0, 0.99, 0.89, 0.01)
    nsim = c4.select_slider("length", [250, 500, 1000, 2000, 5000], 1000)
    c1, c2, c3 = st.columns(3)
    sdist = c1.radio("innovations", ["gaussian", "student_t", "ged"], format_func=C.DIST_LABELS.get, horizontal=True)
    shape = c2.slider("ν (Student-t) or b (GED)", 0.8, 30.0, 5.0, 0.1)
    seed = c3.number_input("seed", 1, 10_000, 42)
    if sdist == "student_t" and shape <= 2.05:
        st.error("Student-t needs ν > 2 for a finite variance.")
        st.stop()
    if al + be >= 1:
        st.warning(f"α+β = {al + be:.2f} ≥ 1: the variance has no long-run level and can explode.")
    e, h = R.simulate_garch(int(nsim), om, al, be, sdist, shape, int(seed))
    figs = make_subplots(rows=2, cols=2, subplot_titles=("simulated returns ε_t", "conditional volatility √h_t",
                                                         "histogram of ε/sd vs normal", "ACF: ε (blue) and ε² (orange)"),
                         vertical_spacing=0.15)
    figs.add_trace(go.Scatter(y=e, line=dict(color=C.GREY, width=0.7)), 1, 1)
    figs.add_trace(go.Scatter(y=np.sqrt(h), line=dict(color=C.RAW)), 1, 2)
    zz = e / e.std()
    figs.add_trace(go.Histogram(x=zz, histnorm="probability density", nbinsx=80, marker_color=C.RAW, opacity=0.6), 2, 1)
    xs = np.linspace(-6, 6, 200)
    figs.add_trace(go.Scatter(x=xs, y=np.exp(-xs ** 2 / 2) / math.sqrt(2 * math.pi), line=dict(color=C.PAPER)), 2, 1)

    def acf(x, k=20):
        x = x - x.mean()
        return [np.sum(x[i:] * x[:-i]) / np.sum(x * x) for i in range(1, k + 1)]

    figs.add_trace(go.Bar(x=list(range(1, 21)), y=acf(e), marker_color=C.RAW), 2, 2)
    figs.add_trace(go.Bar(x=list(range(1, 21)), y=acf(e ** 2), marker_color=C.DWT), 2, 2)
    figs.update_layout(height=560, showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
    C.show(figs, howto='Top-left: simulated returns. Top-right: the conditional volatility the model assigns each day (it rises after big moves). Bottom-left: histogram of the simulated returns against the normal bell curve (red); fatter tails show as bars outside the curve. Bottom-right: autocorrelation of returns (blue, near 0) and of squared returns (orange, persistent): the clustering signature.')
    kurt = float(np.mean(zz ** 4))
    st.markdown(f"Sample kurtosis of ε: **{kurt:.2f}** (normal = 3). Even Gaussian innovations give kurtosis above 3 when the variance "
                "changes over time: volatility clustering itself creates fat tails.")
    if st.button("Estimate GARCH(1,1) back from this sample"):
        cols = st.columns(3)
        for col, d in zip(cols, ["gaussian", "student_t", "ged"]):
            f = R.fit_garch11(e - e.mean(), d)
            col.markdown(f"**{C.DIST_LABELS[d]} likelihood**")
            col.write(pd.DataFrame({"true": [om, al, be], "estimated": [f.omega, f.alpha, f.beta]}, index=["ω", "α", "β"]))
            col.caption(f"log-lik {f.loglik:.1f}, AIC {f.aic:.1f}" + (f", shape {f.shape:.2f}" if d != "gaussian" else ""))
        st.caption("Two-step logic as in the project (here the mean is just the sample mean). Lower AIC = better in-sample fit.")
