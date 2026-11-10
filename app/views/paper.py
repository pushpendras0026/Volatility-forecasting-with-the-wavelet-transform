"""The original paper: what it claimed and how, kept separate from what we did."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ on the path when run standalone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import common as C

C.setup("The paper")
st.title("The original paper")
st.markdown("**Ismail, M. T., Audu, B. and Tumala, M. M. (2016).** *Volatility forecasting with the wavelet transformation "
            "algorithm GARCH model: Evidence from African stock markets.* The Journal of Finance and Data Science 2, 125-135. "
            "[doi:10.1016/j.jfds.2016.09.002](https://doi.org/10.1016/j.jfds.2016.09.002)")
C.note("Everything in a <b>red</b> box on this page is what <b>the paper</b> did or claimed. <b>Blue</b> boxes are <b>our</b> "
       "project. Paper numbers are transcribed from the PDF into <code>data/paper/*.csv</code>; see "
       "<code>data/paper/README.md</code> for how the tables were transcribed.", "note")

st.header("1. The question the paper asks")
C.note("Can a <b>MODWT-GARCH(1,1)</b> model (GARCH fitted to wavelet-transformed returns) model and forecast the volatility "
       "of African stock markets better than a plain <b>GARCH(1,1)</b> on the returns?", "paper")

st.header("2. Data")
C.note("Daily index prices of four African markets, 2 January 2000 to 31 December 2014, from Datastream: Kenya (NSE20), "
       "Nigeria (All Share), South Africa (FTSE/JSE100), Tunisia (TUNINDEX). Chosen to represent the East, West, South and North "
       "African regions.", "paper")
t1 = C.read_csv("paper/paper_table1_descriptive.csv")
st.markdown("**Paper Table 1: descriptive statistics of daily returns** (as printed)")
st.dataframe(t1, hide_index=True, width="stretch")
st.caption("The paper labels the mean and standard deviation columns as '%' although the magnitudes look like decimals. "
           "Kurtosis above 3 and the Jarque-Bera test reject normality: fat tails.")

st.header("3. Method, step by step")
C.note("""<ol>
<li>Returns r<sub>t</sub> = ln P<sub>t</sub> − ln P<sub>t−1</sub>.</li>
<li>Fit ARMA(p,q) to the returns, choosing p and q by AIC after 'systematically over-fitting' (Box-Jenkins). Check residuals with a
serial-correlation (Breusch-Godfrey) LM test and an ARCH test.</li>
<li>Transform returns with a one-level Haar wavelet. The paper writes its formula (5) as
w<sub>1</sub> = (r<sub>2k</sub> − r<sub>2k−1</sub>)/√2, which is the <i>paired, decimated</i> (DWT-style) Haar detail, although it calls it MODWT.</li>
<li>Fit ARMA to the transformed series by AIC, then GARCH(1,1) to both the raw and the transformed models.</li>
<li>Compare in-sample AIC (Table 11).</li>
<li>Forecast: one-step-ahead variance for only the <b>last five days</b> of the sample, re-estimating on a moving sample, and score
against a 'true volatility' g² = (r<sub>t</sub> − r̄)², r̄ a moving average (equations 7-8). Report MSE (Table 12).</li></ol>""", "paper")

st.header("4. What the paper reports")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Table 10: chosen ARMA orders and AIC**")
    st.dataframe(C.read_csv("paper/paper_table10_orders.csv"), hide_index=True, width="stretch")
with c2:
    st.markdown("**Table 12: forecast MSE**")
    t12 = C.read_csv("paper/paper_table12_mse.csv")
    st.dataframe(t12, hide_index=True, width="stretch")
st.markdown("**Table 11: GARCH(1,1) estimates and AIC** (α+β columns computed by us)")
t11 = C.read_csv("paper/paper_table11_garch.csv")
st.dataframe(t11, hide_index=True, width="stretch")
fig = go.Figure()
fig.add_trace(go.Bar(x=t12.country, y=t12.garch_mse, name="GARCH(1,1)", marker_color=C.RAW))
fig.add_trace(go.Bar(x=t12.country, y=t12.modwt_garch_mse, name="MODWT-GARCH(1,1)", marker_color=C.MODWT))
fig.update_layout(yaxis_type="log", height=300, barmode="group", yaxis_title="MSE (log scale)", margin=dict(l=10, r=10, t=10, b=10))
C.show(fig, howto="Bars compare the paper's reported MSE for plain GARCH(1,1) (blue) with MODWT-GARCH(1,1) (green) for each country, on a log scale. A shorter green bar means the paper claims wavelets helped.")
better = (t12.modwt_garch_mse < t12.garch_mse).sum()
C.note(f"<b>Claim:</b> MODWT-GARCH(1,1) gives lower forecast MSE in {better} of {len(t12)} markets (all except Kenya) and lower "
       "AIC in all but South Africa; the abstract says GARCH(1,1) 'underestimates' while MODWT-GARCH 'generates an accurate "
       "forecast'. Conclusion: MODWT-GARCH 'best fits' African returns and should be tried elsewhere.", "paper")

st.header("5. Reading the paper critically")
nig = t11[t11.country == "Nigeria"].iloc[0]
st.markdown(
    f"""
