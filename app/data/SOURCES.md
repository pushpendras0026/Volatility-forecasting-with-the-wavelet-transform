# Sources of app/data

All paths are relative to the project root (`Rhythm/`). Everything except `paper/` and `validation/` is
recreated by `tools/sync_data.py`; the exact per-file list with byte sizes is `SYNC_MANIFEST.csv`.
`<RUN>` = `submission/results/f5f86cf4d1fb` (from `submission/results/LATEST.txt`);
`<DIST>` = `submission/Distribution/results/1cec5bd53bb8` (from `submission/Distribution/LATEST.txt`).

| app/data path | Origin | Treatment |
|---|---|---|
| `prices/<dataset>.csv`, `prices/manifest.csv`, `prices/issues.csv` | `submission/data/` | byte copy |
| `results/tables/*.csv` (16 files) | `<RUN>/tables/` | byte copy |
| `results/run/SUMMARY.md`, `config.txt`, `frozen_parameter_choices.csv`, `parameter_validation_scores.csv`, `later_all_metrics.csv`, `sensitivity_plan.csv`, `historical_status.csv`, `later_status.csv`, `VERIFIED.txt` | `<RUN>/` | byte copy |
| `results/RUN_ID.txt` | name of `<RUN>` | written |
| `results/per_dataset/<ds>/{metrics, initial_orders, ensemble_selection, mlp_architecture_scores, mlp_validation_scores, modwt_validation_selection, component_validation_selection, split, frozen_registry}.csv` | `<RUN>/historical/baseline/<ds>/` | byte copy |
| `results/per_dataset/<stock>/later_metrics.csv` | `<RUN>/later/baseline/<stock>/metrics.csv` | byte copy |
| `results/per_dataset/<ds>/core_refit_parameters.csv.gz` | `<RUN>/historical/baseline/<ds>/{validation,test}/diagnostics.csv` | rows for the 11 core return models; columns dataset, period, model_id, component, origin_date, p, q, mean_AIC, omega, alpha, beta, nu, Ljung-Box/serial/ARCH p-values; gzip |
| `forecasts/test_<ds>.csv.gz` | `<RUN>/historical/baseline/<ds>/test_forecasts.csv` | all models; columns model_id, target_date, actual, prediction, return_mean, return_variance, moving_mean, fit_status, refitted; 12 significant digits; gzip |
| `forecasts/later_<stock>.csv.gz` | `<RUN>/later/baseline/<stock>/test_forecasts.csv` | as above |
| `forecasts/validation_core_<ds>.csv.gz` | `<RUN>/historical/baseline/<ds>/validation/forecasts.csv` | core models only, as above |
| `distribution/{innovation_distribution_comparison, heldout_win_counts, heldout_winners, fit_status_summary, baseline_reproduction, job_failures}.csv`, `COMPARISON.md` | `<DIST>/` | byte copy |
| `distribution/fit_attempts_all.csv.gz` | `<DIST>/<ds>/<pipeline>/fit_attempts.csv` (18 files) | row-bound; gzip |
| `distribution/forecasts/<ds>_<pipeline>_<period>.csv.gz` | `<DIST>/<ds>/<pipeline>/<period>/forecasts.csv` | slim columns as above; gzip |
| `legacy/{forecast_bias, structural_order_pairwise, calibrated_metrics, core_comparison_metrics, strategy_pairwise}.csv`, `source_run.txt`, `run_config.txt` | `final_latex_submission/generated/` | byte copy. **Older 2013-2014 run** (`project/output/05d2718a43f7`, now under `archive/`); shown only on the discrepancy tab |
| `derived/return_moments.csv` | computed from `prices/*.csv` by `sync_data.descriptive_stats` | r = diff(log(Price)); population mean/sd/skewness/kurtosis, Ljung-Box Q(24) on returns, Jarque-Bera, for the full file, 2004-2014 and 2004-2009 |
| `paper/*.csv`, `paper/README.md` | `archive/legacy_20261105/ATSA_MODWT_GARCH/papers/base_paper.pdf` | **hand transcription** (pdftotext); row alignment rules in `paper/README.md` |
| `validation/*` | `tools/validate_against_r.py` | Python re-implementation vs the R forecasts above |
| `SYNC_MANIFEST.csv` | `tools/sync_data.py` | per-file list |

## Other runs

`python tools/sync_data.py --code <folder> [--run <results/id>] [--dist <Distribution/results/id>] --tag <tag> --label "<text>"`
writes the same layout to `app/data_<tag>/` (with its own `RUN_INFO.txt` and `SYNC_MANIFEST.csv`). The app's sidebar
selector switches between `data/` (as submitted) and any `data_<tag>/`.
