"""Recreate app/data from the project sources (read-only).

Run from anywhere:
    python app/tools/sync_data.py            # uses ../.. as the project root
    python app/tools/sync_data.py --root C:/path/to/Rhythm

Only files under app/data are written. Project sources are never modified.
Hand-written files under app/data/paper/ (transcribed from the paper PDF) are
not touched by this script.

Large per-origin forecast files are slimmed (columns kept: see SLIM_COLS) and
written as gzip-compressed CSV. Values are written with 12 significant digits;
all summary tables are copied byte-for-byte.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

APP = Path(__file__).resolve().parents[1]
DATASETS = ["south_africa", "tunisia", "nigeria", "india_infosys", "usa_ibm", "google_class_a"]
STOCKS = ["india_infosys", "usa_ibm", "google_class_a"]
SLIM_COLS = ["model_id", "target_date", "actual", "prediction", "return_mean",
             "return_variance", "moving_mean", "fit_status", "refitted"]
CORE_DIAG_MODELS = ["raw_arima", "dwt_arima", "modwt_arima", "raw_garch", "dwt_garch", "modwt_garch",
                    "raw_garch_student_t", "dwt_garch_student_t", "modwt_garch_student_t",
                    "modwt_garch_structural", "modwt_garch_structural_student_t"]
DIAG_COLS = ["dataset", "period", "model_id", "component", "origin_date", "p", "q", "mean_AIC",
             "omega", "alpha", "beta", "nu", "ljung_box_p", "squared_ljung_box_p",
             "serial_F", "serial_F_p", "arch_F", "arch_F_p"]
FLOAT_FMT = "%.12g"


def latest(path: Path) -> str:
    """LATEST.txt holds an absolute path; only its final folder name is used."""
    return Path(path.read_text().strip().replace("\\", "/")).name


def copy(src: Path, dst: Path, log: list):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    log.append((dst, src))


def write_slim(df: pd.DataFrame, dst: Path, src_desc: str, log: list):
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dst, index=False, float_format=FLOAT_FMT, compression="gzip")
    log.append((dst, src_desc))


def slim_forecasts(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=lambda c: c in SLIM_COLS)
    return df[[c for c in SLIM_COLS if c in df.columns]]


def chi2_sf(x: float, df: int) -> float:
    try:
        from scipy.stats import chi2
        return float(chi2.sf(x, df))
    except ImportError:  # scipy is in requirements.txt; without it p-values are left blank
        return float("nan")


def descriptive_stats(prices_dir: Path) -> pd.DataFrame:
    """Return statistics computed from the prepared price files (same r as R: diff(log(Price)))."""
    rows = []
    for ds in DATASETS:
        p = pd.read_csv(prices_dir / f"{ds}.csv", parse_dates=["Date"])
        r = pd.Series(np.diff(np.log(p["Price"].to_numpy())), index=p["Date"].iloc[1:].to_numpy())
        windows = {"full_file": (None, None), "2004-2014": ("2004-01-01", "2014-12-31"),
                   "train_2004-2009": ("2004-01-01", "2009-12-31")}
        for name, (a, b) in windows.items():
            x = r
            if a:
                x = x[(x.index >= pd.Timestamp(a)) & (x.index <= pd.Timestamp(b))]
            v = x.to_numpy()
            n = len(v)
            m, s = v.mean(), v.std()  # population moments, as in the deck formula (1/n)
            skew = ((v - m) ** 3).mean() / s ** 3
            kurt = ((v - m) ** 4).mean() / s ** 4
            d = v - m
            acf = np.array([np.sum(d[k:] * d[:-k]) for k in range(1, 25)]) / np.sum(d ** 2)
            q24 = n * (n + 2) * np.sum(acf ** 2 / (n - np.arange(1, 25)))
            jb = n / 6 * (skew ** 2 + (kurt - 3) ** 2 / 4)
            rows.append(dict(dataset=ds, window=name, n_returns=n, first=str(x.index.min().date()),
                             last=str(x.index.max().date()), mean=m, sd=s, skewness=skew, kurtosis=kurt,
                             ljung_box_Q24=q24, ljung_box_Q24_p=chi2_sf(q24, 24),
                             jarque_bera=jb, jarque_bera_p=chi2_sf(jb, 2),
                             min_return=v.min(), max_return=v.max(),
                             share_abs_gt_3sd=float(np.mean(np.abs(v - m) > 3 * s))))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(APP.parent), help="project root (folder containing submission/)")
    ap.add_argument("--code", default=None,
                    help="code folder holding data/, results/LATEST.txt and Distribution/ (default <root>/submission)")
    ap.add_argument("--run", default=None, help="result run folder (default: from <code>/results/LATEST.txt)")
    ap.add_argument("--dist", default=None, help="Distribution run folder (default: from <code>/Distribution/LATEST.txt)")
    ap.add_argument("--tag", default="", help="empty = write app/data (as submitted); e.g. 'corrected' writes app/data_corrected")
    ap.add_argument("--label", default="As submitted (5 Nov 2026)", help="label shown in the app's run selector")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    sub = Path(args.code).resolve() if args.code else root / "submission"
    run = Path(args.run).resolve() if args.run else sub / "results" / latest(sub / "results" / "LATEST.txt")
    if args.dist:
        dist = Path(args.dist).resolve()
    else:
        dl = sub / "Distribution" / "LATEST.txt"
        dist = sub / "Distribution" / "results" / latest(dl) if dl.exists() else \
            root / "submission" / "Distribution" / "results" / latest(root / "submission" / "Distribution" / "LATEST.txt")
    legacy = root / "final_latex_submission" / "generated"
    out = APP / ("data" if not args.tag else f"data_{args.tag}")
    print(f"code={sub}\nrun={run}\ndist={dist}\nout={out}")
    log: list = []

    # Clean generated folders only (never data/paper, which is hand-written).
    for d in ["prices", "results", "forecasts", "distribution", "legacy", "derived"]:
        if (out / d).exists():
            shutil.rmtree(out / d)

    # 1. Prepared prices
    for f in ["manifest.csv", "issues.csv"] + [f"{d}.csv" for d in DATASETS]:
        copy(sub / "data" / f, out / "prices" / f, log)

    # 2. Final run summary tables (byte copies)
    for f in sorted((run / "tables").glob("*.csv")):
        copy(f, out / "results" / "tables" / f.name, log)
    for f in ["SUMMARY.md", "frozen_parameter_choices.csv", "parameter_validation_scores.csv",
              "later_all_metrics.csv", "sensitivity_plan.csv", "config.txt", "historical_status.csv",
              "later_status.csv", "VERIFIED.txt"]:
        if (run / f).exists():
            copy(run / f, out / "results" / "run" / f, log)
    (out / "results" / "RUN_ID.txt").write_text(run.name + "\n")
    (out / "RUN_INFO.txt").write_text(f"label={args.label}\nrun={run}\ndistribution={dist}\ncode={sub}\n".replace(str(root), "<project>"))
    log.append((out / "results" / "RUN_ID.txt", f"name of {run}"))

    # 3. Per-dataset small files, slim forecasts and GARCH refit parameters
    for ds in DATASETS:
        base = run / "historical" / "baseline" / ds
        for f in ["metrics.csv", "initial_orders.csv", "ensemble_selection.csv", "mlp_architecture_scores.csv",
                  "mlp_validation_scores.csv", "modwt_validation_selection.csv",
                  "component_validation_selection.csv", "split.csv", "frozen_registry.csv"]:
            copy(base / f, out / "results" / "per_dataset" / ds / f, log)
        write_slim(slim_forecasts(base / "test_forecasts.csv"), out / "forecasts" / f"test_{ds}.csv.gz",
                   f"{base / 'test_forecasts.csv'} (slimmed columns)", log)
        write_slim(slim_forecasts(base / "validation" / "forecasts.csv").query("model_id in @CORE_DIAG_MODELS"),
                   out / "forecasts" / f"validation_core_{ds}.csv.gz",
                   f"{base / 'validation' / 'forecasts.csv'} (core models, slimmed)", log)
        diags = []
        for period in ["validation", "test"]:
            d = pd.read_csv(base / period / "diagnostics.csv")
            diags.append(d[d.model_id.isin(CORE_DIAG_MODELS)][[c for c in DIAG_COLS if c in d.columns]])
        write_slim(pd.concat(diags), out / "results" / "per_dataset" / ds / "core_refit_parameters.csv.gz",
                   f"{base}/{{validation,test}}/diagnostics.csv (core models, selected columns)", log)
        if ds in STOCKS:
            lb = run / "later" / "baseline" / ds
            copy(lb / "metrics.csv", out / "results" / "per_dataset" / ds / "later_metrics.csv", log)
            write_slim(slim_forecasts(lb / "test_forecasts.csv"), out / "forecasts" / f"later_{ds}.csv.gz",
                       f"{lb / 'test_forecasts.csv'} (slimmed columns)", log)

    # 4. Distribution extension
    for f in ["innovation_distribution_comparison.csv", "heldout_win_counts.csv", "heldout_winners.csv",
              "fit_status_summary.csv", "baseline_reproduction.csv", "COMPARISON.md", "job_failures.csv"]:
        copy(dist / f, out / "distribution" / f, log)
    (out / "distribution" / "RUN_ID.txt").write_text(dist.name + "\n")
    attempts = []
    for ds in DATASETS:
        for pipe in ["raw_garch", "dwt_garch", "modwt_garch"]:
            d = dist / ds / pipe
            attempts.append(pd.read_csv(d / "fit_attempts.csv"))
            for period in ["test", "later"]:
                f = d / period / "forecasts.csv"
                if f.exists():
                    write_slim(slim_forecasts(f), out / "distribution" / "forecasts" / f"{ds}_{pipe}_{period}.csv.gz",
                               f"{f} (slimmed columns)", log)
    write_slim(pd.concat(attempts), out / "distribution" / "fit_attempts_all.csv.gz",
               f"{dist}/<dataset>/<pipeline>/fit_attempts.csv (row-bound)", log)

    # 5. Older lineage used by some slides
    for f in ["forecast_bias.csv", "structural_order_pairwise.csv", "calibrated_metrics.csv",
              "core_comparison_metrics.csv", "strategy_pairwise.csv", "source_run.txt", "run_config.txt"]:
        copy(legacy / f, out / "legacy" / f, log)

    # 6. Derived: descriptive statistics computed from the prepared prices
    stats = descriptive_stats(out / "prices")
    (out / "derived").mkdir(parents=True, exist_ok=True)
    stats.to_csv(out / "derived" / "return_moments.csv", index=False, float_format=FLOAT_FMT)
    log.append((out / "derived" / "return_moments.csv", "computed by sync_data.descriptive_stats from data/prices"))

    # Manifest of what was written
    rows = [dict(file=str(p.relative_to(APP)).replace("\\", "/"), bytes=p.stat().st_size,
                 source=str(s).replace(str(root), "<project>").replace("\\", "/")) for p, s in log]
    pd.DataFrame(rows).to_csv(out / "SYNC_MANIFEST.csv", index=False)
    total = sum(r["bytes"] for r in rows)
    print(f"Wrote {len(rows)} files, {total / 1e6:.1f} MB, run={run.name}, distribution={dist.name}")


if __name__ == "__main__":
    main()
