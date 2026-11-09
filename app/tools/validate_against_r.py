"""Validate the Python re-implementation (lib/reimpl.py) against the saved R forecasts.

For each case we replay the R refit schedule (the dates where R's `refitted` flag is TRUE),
starting at the first test-period refit so both implementations begin from a fresh fit,
using the R frozen ARMA order. We then compare per-date forecasts and GARCH parameters.

Writes app/data/validation/*.csv and app/VALIDATION.md.
Run:  app/.venv/Scripts/python.exe app/tools/validate_against_r.py [--n 120]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from lib import reimpl as R  # noqa: E402

DATA = APP / "data"
CASES = [  # dataset, transform, distribution, R model id, source
    ("south_africa", "raw", "gaussian", "raw_garch", "main"),
    ("south_africa", "modwt", "gaussian", "modwt_garch", "main"),
    ("south_africa", "dwt", "gaussian", "dwt_garch", "main"),
    ("south_africa", "raw", "student_t", "raw_garch_student_t", "main"),
    ("south_africa", "raw", "ged", "raw_garch__ged", "dist"),
    ("nigeria", "raw", "gaussian", "raw_garch", "main"),
    ("nigeria", "modwt", "gaussian", "modwt_garch", "main"),
]


def series(ds):
    p = pd.read_csv(DATA / "prices" / f"{ds}.csv", parse_dates=["Date"])
    r = np.diff(np.log(p.Price.to_numpy()))
    return p.Date.iloc[1:].reset_index(drop=True), r


def order(ds, model_id):
    o = pd.read_csv(DATA / "results" / "per_dataset" / ds / "initial_orders.csv")
    sister = model_id.replace("__ged", "").replace("_student_t", "")
    row = o[(o.model_id == sister) & (o.component == "x")].iloc[0]
    return int(row.p), int(row.q)


def r_forecasts(ds, model_id, source, transform):
    if source == "main":
        f = pd.read_csv(DATA / "forecasts" / f"test_{ds}.csv.gz", parse_dates=["target_date"])
        f = f[f.model_id == model_id]
    else:
        f = pd.read_csv(DATA / "distribution" / "forecasts" / f"{ds}_{transform}_garch_test.csv.gz", parse_dates=["target_date"])
        f = f[f.model_id == model_id]
    return f.sort_values("target_date").reset_index(drop=True)


def r_params(ds, model_id, source):
    if source == "main":
        d = pd.read_csv(DATA / "results" / "per_dataset" / ds / "core_refit_parameters.csv.gz")
        d = d[(d.model_id == model_id) & (d.period == "test")][["origin_date", "omega", "alpha", "beta", "nu"]]
        return d.rename(columns={"nu": "shape"})
    a = pd.read_csv(DATA / "distribution" / "fit_attempts_all.csv.gz")
    a = a[(a.dataset == ds) & (a.model_id == model_id) & (a.period == "test")]
    return a[["origin_date", "omega", "alpha", "beta", "ged_shape"]].rename(columns={"ged_shape": "shape"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120, help="number of test dates per case")
    args = ap.parse_args()
    out = DATA / "validation"
    out.mkdir(parents=True, exist_ok=True)
    allf, allp, summ = [], [], []
    for ds, tr, dist, mid, src in CASES:
        t0 = time.time()
        dates, r = series(ds)
        rf = r_forecasts(ds, mid, src, tr)
        first = rf.index[rf.refitted.astype(str).str.upper() == "TRUE"][0]
        rf = rf.iloc[first: first + args.n].reset_index(drop=True)
        idx = {d: i for i, d in enumerate(dates)}
        tidx = [idx[d] for d in rf.target_date]
        refits = {idx[d] for d, f in zip(rf.target_date, rf.refitted.astype(str).str.upper()) if f == "TRUE"}
        p, q = order(ds, mid)
        res = R.rolling_forecast(dates.to_numpy(), r, tidx, tr, p, q, dist, window=1024, refit_every=20,
                                 refit_targets=refits)
        py = pd.DataFrame(res.rows)
        m = rf[["target_date", "actual", "prediction", "return_mean", "return_variance"]].merge(
            py[["target_date", "actual", "prediction", "return_mean", "return_variance", "fit_status"]],
            on="target_date", suffixes=("_R", "_py"))
        m.insert(0, "case", f"{ds}/{mid}")
        m["rel_diff_prediction"] = (m.prediction_py - m.prediction_R) / m.prediction_R
        allf.append(m)
        pr = pd.DataFrame(res.refits)
        pr["origin_date"] = pd.to_datetime(pr.origin_date).dt.strftime("%Y-%m-%d")
        rp = r_params(ds, mid, src)
        pm = rp.merge(pr[["origin_date", "omega", "alpha", "beta", "shape"]], on="origin_date", suffixes=("_R", "_py"))
        pm.insert(0, "case", f"{ds}/{mid}")
        allp.append(pm)
        ok = m.dropna(subset=["prediction_py", "prediction_R"])
        mse_R = np.mean((ok.actual_R - ok.prediction_R) ** 2)
        mse_py = np.mean((ok.actual_R - ok.prediction_py) ** 2)
        summ.append(dict(case=f"{ds}/{mid}", dataset=ds, transform=tr, distribution=dist, arma=f"({p},{q})",
                         first_date=str(rf.target_date.min().date()), last_date=str(rf.target_date.max().date()),
                         n=len(ok), refits=len(refits),
                         max_abs_actual_diff=float(np.max(np.abs(ok.actual_R - ok.actual_py))),
                         median_abs_rel_diff_pct=100 * float(np.median(np.abs(ok.rel_diff_prediction))),
                         max_abs_rel_diff_pct=100 * float(np.max(np.abs(ok.rel_diff_prediction))),
                         corr=float(np.corrcoef(ok.prediction_R, ok.prediction_py)[0, 1]),
                         MSE_R=mse_R, MSE_py=mse_py, MSE_diff_pct=100 * (mse_py - mse_R) / mse_R,
                         max_abs_alpha_diff=float(np.max(np.abs(pm.alpha_R - pm.alpha_py))) if len(pm) else np.nan,
                         max_abs_beta_diff=float(np.max(np.abs(pm.beta_R - pm.beta_py))) if len(pm) else np.nan,
                         py_failures=int((py.fit_status != "ok").sum()), seconds=time.time() - t0))
        print(summ[-1]["case"], f"{summ[-1]['median_abs_rel_diff_pct']:.4f}% median, {summ[-1]['seconds']:.0f}s", flush=True)
    F, P, S = pd.concat(allf), pd.concat(allp), pd.DataFrame(summ)
    F.to_csv(out / "validation_forecasts.csv.gz", index=False, float_format="%.12g", compression="gzip")
    P.to_csv(out / "validation_params.csv", index=False, float_format="%.10g")
    S.to_csv(out / "validation_summary.csv", index=False, float_format="%.6g")
    write_md(S, P, args.n)


def write_md(S, P, n):
    lines = [
        "# Validation of the Python re-implementation against the R outputs",
        "",
        "Generated by `tools/validate_against_r.py` (rerun it to refresh). The Parameter lab uses `lib/reimpl.py`, a Python",
        "re-implementation written for learning. **Official numbers come from the R code** in `submission/R/`.",
        "",
        "## Protocol",
        "",
        f"- For each case, take the first {n} historical-test dates starting at the first date on which R refitted the model",
        "  (so both implementations start from a fresh fit), and replay R's exact refit dates (`refitted == TRUE`).",
        "- Same data file, same frozen ARMA order (`initial_orders.csv`), 1,024-return window, same target definition,",
        "  same Haar transform and moment restoration, same GARCH parameter map, scaling, initial variance and start points.",
        "- Differences that remain by design: ARMA is estimated with statsmodels' exact Kalman likelihood instead of R's",
        "  `stats::arima` (CSS-ML); GARCH uses scipy BFGS with analytic-free numerical gradients instead of R `optim` BFGS",
        "  (different finite-difference steps and stopping tolerances).",
        "- R forecasts: `data/forecasts/test_<dataset>.csv.gz` (main run) or `data/distribution/forecasts/` (GED).",
        "  R GARCH parameters: `core_refit_parameters.csv.gz` (diagnostics.csv) or `fit_attempts_all.csv.gz` (GED).",
        "",
        "## Results",
        "",
        "| case | ARMA | dates | n | refits | median abs. rel. diff of forecast | max abs. rel. diff | corr | MSE diff (py vs R) | max abs Δα | max abs Δβ |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, s in S.iterrows():
        lines.append(f"| {s.case} | {s.arma} | {s.first_date} to {s.last_date} | {s.n} | {s.refits} | "
                     f"{s.median_abs_rel_diff_pct:.3f}% | {s.max_abs_rel_diff_pct:.3f}% | {s["corr"]:.6f} | "
                     f"{s.MSE_diff_pct:+.3f}% | {s.max_abs_alpha_diff:.2e} | {s.max_abs_beta_diff:.2e} |")
    lines += [
        "",
        f"The target `actual` agreed to within {S.max_abs_actual_diff.max():.1e} in every case (identical definition).",
        "",
        "## Reading the result honestly",
        "",
        "- Agreement is close but not bit-exact. Forecast differences come from slightly different optimum points of",
        "  the ARMA and GARCH likelihoods (different optimisers), which then propagate through the filters.",
    ]
    F = pd.read_csv(DATA / "validation" / "validation_forecasts.csv.gz")
    for case, g in F.groupby("case"):
        a = g.rel_diff_prediction.abs()
        worst = g.loc[a.idxmax()]
        lines.append(f"- `{case}`: {int((a > 0.01).sum())} of {len(g)} dates differ by more than 1%; largest on "
                     f"{worst.target_date} (R {worst.prediction_R:.3e}, Python {worst.prediction_py:.3e}).")
    lines += [
        "- Raw-return GARCH (Gaussian, Student-t, GED) agrees to a few thousandths of a percent: the implementation of",
        "  the target, GARCH likelihoods, parameter map and rolling loop is the same.",
        "- The MODWT and DWT cases differ more, and not uniformly (Nigeria MODWT stays within 1%; South Africa MODWT",
        "  and DWT do not). Likely cause (not proven here, because R's ARMA coefficients are only stored in .rds files):",
        "  the Haar MODWT detail has an MA root at one, which makes the ARMA likelihood flat near the optimum, and",
        "  paired DWT fits only about 511 values; statsmodels and R's `arima` can then stop at different coefficients",
        "  or local optima, and the difference persists until the next refit.",
        "- The lab is therefore suitable for learning how parameters change forecasts, not for reproducing the official",
        "  tables to the last digit. All tables and plots on the Results page are read from the saved R outputs.",
        "",
        "Per-date comparisons: `data/validation/validation_forecasts.csv.gz`; refit parameters: `data/validation/validation_params.csv`.",
    ]
    (APP / "VALIDATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
