# Innovation distribution robustness experiment

This folder is a separate sensitivity experiment. The primary Gaussian workflow,
configuration, data and existing outputs are unchanged. Nothing in the production
runner imports this folder. All new files and outputs stay inside `Distribution/`.

Run after the main run and `tools/analyze.R` (R 4.6.x; base/recommended packages
only), from any directory:

```sh
Rscript code_submission/Distribution/tests.R
Rscript code_submission/Distribution/innovation_distribution_robustness.R --workers 16
Rscript code_submission/Distribution/report.R
```

`--workers` only controls parallelism (default 6); results do not depend on it.
The runner reads the main run named in `../results/LATEST.txt`, prints its result
directory and, on completion, writes `LATEST.txt` here as a relative path
(`results/<id>`), so the folder can be moved. The id hashes root-relative,
line-ending-normalized code, data and frozen-plan content. `tests.R` writes only
to a temporary directory. Completed dataset/pipeline jobs are
reused only under the same code, data, configuration and frozen-plan fingerprint.
An interrupted job restarts; other completed jobs are retained. No shortened
sample, alternative split, faster refit cadence or different order search is used.

## What is held fixed

- The six audited datasets and `load_prices()`, `make_targets()` and
  `calendar_split()` functions, including `diff(log(Price))` and the squared
  deviation from the preceding 20-return mean.
- The saved initial-training ARMA orders in the original baseline frozen plans
  (for the paired DWT, both the detail and the approximation orders).
  There is no distribution-specific order selection or test-period tuning.
- The raw, DWT and MODWT core GARCH specifications (three matched experiments
  per dataset). The structural extra-MA variant, ensembles and MLP are outside
  this small experiment's scope.
- Gaussian ARMA mean ML followed by GARCH(1,1) on its fixed residuals. This is
  two-step fitting, not joint ARMA-GARCH likelihood estimation. The mean remains
  Gaussian under all three variance innovation assumptions.
- The existing 1,024-return moving window and 20-observation refit cadence,
  variance initialization, stationarity parameter map and causal forecast loop.
  Validation (2010–2011) is replayed to carry exactly the same state/cadence into
  the 2012–2014 test. Stocks continue into 2015–2025 from the test state.
- The same target moment conversion, training-only MAPE threshold and existing
  `calculate_metrics()` function. It reports MSE, RMSE, MAE, predictive R2, MAPE
  and masked MAPE; QLIKE is not a metric in this project and is not introduced.
  Comparisons use common successful forecast dates within each matched trio
  (Gaussian, Student-t, GED of one pipeline). The main run's core table matches
  raw/DWT/MODWT instead, so Gaussian MSEs here can differ slightly from it;
  `sample_reconciliation_distribution.csv` shows both samples with their n.
  with independent metrics and coverage also retained. Validation rows are
  diagnostics, not out-of-sample test evidence in the discussion.

## Implementation and audit

`R/models.R::fit_garch11()` contains the Gaussian negative log likelihood;
`fit_stat_model(..., distribution='gaussian')` selects it by default. The project
already contains `fit_garch11_t()` and Student-t controls. Both production fitters
are called without modification. Functions from `R/` are sourced into a private
environment where a local dispatch adds GED; the production files are never edited.
All distributions use the original `run_forecasts()` and `forecast_garch11()`.

GED is implemented locally because this project uses custom base-R likelihoods
rather than a distribution-aware GARCH library. Its unit-variance density is
`b/(2*a*Gamma(1/b))*exp(-abs(z/a)^b)` with
`a=sqrt(Gamma(1/b)/Gamma(3/b))`. This agrees with the
[standardized GED convention](https://search.r-project.org/CRAN/refmans/fGarch/html/dist-ged.html).
Shape 2 nests Gaussian and shape 1 is standardized Laplace. Numerical integration
tests check normalization and variance. GED uses the same variance starts and
parameter map as Gaussian and the Student-t optimizer's 350-iteration limit;
its shape has a numerical guard `[0.1,100]`, flagged if approached. Existing
Gaussian and Student-t optimizer settings are preserved exactly. Local optima
remain possible; this is not an optimizer comparison.

The runner replays both existing distributions against their saved per-origin
forecasts and verifies dates, targets, moments, statuses, refit timing, threshold
and window boundaries (relative tolerance `1e-12` for CSV serialization). It also
hashes the code, data and the baseline run outside this folder before and after
execution (other run folders are excluded).
Numerical equivalence of the replay and unchanged file hashes are distinct checks.

## Outputs

Under `results/<fingerprint>/`:

- `innovation_distribution_comparison.csv`: one row per dataset, pipeline,
  period and distribution; existing evaluation metrics, coverage, fit failures,
  convergence, ARMA orders, variance parameters and distribution shape.
- `COMPARISON.md`: readable complete held-out comparison and interpretation,
  generated by `report.R`.
- `<dataset>/<pipeline>/fit_attempts.csv`: every attempted refit with its date,
  window, parameter estimates, log likelihood, AIC/BIC, convergence and errors.
- `<dataset>/<pipeline>/<period>/`: per-origin forecasts, failures, diagnostics,
  progress, first fit objects and final checkpoint states.
- `sample_reconciliation_distribution.csv`: Gaussian MSE on the distribution-trio
  sample next to the main run's core-sample MSE of the same forecasts.
- `timing.csv` (per pipeline): wall-clock seconds, kept out of `comparison.csv` so
  that the comparison is bit-identical on re-run.
- `baseline_reproduction.csv`, `baseline_integrity.csv`, `input_checksums.csv`,
  `config.rds`, `sessionInfo.txt`: reproducibility and isolation evidence.
- `job_failures.csv`: failures outside individual model fits. Individual fitting
  failures are caught by the unchanged forecast loop and do not stop other models.

**Fit statistics are conditional GARCH likelihoods on the fixed ARMA residuals.**
The comparison row uses the first successful refit *within that period*, with its
origin and sample size explicitly recorded. It is not the whole-sample likelihood,
an average across refits, or joint ARMA-GARCH AIC/BIC. Parameter counts are 3 for
Gaussian and 4 for Student-t/GED. Compare these statistics only for the same
dataset, pipeline, fitting origin and residual sample. The full refit history
allows other snapshots to be inspected. Forecast scores cover the entire declared
period, including dates before its first refit when inherited parameters are used.

Better in-sample likelihood does not imply better forecasts. The report makes
descriptive comparisons without significance tests or a prespecified threshold
for 'material' improvement. The later stock period retains the project's existing
limitation: a retrospective temporal evaluation, not an untouched confirmatory
holdout. This experiment supplies robustness evidence and does not replace or
reselect the primary Gaussian baseline.
