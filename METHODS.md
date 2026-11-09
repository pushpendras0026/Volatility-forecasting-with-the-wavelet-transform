# Methods and interpretation

## Data provenance

Only the six CSVs listed in `data/manifest.csv` are inputs. Each was prepared from
the supplied source file using its existing price-field convention. Stocks use
the supplied adjusted-close field where available; the provider's adjustment
convention has not been independently established. Source filenames, original
and prepared MD5 checksums, date bounds and retained flags are provided. No
synthetic values, calendar filling, return winsorisation or automatic outlier
removal is performed. Prepared files start in 2004 at actual availability.

## Fixed protocol

Training: through 31 December 2009. Validation: 1 January 2010 through
31 December 2011. Historical test: 1 January 2012 through 31 December 2014.
Later stock evaluation: 1 January 2015 through 31 December 2025. Boundaries are
disjoint. Orders and model choices are fixed before testing; numerical model
parameters refit on available prefixes at the declared cadence. Thus later data
enter subsequent rolling fits only after they have been observed.

For wavelet-family and standalone specification selection, candidates require
at least 95% valid validation forecasts, then compete on common successful
validation dates. The exact selected rows, coverage and common sample are
exported. If a family has no eligible candidate, its declared Haar/J=2 member or
original MODWT model is retained and the fallback is visible in the selection
records. Neural-network selection requires valid forecasts for every validation
origin across all seeds of a candidate architecture; its fallback is explicit.

Parameter sensitivity choices are written to `frozen_parameter_choices.rds`
after validation and before the later evaluation jobs start. No later-period
score changes this file or selects a new order, filter, level, hidden size,
decay, member or scenario.

## Accuracy, coverage and sample rules

MSE, RMSE, MAE and predictive R-squared use the same squared-return target.
Forecasts are joined on dataset, origin, target date and horizon. A forecast
counts only if it has `fit_status` ok and a finite value. Because models fail on
different dates, every score is computed on an explicit matched-date sample, and
every score table carries `n` and a `sample_rule` column:

