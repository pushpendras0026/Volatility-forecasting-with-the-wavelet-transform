# Final six-series results

Training 2004-2009; validation 2010-2011; historical test 2012-2014. Later stock evaluation 2015-2025. Settings and members remain frozen; fitted parameters update on observed prefixes.

## How every number is sampled

Forecasts can fail on some dates, so each score is computed on a stated matched-date sample. The same model therefore has slightly different scores in different tables. Rules used here:

- core: intersection of dates on which raw_garch, dwt_garch and modwt_garch all succeeded (per dataset/period).
- all-model: intersection of dates on which every model with >=1 success in the dataset/period succeeded (44 model IDs).
- pairwise: dates on which both the model and its control succeeded.
- MLP table: dates on which raw_garch, mlp, mlp_seed202, mlp_seed303 and the three ensembles all succeeded.
- own: all dates on which this model succeeded (independent_* columns).
- Distribution/ results: dates on which the Gaussian, Student-t and GED versions of one pipeline all succeeded (Distribution/results/<id>/sample_reconciliation_distribution.csv).

`tables/sample_reconciliation.csv` reports raw/DWT/MODWT GARCH, the MODWT ensemble and the MLP under every rule.

## Core GARCH comparison

RMSE x 10,000, historical test 2012-2014. Sample: core rule; n = number of matched dates.

| Series | n | first | last | Raw | DWT | MODWT |
| --- | --- | --- | --- | --- | --- | --- |
| South Africa | 749 | 2012-01-03 | 2014-12-31 | 1.3426 | 1.3448 | 1.3394 |
| Tunisia | 745 | 2012-01-02 | 2014-12-31 | 0.7076 | 0.6790 | 0.7061 |
| Nigeria | 745 | 2012-01-03 | 2014-12-31 | 1.8920 | 1.8015 | 1.9173 |
| Infosys | 736 | 2012-01-02 | 2014-12-31 | 25.3177 | 24.9339 | 25.2165 |
| IBM | 751 | 2012-01-03 | 2014-12-31 | 4.1300 | 4.1585 | 4.1305 |
| Google | 752 | 2012-01-03 | 2014-12-31 | 7.7822 | 7.7857 | 7.7781 |

## Raw GARCH under each sample rule

RMSE x 10,000. Differences between rows come only from the dates included.

| Series | Period | Sample | n | RMSE_x1e4 |
| --- | --- | --- | --- | --- |
| south_africa | test | own |  749 | 1.3426 |
| south_africa | test | core |  749 | 1.3426 |
| south_africa | test | all |  688 | 1.3771 |
| south_africa | test | mlp |  688 | 1.3771 |
| tunisia | test | own |  745 | 0.7076 |
| tunisia | test | core |  745 | 0.7076 |
| tunisia | test | all |  540 | 0.3794 |
| tunisia | test | mlp |  540 | 0.3794 |
| nigeria | test | own |  745 | 1.8920 |
| nigeria | test | core |  745 | 1.8920 |
| nigeria | test | all |  745 | 1.8920 |
| nigeria | test | mlp |  745 | 1.8920 |
| india_infosys | test | own |  737 | 25.3009 |
| india_infosys | test | core |  736 | 25.3177 |
| india_infosys | test | all |  199 | 23.1670 |
| india_infosys | test | mlp |  199 | 23.1670 |
| india_infosys | later | own | 2716 | 9.5957 |
| india_infosys | later | core | 2714 | 9.5991 |
| india_infosys | later | all | 1218 | 8.6361 |
| india_infosys | later | mlp | 1218 | 8.6361 |
| usa_ibm | test | own |  751 | 4.1300 |
| usa_ibm | test | core |  751 | 4.1300 |
| usa_ibm | test | all |  751 | 4.1300 |
| usa_ibm | test | mlp |  751 | 4.1300 |
| usa_ibm | later | own | 2746 | 8.4015 |
| usa_ibm | later | core | 2743 | 8.4059 |
| usa_ibm | later | all | 2636 | 8.5343 |
| usa_ibm | later | mlp | 2636 | 8.5343 |
| google_class_a | test | own |  752 | 7.7822 |
| google_class_a | test | core |  752 | 7.7822 |
| google_class_a | test | all |  704 | 7.9898 |
| google_class_a | test | mlp |  704 | 7.9898 |
| google_class_a | later | own | 2763 | 9.1386 |
| google_class_a | later | core | 2760 | 9.0563 |
| google_class_a | later | all | 2692 | 9.1273 |
| google_class_a | later | mlp | 2692 | 9.1273 |

