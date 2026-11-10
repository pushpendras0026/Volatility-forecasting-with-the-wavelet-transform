"""Searchable glossary of every term used in the study."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ on the path when run standalone

import pandas as pd
import streamlit as st

from lib import common as C

C.setup("Glossary")
st.markdown('<div class="hero"><h1>Glossary</h1>Plain-language definitions of every term in the app, with the lesson '
            "that explains it. Type to filter.</div>", unsafe_allow_html=True)

T = [
    ("Return (log return)", "Basics", "r_t = ln P_t - ln P_(t-1): the daily proportional price change. Roughly the percent change divided by 100.", "s03"),
    ("Volatility", "Basics", "The typical size of returns. It is not directly observed, so it must be estimated or forecast.", "s01"),
    ("Volatility clustering", "Basics", "Large moves tend to be followed by large moves and calm days by calm days.", "s01"),
    ("Target y(t+1)", "Basics", "(r_(t+1) - mean of the last 20 returns)^2: the squared surprise, a noisy stand-in for tomorrow's variance. Every model forecasts this.", "s03"),
    ("Kurtosis", "Basics", "A measure of tail weight. A normal distribution has 3; financial returns are usually far higher.", "s04"),
    ("Heavy / fat tails", "Basics", "Extreme days occur much more often than a normal distribution implies.", "s04"),
    ("Stationarity", "Time series", "Statistical properties (mean, variance, autocorrelation) do not change over time. Returns are roughly stationary; prices are not.", "s05"),
    ("Autocorrelation (ACF)", "Time series", "Correlation of a series with itself shifted by k days. Returns have almost none; squared returns have a lot.", "s05"),
    ("ARMA(p,q)", "Time series", "Mean model: today's value depends on p past values (AR) and q past shocks (MA).", "s05"),
    ("ARCH effect / ARCH test", "Time series", "Evidence that squared residuals are autocorrelated, meaning the variance is time varying and a GARCH model is appropriate.", "s05"),
    ("GARCH(1,1)", "Models", "h_t = omega + alpha*e_(t-1)^2 + beta*h_(t-1): tomorrow's variance from a constant, yesterday's shock and yesterday's variance.", "s06"),
    ("alpha, beta, persistence", "Models", "alpha: reaction to the latest shock. beta: memory of the previous variance. alpha+beta close to 1 means shocks fade slowly.", "s06"),
    ("Conditional variance h_t", "Models", "The variance of today's return given everything known yesterday.", "s06"),
    ("Innovation distribution", "Models", "The distribution assumed for the standardised shocks: Gaussian, Student-t or GED.", "s12"),
    ("Student-t", "Models", "Bell-shaped with heavier tails than the normal; the degrees of freedom nu control the tail weight (small nu = heavier).", "s12"),
    ("GED", "Models", "Generalised error distribution: a shape parameter moves it from fat-tailed (below 2) to normal (2) to thin-tailed (above 2).", "s12"),
    ("Likelihood", "Estimation", "How probable the observed data are under given parameters. Fitting picks the parameters that maximise it.", "s06"),
    ("AIC / BIC", "Estimation", "Fit scores that penalise extra parameters (AIC: 2k, BIC: k ln n). Lower is better; used to choose the ARMA order.", "s05"),
    ("Wavelet", "Wavelets", "A short wave-like filter that splits a series into components that live at different time scales.", "s07"),
    ("DWT (paired)", "Wavelets", "Discrete wavelet transform: non-overlapping pairs, so each level halves the number of values.", "s07"),
    ("MODWT (overlapping)", "Wavelets", "Maximal-overlap DWT: one value per day at every level, shift-invariant, so it suits rolling forecasts.", "s07"),
    ("Haar filter", "Wavelets", "The simplest wavelet: the scaling filter averages two neighbours and the wavelet filter differences them.", "s07"),
    ("Detail / smooth component", "Wavelets", "Details hold fast fluctuations; the smooth part holds the slow level. Together they rebuild the series.", "s07"),
    ("Multi-resolution analysis (MRA)", "Wavelets", "Rewriting a series as a sum of components, one per time scale.", "s07"),
    ("Restoration", "Wavelets", "Mapping a forecast made on wavelet components back to a variance forecast for the original return.", "s08"),
    ("Rolling window", "Protocol", "Each forecast uses only the most recent N returns, sliding forward one day at a time.", "s10"),
    ("Refit cadence", "Protocol", "How often the model parameters are re-estimated (for example every 20 days).", "s10"),
    ("Train / validation / test", "Protocol", "Fit on the oldest data, choose settings on the middle period, report on the newest period untouched.", "s10"),
    ("Look-ahead leakage", "Protocol", "Using information from the future when making a forecast. The protocol is built to rule this out.", "s10"),
    ("RMSE / MSE / MAE", "Evaluation", "Typical forecast error: root mean squared, mean squared and mean absolute error. Lower is better.", "s11"),
    ("RMSE ratio", "Evaluation", "A model's RMSE divided by raw GARCH's; below 1 means better.", "s11"),
    ("Matched dates", "Evaluation", "Models are compared only on days where every compared model produced a forecast.", "s11"),
    ("Ensemble", "Extensions", "Average of several models' forecasts. Often more stable than any single member.", "s14"),
    ("MLP (neural network)", "Extensions", "A small feed-forward network with sigmoid hidden units trained on lagged targets; three random seeds are reported.", "s15"),
    ("Weight decay", "Extensions", "A penalty on large network weights that reduces over-fitting.", "s15"),
]
MICRO = {
    "Target y(t+1)": ["proof_target"], "GARCH(1,1)": ["proof_garch_uncond"], "alpha, beta, persistence": ["proof_garch_uncond"],
    "Likelihood": ["proof_ll_gaussian", "effect_gaussian_sigma"], "AIC / BIC": ["proof_aic"],
    "Student-t": ["proof_ll_student_t", "effect_student_nu"], "GED": ["proof_ll_ged", "effect_ged_shape"],
    "Innovation distribution": ["proof_ll_gaussian", "proof_ll_student_t", "proof_ll_ged"],
    "Haar filter": ["proof_haar_recon"], "Ensemble": ["proof_ensemble"],
}
df = pd.DataFrame(T, columns=["Term", "Topic", "Definition", "Lesson"])
c1, c2 = st.columns([3, 2])
q = c1.text_input("Search", placeholder="e.g. tail, window, wavelet")
topics = c2.multiselect("Topic", sorted(df.Topic.unique()))
if topics:
    df = df[df.Topic.isin(topics)]
if q:
    ql = q.lower()
    df = df[df.apply(lambda r: ql in (r.Term + " " + r.Definition).lower(), axis=1)]
st.caption(f"{len(df)} terms")
for _, r in df.iterrows():
    with st.expander(f"**{r.Term}**  ·  {r.Topic}"):
        st.write(r.Definition)
        st.caption(f"Full lesson: {int(r.Lesson[1:])}. {C.CLIP_TITLES[r.Lesson]} (Video lessons tab)")
        for key in MICRO.get(r.Term, []):
            C.micro(key)
C.download(df.drop(columns="Lesson"), "glossary.csv", "Download glossary (CSV)")
