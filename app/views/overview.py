"""Overview: problem statement, empirical illustration and study design."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from scipy import stats

from lib import common as C

C.setup("Overview")
cfg = C.config()

st.markdown(
    '<div class="hero"><h1>Volatility forecasting with the wavelet transform</h1>'
    "Does splitting returns into time scales before fitting a GARCH model improve tomorrow's volatility forecast? "
    "An interactive replication and extension.<br>"
    '<span class="chip">DA-3041 Group 9 · IIT Guwahati</span><span class="chip">Neeharika</span>'
    '<span class="chip">Pratyaksha Jha</span><span class="chip">Pushpendra Singh</span>'
    '<span class="chip">Somita Agarwal</span></div>', unsafe_allow_html=True)
st.markdown(
    "This application accompanies our study of whether a wavelet decomposition improves GARCH volatility forecasts. "
    "It does not assume familiarity with the original paper. It defines the terminology, summarises the paper, documents every "
    "model specification we evaluated, reports the saved out-of-sample results, and provides a Python implementation "
    "in the **Parameter lab** for experimenting with model settings.")

st.header("1. Problem statement")
c1, c2 = st.columns([3, 2])
with c1:
    st.markdown(
        """
* The daily percentage change of an asset price is its **return**.
* The *direction* of returns is close to unpredictable, but their *magnitude* is persistent:
  periods of large price changes tend to be followed by further large changes, and quiet periods by quiet periods.
  The typical size of returns is called **volatility**.
* One-day-ahead volatility forecasts feed risk limits, option pricing, margin requirements and Value-at-Risk.

**Why the problem is difficult**

1. Volatility is **latent**. Only one return is observed per day, so a noisy proxy (the squared return) must be used.
2. **Volatility clustering**: the conditional variance changes over time, so models with constant error variance
   (ordinary regression, ARMA) misspecify the variance.
3. **Heavy tails**: extreme returns occur far more often than a normal distribution implies.
4. The signal-to-noise ratio is low, so forecasts are prone to over-fitting.
        """)
with c2:
    C.note("<b>Research question</b><br>Does decomposing a return series into time scales with a "
           "<b>wavelet transform</b> (in particular the MODWT) before fitting a GARCH model yield more accurate "
           "one-day-ahead volatility forecasts than fitting GARCH directly to the raw returns?")
    _cs = C.read_csv("results/tables/core_scores.csv")
    _cs = _cs[_cs.split == "test"].pivot(index="dataset", columns="model_id", values="RMSE")
    _gap = (100 * (_cs["modwt_garch"] / _cs["raw_garch"] - 1)).abs().max()
    _dw = int((_cs["dwt_garch"] < _cs["raw_garch"]).sum())
    C.note("<b>Summary of findings</b> (2012-2014 test period; see the Results explorer)<br>"
           f"The effect of the wavelet pre-processing is small. MODWT-GARCH differs from raw GARCH by at most {_gap:.2f}% in RMSE. "
           f"Paired-DWT GARCH has lower RMSE than raw GARCH in {_dw} of {len(_cs)} series. "
           "No extension (alternative innovation distribution, ensemble or neural network) is best in every market.", "ours")

# ----------------------------------------------------------------------------- story
st.header("2. Empirical illustration")
ds = st.selectbox("Market", C.DATASETS, index=C.DATASETS.index("south_africa"),
                  format_func=C.label)
d = C.returns_and_target(ds, cfg["mean_window"])
p = C.prices(ds)
d["vol20"] = d["r"].rolling(20).std() * np.sqrt(252)
d = d.dropna(subset=["vol20"])
calm = d.loc[d["vol20"].idxmin()]
storm = d.loc[d["vol20"].idxmax()]
big = d.loc[d["r"].abs().idxmax()]
mf = C.manifest().set_index("dataset").loc[ds]

st.markdown(
    f"Our file for **{C.label(ds)}** ({mf['type']}) has {int(mf['n_prices']):,} daily prices from "
    f"{mf['first_price']} to {mf['last_price']}. "
    f"The lowest-volatility 20-day window ended on **{calm.Date.date()}**: annualised volatility about "
    f"**{calm.vol20 * 100:.1f}%**. The highest-volatility window ended on **{storm.Date.date()}**: about "
    f"**{storm.vol20 * 100:.1f}%**, roughly {storm.vol20 / calm.vol20:.0f} times larger. "
    f"The single largest daily move was **{big.r * 100:+.2f}%** on {big.Date.date()}.")

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                    subplot_titles=("Price", "Daily log return r_t (%)", "20-day rolling volatility, annualised (%)"))
fig.add_trace(go.Scatter(x=p.Date, y=p.Price, line=dict(color=C.RAW, width=1), name="price"), 1, 1)
fig.add_trace(go.Scatter(x=d.Date, y=d.r * 100, line=dict(color=C.GREY, width=0.7), name="return"), 2, 1)
fig.add_trace(go.Scatter(x=d.Date, y=d.vol20 * 100, line=dict(color=C.DWT, width=1.2), name="volatility"), 3, 1)
for when, col in [(calm.Date, C.MODWT), (storm.Date, C.PAPER)]:
    fig.add_vline(x=when, line=dict(color=col, dash="dot"))
fig.update_layout(height=620, showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
C.show(fig, howto='Top: price. Middle: daily log return in percent, where clusters of large bars are the stormy periods. Bottom: rolling 20-day volatility, annualised. Dotted lines mark the calmest (green) and stormiest (red) windows.')
st.caption("Dotted lines mark the lowest-volatility (green) and highest-volatility (red) 20-day windows. Large returns occur in "
           "clusters (middle panel), which is the volatility clustering described above.")

st.subheader("Heavy tails: frequency of extreme returns")
r = d["r"].to_numpy()
z = (r - r.mean()) / r.std()
k_obs = [(np.abs(z) > k).mean() for k in (3, 4, 5)]
k_norm = [2 * stats.norm.sf(k) for k in (3, 4, 5)]
c1, c2 = st.columns([3, 2])
with c1:
    xs = np.linspace(-6, 6, 400)
    h = go.Figure()
    h.add_trace(go.Histogram(x=np.clip(z, -8, 8), histnorm="probability density", nbinsx=160,
                             marker_color=C.RAW, opacity=0.6, name="standardised returns"))
    h.add_trace(go.Scatter(x=xs, y=stats.norm.pdf(xs), line=dict(color=C.PAPER), name="normal curve"))
    h.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="(r - mean)/sd, clipped at ±8")
    C.show(h, howto='Blue bars are the real standardised returns; the red curve is the normal bell curve. Bars above the curve far from the centre show that extreme days are much more common than a normal distribution predicts.')
with c2:
    st.dataframe(pd.DataFrame({"move larger than": ["3 sd", "4 sd", "5 sd"],
                               "observed share": [f"{v:.3%}" for v in k_obs],
                               "normal predicts": [f"{v:.4%}" for v in k_norm],
                               "ratio": [f"{a / b:.0f}x" for a, b in zip(k_obs, k_norm)]}),
                 hide_index=True, width="stretch")
    mom = C.read_csv("derived/return_moments.csv")
    km = mom[(mom.dataset == ds) & (mom.window == "full_file")].iloc[0]
    st.markdown(f"Kurtosis of these returns: **{km['kurtosis']:.2f}** (a normal distribution has 3). "
                "Higher kurtosis indicates heavier tails. See the *Concepts* page, section *Distributions and tails*.")

# ----------------------------------------------------------------------------- plan
st.header("3. Study design")
st.markdown(C.pills(), unsafe_allow_html=True)
st.graphviz_chart(f"""
digraph G {{ rankdir=LR; bgcolor="transparent"; edge [color="#8A94A6"]; node [shape=box, style="rounded,filled", color="#3A475C", fontname="Helvetica", fontsize=11];
 P [label="Daily prices P_t", fillcolor="#1C2536", fontcolor="#E6EAF2"]; R [label="log returns r_t", fillcolor="#1C2536", fontcolor="#E6EAF2"];
 A [label="A: raw returns", fillcolor="{C.RAW}", fontcolor="#0B0F17"];
 B [label="B: paired Haar DWT details", fillcolor="{C.DWT}", fontcolor="#0B0F17"];
 M [label="C: overlapping Haar MODWT details", fillcolor="{C.MODWT}", fontcolor="#0B0F17"];
 F [label="ARMA mean (AIC) then\\nGARCH(1,1) on residuals", fillcolor="#1C2536", fontcolor="#E6EAF2"];
 S [label="restore return mean and variance", fillcolor="#1C2536", fontcolor="#E6EAF2"];
 Y [label="forecast of tomorrow's\\nsquared deviation y_(t+1)", fillcolor="#1C2536", fontcolor="#E6EAF2"];
 P->R; R->A; R->B; R->M; A->F; B->F; M->F; F->S; S->Y; }}""")
st.markdown(
    f"""
