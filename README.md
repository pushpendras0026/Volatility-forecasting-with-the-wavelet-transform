# Wavelet + GARCH volatility forecasting: final code submission (DA-3041, Group 9)

Code for the DA-3041 Group 9 project. It contains one model
implementation, one configuration, six prepared datasets, the parallel experiment
runner, tests, the Innovation-distribution extension (`Distribution/`) and the
results of the final run.

## Run

Requirements: R 4.6.x with the recommended package `nnet`. No other R package,
no Python, no internet connection. Tested with R 4.6.2 (Windows, ucrt) and
nnet 7.3-21.

One command (any platform), from this folder or with its path:

```sh
Rscript run_all.R --workers 16        # or: ./reproduce.ps1 -Workers 16 ; sh reproduce.sh 16
```

`run_all.R` runs, in fresh R processes, stopping at the first failure:

| Step | Script | Writes |
|---|---|---|
| 1 | `tests/run_tests.R` | nothing (temporary directory only) |
| 2 | `tests/test_stat_tests.R` | nothing (temporary directory only) |
| 3 | `run.R --workers N` | `results/<run id>/`, then `results/LATEST.txt` |
| 4 | `tools/analyze.R` | `results/<run id>/tables/`, `SUMMARY.md`, `VERIFIED.txt`; copies `SUMMARY.md` to `results/` |
| 5 | `tools/figures.R` | `results/<run id>/figures/` |
| 6 | `Distribution/tests.R` | nothing (temporary directory only) |
| 7 | `Distribution/innovation_distribution_robustness.R --workers N` | `Distribution/results/<id>/`, then `Distribution/LATEST.txt` |
| 8 | `Distribution/report.R` | `COMPARISON.md` and summary CSVs in that folder |
| 9 | `tools/package.R` | `FILE_SHA256SUMS.csv` (SHA-256 of every file) |

The steps can also be run one by one with `Rscript <script>`. `tools/progress.R`
shows the progress of a running `run.R`.

The recorded model-fitting time of the final run is about 3.8 CPU-hours in total
(`tables/timing.csv`), spread over the workers; with one worker it all runs in sequence.

## Reproducibility

- **Run id.** `results/<run id>` is a hash of the scientific configuration and
  the content of `R/`, `config/`, `run.R` and `data/`, keyed by paths relative to
  this folder, with carriage returns removed before hashing. The id is therefore
  the same wherever the folder is copied, however `run.R` is invoked, and after
  line-ending conversion. Worker count and CLI flags are not part of it.
- **Resume.** Completed jobs inside an identical run id are reused; interrupted
  jobs restart from scratch.
- **Pointers.** `results/LATEST.txt` and `Distribution/LATEST.txt` hold relative
  paths (`results/<id>`) and are written only when a run completes. While
  `run.R` is running, `results/RUNNING.txt` names the run in progress.
- **Determinism.** The forecasts do not depend on the worker count or on job
  scheduling. Re-running gives
  bit-identical forecasts, metrics and tables. The only fields that change between
  re-runs are wall-clock values (`elapsed_seconds` in forecast files,
  `median_seconds`/`total_seconds` in per-job `metrics.csv` and `tables/timing.csv`,
  timestamps in `progress.csv`, `frozen_at` inside `frozen_parameter_choices.rds`)
  and the environment records `config.txt`/`sessionInfo.txt`.
- **Data integrity.** `data/manifest.csv` records the original CRLF file MD5
  (`prepared_md5`) and a line-ending-independent MD5 (`content_md5_lf`), which the
  loader checks. `.gitattributes` keeps CSV files byte-exact under git.
- **Tests never write into this folder.**

## Data and periods

South Africa, Tunisia and Nigeria (indices) and Infosys, IBM and Google (stocks).
Initial training 2004-2009, validation 2010-2011, historical test 2012-2014. The
stocks also have a later evaluation, 2015-2025. Google begins at its August 2004
listing. All available trading dates are used; there is no random split,
interpolation or backfill. Known data issues (for example Tunisia's -0.27/+0.27
returns on 15-16 September 2004) are listed in `data/issues.csv` and kept.

