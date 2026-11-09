# Final six-series results

Training 2004-2009; validation 2010-2011; historical test 2012-2014. Later stock evaluation 2015-2025. Settings and members remain frozen; fitted parameters update on observed prefixes.

## Core GARCH comparison

RMSE x 10,000 on joint successful dates of the three models.

| Series | n | Raw | DWT | MODWT |
| --- | --- | --- | --- | --- |
| South Africa | 749 | 1.3426 | 2.6444 | 1.3394 |
| Tunisia | 745 | 0.7076 | 1.0352 | 0.7061 |
| Nigeria | 745 | 1.8920 | 2.1052 | 1.9173 |
| Infosys | 736 | 25.3177 | 34.0209 | 25.2165 |
| IBM | 751 | 4.1300 | 6.7643 | 4.1305 |
| Google | 752 | 7.7822 | 11.7403 | 7.7781 |

## Same definitions on later stock data

Positive percentages mean lower MSE than raw GARCH. Each period uses pairwise matched dates; see coverage and full sample counts in the CSVs. The trend column compares only the sign of the point MSE difference.

| dataset | slot | historical_gain_pct | later_gain_pct | same_direction |
| --- | --- | --- | --- | --- |
| india_infosys | dwt_garch | -80.57% | -113.40% | TRUE |
| india_infosys | modwt_garch | +0.80% | +0.30% | TRUE |
| india_infosys | selected_modwt | +1.93% | +0.68% | TRUE |
| india_infosys | component | +2.65% | -0.58% | FALSE |
| india_infosys | ensemble_base | -7.88% | -8.88% | TRUE |
| india_infosys | ensemble_all | -7.31% | -4.75% | TRUE |
| india_infosys | ensemble_modwt | -10.91% | -6.57% | TRUE |
| india_infosys | mlp | -812.02% | -52.51% | TRUE |
| usa_ibm | dwt_garch | -168.26% | -118.91% | TRUE |
| usa_ibm | modwt_garch | -0.02% | +0.07% | FALSE |
| usa_ibm | selected_modwt | -0.02% | +0.07% | FALSE |
| usa_ibm | component | +0.21% | -2.78% | FALSE |
| usa_ibm | ensemble_base | -23.82% | -11.83% | TRUE |
| usa_ibm | ensemble_all | -12.50% | -7.77% | TRUE |
| usa_ibm | ensemble_modwt | -11.22% | -10.34% | TRUE |
| usa_ibm | mlp | -4.36% | -51.06% | TRUE |
| google_class_a | dwt_garch | -127.59% | -169.65% | TRUE |
| google_class_a | modwt_garch | +0.11% | -0.28% | FALSE |
| google_class_a | selected_modwt | +0.11% | -0.28% | FALSE |
| google_class_a | component | +0.32% | -0.34% | FALSE |
| google_class_a | ensemble_base | -19.60% | -11.04% | TRUE |
| google_class_a | ensemble_all | -11.54% | -6.04% | TRUE |
| google_class_a | ensemble_modwt | -12.34% | -7.38% | TRUE |
| google_class_a | mlp | -5.51% | -71.19% | TRUE |

## What is included

- All 44 final model IDs per dataset, including the three ensembles and three MLP seeds; 24 wavelet component specifications.
- Six sensitivity scenarios for each of the three core GARCH pipelines on all six series, and on the stocks after 2014.
- Full AIC/diagnostic grids, validation selections, failed fits, raw forecasts, coverage, parameter effects, and descriptive paired block-bootstrap intervals.
- The same-dependence trend is measured, not assumed. Later performance changes are retained.
- These are retrospective historical comparisons. Small loss differences and unadjusted descriptive intervals do not establish universal superiority.
- The MRA mixed branch sums conditional means; residual GARCH variance is not added to its point target forecast.
