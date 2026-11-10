# Numbers written in the app's prose, and deck discrepancies

Rule: results shown in the app are computed at run time from files in `app/data/` (tables, forecasts, derived
statistics) and printed with f-strings. Experiment settings in prose (window, cadence, mean window, AIC order cap,
periods, MLP grid) are parsed at run time from `data/results/run/config.txt` by `lib/common.config()`.
This file lists the numbers that are **typed** in prose, with their source.

## A. Typed numbers and their sources

| Number(s) in prose | Where in the app | Source |
|---|---|---|
| Roll numbers 240150008, 240150025, 240150026, 240150035; Group 9 | Start here, Team | `final_latex_submission/main.tex` `\author` |
| 12 lags (serial and ARCH F tests); Ljung-Box Q(24), fitdf = p+q; 5% level | Concepts, Results/Diagnostics | `submission/R/models.R` (`residual_lag_test(e,12L)`, `max(24L, p+q+5L)`); METHODS.md |
| AIC = −2ℓ + 2k, BIC = −2ℓ + k ln n, k = ARMA coefs + intercept + σ² | Concepts, discrepancy tab | `submission/R/models.R` `fit_mean` |
| GARCH start points; softmax map; Student-t ν = 2 + e^u; GED shape guard 0.1-100; 250/350 optimiser iterations | lib/reimpl.py, Architecture | `submission/R/models.R`; `submission/Distribution/innovation_distribution_robustness.R` |
| MODWT factors 2 and 4; DWT factors √2 and 2 | Concepts, Architecture | `submission/R/wavelets.R` `restore_haar_moments` |
| "about 511" DWT details from a 1,024 window | Concepts, Architecture, VALIDATION.md | `paired_haar()`: (1024 − 1) values, first dropped when odd, 2 per pair → 511 |
| 24 MRA models = 2 transforms × 3 filters × 2 levels × 2 allocations | Concepts, Architecture | `submission/config/experiment.R` `model_registry` |
| "all 44 model IDs" (all-model common dates) | Architecture, Results | `submission/VALIDATION.md` ("44 final model IDs per dataset"); `tables/all_model_scores.csv` |
| MLP 7 inputs, sigmoid units, no skip connections; seeds 101/202/303; decay 0.001/0.01; 3 or 5 units | Concepts, Architecture | `submission/R/mlp.R`; `config/experiment.R` (also parsed from config.txt where shown with f-strings) |
| Haar filter (1,1)/√2 and (1,−1)/√2; db4 = 8 taps, db6 = 12 taps | Concepts | `submission/R/wavelets.R` |
| Kurtosis of a normal = 3; ±1.96/√n ACF band; √252 annualisation; 20-day rolling volatility | Start here, Concepts | standard statistics (display choices, not project results) |
| Display windows: last 500 days, last 256 targets, last 1,024 returns in the likelihood demo | Concepts | display choices |
| Lab timing hints "~0.01 s per day, ~1 s per refit", "~16 fits" | Parameter lab | measured on the development machine; 16 = (3+1)² candidate orders |
| Paper: 2000-2014, four markets, Datastream, last five forecast days; Tables 1, 10, 11, 12 | The paper | `base_paper.pdf`; tables transcribed in `data/paper/*.csv` |
| "up to five orders of magnitude" (paper Table 12) | The paper | ratio of largest to smallest MSE in `paper_table12_mse.csv` (4.7e-4 / 3.0e-9 ≈ 1.6e5) |
| Slide values quoted as wrong: 272.37, 0.934, 0.998, "2 log k", 8.41% vs 8.02% | Results → Known discrepancies | `final_latex_submission/segments/3_results.tex`, `RESULTS_AND_DEFENCE.md`, `submission/VALIDATION.md` (file values next to them are read from data files) |

## B. Deck and documents vs result files

The app always shows the result-file value. Verified by reading the files listed (independently of, and consistent with,
the project audit `_audit/audit_numbers.md`).

| Item | Deck / document says | Result files say | Files |
|---|---|---|---|
| Backup "Non-normality" table | Nigeria kurtosis 272.37, SA 8.61, Tunisia 8.42 (mean, skew identical to the paper) | Nigeria 5.24, South Africa 6.90, Tunisia 522.5 (full prepared files; Tunisia driven by the ±0.27 returns of 15-16 Sep 2004) | `data/derived/return_moments.csv`; the deck values equal the paper's Table 1 (`data/paper/paper_table1_descriptive.csv`) |
| Model-selection / diagnostics slides: ARMA orders and AIC | SA (2,2) −6552.3, Tun (3,2), Nig (0,2), Inf (1,1), IBM (0,0), Google (0,0) | SA (3,1), Tun (2,0), Nig (0,3), Inf (0,3), IBM (2,2), Google (3,2) | `results/tables/aic_candidate_grids.csv` (`chosen`), `initial_orders.csv`; deck values are from the older run's native windows |
| Diagnostics slide F/p values | as printed | match the final run (`initial_diagnostics.csv`), but are paired with the older orders | same |
| Diagnostics interpretation | "no significant serial correlation" | Tunisia serial F p = 0.0262 (< 0.05) | `results/tables/initial_diagnostics.csv` |
| AIC formula | −2ℓ + 2 log k | −2ℓ + 2k | `submission/R/models.R` |
| Ensemble Results slide (bias ratios) | Nigeria MODWT 0.934, SA MODWT 0.998 | 0.834 and 0.992; whole table is the older 2013-2014 run, "ensemble" = refit-10/window-512 strategy | `data/legacy/forecast_bias.csv` |
| Figure_1.png ratios | e.g. Tunisia MLP ratio below 1 | numerator and denominator from different samples; matched-date MLP/raw ratios are all > 1 | `results/tables/mlp_test_seed_effects.csv` (`RMSE_ratio`) |
| MLP results slide | n = 688 / 540 / ... | correct for the dates where raw GARCH, all 3 MLP seeds and all 3 ensembles succeed; pairwise values differ | `results/tables/all_model_scores.csv` vs `mlp_test_seed_effects.csv` |
| Nigeria ensemble gain | VALIDATION.md 8.02%; RESULTS_AND_DEFENCE.md 8.41% | 8.02% = final MODWT ensemble 2012-2014; 8.41% = older 2013-2014 fast ensemble | `results/tables/extension_comparisons.csv`; `data/legacy/strategy_pairwise.csv` |
| RESULTS_AND_DEFENCE.md "primary comparison is the common 2013-2014 test" | 2013-2014 | final primary test is 2012-2014 | `results/tables/splits.csv` |
| Forecast figures for SA/Tunisia, calibration, order-sensitivity, native appendices, AIC heatmap | presented beside final results | older 2013-2014 / native run | `final_latex_submission/generated/` (labelled "older 2013-2014 run" in the app) |
| Paper Table 11 vs its text | "α+β less than unity" for all models | transcribed Nigeria sums 1.05 and 1.13 | `data/paper/paper_table11_garch.csv` |

Values that **match** the files exactly (checked in the app or by the audit): core RMSE table (`core_scores.csv`),
distribution win counts and MSE changes (`heldout_win_counts.csv`, `heldout_winners.csv`), Nigeria and Google overall
tables (`all_model_scores.csv`), MLP table (all-model-subset sample).