Model orders, ensemble membership, neural-network hyperparameters and
sensitivity choices are frozen on the validation period. Parameters keep refitting
on observed data under the rolling protocol. The later stock period was seen in
earlier exploratory work, so it is a retrospective robustness check, not an
untouched holdout.

## Models

Target: `y[t+1] = (r[t+1] - mean(r[t-19..t]))^2` on decimal log returns.

- Core return models: raw, paired Haar DWT and overlapping Haar MODWT inputs, each
  with an ARMA mean (orders by AIC on the last 1,024 training returns) and, for the
  GARCH variants, Gaussian or Student-t GARCH(1,1) fitted in a second step.
  Fitting window 1,024 observations, refit every 20 observations.
- Extension models: structural MODWT (raw order plus one MA lag), direct-target
  ARMA, 24 multiresolution (MRA) component models (DWT/MODWT x Haar/db4/db6 x
  J=1/2 x all-ARMA/mixed), three equal-weight ensembles, and an MLP with three
  reported seeds.
- Sensitivity study: windows 768/1,024/1,536, refit cadence 20/40/60, AIC/BIC and
  order caps 3/5, one change at a time, for the three core GARCH pipelines.
- `Distribution/`: Gaussian, Student-t and GED innovations for the three core
  GARCH pipelines (separate experiment; see `Distribution/README.md`).

`ARCHITECTURE.md` gives the block diagrams and equations (including the paired-DWT
restoration). `METHODS.md` covers selection, sample rules for every
score, the descriptive/normality/stationarity tests and the limits of the evidence.

## Where the results are

- `results/LATEST.txt` names the final run. Its `SUMMARY.md` (copied to
  `results/SUMMARY.md`) gives the headline tables with the matched-date sample of
  every number.
- `results/<id>/tables/`: all score tables (each has a `sample_rule` column),
  `sample_reconciliation.csv` (one model under every sample rule),
  `descriptive_normality_stationarity.csv`, diagnostics and AIC grids.
- `Distribution/results/<id>/COMPARISON.md` and its CSVs.

## Zipped raw outputs

To keep every file well under GitHub's size limit, the per-job raw outputs (forecasts,
diagnostics, fitted plans) are stored as zip files:

- `results/4a2eba328565/zipped/*.zip` -> `results/4a2eba328565/historical/` and `later/`
- `Distribution/results/012f70154fae/zipped/*.zip` -> the per-series folders

Every zip stores paths relative to the repository root, so unzip them **at the
repository root** (for example `for f in results/*/zipped/*.zip Distribution/results/*/zipped/*.zip; do unzip -o "$f"; done`)
before running `tools/analyze.R`, `tools/figures.R` or `Distribution/report.R` on the
saved run. The tables, figures and `SUMMARY.md` files are already unzipped. A fresh
`Rscript run_all.R` does not need the zips at all; it recomputes everything.

## Layout

- `R/`: the causal forecast loop and the model, wavelet, MLP, ensemble, metric and data functions.
- `config/experiment.R`: every scientific choice and the parameter grid.
- `data/`: the six prepared CSVs, `manifest.csv` (provenance and checksums), `issues.csv`.
- `tests/`: unit and leakage tests; `test_stat_tests.R` validates the statistical tests against independent reference values in `tests/reference/`.
- `tools/`: `analyze.R` (tables, SUMMARY), `figures.R`, `stat_tests.R` (test implementations), `progress.R`, `package.R`.
- `Distribution/`: innovation-distribution experiment.
- `results/`: the final run.
- `report/`: the ICML-style report (`main.tex`/`main.pdf`) and supplementary material.

Main R functions used: `stats::arima` (ARMA estimation and exact state-space
filtering), `stats::optim` (GARCH likelihoods), `stats::Box.test`,
`stats::shapiro.test`, `nnet::nnet` (MLP), `parallel` (PSOCK workers). Wavelets,
GARCH and GED likelihoods, the statistical tests and the metrics are implemented
in this folder.
