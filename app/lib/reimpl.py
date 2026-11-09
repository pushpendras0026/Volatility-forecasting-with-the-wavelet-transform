"""Python re-implementation of the core R pipelines, for learning.

Mirrors submission/R/models.R, wavelets.R and engine.R:
  * ARMA(p,q) mean with constant by exact Gaussian ML on x/sd(x)   (R: stats::arima, here statsmodels ARIMA)
  * GARCH(1,1) fitted in a second step to the fixed ARMA residuals  (R: stats::optim BFGS, here scipy BFGS)
      - same positive/stationary parameter map (softmax slack below alpha+beta=1)
      - same scaling z = e / sqrt(mean(e^2)), same initial variance h_1 = 1 (scaled), same two start points
      - Gaussian, variance-standardised Student-t (nu = 2 + exp(u4)), unit-variance GED (shape = exp(u4))
  * Haar transforms: MODWT detail w_t = (r_t - r_{t-1})/2 ; paired DWT detail (r_b - r_a)/sqrt(2)
  * moment restoration: MODWT mu_r = r_t + 2 mu_w, h_r = 4 h_w ; DWT mu_r = r_t + sqrt2 mu_d, h_r = 2 h_d
  * target forecast  yhat = h_r + (mu_r - mean(last 20 returns))^2
  * rolling window (last W returns), refit every K origins, exact state refiltering every day

Official numbers always come from the R code. Differences come from optimiser
details (R optim's finite-difference gradient and tolerances versus scipy's) and
from statsmodels' versus R's exact-likelihood ARMA implementations.
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field

import numpy as np
from scipy import optimize, signal, special

warnings.filterwarnings("ignore")


# ----------------------------------------------------------------------------- transforms
def causal_haar(r: np.ndarray) -> np.ndarray:
    return np.diff(r) / 2.0


def paired_haar(r: np.ndarray) -> np.ndarray:
    x = r[:-1]                      # r_t is the known anchor of the next pair (r_t, r_{t+1})
    if len(x) % 2:
        x = x[1:]
    pairs = x.reshape(-1, 2)
    return (pairs[:, 1] - pairs[:, 0]) / math.sqrt(2.0)


def transform_input(r: np.ndarray, transform: str) -> np.ndarray:
    if transform == "raw":
        return r
    if transform == "modwt":
        return causal_haar(r)
    if transform == "dwt":
        return paired_haar(r)
    raise ValueError(transform)


def restore(mu: float, h: float, last_r: float, transform: str) -> tuple[float, float]:
    if transform == "raw":
        return mu, h
    f = 2.0 if transform == "modwt" else math.sqrt(2.0)
    return last_r + f * mu, f * f * h


# ----------------------------------------------------------------------------- ARMA
@dataclass
class ArmaFit:
    p: int
    q: int
    scale: float
    params: np.ndarray
    sigma2: float
    loglik: float
    aic: float
    bic: float
    model: object = None


def _arima(z, p, q):
    from statsmodels.tsa.arima.model import ARIMA
    return ARIMA(z, order=(p, 0, q), trend="c")


def fit_arma(x: np.ndarray, p: int, q: int) -> ArmaFit:
    x = np.asarray(x, float)
    scale = float(np.std(x, ddof=1))
    z = x / scale
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = _arima(z, p, q).fit(method="statespace", method_kwargs={"maxiter": 300})
    n = len(x)
    k = len(res.params)                      # const + ar + ma + sigma2  (R: coef + 1)
    ll = float(res.llf) - n * math.log(scale)
    return ArmaFit(p, q, scale, np.asarray(res.params), float(res.params[-1]) * scale ** 2, ll,
                   -2 * ll + 2 * k, -2 * ll + math.log(n) * k, res)


def filter_arma(fit: ArmaFit, x: np.ndarray) -> tuple[np.ndarray, float]:
    """Exact Kalman refilter with fixed parameters; returns residuals and one-step mean forecast."""
    z = np.asarray(x, float) / fit.scale
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = _arima(z, fit.p, fit.q).filter(fit.params)
    e = np.asarray(res.resid) * fit.scale
    mu = float(res.forecast(1)[0]) * fit.scale
    return e, mu


def select_arma(x: np.ndarray, max_pq: int = 3, criterion: str = "AIC"):
    rows, best = [], None
    for p in range(max_pq + 1):
        for q in range(max_pq + 1):
            try:
                f = fit_arma(x, p, q)
                val = f.aic if criterion == "AIC" else f.bic
                rows.append(dict(p=p, q=q, AIC=f.aic, BIC=f.bic, loglik=f.loglik))
                if best is None or val < best[0]:
                    best = (val, p, q)
            except Exception as exc:  # noqa: BLE001
                rows.append(dict(p=p, q=q, AIC=np.nan, BIC=np.nan, loglik=np.nan, error=str(exc)))
    return best[1], best[2], rows


# ----------------------------------------------------------------------------- GARCH
def garch_parameters(u):
    a, b = math.exp(u[1]), math.exp(u[2])
    den = 1.0 + a + b
    return math.exp(u[0]), a / den, b / den


def garch_variances(e: np.ndarray, omega: float, alpha: float, beta: float, h1: float) -> np.ndarray:
    drive = omega + alpha * np.concatenate(([0.0], e[:-1] ** 2))
    drive[0] = h1
    return signal.lfilter([1.0], [1.0, -beta], drive)


def ged_logpdf(z, shape):
    log_a = 0.5 * (special.gammaln(1 / shape) - special.gammaln(3 / shape))
    return math.log(shape) - math.log(2) - log_a - special.gammaln(1 / shape) - np.exp(shape * (np.log(np.abs(z) + 1e-300) - log_a))


def t_std_logpdf(z, nu):
    return (special.gammaln((nu + 1) / 2) - special.gammaln(nu / 2) - 0.5 * math.log(math.pi * (nu - 2))
            - ((nu + 1) / 2) * np.log1p(z ** 2 / (nu - 2)))


STARTS = {
    "gaussian": [[math.log(.05), math.log(.10 / .05), math.log(.85 / .05)],
                 [math.log(.15), math.log(.15 / .15), math.log(.70 / .15)]],
    "student_t": [[math.log(.05), math.log(2), math.log(17), math.log(6)],
                  [math.log(.15), 0.0, math.log(.7 / .15), math.log(3)]],
    "ged": [[math.log(.05), math.log(2), math.log(17), math.log(2)],
            [math.log(.15), 0.0, math.log(.7 / .15), math.log(1.5)]],
}


@dataclass
class GarchFit:
    omega: float
    alpha: float
    beta: float
    initial_variance: float
    distribution: str
    shape: float = float("nan")   # nu for Student-t, GED shape for GED
    loglik: float = float("nan")
    aic: float = float("nan")
    k: int = 3
    converged: bool = True


def fit_garch11(e: np.ndarray, distribution: str = "gaussian") -> GarchFit:
    e = np.asarray(e, float)
    sc = math.sqrt(float(np.mean(e ** 2)))
    z = e / sc

    def objective(u):
        if not np.all(np.isfinite(u)) or np.any(np.abs(u) > 30):
            return 1e15
        om, al, be = garch_parameters(u)
        h = garch_variances(z, om, al, be, 1.0)
        if not np.all(np.isfinite(h)) or np.any(h <= 0):
            return 1e15
        if distribution == "gaussian":
            v = 0.5 * np.sum(math.log(2 * math.pi) + np.log(h) + z ** 2 / h)
        elif distribution == "student_t":
            nu = 2 + math.exp(u[3])
            v = -np.sum(t_std_logpdf(z / np.sqrt(h), nu) - 0.5 * np.log(h))
        else:
            shape = math.exp(u[3])
            if shape < .1 or shape > 100:
                return 1e15
            v = -np.sum(ged_logpdf(z / np.sqrt(h), shape) - 0.5 * np.log(h))
        return float(v) if np.isfinite(v) else 1e15

    best = None
    for s in STARTS[distribution]:
        try:
            r = optimize.minimize(objective, np.array(s), method="BFGS",
                                  options={"maxiter": 350 if distribution != "gaussian" else 250})
        except Exception:  # noqa: BLE001
            continue
        if np.isfinite(r.fun) and r.fun < 1e14 and (best is None or r.fun < best.fun):
            best = r
    if best is None:
        raise RuntimeError("GARCH(1,1) did not converge")
    om, al, be = garch_parameters(best.x[:3])
    k = 3 if distribution == "gaussian" else 4
    ll = -best.fun - len(e) * math.log(sc)
    shape = float("nan")
    if distribution == "student_t":
        shape = 2 + math.exp(best.x[3])
    elif distribution == "ged":
        shape = math.exp(best.x[3])
    return GarchFit(om * sc ** 2, al, be, sc ** 2, distribution, shape, ll, -2 * ll + 2 * k, k, bool(best.success))


def forecast_garch(fit: GarchFit, e: np.ndarray) -> float:
    h = garch_variances(e, fit.omega, fit.alpha, fit.beta, fit.initial_variance)
    return fit.omega + fit.alpha * e[-1] ** 2 + fit.beta * h[-1]


# ----------------------------------------------------------------------------- rolling loop
@dataclass
class RollingResult:
    rows: list = field(default_factory=list)
    refits: list = field(default_factory=list)


def rolling_forecast(dates, r: np.ndarray, target_idx, transform: str, p: int, q: int,
                     distribution: str = "gaussian", window: int = 1024, refit_every: int = 20,
                     mean_window: int = 20, refit_targets=None, progress=None) -> RollingResult:
    """One-step forecasts of y for each target index i (target r[i], origin i-1).

    refit_targets: optional set of target indices at which to refit (to replay the R schedule);
    otherwise refit when origin - last_refit_origin >= refit_every.
    """
    out = RollingResult()
    arma = garch = None
    last_origin = -10 ** 9
    n_t = len(target_idx)
    for j, i in enumerate(target_idx):
        origin = i - 1
        past = r[: i]
        rw = past[-window:]
        x = transform_input(rw, transform)
        refit = arma is None or (origin - last_origin >= refit_every if refit_targets is None else i in refit_targets)
        status, err = "ok", ""
        try:
            if refit:
                arma = fit_arma(x, p, q)
                e0, _ = filter_arma(arma, x)
                garch = fit_garch11(e0, distribution)
                last_origin = origin
                out.refits.append(dict(target_date=dates[i], origin_date=dates[origin], omega=garch.omega,
                                       alpha=garch.alpha, beta=garch.beta, shape=garch.shape,
                                       garch_loglik=garch.loglik, arma_aic=arma.aic, n=len(x)))
            e, mu_x = filter_arma(arma, x)
            h_x = forecast_garch(garch, e)
            mu, h = restore(mu_x, h_x, past[-1], transform)
            ma = float(np.mean(past[-mean_window:]))
            pred = h + (mu - ma) ** 2
        except Exception as exc:  # noqa: BLE001
            status, err, pred, mu, h, ma = "failed", str(exc), np.nan, np.nan, np.nan, float(np.mean(past[-mean_window:]))
        actual = (r[i] - float(np.mean(r[i - mean_window: i]))) ** 2
        out.rows.append(dict(target_date=dates[i], actual=actual, prediction=pred, return_mean=mu,
                             return_variance=h, moving_mean=ma, refitted=refit, fit_status=status, error=err))
        if progress is not None:
            progress((j + 1) / n_t)
    return out


# ----------------------------------------------------------------------------- simulator
def simulate_garch(n: int, omega: float, alpha: float, beta: float, distribution: str = "gaussian",
                   shape: float = 6.0, seed: int = 1):
    rng = np.random.default_rng(seed)
    if distribution == "gaussian":
        z = rng.standard_normal(n)
    elif distribution == "student_t":
        z = rng.standard_t(shape, n) * math.sqrt((shape - 2) / shape)
    else:
        # GED with unit variance: |z/a|^b ~ Gamma(1/b, 1)
        a = math.sqrt(math.gamma(1 / shape) / math.gamma(3 / shape))
        g = rng.gamma(1 / shape, 1.0, n)
        z = a * g ** (1 / shape) * rng.choice([-1.0, 1.0], n)
    h = np.empty(n)
    e = np.empty(n)
    h[0] = omega / max(1e-12, 1 - alpha - beta) if alpha + beta < 1 else omega * 10
    e[0] = math.sqrt(h[0]) * z[0]
    for t in range(1, n):
        h[t] = omega + alpha * e[t - 1] ** 2 + beta * h[t - 1]
        e[t] = math.sqrt(h[t]) * z[t]
    return e, h


def metrics(actual, pred) -> dict:
    a, p = np.asarray(actual, float), np.asarray(pred, float)
    ok = np.isfinite(a) & np.isfinite(p)
    a, p = a[ok], p[ok]
    err = a - p
    tv = np.sum((a - a.mean()) ** 2)
    mse = float(np.mean(err ** 2))
    return dict(n=int(ok.sum()), MSE=mse, RMSE=math.sqrt(mse), MAE=float(np.mean(np.abs(err))),
                R2=float(1 - np.sum(err ** 2) / tv) if tv > 0 else float("nan"))