* **Data**: three African stock indices (South Africa, Tunisia, Nigeria) and three stocks (Infosys, IBM, Google).
* **Time split**: train {cfg['training'][0][:4]}-{cfg['training'][1][:4]}, validation {cfg['validation'][0][:4]}-{cfg['validation'][1][:4]},
  test {cfg['test'][0][:4]}-{cfg['test'][1][:4]}; the stocks are also evaluated in {cfg['later'][0][:4]}-{cfg['later'][1][:4]}.
* **Rolling forecasts**: each day the model sees only the past {cfg['max_window']:,} returns, and its parameters are re-estimated every {cfg['refit_every']} days.
* **Extensions**: (1) fat-tailed innovation distributions (Student-t, GED); (2) wavelet component models of the target and
  equal-weight ensembles; (3) a small neural network (MLP).

""")

st.header("4. Your learning path")
st.markdown("Tick each step as you finish it. Progress is kept for this browser session.")
steps = [("views/lessons.py", "Watch the video lessons", "Seventeen short narrated animations, from returns to the MLP."),
         ("views/concepts.py", "Work through the Concepts", "Formulas, interactive plots and silent derivation clips (log-likelihoods, parameter effects)."),
         ("views/glossary.py", "Look up any term in the Glossary", "Searchable, with the matching derivation clip."),
         ("views/paper.py", "Read what the paper claimed", "Kept separate from what we did."),
         ("views/architecture.py", "Explore every architecture", "Block diagram, equations and saved results per model."),
         ("views/results.py", "Check the results and compare models", "Includes a day-by-day head-to-head."),
         ("views/lab.py", "Change parameters in the Parameter lab", "Orders, window, refit cadence and innovation distribution.")]
done = 0
for i, (page, title, sub) in enumerate(steps):
    c1, c2 = st.columns([1, 6])
    ok = c1.checkbox(" ", key=f"path_{i}", label_visibility="collapsed")
    done += bool(ok)
    with c2:
        st.page_link(page, label=f"**{title}**")
        st.caption(sub)
st.progress(done / len(steps), text=f"{done} of {len(steps)} steps completed")