## MLP seeds versus raw GARCH

RMSE x 10,000, 2012-2014. Sample: dates on which raw_garch, mlp, mlp_seed202, mlp_seed303 and the three ensembles all succeeded.

| Series | n | Raw | Seed101 | Seed202 | Seed303 |
| --- | --- | --- | --- | --- | --- |
| south_africa | 688 | 1.3771 | 1.5194 | 1.5140 | 1.4648 |
| tunisia | 540 | 0.3794 | 0.4083 | 0.4201 | 0.5413 |
| nigeria | 745 | 1.8920 | 2.4044 | 2.0768 | 2.0256 |
| india_infosys | 199 | 23.1670 | 33.2734 | 24.0858 | 33.2707 |
| usa_ibm | 751 | 4.1300 | 4.2190 | 4.1655 | 4.2011 |
| google_class_a | 704 | 7.9898 | 8.1453 | 8.0270 | 8.0803 |

## Same definitions on later stock data

Positive percentages mean lower MSE than raw GARCH. Each period uses pairwise matched dates (n shown). The trend column compares only the sign of the point MSE difference.

| dataset | slot | historical_gain_pct | historical_n | later_gain_pct | later_n | same_direction |
| --- | --- | --- | --- | --- | --- | --- |
| india_infosys | dwt_garch | +3.01% | 736 | +2.61% | 2714 | TRUE |
| india_infosys | modwt_garch | +0.80% | 737 | +0.30% | 2716 | TRUE |
| india_infosys | selected_modwt | +1.93% | 737 | +0.68% | 2716 | TRUE |
| india_infosys | component | +2.65% | 737 | -0.58% | 2716 | FALSE |
| india_infosys | ensemble_base | +4.09% | 736 | +1.40% | 2714 | TRUE |
| india_infosys | ensemble_all | +0.84% | 714 | +1.36% | 2567 | TRUE |
| india_infosys | ensemble_modwt | -10.91% | 737 | -6.57% | 2716 | TRUE |
| india_infosys | mlp | -812.02% | 457 | -52.51% | 1716 | TRUE |
| usa_ibm | dwt_garch | -1.39% | 751 | +1.72% | 2743 | FALSE |
| usa_ibm | modwt_garch | -0.02% | 751 | +0.07% | 2746 | FALSE |
| usa_ibm | selected_modwt | -0.02% | 751 | +0.07% | 2746 | FALSE |
| usa_ibm | component | +0.21% | 751 | -2.78% | 2746 | FALSE |
| usa_ibm | ensemble_base | -0.12% | 751 | -0.52% | 2743 | TRUE |
| usa_ibm | ensemble_all | -0.93% | 751 | -0.80% | 2716 | TRUE |
| usa_ibm | ensemble_modwt | -11.22% | 751 | -10.34% | 2746 | TRUE |
| usa_ibm | mlp | -4.36% | 751 | -51.05% | 2726 | TRUE |
| google_class_a | dwt_garch | -0.09% | 752 | -5.49% | 2760 | TRUE |
| google_class_a | modwt_garch | +0.11% | 752 | -0.28% | 2763 | FALSE |
| google_class_a | selected_modwt | +0.11% | 752 | -0.28% | 2763 | FALSE |
| google_class_a | component | +0.32% | 752 | -0.34% | 2763 | FALSE |
| google_class_a | ensemble_base | -0.73% | 752 | +1.42% | 2760 | FALSE |
| google_class_a | ensemble_all | -1.74% | 738 | +1.20% | 2758 | FALSE |
| google_class_a | ensemble_modwt | -12.34% | 752 | -7.38% | 2763 | TRUE |
| google_class_a | mlp | -5.51% | 752 | -71.18% | 2723 | TRUE |

## Returns: descriptive statistics, normality and stationarity

Decimal log returns. Kurt is raw kurtosis (normal = 3); ExcessKurt = Kurt - 3. JB: Jarque-Bera, chi2(2). ADF: constant, AIC lag choice, MacKinnon p-value. KPSS: level stationarity, Bartlett kernel with Hobijn-Franses-Ooms bandwidth, p from the KPSS (1992) table (bounded to 0.01-0.10). Q24_p: Ljung-Box Q(24) on returns. Skewness/kurtosis z-tests, K2, Anderson-Darling, Shapiro-Wilk, Q(24) of squares, ARCH-LM(12) and BDS (m = 2..6) are in tables/descriptive_normality_stationarity.csv. Tunisia kurtosis is dominated by the -0.27/+0.27 returns of 15-16 Sep 2004 (data/issues.csv).