| Rule | Dates used | Where |
|---|---|---|
| core | raw, DWT and MODWT GARCH all succeeded | `core_scores.csv`, SUMMARY core table |
| all-model | every model with at least one success succeeded | `all_model_scores.csv` (the deck's "overall" tables) |
| pairwise | the model and its control both succeeded | `extension_comparisons.csv`, `wavelet_effects.csv`, `likelihood_order_effects.csv`, `mlp_test_seed_effects.csv`, trend tables |
| MLP table | raw GARCH, three MLP seeds and three ensembles all succeeded | `mlp_seed_table.csv` (the deck's MLP table) |
| own | all successful dates of that model | `independent_*` columns |
| distribution trio | Gaussian, Student-t and GED versions of one pipeline all succeeded | `Distribution/results/<id>/` |

The same model therefore has slightly different scores in different tables; for
example raw GARCH for Google 2015-2025 differs between the core, all-model and
pairwise samples. `tables/sample_reconciliation.csv` reports raw, DWT and MODWT
GARCH, the MODWT ensemble and the MLP under each rule, and
`Distribution/results/<id>/sample_reconciliation_distribution.csv` puts each
Gaussian distribution-trio score next to the core-sample score of the same
forecasts. A model failing on difficult dates must not be presented as superior
on the basis of its surviving dates only. The MLP fails often at its 300-iteration
cap (for example Infosys and Tunisia), so its scores rest on fewer dates; its `n`
is always shown.

Positive percentage MSE reduction means lower error relative to the stated
comparator. Raw loss magnitudes across different stocks are not market rankings.
For overview parameter plots, errors are normalized within each dataset/model
before taking an equal-dataset geometric mean; no large-scale series dominates
that summary simply because its units or shocks are larger.

## Diagnostics

Candidate identification tables retain AIC/BIC, convergence, serial auxiliary
F/LM tests and ARCH F/LM tests. Serial regression uses residuals on an intercept
and 12 residual lags; ARCH regression uses squared residuals on 12 squared lags.
LM is `(n-p-q)*R-squared`, with a chi-square reference. F reference distributions
are approximate for estimated ARMA residuals. This serial auxiliary regression
is not mislabeled as a regression-specific Breusch-Godfrey test.

Ljung-Box Q(24) uses `fitdf=p+q`. GARCH checks use standardized innovations.
Nominal decisions use alpha=0.05: significance rejects the relevant
no-dependence null; non-significance does not prove it. AIC values compare
orders within a common input series and sample, not different markets or raw
versus transformed response dimensions. There is no diagnostic-driven iterative
re-identification of orders.

## Return properties: descriptive, normality and stationarity tests

`tables/descriptive_normality_stationarity.csv` describes the decimal log returns
of every series on the training period (2004-2009) and on the full prepared
sample (indices to 2014, stocks to 2025). It contains the statistics and tests
reported by the two reference papers:

- Ismail et al. (2016), Table 1: n, mean, standard deviation, skewness, kurtosis,
  Ljung-Box Q(24) and Jarque-Bera. Their residual Breusch-Godfrey and ARCH tests
  correspond to the serial/ARCH auxiliary regressions above.
- Rubio et al. (2023), Tables 2, 4 and 5: skewness and kurtosis z-tests,
  Jarque-Bera, ADF, KPSS, BDS (dimensions 2-6), Shapiro-Wilk, D'Agostino K^2 and
  Anderson-Darling.

Neither paper uses Phillips-Perron, so it is not computed. Definitions:

- Moments use the population (biased) estimators. `kurtosis_raw` is the raw
  kurtosis (3 for a normal distribution, the convention of the 2016 paper);
  `excess_kurtosis` = raw - 3.
- Jarque-Bera: `n/6*(S^2+(K-3)^2/4)`, chi-square(2) p-value.
- Skewness test: D'Agostino (1970). Kurtosis test: Anscombe and Glynn (1983).
  K^2 is the sum of their squares, chi-square(2).
- Anderson-Darling: A^2 with estimated mean and variance; p-value from the modified
  statistic, D'Agostino and Stephens (1986).
- Shapiro-Wilk: `stats::shapiro.test`; undefined above 5,000 observations (NA for
  the full stock samples).
- ADF: regression with a constant; lag chosen by AIC over 0..ceiling(12(n/100)^(1/4))
  on a common sample, then re-estimated; p-value from MacKinnon (1994), critical
  values from MacKinnon (2010).
- KPSS: level stationarity; Bartlett-kernel (Newey-West) long-run variance with
  the Hobijn, Franses and Ooms (1998) automatic bandwidth; p-value interpolated in
  the KPSS (1992) table and therefore bounded to [0.01, 0.10].
- Ljung-Box Q(24) on returns and on squared demeaned returns; Engle ARCH-LM with
  12 lags.
- BDS: epsilon = 1.5 standard deviations, dimensions 2-6, asymptotic normal
  p-values.

`tests/test_stat_tests.R` checks closed forms and published table values and
compares 264 statistics on the real data with independent implementations
(statsmodels 0.15.0 and scipy 1.18.1; reference values in
`tests/reference/stat_tests_reference.csv`, generator `make_reference.py`). All
agree to about 1e-11 relative difference. Tunisia's kurtosis is dominated by two
returns on 15-16 September 2004 (`data/issues.csv`).

## Scope of evidence

All declared settings, including unsuccessful models, remain in the outputs.
Diagnostic significance is not forecast superiority. Small differences in test
MSE are point estimates. Descriptive paired block-bootstrap intervals, where
shown, are not corrected for model search or multiple comparisons. Model search
was motivated by previously inspected historical results, including the former
native-period stock analyses; even the later calendar evaluation is therefore
retrospective rather than a newly untouched holdout. A changed performance
direction after 2014 is reported as a changed trend, not hidden.

Paired-DWT forecasts condition on the observed first return of the forecast pair
(see ARCHITECTURE.md).

This is a two-step, stationary implementation-based comparison. It is not an
exact numerical replication of the paper's data, target or estimator. Mixed MRA
allocation changes its conditional-mean specification; its residual GARCH
variances do not themselves enter the summed point prediction.

## Main functions

R `stats::arima` estimates (CSS-ML, with an exact-ML fallback) and exactly refilters mean models; `stats::optim` fits
the custom stationary Gaussian/Student-t GARCH likelihoods; `stats::Box.test`
provides Ljung-Box checks. `nnet::nnet` fits the MLP. `parallel::makePSOCKcluster`
and `parallel::parLapplyLB` distribute independent jobs. Wavelet filtering,
reconstruction, moment restoration, auxiliary diagnostics and metrics use local
base-R functions.

References: Ismail, Audu and Tumala (2016), DOI 10.1016/j.jfds.2016.09.002;
Rubio et al. (2023), DOI 10.1007/s40822-023-00243-x; Engle (1982);
Bollerslev (1986); Percival and Walden (2000); Jarque and Bera (1987); Dickey and
Fuller (1979); MacKinnon (1994, 2010); Kwiatkowski, Phillips, Schmidt and Shin
(1992); Hobijn, Franses and Ooms (1998); Brock, Dechert, Scheinkman and LeBaron
(1996); D'Agostino and Stephens (1986).
