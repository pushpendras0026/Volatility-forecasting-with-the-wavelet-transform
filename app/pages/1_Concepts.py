"""Concepts and glossary: every term with intuition, formula and a small interactive plot."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ on the path when run standalone

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from scipy import special, stats

from lib import common as C
from lib import reimpl as R
from lib import wavelets as W

C.setup("Concepts")
cfg = C.config()
st.title("Concepts and glossary")
st.markdown("Each term has an **intuition**, a **formula** and, where useful, an interactive plot. "
            "Plots marked *real data* use our prepared CSVs.")

ds = st.sidebar.selectbox("Dataset for real-data examples", C.DATASETS, format_func=C.label)
D = C.returns_and_target(ds, cfg["mean_window"]).dropna().reset_index(drop=True)

tabs = st.tabs(["Returns and volatility", "ARMA and GARCH", "Likelihood, AIC, BIC", "Distributions and tails",
                "Wavelets", "Forecasting protocol", "Evaluation", "Extensions"])


def term(name):
    st.markdown(f"### {name}")


def acf(x, nlags=30):
    x = np.asarray(x) - np.mean(x)
    d = np.sum(x ** 2)
    return np.array([np.sum(x[k:] * x[:-k]) / d for k in range(1, nlags + 1)])


# ============================================================================ 1
with tabs[0]:
    term("Log return")
    st.markdown("**Intuition:** the continuously compounded percentage change of the price from one day to the next. "
                "Log returns add up over time and are roughly the percentage change for small moves.")
    st.latex(r"r_t=\ln P_t-\ln P_{t-1}")
    st.markdown("In the R code: `r <- diff(log(Price))` (`R/data.R`, `make_targets`). Returns are kept as decimals "
                "(0.01 means 1%).")

    term("Volatility")
    st.markdown("**Intuition:** how widely returns swing around their mean *given what we know today*. "
                "It is a standard deviation that changes over time.")
    st.latex(r"\sigma_t=\sqrt{\operatorname{Var}(r_t\mid \mathcal F_{t-1})},\qquad h_t=\sigma_t^2\;(\text{conditional variance})")

    term("Squared-return proxy: the forecast target y")
    st.markdown(f"Volatility is never observed. We use a noisy but unbiased-in-spirit proxy: tomorrow's squared deviation of the "
                f"return from the mean of the previous {cfg['mean_window']} returns.")
    st.latex(r"\bar r^{(20)}_t=\frac1{20}\sum_{i=0}^{19} r_{t-i},\qquad y_{t+1}=\big(r_{t+1}-\bar r^{(20)}_t\big)^2")
    st.markdown("A model that predicts a mean $\\hat\\mu_{t+1}$ and a variance $\\hat h_{t+1}$ for $r_{t+1}$ implies")
    st.latex(r"\hat y_{t+1}=E[(r_{t+1}-\bar r^{(20)}_t)^2\mid\mathcal F_t]=\hat h_{t+1}+(\hat\mu_{t+1}-\bar r^{(20)}_t)^2")
    st.markdown("because $E[(X-c)^2]=\\operatorname{Var}X+(EX-c)^2$. This is how every return-based model is turned into a "
                "forecast of the *same* target, so all models can be compared fairly.")
    fig = go.Figure()
    tail = D.tail(500)
    fig.add_trace(go.Scatter(x=tail.Date, y=tail.y * 1e4, line=dict(color=C.ACTUAL, width=1), name="y (x 1e4)"))
    fig.add_trace(go.Scatter(x=tail.Date, y=tail.y.rolling(20).mean() * 1e4, line=dict(color=C.RAW), name="20-day average of y"))
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="x 1e4")
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Real data, {C.label(ds)}, last 500 days of the file. The proxy is highly dispersed: a single large move dominates. "
               "That is why even a perfect variance forecast has a low R².")

    term("Stationarity")
    st.markdown("**Intuition:** the statistical rules of the series (mean, variance, autocorrelations) do not drift over time. "
                "Prices are not stationary (they trend); returns are much closer to stationary. ARMA and GARCH assume a "
                "stationary process; GARCH(1,1) is covariance-stationary only when $\\alpha+\\beta<1$.")
    st.markdown("We do **not** run a formal unit-root (ADF) test in the project; we model returns, which is standard "
                "(METHODS.md states no ADF test is performed).")

    term("Autocorrelation (ACF)")
    st.markdown("**Intuition:** the correlation of a series with its own past, at lag k. Returns have almost no "
                "autocorrelation; **squared** returns have a lot. That gap is the signature of volatility clustering.")
    st.latex(r"\rho_k=\frac{\sum_t (x_t-\bar x)(x_{t-k}-\bar x)}{\sum_t (x_t-\bar x)^2}")
    nl = st.slider("Lags", 10, 60, 30, key="acf")
    a1, a2 = acf(D.r, nl), acf(D.r ** 2, nl)
    band = 1.96 / math.sqrt(len(D))
    fig = make_subplots(rows=1, cols=2, subplot_titles=("ACF of returns r", "ACF of squared returns r²"))
    fig.add_trace(go.Bar(x=list(range(1, nl + 1)), y=a1, marker_color=C.RAW), 1, 1)
    fig.add_trace(go.Bar(x=list(range(1, nl + 1)), y=a2, marker_color=C.DWT), 1, 2)
    for c in (1, 2):
        fig.add_hline(y=band, line_dash="dot", row=1, col=c)
        fig.add_hline(y=-band, line_dash="dot", row=1, col=c)
    fig.update_layout(height=280, showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Real data. Dotted lines: approximate 95% band for white noise.")

    term("Heteroskedasticity and the ARCH effect")
    st.markdown("**Heteroskedasticity** = changing variance. An **ARCH effect** means today's squared residual can be predicted "
                "from past squared residuals. The project tests it with Engle's auxiliary regression (12 lags):")
    st.latex(r"\hat e_t^2=c+\sum_{i=1}^{12}a_i\hat e_{t-i}^2+u_t,\qquad H_0:a_1=\dots=a_{12}=0\;(F\text{ test})")
    st.markdown("The serial-correlation test is the same regression on $\\hat e_t$ instead of $\\hat e_t^2$. Ljung-Box $Q(24)$ is also stored.")
    diag = C.read_csv("results/tables/initial_diagnostics.csv")
    dd = diag[(diag.dataset == ds) & (diag.period == "validation") & (diag.component == "x") &
              diag.model_id.isin(["raw_arima", "dwt_arima", "modwt_arima", "raw_garch", "dwt_garch", "modwt_garch"])]
    show = dd[["model_id", "p", "q", "standardized", "serial_F", "serial_F_p", "arch_F", "arch_F_p", "ljung_box_p"]].copy()
    show["model_id"] = show.model_id.map(C.friendly)
    st.dataframe(show.rename(columns={"standardized": "on z=e/sqrt(h)?"}), hide_index=True, width="stretch")
    sig_before = dd[dd.model_id.str.endswith("arima")].arch_F_p.lt(0.05).sum()
    sig_after = dd[dd.model_id.str.endswith("garch")].arch_F_p.lt(0.05).sum()
    st.caption(f"Real data, `tables/initial_diagnostics.csv`, first fit on the training window ending "
               f"{dd.origin_date.iloc[0] if len(dd) else ''}. ARCH test significant at 5% in {sig_before} of 3 ARMA fits "
               f"(before GARCH) and {sig_after} of 3 GARCH fits (on standardised innovations). A significant ARCH test motivates a "
               "variance model; it does not prove a better forecast.")

# ============================================================================ 2
with tabs[1]:
    term("ARMA(p, q): the conditional mean")
    st.markdown("**Intuition:** today's value is a constant plus a weighted sum of the last p values (AR part) and of the last q "
                "forecast errors (MA part). It models the *mean*, with a **constant** error variance.")
    st.latex(r"x_t=c+\sum_{i=1}^p\phi_i x_{t-i}+\varepsilon_t+\sum_{j=1}^q\theta_j\varepsilon_{t-j}")
    st.markdown(f"In the project, p and q are chosen by AIC over the grid $0\\le p,q\\le {cfg['max_pq']}$ on the training window; "
                "the order is then frozen. ARMA(p,q) is ARIMA(p,0,q): returns are not differenced again. "
                "R: `stats::arima` with exact Gaussian maximum likelihood.")
    c1, c2, c3 = st.columns(3)
    phi = c1.slider("AR coefficient φ1", -0.95, 0.95, 0.5, 0.05)
    th = c2.slider("MA coefficient θ1", -0.95, 0.95, 0.0, 0.05)
    seed = c3.number_input("seed", 1, 999, 7, key="armaseed")
    rng = np.random.default_rng(int(seed))
    eps = rng.standard_normal(400)
    x = np.zeros(400)
    for t in range(1, 400):
        x[t] = phi * x[t - 1] + eps[t] + th * eps[t - 1]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Simulated ARMA(1,1)", "Its ACF"), column_widths=[0.65, 0.35])
    fig.add_trace(go.Scatter(y=x, line=dict(color=C.RAW, width=1)), 1, 1)
    fig.add_trace(go.Bar(x=list(range(1, 21)), y=acf(x, 20), marker_color=C.RAW), 1, 2)
    fig.update_layout(height=260, showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")

    term("GARCH(1,1): the conditional variance")
    st.markdown("**Intuition:** tomorrow's variance = a floor ω + a reaction α to today's surprise + a memory β of today's variance. "
                "A large shock raises variance, which then decays slowly at rate α+β (the **persistence**).")
    st.latex(r"\varepsilon_t=\sqrt{h_t}\,z_t,\; z_t\stackrel{iid}{\sim}(0,1),\qquad h_t=\omega+\alpha\varepsilon_{t-1}^2+\beta h_{t-1}")
    st.latex(r"\bar h=\frac{\omega}{1-\alpha-\beta}\;(\alpha+\beta<1),\qquad E[h_{t+k}]-\bar h=(\alpha+\beta)^{k-1}(h_{t+1}-\bar h),"
             r"\qquad \text{half-life}=\frac{\ln 0.5}{\ln(\alpha+\beta)}")
    c1, c2, c3 = st.columns(3)
    al = c1.slider("α (reaction)", 0.0, 0.5, 0.08, 0.01)
    be = c2.slider("β (memory)", 0.0, 0.99, 0.90, 0.01)
    shock = c3.slider("shock size (in sd)", 1.0, 10.0, 5.0, 0.5)
    pers = al + be
    if pers >= 1:
        st.error(f"α+β = {pers:.2f} ≥ 1: not covariance-stationary, the long-run variance does not exist. "
                 "(The R code's parameter map forbids this: α and β are a softmax with slack below 1.)")
    else:
        hl = math.log(0.5) / math.log(pers) if pers > 0 else 0
        omega = 1 - pers  # long-run variance = 1
        k = np.arange(0, 120)
        h1 = omega + al * shock ** 2 + be * 1.0
        path = 1 + (h1 - 1) * pers ** k
        e, h = R.simulate_garch(1000, omega, al, be, seed=3)
        fig = make_subplots(rows=1, cols=2, subplot_titles=(f"Variance after a {shock:g}-sd shock (long-run = 1)",
                                                            "Simulated returns with this GARCH"))
        fig.add_trace(go.Scatter(x=k, y=path, line=dict(color=C.DWT)), 1, 1)
        fig.add_trace(go.Scatter(y=e, line=dict(color=C.GREY, width=0.7)), 1, 2)
        fig.add_trace(go.Scatter(y=2 * np.sqrt(h), line=dict(color=C.RAW, width=1)), 1, 2)
        fig.add_trace(go.Scatter(y=-2 * np.sqrt(h), line=dict(color=C.RAW, width=1)), 1, 2)
        fig.update_layout(height=300, showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width="stretch")
        st.markdown(f"Persistence α+β = **{pers:.2f}**; half-life of a variance shock ≈ **{hl:.1f} days**. "
                    "Blue lines in the right plot: ±2 conditional standard deviations.")
    par = C.read_csv("results/tables/initial_diagnostics.csv")
    par = par[(par.period == "validation") & par.model_id.isin(["raw_garch", "dwt_garch", "modwt_garch"])]
    par = par.assign(persistence=par.alpha + par.beta, dataset=par.dataset.map(C.label), model=par.model_id.map(C.friendly))
    st.markdown("**Fitted on real data** (first fit, training window ending 2009-12-31, `tables/initial_diagnostics.csv`):")
    st.dataframe(par[["dataset", "model", "p", "q", "omega", "alpha", "beta", "persistence"]], hide_index=True,
                 width="stretch")

    term("Two-step estimation")
    st.markdown("The project first fits the ARMA mean by Gaussian ML (constant variance), takes its residuals $\\hat e_t$ as fixed, "
                "then fits GARCH(1,1) to $\\hat e_t$ by ML. It is **not** joint ARMA-GARCH maximum likelihood (ARCHITECTURE.md). "
                "Between refits, coefficients are fixed and the ARMA state and GARCH variance are re-filtered every day on the "
                "current window, so a forecast never reuses a stale state.")

# ============================================================================ 3
with tabs[2]:
    term("Likelihood and maximum likelihood (MLE)")
    st.markdown("**Intuition:** the likelihood is the probability (density) of the data we actually observed, as a function of the "
                "parameters. MLE picks the parameters that make the observed data most probable. We maximise the log, ℓ.")
    st.latex(r"\ell(\omega,\alpha,\beta)=-\frac12\sum_{t}\Big[\ln(2\pi)+\ln h_t+\frac{\varepsilon_t^2}{h_t}\Big]\quad(\text{Gaussian GARCH})")
    st.markdown("Interactive: the log-likelihood of a Gaussian GARCH(1,1) on real residuals, as you move α with β fixed. "
                "The peak is (close to) the MLE.")
    x = D.r.tail(1024).to_numpy()
    e = x - x.mean()
    sc = math.sqrt(np.mean(e ** 2))
    z = e / sc
    bfix = st.slider("fixed β", 0.5, 0.97, 0.88, 0.01)
    alphas = np.linspace(0.005, min(0.5, 0.995 - bfix), 60)
    lls = []
    for a in alphas:
        om = 1 - a - bfix  # unit long-run variance (scaled data)
        h = R.garch_variances(z, om, a, bfix, 1.0)
        lls.append(-0.5 * np.sum(np.log(2 * np.pi) + np.log(h) + z ** 2 / h))
    fig = go.Figure(go.Scatter(x=alphas, y=lls, line=dict(color=C.RAW)))
    fig.update_layout(height=260, xaxis_title="α", yaxis_title="log-likelihood (scaled data)", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Real data: last 1,024 demeaned returns of {C.label(ds)}, with ω set so the long-run variance matches the sample.")

    term("AIC and BIC")
    st.markdown("**Intuition:** a better fit raises ℓ, but more parameters always help in-sample. AIC and BIC subtract a penalty "
                "for the number of parameters k. Lower is better. BIC penalises more (ln n > 2 when n > 7) so picks smaller models.")
    st.latex(r"\mathrm{AIC}=-2\ell+2k,\qquad \mathrm{BIC}=-2\ell+k\ln n")
    st.markdown("In `R/models.R`, k = number of ARMA coefficients + intercept + σ². "
                                "AIC values are only comparable for the **same series and sample**: never across markets or across raw and "
                "transformed inputs.")
    g = C.read_csv("results/tables/aic_candidate_grids.csv")
    mid = st.selectbox("Candidate grid for", ["raw_arima", "dwt_arima", "modwt_arima"], format_func=C.friendly)
    crit = st.radio("criterion", ["AIC", "BIC"], horizontal=True)
    gg = g[(g.dataset == ds) & (g.model_id == mid) & (g.component == "x")]
    if len(gg):
        piv = gg.pivot(index="p", columns="q", values=crit)
        dpiv = piv - np.nanmin(piv.values)
        fig = go.Figure(go.Heatmap(z=dpiv.values, x=[f"q={c}" for c in dpiv.columns], y=[f"p={i}" for i in dpiv.index],
                                   text=np.round(dpiv.values, 1), texttemplate="%{text}", colorscale="Blues", reversescale=True))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), title=f"Δ{crit} = {crit}(p,q) − min")
        st.plotly_chart(fig, width="stretch")
        best = gg.loc[gg[crit].idxmin()]
        chosen = gg[gg.chosen.astype(str).str.upper() == "TRUE"]
        st.caption(f"Real data, `tables/aic_candidate_grids.csv`. Minimum {crit}: ({int(best.p)},{int(best.q)}). "
                   f"Order used by the project (AIC): " +
                   (f"({int(chosen.p.iloc[0])},{int(chosen.q.iloc[0])})" if len(chosen) else "n/a") + ".")

# ============================================================================ 4
with tabs[3]:
    term("Innovation distributions: Gaussian, Student-t, GED")
    st.markdown("GARCH says $\\varepsilon_t=\\sqrt{h_t}z_t$. The **innovation** $z_t$ has mean 0 and variance 1, but its *shape* is a "
                "modelling choice. All three below are scaled to **unit variance**, so they differ only in shape.")
    st.latex(r"\text{Student-t: } f(z)=\frac{\Gamma(\frac{\nu+1}2)}{\Gamma(\frac\nu2)\sqrt{\pi(\nu-2)}}\Big(1+\frac{z^2}{\nu-2}\Big)^{-\frac{\nu+1}2},\;\nu>2")
    st.latex(r"\text{GED: } f(z)=\frac{b}{2a\,\Gamma(1/b)}\exp\!\big(-|z/a|^b\big),\quad a=\sqrt{\Gamma(1/b)/\Gamma(3/b)}")
    st.markdown("GED shape b = 2 is exactly Gaussian; b = 1 is Laplace; b < 2 gives fatter tails and a sharper peak. "
                "Student-t approaches Gaussian as ν → ∞. (Formulas as in `R/models.R` and `Distribution/innovation_distribution_robustness.R`.)")
    c1, c2, c3 = st.columns(3)
    nu = c1.slider("Student-t ν", 2.1, 30.0, 5.0, 0.1)
    b = c2.slider("GED shape b", 0.5, 3.0, 1.3, 0.05)
    logy = c3.checkbox("log scale (see the tails)", True)
    zs = np.linspace(-7, 7, 600)
    f_n = stats.norm.pdf(zs)
    f_t = np.exp(R.t_std_logpdf(zs, nu))
    f_g = np.exp(R.ged_logpdf(zs, b))
    fig = go.Figure()
    for y_, name, col in [(f_n, "Gaussian", C.DIST_COLOURS["gaussian"]), (f_t, f"Student-t ν={nu:g}", C.DIST_COLOURS["student_t"]),
                          (f_g, f"GED b={b:g}", C.DIST_COLOURS["ged"])]:
        fig.add_trace(go.Scatter(x=zs, y=y_, name=name, line=dict(color=col)))
    fig.update_layout(height=320, yaxis_type="log" if logy else "linear", margin=dict(l=10, r=10, t=10, b=10), xaxis_title="z")
    st.plotly_chart(fig, width="stretch")
    ks = [2, 3, 4, 5]
    t_scale = math.sqrt((nu - 2) / nu)
    a = math.sqrt(math.gamma(1 / b) / math.gamma(3 / b))
    tail = pd.DataFrame({
        "P(|z| > k)": [f"k = {k}" for k in ks],
        "Gaussian": [2 * stats.norm.sf(k) for k in ks],
        "Student-t": [2 * stats.t.sf(k / t_scale, nu) for k in ks],
        "GED": [special.gammaincc(1 / b, (k / a) ** b) for k in ks],
    })
    st.dataframe(tail.style.format({"Gaussian": "{:.2e}", "Student-t": "{:.2e}", "GED": "{:.2e}"}), hide_index=True,
                 width="stretch")
    st.markdown("**Why it matters:** if real innovations have fat tails, a Gaussian likelihood assigns almost negligible probability to each extreme day "
                "and over-reacts to it when estimating α and β. A fat-tailed likelihood can down-weight such days. "
                "Extension 1 tests whether this improves the *forecasts* (Results page).")

    term("Skewness, kurtosis and fat tails")
    st.latex(r"S=\frac{\frac1n\sum(x_i-\bar x)^3}{s^3},\qquad K=\frac{\frac1n\sum(x_i-\bar x)^4}{s^4}\quad(K=3\text{ for a normal})")
    mom = C.read_csv("derived/return_moments.csv")
    win = st.radio("Sample window", ["full_file", "2004-2014", "train_2004-2009"], horizontal=True)
    m = mom[mom.window == win].copy()
    m["dataset"] = m.dataset.map(C.label)
    st.dataframe(m[["dataset", "first", "last", "n_returns", "mean", "sd", "skewness", "kurtosis", "ljung_box_Q24_p",
                    "jarque_bera_p", "min_return", "max_return"]].style.format(
        {"mean": "{:.2e}", "sd": "{:.4f}", "skewness": "{:.2f}", "kurtosis": "{:.2f}", "ljung_box_Q24_p": "{:.2g}",
         "jarque_bera_p": "{:.2g}", "min_return": "{:.4f}", "max_return": "{:.4f}"}),
        hide_index=True, width="stretch")
    tun = mom[(mom.dataset == "tunisia") & (mom.window == "full_file")].iloc[0]
    st.caption(f"Computed by `tools/sync_data.py` from the prepared price files (decimal returns; Ljung-Box Q(24) on returns; "
               f"Jarque-Bera). Tunisia's kurtosis ({tun['kurtosis']:.1f}) is driven by two adjacent returns of about "
               f"{tun.min_return:+.4f} and {tun.max_return:+.4f} in September 2004, flagged in `data/issues.csv` and kept "
               "(no outlier removal). The paper's Table 1 (e.g. Nigeria kurtosis 272.37) uses 2000-2014 Datastream "
               "data and is not comparable with our prepared files.")

# ============================================================================ 5
with tabs[4]:
    term("Wavelets and wavelet filters (Haar, db4, db6)")
    st.markdown("**Intuition:** a wavelet transform splits a series into pieces that live at different **time scales**: a smooth "
                "slow part (approximation) and fast wiggles (details), while keeping *when* things happen. "
                "It works with a pair of filters: a low-pass **scaling** filter g (averages) and a high-pass **wavelet** filter h "
                "(differences), with $h_l=(-1)^l g_{L-1-l}$.")
    filt = st.radio("Filter", ["haar", "db4", "db6"], horizontal=True)
    g, h = W.wavelet_filter(filt)
    fig = make_subplots(rows=1, cols=2, subplot_titles=(f"scaling g ({len(g)} taps)", f"wavelet h ({len(h)} taps)"))
    fig.add_trace(go.Bar(y=g, marker_color=C.RAW), 1, 1)
    fig.add_trace(go.Bar(y=h, marker_color=C.DWT), 1, 2)
    fig.update_layout(height=250, showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")
    st.markdown("Haar is the simplest: $g=(1,1)/\\sqrt2$ (pairwise average), $h=(1,-1)/\\sqrt2$ (pairwise difference). "
                "'db4' and 'db6' (Daubechies) have 4 and 6 vanishing moments (8 and 12 taps): smoother, but longer, so more "
                "boundary effects. Coefficients are those in `R/wavelets.R`.")

    term("DWT vs MODWT: decimation, shift invariance, boundary")
    st.markdown(
        """