* **Five forecast days.** The MSE comparison uses only the last five days of each sample. Five squared errors cannot
  separate two models reliably; a single low- or high-volatility day can determine the winner.
* **MSE magnitudes differ by up to five orders of magnitude** across markets in Table 12 (for example South Africa
  {t12.loc[t12.country == 'South Africa', 'modwt_garch_mse'].iloc[0]:g} vs {t12.loc[t12.country == 'South Africa', 'garch_mse'].iloc[0]:g}),
  which is hard to reconcile with forecasting the same kind of target.
* **Stationarity.** The text says α+β < 1 for all models, but the transcribed Nigeria estimates sum to
  {nig.garch_alpha1_plus_beta1:.2f} (GARCH) and {nig.modwt_alpha1_plus_beta1:.2f} (MODWT-GARCH). Our R code uses a parameter map that
  enforces α+β < 1, so it cannot reproduce these values (comment in `R/models.R`).
* **AIC across different series.** AIC of a model for the returns and AIC of a model for the *transformed* series are
  likelihoods of different data, so comparing them does not show which forecasts returns better.
* **'MODWT' vs DWT.** Formula (5) is a paired (decimated) Haar difference. The true MODWT detail is overlapping:
  (r<sub>t</sub> − r<sub>t−1</sub>)/2. This ambiguity is why we test **both**.
* **Variance of the transformed series is not the variance of returns.** A forecast of the wavelet detail's variance must be
  mapped back to the return scale before it is compared with returns; the paper does not describe this step.
    """, unsafe_allow_html=True)

st.header("6. What we did differently")
C.note("""<ul>
<li><b>Data</b>: South Africa, Tunisia, Nigeria indices (Kenya is not part of the final six-series run) plus Infosys, IBM and Google;
2004 onward, from supplied files (not Datastream).</li>
<li><b>Both readings of the transform</b>: paired DWT (the paper's formula) and overlapping MODWT, with an explicit restoration of
return mean and variance.</li>
<li><b>A common target</b> for every model: y<sub>t+1</sub> = (r<sub>t+1</sub> − mean of last 20 returns)², the daily analogue of the paper's g².</li>
<li><b>Hundreds of out-of-sample forecasts</b> instead of five: a rolling 1,024-day window, refit every 20 days, train 2004-2009,
validation 2010-2011, test 2012-2014, stocks also 2015-2025.</li>
<li><b>Extensions</b>: Student-t and GED innovations, wavelet component models, ensembles and an MLP; all failures and losses kept.</li>
</ul>""", "ours")
st.markdown("So our study is a **re-examination** of the paper's idea, not an exact numerical replication of its data, "
            "target or estimator (METHODS.md). The findings are on the *Results explorer* page.")

st.header("7. Second reference")
st.markdown("Rubio, L., Palacio Pinedo, A., Mejía Castaño, A. and Ramos, F. (2023). *Forecasting volatility by using wavelet "
            "transform, ARIMA and GARCH models.* Eurasian Economic Review 13, 803-830 "
            "([doi:10.1007/s40822-023-00243-x](https://doi.org/10.1007/s40822-023-00243-x)). Uses wavelet pre-processing with ARIMA, "
            "hybridised with GARCH, on Tesla volatility. It motivated the *component (MRA) models* in our Extension 2.")