| Series | Sample | n | Mean | SD | Skew | ExcessKurt | Kurt | JB_p | ADF | KPSS | Q24_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| South Africa | training (2004-01-05..2009-12-31) | 1501 | 0.000645 | 0.0144 | -0.197 | 3.28 | 6.28 | <1e-4 | -24.05 (p <1e-4, lag 2) | 0.249 (p > 0.10) | 0.0049 |
| South Africa | full (2004-01-05..2014-12-31) | 2750 | 0.000565 | 0.0125 | -0.183 | 3.90 | 6.90 | <1e-4 | -25.88 (p <1e-4, lag 4) | 0.147 (p > 0.10) | 0.0006 |
| Tunisia | training (2004-01-05..2009-12-31) | 1485 | 0.000827 | 0.0111 | -0.370 | 438.26 | 441.26 | <1e-4 | -35.17 (p <1e-4, lag 1) | 0.103 (p > 0.10) | <1e-4 |
| Tunisia | full (2004-01-05..2014-12-31) | 2720 | 0.000514 | 0.00918 | -0.383 | 519.53 | 522.53 | <1e-4 | -64.27 (p <1e-4, lag 0) | 0.463 (interpolated) | <1e-4 |
| Nigeria | training (2004-01-05..2009-12-31) | 1484 | 1.87e-05 | 0.0109 | -0.025 | 1.62 | 4.62 | <1e-4 | -19.09 (p <1e-4, lag 2) | 0.606 (interpolated) | <1e-4 |
| Nigeria | full (2004-01-05..2014-12-31) | 2722 | 0.000198 | 0.00998 | 0.002 | 2.24 | 5.24 | <1e-4 | -25.36 (p <1e-4, lag 2) | 0.180 (p > 0.10) | <1e-4 |
| Infosys | training (2004-01-02..2009-12-31) | 1495 | 0.000932 | 0.0223 | 0.033 | 3.15 | 6.15 | <1e-4 | -25.16 (p <1e-4, lag 2) | 0.136 (p > 0.10) | 0.0047 |
| Infosys | full (2004-01-02..2025-12-31) | 5444 | 0.000621 | 0.0187 | -0.576 | 11.89 | 14.89 | <1e-4 | -45.18 (p <1e-4, lag 2) | 0.055 (p > 0.10) | 0.0014 |
| IBM | training (2004-01-05..2009-12-31) | 1510 | 0.000291 | 0.0146 | 0.077 | 6.07 | 9.07 | <1e-4 | -17.89 (p <1e-4, lag 4) | 0.108 (p > 0.10) | 0.0387 |
| IBM | full (2004-01-05..2025-12-31) | 5534 | 0.000335 | 0.0144 | -0.339 | 9.36 | 12.36 | <1e-4 | -22.92 (p <1e-4, lag 9) | 0.124 (p > 0.10) | <1e-4 |
| Google | training (2004-08-20..2009-12-31) | 1352 | 0.00135 | 0.0239 | 0.487 | 6.38 | 9.38 | <1e-4 | -9.72 (p <1e-4, lag 11) | 0.449 (interpolated) | 0.0094 |
| Google | full (2004-08-20..2025-12-31) | 5376 | 0.000899 | 0.0192 | 0.316 | 7.67 | 10.67 | <1e-4 | -28.44 (p <1e-4, lag 6) | 0.108 (p > 0.10) | 0.2435 |

## What is included

- All 44 final model IDs per dataset, including the three ensembles and three MLP seeds; 24 wavelet component specifications.
- Six sensitivity scenarios for each of the three core GARCH pipelines on all six series, and on the stocks after 2014.
- Full AIC/diagnostic grids, validation selections, failed fits, raw forecasts, coverage, parameter effects, and descriptive paired block-bootstrap intervals.
- Paired DWT forecasts condition on the observed first return of the forecast pair (detail and approximation models; see ARCHITECTURE.md).
- These are retrospective historical comparisons. Small loss differences and unadjusted descriptive intervals do not establish universal superiority.
- The MRA mixed branch sums conditional means; residual GARCH variance is not added to its point target forecast.
