"""Architecture navigator: every model we tested, with diagram, equations, training and saved results."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ on the path when run standalone

import re

import numpy as np
import pandas as pd
import streamlit as st

from lib import common as C

C.setup("Architecture navigator")
cfg = C.config()
st.title("Architecture navigator")
st.markdown("Select any evaluated architecture to view its block diagram, equations, training and validation procedure, "
            "and its saved R results on every dataset.")

reg = C.model_catalogue()
mra_ids = sorted(reg.model_id[reg.kind == "mra"])
FAMILIES = {
    "Core GARCH pipelines (A raw / B DWT / C MODWT)": ["raw_garch", "dwt_garch", "modwt_garch"],
    "ARMA-only controls (no GARCH)": ["raw_arima", "dwt_arima", "modwt_arima"],
    "Student-t GARCH (main run)": ["raw_garch_student_t", "dwt_garch_student_t", "modwt_garch_student_t"],
    "GED GARCH (Distribution extension)": ["raw_garch__ged", "dwt_garch__ged", "modwt_garch__ged"],
    "Extra-MA-lag MODWT": ["modwt_garch_structural", "modwt_garch_structural_student_t"],
    "Direct-target ARMA": ["direct_y_arima"],
    "MRA component models (24)": mra_ids,
    "Ensembles (3)": ["ensemble_base_only", "ensemble_all", "ensemble_modwt"],
    "MLP (3 seeds)": ["mlp", "mlp_seed202", "mlp_seed303"],
    "Simple baselines": ["naive", "trailing_mean"],
}
c1, c2 = st.columns([2, 3])
fam = c1.selectbox("Family", list(FAMILIES))
labels = {f"{C.friendly(m)}  ·  {m}": m for m in FAMILIES[fam]}
mid = labels[c2.selectbox("Model", list(labels), key=f"model_{fam}")]
st.markdown(f"## {C.friendly(mid)}  `{mid}`")


def node(name, label, col="#eeeeee", font="black"):
    return f'{name} [label="{label}", fillcolor="{col}", fontcolor="{font}"];'


def dot(body):
    return ('digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11]; '
            + body + " }")


def transform_of(m):
    for t in ("raw", "dwt", "modwt"):
        if m.startswith(t + "_"):
            return t
    return None


# ----------------------------------------------------------------------------- per-kind explanation
tr = transform_of(mid)
if mid.startswith(("raw_", "dwt_", "modwt_")):
    col = C.PIPE_COLOURS[tr]
    garch = "garch" in mid
    dist = "GED" if mid.endswith("__ged") else ("Student-t" if "student_t" in mid else "Gaussian")
    extra = "structural" in mid
    tlabel = {"raw": "x_t = r_t (raw returns)", "dwt": "paired Haar DWT\\nd_k=(r_2k − r_2k−1)/√2",
              "modwt": "overlapping Haar MODWT\\nw_t=(r_t − r_t−1)/2"}[tr]
    order = "order (p, q+1) from raw ARMA" if extra else f"ARMA(p,q), AIC, p,q ≤ {cfg['max_pq']}"
    var = f"GARCH(1,1), {dist} innovations\\non fixed ARMA residuals" if garch else "constant variance σ²"
    body = (node("P", "prices → log returns r_t") + node("T", tlabel, col, "white") + node("M", order) +
            node("V", var) + node("S", "restore return moments\\nμ_r, h_r") +
            node("Y", "ŷ = h_r + (μ_r − r̄20)²") + "P->T->M->V->S->Y;")
    st.graphviz_chart(dot(body))
    st.latex({"raw": r"x_t=r_t", "dwt": r"d_k=\tfrac{r_{2k}-r_{2k-1}}{\sqrt2}",
              "modwt": r"w_t=\tfrac{r_t-r_{t-1}}{2}"}[tr] +
             r",\quad x_t=c+\sum_{i\le p}\phi_i x_{t-i}+e_t+\sum_{j\le q}\theta_j e_{t-j}")
    if garch:
        st.latex(r"e_t=\sqrt{h_t}z_t,\quad h_t=\omega+\alpha e_{t-1}^2+\beta h_{t-1},\quad z_t\sim " +
                 {"Gaussian": r"N(0,1)", "Student-t": r"t_\nu\text{ (unit variance)}", "GED": r"\mathrm{GED}_b\text{ (unit variance)}"}[dist])
    st.latex({"raw": r"\hat\mu_r=\hat\mu_x,\ \hat h_r=\hat h_x", "dwt": r"\hat\mu_r=r_t+\sqrt2\hat\mu_d,\ \hat h_r=2\hat h_d",
              "modwt": r"\hat\mu_r=r_t+2\hat\mu_w,\ \hat h_r=4\hat h_w"}[tr] +
             r",\qquad \hat y_{t+1}=\hat h_r+(\hat\mu_r-\bar r^{(20)}_t)^2")
    notes = []
    if not garch:
        notes.append("Control: the same mean model with a constant variance, to isolate what GARCH adds.")
    if dist == "Student-t":
        notes.append("Same ARMA order as the Gaussian sister model; ν = 2 + e^u estimated with α, β, ω (k = 4).")
    if dist == "GED":
        notes.append("Run separately in `Distribution/` with the same frozen orders, window, cadence and target; "
                     "GED shape b estimated (guard 0.1-100). Not part of ensembles.")
    if extra:
        notes.append("The Haar detail multiplies the raw MA polynomial by (1−B)/2, adding one MA lag. This variant takes the raw "
                     "return order (p,q) and fits (p,q+1) to the MODWT details. The unit root is not imposed.")
    if tr == "dwt":
        notes.append("Decimation: a 1,024-return window gives about 511 details, and pairs are re-aligned every day so the "
                     "known r_t anchors tomorrow's pair.")
    for n in notes:
        st.markdown("* " + n)
elif mid == "direct_y_arima":
    st.graphviz_chart(dot(node("Y0", "past targets y_1..y_t") + node("A", "ARMA(p,q) on y\\nAIC, p,q ≤ 3") +
                          node("Y", "ŷ = max(0, μ̂_y)") + "Y0->A->Y;"))
    st.latex(r"y_t=c+\sum\phi_i y_{t-i}+e_t+\sum\theta_j e_{t-j},\qquad \hat y_{t+1}=\max(0,\hat\mu_{y,t+1})")
    st.markdown("* Models the target directly instead of returns. A control for the MRA component models (same target, no decomposition).")
elif mid.startswith("mra_"):
    m = re.match(r"mra_(dwt|modwt)_(haar|db4|db6)_(all_arima|mixed)(_j1)?$", mid)
    tr_, filt, alloc, j1 = m.group(1), m.group(2), m.group(3), m.group(4)
    J = 1 if j1 else 2
    col = C.PIPE_COLOURS[tr_]
    comps = [f"A{J}"] + [f"D{j}" for j in range(J, 0, -1)]
    body = node("Y0", "past targets y (observed prefix)") + node("W", f"{tr_.upper()} {filt}, J={J}\\nprefix reflection", col, "white")
    for c in comps:
        model = "ARMA (AIC, p,q ≤ 2)" if (alloc == "all_arima" or c.startswith("A")) else "AR(1) mean\\n+ residual GARCH"
        body += node(c, f"{c}: {model}") + f"W->{c}; {c}->S;"
    body += node("S", "sum of component\\nmean forecasts") + node("Y", "ŷ = max(0, Σ μ̂_c)") + "Y0->W; S->Y;"
    st.graphviz_chart(dot(body))
    st.latex(r"y=" + "+".join(comps) + r",\qquad \hat y_{t+1}=\max\Big(0,\sum_c \hat\mu_{c,t+1}\Big)")
    st.markdown(f"* Decomposition recomputed at every origin on the last ≤ {cfg['max_window']:,} targets only (no future data).\n"
                "* In the *mixed* branch the residual GARCH variances are **not** added to the point forecast; its difference "
                "from *all-ARMA* comes from the AR(1) mean allocation (ARCHITECTURE.md).\n"
                "* 24 = 2 transforms × 3 filters × 2 levels × 2 allocations. Validation picks one per transform × allocation "
                "family for the combined/MODWT ensembles.")
elif mid.startswith("ensemble"):
    fs = C.read_csv("results/tables/frozen_selections.csv")
    key = {"ensemble_base_only": "members_base", "ensemble_all": "members_combined", "ensemble_modwt": "members_modwt"}[mid]
    st.graphviz_chart(dot(node("V", "validation forecasts\\n2010-2011") + node("F", "freeze members") +
                          node("K", "K member forecasts\\n(same date)") + node("E", "ŷ = (1/K) Σ ŷ_k\\n(any member missing → unavailable)") +
                          "V->F->K->E;"))
    st.latex(r"\hat y^{\,ens}_{t+1}=\frac1K\sum_{k=1}^K \hat y^{(k)}_{t+1}")
    st.markdown({"ensemble_base_only": "**Base**: the six return models (raw/DWT/MODWT × ARMA/GARCH).",
                 "ensemble_all": "**Combined**: base six + direct-target ARMA + the four validation-selected MRA family winners.",
                 "ensemble_modwt": "**MODWT**: MODWT ARMA, MODWT-GARCH and the two selected MODWT MRA winners."}[mid])
    mem = fs[["dataset", key]].copy()
    mem["dataset"] = mem.dataset.map(C.label)
    mem[key] = mem[key].str.split(";").apply(lambda xs: ", ".join(C.friendly(x) for x in xs))
    st.markdown("**Frozen members per dataset** (`tables/frozen_selections.csv`)")
    st.dataframe(mem.rename(columns={key: "members"}), hide_index=True, width="stretch")
elif mid.startswith("mlp"):
    st.graphviz_chart(dot(node("X", "7 inputs: y_t..y_t−4,\\nmean5, mean20") + node("S", "standardise\\n(training mean, sd)") +
                          node("H", "hidden layer\\n3 or 5 sigmoid units") + node("O", "1 linear output") +
                          node("Y", "ŷ = max(0, scale × o)") + "X->S->H->O->Y;"))
    st.latex(r"a_j=\sigma\big(b_j+w_j^\top \tilde x\big),\quad o=b_0+\sum_j v_j a_j,\quad \hat y=\max(0,\bar y_{train}\,o)")
    seeds = [int(s) for s in cfg.get("mlp_seeds", [])]
    st.markdown(f"* R `nnet`: squared error, weight decay, no skip connections, ≤ {cfg.get('mlp_maxit')} iterations, refit every "
                f"{cfg['refit_every']} origins.\n* Validation chooses hidden size and decay by mean MSE across seeds {seeds}; "
                "fits that hit the iteration limit are flagged unavailable. `mlp` is seed 101.")
    fs = C.read_csv("results/tables/frozen_selections.csv")[["dataset", "mlp_hidden", "mlp_decay", "mlp_fallback"]]
    fs["dataset"] = fs.dataset.map(C.label)
    st.dataframe(fs, hide_index=True, width="stretch")
    st.caption("mlp_fallback = TRUE means no architecture was fully valid on validation, so the declared 5-unit / 0.01 fallback was used.")
else:
    st.graphviz_chart(dot(node("Y0", "past targets y") + node("Y", "naive: ŷ = y_t\\ntrailing mean: mean of last 20 y") + "Y0->Y;"))
    st.markdown("Reference points. Any useful model should beat these.")

# ----------------------------------------------------------------------------- training
st.markdown("### How it was trained and validated")
st.markdown(f"* Orders chosen once on the initial training window (data to {cfg['training'][1]}) by {cfg['criterion']}; frozen.\n"
            f"* Rolling window of ≤ {cfg['max_window']:,} observations; parameters refit every {cfg['refit_every']} origins; "
            "states re-filtered daily.\n"
            f"* Validation {cfg['validation'][0][:4]}-{cfg['validation'][1][:4]} used only for choosing among variants; test "
            f"{cfg['test'][0][:4]}-{cfg['test'][1][:4]}; stocks also {cfg['later'][0][:4]}-{cfg['later'][1][:4]} with everything frozen.")
if not mid.endswith("__ged") and not mid.startswith(("ensemble", "mlp", "naive", "trailing")):
    rows = []
    for ds in C.DATASETS:
        o = C.read_csv(f"results/per_dataset/{ds}/initial_orders.csv")
        o = o[o.model_id == mid]
        if len(o):
            rows.append({"dataset": C.label(ds), **{f"{r.component}": f"({r.p},{r.q})" for r in o.itertuples()}})
    if rows:
        st.markdown("**Frozen ARMA orders (p,q)** per component (`initial_orders.csv`)")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ----------------------------------------------------------------------------- results
st.markdown("### Saved results")
if mid.endswith("__ged"):
    dc = C.read_csv("distribution/innovation_distribution_comparison.csv")
    pipe = mid.replace("__ged", "")
    z = dc[(dc.pipeline == pipe) & (dc.split != "validation")].copy()
    z["RMSE x1e4"] = z.RMSE * 1e4
    z["MAE x1e4"] = z.MAE * 1e4
    piv = z.pivot_table(index=["dataset", "split"], columns="distribution", values="MSE")
    piv["GED vs Gaussian MSE %"] = 100 * (piv["ged"] - piv["gaussian"]) / piv["gaussian"]
    piv["Student-t vs Gaussian MSE %"] = 100 * (piv["student_t"] - piv["gaussian"]) / piv["gaussian"]
    piv = piv.reset_index()
    piv["dataset"] = piv.dataset.map(C.label)
    st.dataframe(piv.style.format({"gaussian": "{:.3e}", "student_t": "{:.3e}", "ged": "{:.3e}",
                                   "GED vs Gaussian MSE %": "{:+.2f}", "Student-t vs Gaussian MSE %": "{:+.2f}"}),
                 hide_index=True, width="stretch")
    st.caption("MSE on common successful dates of the three distributions (`Distribution/.../innovation_distribution_comparison.csv`). "
               "Negative % = lower MSE than Gaussian.")
else:
    sc = C.all_scores()
    z = sc[sc.model_id == mid].copy()
    z["period"] = z.split.map({"test": "2012-2014", "later": "2015-2025"})
    z["dataset"] = z.dataset.map(C.label)
    z["RMSE x1e4"] = z.RMSE * 1e4
    z["MAE x1e4"] = z.MAE * 1e4
    st.markdown("**On the all-model common dates** (`tables/all_model_scores.csv`: every model scored on the dates where all 44 succeeded)")
    st.dataframe(z[["dataset", "period", "n", "RMSE x1e4", "MAE x1e4", "R2", "successful", "requested", "coverage_pct"]]
                 .style.format({"RMSE x1e4": "{:.4f}", "MAE x1e4": "{:.4f}", "R2": "{:.4f}", "coverage_pct": "{:.1f}"}),
                 hide_index=True, width="stretch")
    if mid != "raw_garch":
        rows = []
        for ds in C.DATASETS:
            for per in (["test", "later"] if ds in C.STOCKS else ["test"]):
                fc = C.forecasts(ds, per)
                if mid not in set(fc.model_id):
                    continue
                s, n = C.matched_scores(fc, [mid, "raw_garch"])
                s = s.set_index("model_id")
                if n:
                    rows.append(dict(dataset=C.label(ds), period=C.PERIOD_LABELS[per], n_matched=n,
                                     RMSE_ratio=s.loc[mid, "RMSE"] / s.loc["raw_garch", "RMSE"],
                                     MSE_change_vs_raw_pct=100 * (s.loc[mid, "MSE"] / s.loc["raw_garch", "MSE"] - 1)))
        if rows:
            st.markdown("**Pairwise against raw GARCH on matched dates** (computed here from the saved R per-origin forecasts)")
            pr = pd.DataFrame(rows)
            st.dataframe(pr.style.format({"RMSE_ratio": "{:.4f}", "MSE_change_vs_raw_pct": "{:+.2f}"})
                         .map(lambda v: f"color: {C.MODWT}" if isinstance(v, float) and v < 0 else
                              (f"color: {C.PAPER}" if isinstance(v, float) and v > 0 else ""), subset=["MSE_change_vs_raw_pct"]),
                         hide_index=True, width="stretch")
            wins = (pr.MSE_change_vs_raw_pct < 0).sum()
            st.markdown(f"Lower MSE than raw GARCH in **{wins} of {len(pr)}** dataset-period comparisons. "
                        "Point differences only; small values are within noise.")
st.info("For forecast-vs-actual plots and more filters, open the **Results explorer**.")
