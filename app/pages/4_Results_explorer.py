"""Results explorer: saved R results, exact values, matched dates, negative results included."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ on the path when run standalone

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import common as C

C.setup("Results explorer")
cfg = C.config()
st.title("Results explorer")
st.markdown(f"All values are read from the final R run `{C.read_text('results/RUN_ID.txt').strip()}` and the Distribution run "
            f"`{C.read_text('distribution/RUN_ID.txt').strip()}`. Errors are on the squared-return target y; RMSE and MAE are "
            "shown × 10,000. Lower is better. Positive '% gain' means lower MSE than the comparator.")

tabs = st.tabs(["Core three pipelines", "Explore any models", "Forecast vs actual", "Extensions vs raw GARCH",
                "Distributions (Ext. 1)", "Ensembles (Ext. 2)", "MLP (Ext. 3)", "Settings sensitivity", "Diagnostics"])

# ============================================================================ core
with tabs[0]:
    cs = C.read_csv("results/tables/core_scores.csv")
    cs = cs[cs.split == "test"]
    piv = cs.pivot(index="dataset", columns="model_id", values="RMSE")[["raw_garch", "dwt_garch", "modwt_garch"]] * 1e4
    piv.columns = ["A: Raw GARCH", "B: DWT-GARCH", "C: MODWT-GARCH"]
    piv.insert(0, "n", cs.groupby("dataset").n.first())
    piv = piv.reindex(C.DATASETS)
    piv.index = piv.index.map(C.label)
    st.markdown("**Historical test 2012-2014, RMSE × 10,000 on the dates where all three succeeded** (`tables/core_scores.csv`)")
    st.dataframe(piv.style.format("{:.4f}", subset=["A: Raw GARCH", "B: DWT-GARCH", "C: MODWT-GARCH"])
                 .highlight_min(axis=1, subset=["A: Raw GARCH", "B: DWT-GARCH", "C: MODWT-GARCH"], color="rgba(27,158,119,0.25)"),
                 width="stretch")
    ratio = piv[["A: Raw GARCH", "B: DWT-GARCH", "C: MODWT-GARCH"]].div(piv["A: Raw GARCH"], axis=0)
    fig = go.Figure()
    for col, c in zip(ratio.columns, [C.RAW, C.DWT, C.MODWT]):
        fig.add_trace(go.Bar(x=ratio.index, y=ratio[col], name=col, marker_color=c))
    fig.add_hline(y=1, line_dash="dot")
    fig.update_layout(barmode="group", height=320, yaxis_title="RMSE / raw GARCH RMSE", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    mw = (piv["C: MODWT-GARCH"] < piv["A: Raw GARCH"]).sum()
    dw = (piv["B: DWT-GARCH"] < piv["A: Raw GARCH"]).sum()
    gaps = (100 * (piv["C: MODWT-GARCH"] / piv["A: Raw GARCH"] - 1)).abs()
    st.markdown(f"* MODWT-GARCH has lower RMSE than raw GARCH in **{mw} of {len(piv)}** series, but the largest gap in either "
                f"direction is only {gaps.max():.2f}% of RMSE: in practice they are the same forecaster.\n"
                + f"* Paired-DWT GARCH has lower RMSE than raw GARCH in **{dw} of {len(piv)}** series. The paired transform "
                  "conditions on the already-observed first return of each pair, so its forecasts stay close to raw GARCH.\n"
                + "* Sample sizes differ slightly between series because failed fits remove a date from the joint comparison.")
    summ = C.read_text("results/run/SUMMARY.md")
    with st.expander("SUMMARY.md of the run (verbatim)"):
        st.markdown(summ)

# ============================================================================ explore
with tabs[1]:
    sc = C.all_scores()
    c1, c2, c3 = st.columns(3)
    period = c1.radio("Period", ["test", "later"], format_func=lambda p: C.PERIOD_LABELS[p])
    dss = [d for d in C.DATASETS if period == "test" or d in C.STOCKS]
    ds = c2.selectbox("Dataset", dss, format_func=C.label, key="ex_ds")
    metric = c3.selectbox("Metric", ["RMSE", "MAE", "MSE", "R2"])
    sample = st.radio("Comparison sample", ["Matched dates of the models I select (computed from saved forecasts)",
                                            "All-model common dates (tables/all_model_scores.csv)"])
    fc = C.forecasts(ds, period)
    allm = sorted(fc.model_id.unique(), key=lambda m: (not m.startswith(("raw", "dwt", "modwt")), m))
    default = [m for m in ["raw_garch", "dwt_garch", "modwt_garch", "ensemble_modwt", "direct_y_arima", "mlp"] if m in allm]
    models = st.multiselect("Models", allm, default=default, format_func=C.friendly)
    if models:
        if sample.startswith("Matched"):
            res, n = C.matched_scores(fc, models)
            st.caption(f"{n} matched dates.")
        else:
            res = sc[(sc.dataset == ds) & (sc.split == period) & sc.model_id.isin(models)][["model_id", "n", "MSE", "RMSE", "MAE", "R2"]]
            st.caption(f"{int(res.n.iloc[0]) if len(res) else 0} all-model common dates.")
        res = res.copy()
        scale = 1e4 if metric in ("RMSE", "MAE") else (1e8 if metric == "MSE" else 1)
        res["value"] = res[metric] * scale
        res["name"] = res.model_id.map(C.friendly)
        res = res.sort_values("value", ascending=metric != "R2")
        fig = px.bar(res, x="value", y="name", orientation="h", color="model_id",
                     color_discrete_map={m: C.model_colour(m) for m in res.model_id})
        fig.update_layout(showlegend=False, height=max(250, 28 * len(res)), yaxis_title="",
                          xaxis_title=f"{metric}" + {1e4: " × 1e4", 1e8: " × 1e8", 1: ""}[scale], margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        st.dataframe(res[["name", "model_id", "n", "MSE", "RMSE", "MAE", "R2"]], hide_index=True, width="stretch")
    cov = C.read_csv("results/tables/coverage.csv")
    cv = cov[(cov.dataset == ds) & (cov.period == period) & (cov.coverage_pct < 100)]
    if len(cv):
        st.markdown("**Models with failed forecasts on this dataset/period** (`tables/coverage.csv`)")
        st.dataframe(cv.assign(model=cv.model_id.map(C.friendly)), hide_index=True, width="stretch")

# ============================================================================ forecast plot
with tabs[2]:
    c1, c2, c3 = st.columns(3)
    period = c1.radio("Period ", ["test", "later"], format_func=lambda p: C.PERIOD_LABELS[p])
    dss = [d for d in C.DATASETS if period == "test" or d in C.STOCKS]
    ds = c2.selectbox("Dataset ", dss, format_func=C.label, key="fp_ds")
    agg = c3.radio("Display", ["daily", "monthly average (display only)"])
    fc = C.forecasts(ds, period)
    allm = sorted(fc.model_id.unique())
    models = st.multiselect("Models ", allm, default=["raw_garch", "dwt_garch", "modwt_garch"], format_func=C.friendly)
    fv = fc[fc.model_id.isin(models)]
    fv = fv[C.valid_mask(fv)]
    act = fc.drop_duplicates("target_date")[["target_date", "actual"]].sort_values("target_date")
    dmin, dmax = act.target_date.min().date(), act.target_date.max().date()
    rng = st.slider("Date range", dmin, dmax, (dmin, dmax))
    sel = lambda d: d[(d.target_date.dt.date >= rng[0]) & (d.target_date.dt.date <= rng[1])]
    act, fv = sel(act), sel(fv)
    if agg.startswith("monthly"):
        act = act.set_index("target_date").resample("ME").mean().reset_index()
        fv = fv.groupby("model_id").apply(lambda g: g.set_index("target_date")[["prediction"]].resample("ME").mean(),
                                          include_groups=False).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=act.target_date, y=act.actual * 1e4, name="actual y", line=dict(color=C.ACTUAL, width=1)))
    for m in models:
        z = fv[fv.model_id == m]
        fig.add_trace(go.Scatter(x=z.target_date, y=z.prediction * 1e4, name=C.friendly(m), line=dict(color=C.model_colour(m), width=1.3)))
    fig.update_layout(height=420, yaxis_title="y × 1e4", margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")
    if models:
        res, n = C.matched_scores(sel(fc), models)
        base = sel(fc)
        rows = []
        for m in models:
            z = base[(base.model_id == m)]
            z = z[C.valid_mask(z)]
            rows.append(dict(model=C.friendly(m), n=len(z), mean_forecast_over_mean_actual=z.prediction.mean() / z.actual.mean()))
        st.markdown(f"Matched-date scores in this range (n = {n}):")
        st.dataframe(res.assign(model=res.model_id.map(C.friendly), RMSE_x1e4=res.RMSE * 1e4, MAE_x1e4=res.MAE * 1e4)
                     [["model", "n", "RMSE_x1e4", "MAE_x1e4", "R2"]], hide_index=True, width="stretch")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption("Ratio of mean forecast to mean actual: 1 = unbiased on average, > 1 over-prediction. Scores are always on daily "
                   "values; the monthly view is only for reading the chart.")

# ============================================================================ extensions
with tabs[3]:
    ext = C.read_csv("results/tables/extension_comparisons.csv")
    ext["dataset_l"] = ext.dataset.map(C.label)
    ext["gain_pct"] = ext.improvement_pct
    per = st.radio("Period  ", ["test", "later"], format_func=lambda p: C.PERIOD_LABELS[p], horizontal=True)
    z = ext[ext.period == per]
    slot_names = {"dwt_garch": "DWT-GARCH", "modwt_garch": "MODWT-GARCH", "selected_modwt": "validation-selected MODWT variant",
                  "component": "validation-selected MRA component", "ensemble_base": "Base ensemble",
                  "ensemble_all": "Combined ensemble", "ensemble_modwt": "MODWT ensemble", "mlp": "MLP seed 101"}
    fig = px.bar(z, x="slot", y="gain_pct", color="dataset_l", barmode="group",
                 labels={"gain_pct": "% lower MSE than raw GARCH", "slot": "", "dataset_l": "dataset"})
    fig.update_xaxes(tickvals=list(slot_names), ticktext=list(slot_names.values()))
    fig.add_hline(y=0)
    clip = st.checkbox("Clip the y-axis to ±40% (very negative bars are cut)", True)
    if clip:
        fig.update_yaxes(range=[-40, 15])
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    show = z[["dataset_l", "slot", "model_id", "control", "n_common", "requested", "gain_pct", "RMSE_ratio",
              "descriptive_CI_low", "descriptive_CI_high"]]
    st.dataframe(show.style.format({"gain_pct": "{:+.2f}", "RMSE_ratio": "{:.4f}", "descriptive_CI_low": "{:+.1f}",
                                    "descriptive_CI_high": "{:+.1f}"}), hide_index=True, width="stretch")
    pos = (z.gain_pct > 0).sum()
    st.markdown(f"Positive gains: **{pos} of {len(z)}** rows. CI columns are descriptive paired block-bootstrap intervals "
                "(where computed), not corrected for model search or multiple comparisons; an interval containing 0 means the "
                "sign is not established.")
    st.markdown("#### Does the direction persist after 2014? (stocks)")
    tr = C.read_csv("results/tables/later_period_trends.csv")
    tr["dataset"] = tr.dataset.map(C.label)
    st.dataframe(tr.style.format({"historical_gain_pct": "{:+.2f}", "later_gain_pct": "{:+.2f}",
                                  "historical_coverage": "{:.1f}", "later_coverage": "{:.1f}"}), hide_index=True, width="stretch")
    st.caption(f"Same direction in {int(tr.same_direction.astype(str).str.upper().eq('TRUE').sum())} of {len(tr)} comparisons "
               "(this count includes losses that persisted). The later period is retrospective, not an untouched holdout.")

# ============================================================================ distribution
with tabs[4]:
    wc = C.read_csv("distribution/heldout_win_counts.csv")
    wn = C.read_csv("distribution/heldout_winners.csv")
    dc = C.read_csv("distribution/innovation_distribution_comparison.csv")
    st.markdown("Gaussian vs Student-t vs GED innovations, same datasets, orders, window, cadence, target and metrics "
                "(`Distribution/`). Each *group* = dataset × pipeline × period; distributions compared on the group's common dates.")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"**Lowest-error counts over {len(wn)} held-out groups**")
        st.dataframe(wc.assign(distribution=wc.distribution.map(C.DIST_LABELS)), hide_index=True, width="stretch")
        by = wn.groupby(["period", "best_MSE"]).size().unstack(fill_value=0)
        by.columns = [C.DIST_LABELS[c] for c in by.columns]
        st.markdown("**MSE wins by period**")
        st.dataframe(by, width="stretch")
    with c2:
        wn["group"] = wn.dataset.map(C.label) + " / " + wn.pipeline + " / " + wn.period
        long = wn.melt(id_vars=["group"], value_vars=["student_t_MSE_change_pct", "GED_MSE_change_pct"], var_name="dist", value_name="pct")
        long["dist"] = long.dist.map({"student_t_MSE_change_pct": "Student-t", "GED_MSE_change_pct": "GED"})
        fig = px.bar(long.sort_values("pct"), y="group", x="pct", color="dist", barmode="group", orientation="h",
                     color_discrete_map={"Student-t": C.DIST_COLOURS["student_t"], "GED": C.DIST_COLOURS["ged"]},
                     labels={"pct": "MSE change vs Gaussian (%), negative = better", "group": ""})
        fig.update_layout(height=700, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
    fs = C.read_csv("distribution/fit_status_summary.csv")
    st.markdown(f"Fit attempts (all periods incl. validation): {int(fs.attempts.sum()):,}; failed: {int(fs.failures.sum())}; "
                f"GED shape-guard flags: {int(fs.guard_flags.sum())}.")
    dd = dc[dc.split != "validation"][["dataset", "pipeline", "split", "distribution", "n", "MSE", "MAE", "loglik", "AIC", "alpha", "beta", "nu", "ged_shape", "coverage_pct"]]
    with st.expander("Full comparison table (first-refit likelihood statistics are conditional on fixed ARMA residuals)"):
        st.dataframe(dd, hide_index=True, width="stretch")
    st.markdown("**Interpretation.** Fat-tailed likelihoods fit far better in-sample (much higher log-likelihood), yet the forecast "
                "MSE changes are mostly small and sometimes positive (worse). Better in-sample fit does not imply better forecasts. "
                "Win counts are descriptive, not significance tests.")
    with st.expander("COMPARISON.md (verbatim)"):
        st.markdown(C.read_text("distribution/COMPARISON.md"))

# ============================================================================ ensembles
with tabs[5]:
    ext = C.read_csv("results/tables/extension_comparisons.csv")
    z = ext[ext.slot.str.startswith("ensemble")].copy()
    z["dataset"] = z.dataset.map(C.label)
    piv = z.pivot_table(index="dataset", columns=["period", "slot"], values="improvement_pct")
    st.markdown("**% lower MSE than raw GARCH (pairwise matched dates)** (`tables/extension_comparisons.csv`)")
    st.dataframe(piv.style.format("{:+.2f}").map(lambda v: f"color: {C.MODWT}" if v > 0 else f"color: {C.PAPER}"),
                 width="stretch")
    best = z.loc[z.improvement_pct.idxmax()]
    st.markdown(f"Largest gain: **{best.dataset}**, {best.slot}, {best.period}: {best.improvement_pct:+.2f}% "
                f"(n = {int(best.n_common)} of {int(best.requested)} requested). "
                f"Ensembles improve on raw GARCH in {(z.improvement_pct > 0).sum()} of {len(z)} rows: averaging helps where members "
                "make different errors, and hurts when a weak member (DWT-GARCH) is included.")
    sel = C.read_csv(f"results/per_dataset/{st.selectbox('Validation selection of MRA family winners for', C.DATASETS, format_func=C.label)}/ensemble_selection.csv")
    st.dataframe(sel, hide_index=True, width="stretch")

# ============================================================================ MLP
with tabs[6]:
    m = C.read_csv("results/tables/mlp_test_seed_effects.csv")
    m["dataset"] = m.dataset.map(C.label)
    st.markdown("**Each seed vs raw GARCH on their pairwise matched dates** (`tables/mlp_test_seed_effects.csv`)")
    st.dataframe(m[["dataset", "period", "model_id", "requested", "successful_model", "n_common", "RMSE", "control_RMSE",
                    "RMSE_ratio", "improvement_pct"]].style.format({"RMSE": "{:.3e}", "control_RMSE": "{:.3e}",
                                                                   "RMSE_ratio": "{:.3f}", "improvement_pct": "{:+.2f}"}),
                 hide_index=True, width="stretch")
    st.markdown(f"MLP beats raw GARCH in **{(m.improvement_pct > 0).sum()} of {len(m)}** seed × dataset × period rows. "
                "Seeds disagree strongly on some series, and some seeds hit the iteration limit on many dates "
                "(successful_model < requested): small networks on noisy squared returns are unstable.")
    v = C.read_csv("results/tables/mlp_validation_effects.csv")
    with st.expander("Validation grid (hidden size × decay × seed)"):
        st.dataframe(v, hide_index=True, width="stretch")

# ============================================================================ sensitivity
with tabs[7]:
    pe = C.read_csv("results/tables/parameter_effects.csv")
    st.markdown("One setting changed at a time for the three core GARCH pipelines (`tables/parameter_effects.csv`). "
                "% gain vs the default (window 1,024, refit every 20, AIC, p,q ≤ 3).")
    per = st.radio("Period   ", sorted(pe.period.unique()), horizontal=True, format_func=lambda p: C.PERIOD_LABELS.get(p, p))
    z = pe[pe.period == per].copy()
    z["dataset"] = z.dataset.map(C.label)
    fig = px.strip(z, x="scenario", y="improvement_pct", color="slot",
                   color_discrete_map={"raw_garch": C.RAW, "dwt_garch": C.DWT, "modwt_garch": C.MODWT},
                   hover_data=["dataset"], labels={"improvement_pct": "% lower MSE than default"})
    fig.add_hline(y=0)
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    fp = C.read_csv("results/run/frozen_parameter_choices.csv")
    fp["dataset"] = fp.dataset.map(C.label)
    st.markdown("**Setting chosen on validation for each pipeline** (`frozen_parameter_choices.csv`)")
    st.dataframe(fp, hide_index=True, width="stretch")

# ============================================================================ diagnostics
with tabs[8]:
    dg = C.read_csv("results/tables/initial_diagnostics.csv")
    ds = st.selectbox("Dataset  ", C.DATASETS, format_func=C.label, key="dg")
    z = dg[(dg.dataset == ds) & (dg.period == "validation") & (dg.component == "x") & dg.model_id.str.match(r"^(raw|dwt|modwt)_")]
    st.dataframe(z[["model_id", "p", "q", "mean_AIC", "omega", "alpha", "beta", "nu", "standardized", "serial_F", "serial_F_p",
                    "serial_decision", "arch_F", "arch_F_p", "arch_decision", "ljung_box_p", "squared_ljung_box_p"]],
                 hide_index=True, width="stretch")
    st.caption("First fit at the end of training (origin 2009-12-31). 12-lag auxiliary F tests; Ljung-Box Q(24) with fitdf = p+q. "
               "GARCH rows use standardised innovations. 5% decisions; F references are approximate on estimated residuals.")