* **DWT** (discrete wavelet transform) filters and then keeps every second value (**decimation**, ↓2). Level j has n/2^j coefficients.
  Shifting the data by one day can change the coefficients completely (**not shift-invariant**).
* **MODWT** (maximal overlap DWT) uses rescaled filters $\\tilde g=g/\\sqrt2,\\ \\tilde h=h/\\sqrt2$ and **does not decimate**: one
  coefficient per day at every level, any sample length, and shifting the data just shifts the coefficients.
* **Boundary**: filters near the end of the sample need values beyond it. Using *future* values would leak information.
  The project reflects only the **observed prefix** (`decompose_prefix`), so components near today are less accurate (they lag).
        """)
    st.markdown("**In the core models we use one level of Haar on returns:**")
    st.latex(r"\text{MODWT detail: } w_t=\frac{r_t-r_{t-1}}{2}\qquad\text{paired DWT detail: } d_k=\frac{r_{2k}-r_{2k-1}}{\sqrt2}")
    nshow = 16
    rr = D.r.tail(nshow + 1).to_numpy()
    mod = R.causal_haar(rr)
    dwt = R.paired_haar(rr)
    shift = st.checkbox("Shift the window by one day (shift invariance test)")
    rr2 = D.r.iloc[-(nshow + 2):-1].to_numpy() if shift else rr
    mod2, dwt2 = R.causal_haar(rr2), R.paired_haar(rr2)
    fig = make_subplots(rows=1, cols=2, subplot_titles=(f"MODWT: {len(mod2)} details from {len(rr2)} returns",
                                                        f"paired DWT: {len(dwt2)} details from {len(rr2)} returns"))
    fig.add_trace(go.Bar(y=mod2 * 100, marker_color=C.MODWT), 1, 1)
    fig.add_trace(go.Bar(x=np.arange(1, 2 * len(dwt2), 2), y=dwt2 * 100, marker_color=C.DWT), 1, 2)
    fig.update_layout(height=260, showlegend=False, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="% ")
    st.plotly_chart(fig, width="stretch")
    st.caption("Real data, last returns. With the shift box ticked, the MODWT bars simply move one place; the DWT pairs are formed "
               "from different days, so the DWT values change. The DWT model also has only about half as many observations to fit.")

    term("Undoing the transform: restoring return moments")
    st.markdown("A model of $w_t$ forecasts $\\hat\\mu_w,\\hat h_w$ for tomorrow's detail. Since $r_{t+1}=r_t+2w_{t+1}$ and $r_t$ is "
                "known today:")
    st.latex(r"\text{MODWT: }\hat\mu_r=r_t+2\hat\mu_w,\ \hat h_r=4\hat h_w\qquad \text{DWT: }\hat\mu_r=r_t+\sqrt2\hat\mu_d,\ \hat h_r=2\hat h_d")
    st.markdown("Then $\\hat y=\\hat h_r+(\\hat\\mu_r-\\bar r^{(20)}_t)^2$ as for raw returns. Important consequence: the "
                "detail $w_t$ is a moving average of returns with an MA root at 1, so the ARMA fitted to it has to learn "
                "$(1-B)/2$. This motivated the **extra-MA-lag** variant (order (p, q+1) from the raw order).")

    term("Multiresolution analysis (MRA)")
    st.markdown("MRA re-assembles each level back on the time axis so the pieces **add up exactly** to the original: "
                "$y = A_J + D_J + \\dots + D_1$. Extension 2's component models apply this to the target y itself.")
    c1, c2, c3 = st.columns(3)
    meth = c1.radio("Method", ["modwt", "dwt"], horizontal=True)
    mf = c2.radio("Filter ", ["haar", "db4", "db6"], horizontal=True)
    J = c3.radio("Levels J", [1, 2], index=1, horizontal=True)
    yy = D.y.tail(256).to_numpy() * 1e4
    comps, _ = W.decompose_prefix(yy, meth, mf, J)
    fig = make_subplots(rows=len(comps) + 1, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        subplot_titles=["y (x 1e4)"] + list(comps.keys()))
    fig.add_trace(go.Scatter(y=yy, line=dict(color=C.ACTUAL, width=1)), 1, 1)
    for i, (k, v) in enumerate(comps.items(), start=2):
        fig.add_trace(go.Scatter(y=v, line=dict(color=C.MODWT if meth == "modwt" else C.DWT, width=1)), i, 1)
    fig.update_layout(height=120 * (len(comps) + 1) + 60, showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")
    err = np.max(np.abs(yy - sum(comps.values())))
    st.caption(f"Real data: last 256 targets. Max reconstruction error |y − ΣA,D| = {err:.1e} (exact additivity). "
               "Boundary: reflection of the observed prefix only.")

# ============================================================================ 6
with tabs[5]:
    term("Train / validation / test split")
    st.markdown(f"Chronological, never random. Train {cfg['training'][0]} to {cfg['training'][1]}: choose ARMA orders. "
                f"Validation {cfg['validation'][0]} to {cfg['validation'][1]}: choose among variants (wavelet filter/level, "
                f"MLP size, ensemble members). Test {cfg['test'][0]} to {cfg['test'][1]}: report. "
                f"Stocks continue {cfg['later'][0]} to {cfg['later'][1]} with everything frozen.")
    spl = C.read_csv("results/tables/splits.csv")
    spl["dataset"] = spl.dataset.map(C.label)
    st.dataframe(spl, hide_index=True, width="stretch")

    term("Rolling window and refit cadence")
    st.markdown(f"Each forecast uses only the latest **{cfg['max_window']:,}** returns (the window rolls forward one day at a time). "
                f"Re-estimating every model every day would be slow, so parameters are **refitted every {cfg['refit_every']} "
                f"origins**; in between, the coefficients are fixed but the filters run on the newest data. "
                "The sensitivity study tries windows 768/1,536 and cadences 40/60 (see Results).")
    win_ = st.slider("window (days)", 100, 1500, 400, 50)
    cad = st.slider("refit every (days)", 1, 60, 20)
    T = 120
    fig = go.Figure()
    for t in range(0, T, max(1, T // 12)):
        fig.add_trace(go.Scatter(x=[t - win_, t], y=[t, t], mode="lines", line=dict(color=C.RAW, width=4 if t % cad == 0 else 1),
                                 showlegend=False))
        fig.add_trace(go.Scatter(x=[t + 1], y=[t], mode="markers", marker=dict(color=C.PAPER, size=7), showlegend=False))
    fig.update_layout(height=260, xaxis_title="day", yaxis_title="forecast origin", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Blue bar: data used at that origin (thick = a refit day). Red dot: the day being forecast.")

    term("Look-ahead leakage")
    st.markdown("Using any information from the forecast date or later when building a forecast. Classic traps: decomposing the "
                "**whole** series with a wavelet (the filter at day t uses days after t), standardising with full-sample means, "
                "or choosing models on the test set. The project decomposes only the observed prefix, scales features with "
                "training data only, and freezes all choices before the test.")
    st.markdown("**Demo** (real data): a two-sided 5-day average of y 'predicts' y far better than an honest one-sided average, "
                "only because it peeks at tomorrow.")
    yv = D.y.to_numpy()
    honest = pd.Series(yv).rolling(5).mean().shift(1).to_numpy()
    leaky = pd.Series(yv).rolling(5, center=True).mean().to_numpy()
    ok = np.isfinite(honest) & np.isfinite(leaky)
    mh, ml = R.metrics(yv[ok], honest[ok]), R.metrics(yv[ok], leaky[ok])
    st.dataframe(pd.DataFrame([{"forecast": "honest (past 5 days)", **mh}, {"forecast": "leaky (centred, uses future)", **ml}]),
                 hide_index=True, width="stretch")

# ============================================================================ 7
with tabs[6]:
    term("MSE, RMSE, MAE, predictive R²")
    st.latex(r"\mathrm{MSE}=\frac1n\sum(y_t-\hat y_t)^2,\quad \mathrm{RMSE}=\sqrt{\mathrm{MSE}},\quad \mathrm{MAE}=\frac1n\sum|y_t-\hat y_t|,"
             r"\quad R^2=1-\frac{\sum(y_t-\hat y_t)^2}{\sum(y_t-\bar y)^2}")
    st.markdown("* MSE/RMSE punish big misses heavily (one crash day dominates). MAE is more robust.\n"
                "* Predictive R² compares with the test-sample mean; it is **not** a squared correlation and can be negative "
                "(worse than predicting the average).\n"
                "* Tables show RMSE and MAE × 10,000 because y is tiny (decimal squared returns).\n"
                "* **Matched dates**: models are compared only on dates where all of them produced a valid forecast; "
                "**coverage** = share of requested dates with a valid forecast.")

    term("Diebold-Mariano test (the idea)")
    st.markdown("Is model A's lower average loss more than luck? Take the loss difference $d_t=e_{A,t}^2-e_{B,t}^2$ and test "
                "whether its mean is zero, using a standard error that allows autocorrelation (HAC). "
                "**The project does not report DM tests**; it reports point differences and descriptive paired block-bootstrap "
                "intervals, not corrected for multiple comparisons. Below is a DM statistic computed *in this app* from the saved "
                "forecasts, for illustration only.")
    fc = C.forecasts(ds, "test")
    a_, b_ = st.columns(2)
    ma = a_.selectbox("model A", ["modwt_garch", "dwt_garch", "ensemble_modwt", "mlp"], format_func=C.friendly)
    mb = b_.selectbox("model B", ["raw_garch"], format_func=C.friendly)
    sub = fc[fc.model_id.isin([ma, mb])]
    sub = sub[C.valid_mask(sub)].pivot_table(index="target_date", columns="model_id", values=["actual", "prediction"])
    sub = sub.dropna()
    if len(sub) > 30:
        d = (sub[("actual", ma)] - sub[("prediction", ma)]) ** 2 - (sub[("actual", mb)] - sub[("prediction", mb)]) ** 2
        d = d.to_numpy()
        n = len(d)
        L = int(np.floor(n ** (1 / 3)))
        dc = d - d.mean()
        lrv = np.sum(dc ** 2) / n + 2 * sum((1 - l / (L + 1)) * np.sum(dc[l:] * dc[:-l]) / n for l in range(1, L + 1))
        dm = d.mean() / math.sqrt(lrv / n)
        st.markdown(f"{C.label(ds)}, 2012-2014, n = {n} matched dates: mean loss difference = {d.mean():.3e}, "
                    f"DM = **{dm:.2f}** (Newey-West, {L} lags), two-sided p ≈ **{2 * stats.norm.sf(abs(dm)):.3f}**. "
                    "Negative DM means A has lower MSE. |DM| < 1.96 means the difference is not distinguishable from noise at 5%.")

# ============================================================================ 8
with tabs[7]:
    term("Ensembles (equal-weight forecast averaging)")
    st.markdown("Average the forecasts of K models: $\\hat y^{ens}=\\frac1K\\sum_k\\hat y^{(k)}$. Errors that are not perfectly "
                "correlated partly cancel. No weights are fitted on test data. If any member fails on a date, the ensemble is "
                "marked unavailable (it never silently averages fewer members). Members are listed per dataset on the "
                "Architecture page.")
    term("Component (MRA) models of the target")
    st.markdown("Decompose past y into $A_J, D_J, \\dots, D_1$, forecast each component's next value with its own ARMA "
                "('all-ARMA') or ARMA for $A_J$ and AR(1) means with residual GARCH for details ('mixed'), then add the component "
                "mean forecasts and clip at zero. 2 transforms × 3 filters × 2 levels × 2 allocations = 24 models.")
    term("MLP (multilayer perceptron)")
    st.markdown("A small neural network: 7 inputs ($y_t,\\dots,y_{t-4}$, mean of last 5, mean of last 20), standardised with "
                "training statistics → one hidden layer of 3 or 5 **sigmoid** units → one linear output, rescaled and clipped at 0. "
                "Trained by squared error with weight **decay** (L2 penalty) 0.001 or 0.01, at most "
                f"{cfg.get('mlp_maxit', 300)} iterations (R `nnet`). Seeds 101/202/303 change the random starting weights: the "
                "spread across seeds shows how unstable a small network can be.")
    hs = st.slider("hidden units", 1, 8, 3)
    rng = np.random.default_rng(0)
    xs = np.linspace(-3, 3, 200)
    fig = go.Figure()
    for i in range(hs):
        w, b0 = rng.normal(0, 1.5), rng.normal(0, 1)
        fig.add_trace(go.Scatter(x=xs, y=1 / (1 + np.exp(-(w * xs + b0))), line=dict(width=1), name=f"unit {i + 1}"))
    fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10), title="random sigmoid units: the output is a weighted sum")
    st.plotly_chart(fig, width="stretch")
