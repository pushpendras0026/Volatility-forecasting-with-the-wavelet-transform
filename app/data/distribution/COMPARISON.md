# Innovation distribution sensitivity results

The primary Gaussian pipeline is unchanged. These are descriptive robustness results.

The held-out comparison contains 27 dataset/pipeline/period groups (81 distribution rows).
Historical test: 2012–2014 for six series; later evaluation: 2015–2025 for three stocks.
All three distributions in a group use common successful dates and the existing project metrics.

| Distribution | Lowest MSE groups | Lowest MAE groups |
|---|---:|---:|
| Gaussian | 2 | 4 |
| Student-t | 12 | 5 |
| GED | 13 | 18 |

Wins count groups equally and are descriptive; they do not measure statistical significance or the size of an improvement.
The full CSV also reports RMSE, predictive R2, MAPE, masked MAPE, independent coverage and parameters.
No single distribution is assumed to replace the Gaussian baseline. Inspect both metrics and improvement sizes below.

Across all replayed periods (including validation): 7185 fit attempts, 90 failed attempts, 0 GED shape-guard flags.
Held-out forecasts: 90 failed rows out of 114588 requested rows.

LogLik/AIC/BIC below describe the first successful refit within each period, conditional on fixed ARMA residuals. They are not joint ARMA-GARCH criteria.
The fitting origin and residual sample size are shown. Lower AIC/BIC and higher LogLik describe that fit; lower MSE/MAE describe held-out forecasts.
MAPE is undefined when the target crosses the existing threshold; the CSV retains the project's masked MAPE and exclusion counts.

## later / google_class_a / dwt_garch

ARMA(2,2), GARCH(1,1). Common held-out dates: 2766. Fit origin(s): 2015-01-05; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian |  1420.3 | -2834.6 | -2821.89 | 2.25045e-06 | 0.000894332 | 100.00 | Yes |
| Student-t | 1472.16 | -2936.31 | -2919.37 | 2.2558e-06 | 0.000897674 | 100.00 | Yes |
| GED | 1458.54 | -2909.07 | -2892.12 | 2.17673e-06 | 0.0008782 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +0.238%; GED -3.276%. Lowest MSE: GED; lowest MAE: GED.

## later / google_class_a / modwt_garch

ARMA(0,1), GARCH(1,1). Common held-out dates: 2766. Fit origin(s): 2015-01-05; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 3563.05 | -7120.1 | -7105.31 | 8.36667e-07 | 0.000378794 | 100.00 | Yes |
| Student-t | 3684.04 | -7360.07 | -7340.35 | 8.26508e-07 | 0.00038733 | 100.00 | Yes |
| GED |  3666.6 | -7325.2 | -7305.48 | 8.25541e-07 | 0.00037549 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -1.214%; GED -1.330%. Lowest MSE: GED; lowest MAE: GED.

## later / google_class_a / raw_garch

ARMA(3,2), GARCH(1,1). Common held-out dates: 2763. Fit origin(s): 2015-01-07; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 2854.86 | -5703.73 | -5688.93 | 8.35137e-07 | 0.000384234 | 99.89 | No |
| Student-t |  2974.2 | -5940.41 | -5920.68 | 8.2665e-07 | 0.000390951 | 99.89 | No |
| GED | 2958.22 | -5908.45 | -5888.72 | 8.24082e-07 | 0.00037971 | 99.89 | No |

MSE change relative to Gaussian: Student-t -1.016%; GED -1.324%. Lowest MSE: GED; lowest MAE: GED.

## later / india_infosys / dwt_garch

ARMA(3,2), GARCH(1,1). Common held-out dates: 2715. Fit origin(s): 2015-01-12; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1318.96 | -2631.92 | -2619.21 | 1.96562e-06 | 0.000749676 | 99.96 | No |
| Student-t | 1416.35 | -2824.69 | -2807.75 | 1.82066e-06 | 0.000738178 | 99.96 | No |
| GED | 1404.15 | -2800.29 | -2783.35 | 1.79809e-06 | 0.000706081 | 99.96 | No |

MSE change relative to Gaussian: Student-t -7.375%; GED -8.523%. Lowest MSE: GED; lowest MAE: GED.

## later / india_infosys / modwt_garch

ARMA(2,2), GARCH(1,1). Common held-out dates: 2716. Fit origin(s): 2015-01-09; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 3353.96 | -6701.91 | -6687.12 | 9.18048e-07 | 0.000338727 | 100.00 | Yes |
| Student-t | 3554.02 | -7100.03 | -7080.31 | 9.14366e-07 | 0.000322382 | 100.00 | Yes |
| GED | 3530.78 | -7053.56 | -7033.84 | 9.12108e-07 | 0.000321822 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -0.401%; GED -0.647%. Lowest MSE: GED; lowest MAE: GED.

## later / india_infosys / raw_garch

ARMA(0,3), GARCH(1,1). Common held-out dates: 2716. Fit origin(s): 2015-01-09; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian |    2652 |   -5298 | -5283.21 | 9.20765e-07 | 0.000339161 | 100.00 | Yes |
| Student-t | 2847.82 | -5687.64 | -5667.92 | 9.15861e-07 | 0.00032246 | 100.00 | Yes |
| GED |  2825.1 | -5642.2 | -5622.47 | 9.14234e-07 | 0.000322159 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -0.533%; GED -0.709%. Lowest MSE: GED; lowest MAE: GED.

## later / usa_ibm / dwt_garch

ARMA(3,3), GARCH(1,1). Common held-out dates: 2766. Fit origin(s): 2015-01-05; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1575.66 | -3145.32 | -3132.61 | 1.5374e-06 | 0.000626238 | 100.00 | Yes |
| Student-t |  1592.3 | -3176.59 | -3159.64 | 1.72127e-06 | 0.00067167 | 100.00 | Yes |
| GED | 1590.39 | -3172.78 | -3155.84 | 1.56829e-06 | 0.000628834 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +11.960%; GED +2.009%. Lowest MSE: Gaussian; lowest MAE: Gaussian.

## later / usa_ibm / modwt_garch

ARMA(2,3), GARCH(1,1). Common held-out dates: 2766. Fit origin(s): 2015-01-05; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 3829.93 | -7653.86 | -7639.06 | 7.00689e-07 | 0.000282321 | 100.00 | Yes |
| Student-t | 3923.25 | -7838.51 | -7818.79 | 6.86795e-07 | 0.000288337 | 100.00 | Yes |
| GED |  3907.5 | -7806.99 | -7787.27 | 6.92505e-07 | 0.000278138 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -1.983%; GED -1.168%. Lowest MSE: Student-t; lowest MAE: GED.

## later / usa_ibm / raw_garch

ARMA(2,2), GARCH(1,1). Common held-out dates: 2746. Fit origin(s): 2015-01-08; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian |  3118.9 | -6231.81 | -6217.02 | 7.05854e-07 | 0.000282658 | 99.28 | No |
| Student-t | 3212.38 | -6416.75 | -6397.03 | 6.9663e-07 | 0.000290257 | 99.28 | No |
| GED | 3196.39 | -6384.78 | -6365.05 | 6.99526e-07 | 0.000279653 | 99.28 | No |

MSE change relative to Gaussian: Student-t -1.307%; GED -0.897%. Lowest MSE: Student-t; lowest MAE: GED.

## test / google_class_a / dwt_garch

ARMA(2,2), GARCH(1,1). Common held-out dates: 754. Fit origin(s): 2012-01-25; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1248.59 | -2491.18 | -2478.47 | 1.37619e-06 | 0.000643475 | 100.00 | Yes |
| Student-t | 1301.89 | -2595.78 | -2578.83 | 1.35424e-06 | 0.000609902 | 100.00 | Yes |
| GED | 1293.08 | -2578.16 | -2561.22 | 1.33969e-06 | 0.00060478 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -1.595%; GED -2.652%. Lowest MSE: GED; lowest MAE: GED.

## test / google_class_a / modwt_garch

ARMA(0,1), GARCH(1,1). Common held-out dates: 754. Fit origin(s): 2012-01-25; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 3184.04 | -6362.08 | -6347.29 | 6.03474e-07 | 0.00025873 | 100.00 | Yes |
| Student-t | 3313.97 | -6619.93 | -6600.21 | 6.01614e-07 | 0.00024072 | 100.00 | Yes |
| GED |  3299.6 | -6591.2 | -6571.48 | 6.00454e-07 | 0.000238086 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -0.308%; GED -0.501%. Lowest MSE: GED; lowest MAE: GED.

## test / google_class_a / raw_garch

ARMA(3,2), GARCH(1,1). Common held-out dates: 752. Fit origin(s): 2012-01-25; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 2478.39 | -4950.78 | -4935.98 | 6.05629e-07 | 0.000261083 | 99.73 | No |
| Student-t |  2599.9 | -5191.79 | -5172.06 | 6.0396e-07 | 0.000242477 | 99.73 | No |
| GED | 2583.43 | -5158.87 | -5139.14 | 6.02937e-07 | 0.000240266 | 99.73 | No |

MSE change relative to Gaussian: Student-t -0.275%; GED -0.444%. Lowest MSE: GED; lowest MAE: GED.

## test / india_infosys / dwt_garch

ARMA(3,2), GARCH(1,1). Common held-out dates: 736. Fit origin(s): 2012-01-05; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1236.65 | -2467.31 | -2454.6 | 1.15742e-05 | 0.00112631 | 99.86 | No |
| Student-t |  1260.5 |   -2513 | -2496.05 | 1.17384e-05 | 0.00109111 | 99.86 | No |
| GED | 1255.31 | -2502.62 | -2485.67 | 1.1524e-05 | 0.0010503 | 99.86 | No |

MSE change relative to Gaussian: Student-t +1.419%; GED -0.434%. Lowest MSE: GED; lowest MAE: GED.

## test / india_infosys / modwt_garch

ARMA(2,2), GARCH(1,1). Common held-out dates: 737. Fit origin(s): 2012-01-05; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian |  3227.3 | -6448.61 | -6433.81 | 6.35026e-06 | 0.000531666 | 100.00 | Yes |
| Student-t | 3252.74 | -6497.48 | -6477.75 | 6.27545e-06 | 0.000506682 | 100.00 | Yes |
| GED | 3250.49 | -6492.98 | -6473.26 | 6.30961e-06 | 0.000507273 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -1.178%; GED -0.640%. Lowest MSE: Student-t; lowest MAE: Student-t.

## test / india_infosys / raw_garch

ARMA(0,3), GARCH(1,1). Common held-out dates: 737. Fit origin(s): 2012-01-05; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 2523.09 | -5040.17 | -5025.38 | 6.40133e-06 | 0.000534884 | 100.00 | Yes |
| Student-t | 2546.69 | -5085.38 | -5065.65 | 6.23005e-06 | 0.000500223 | 100.00 | Yes |
| GED |  2544.2 | -5080.4 | -5060.67 | 6.30153e-06 | 0.000505827 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -2.676%; GED -1.559%. Lowest MSE: Student-t; lowest MAE: Student-t.

## test / nigeria / dwt_garch

ARMA(3,0), GARCH(1,1). Common held-out dates: 745. Fit origin(s): 2012-01-11; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1826.15 | -3646.3 | -3633.59 | 4.43192e-08 | 0.000136517 | 100.00 | Yes |
| Student-t |  1848.2 | -3688.41 | -3671.46 | 4.49245e-08 | 0.000138835 | 100.00 | Yes |
| GED | 1847.92 | -3687.84 | -3670.89 | 4.44445e-08 | 0.000136646 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +1.366%; GED +0.283%. Lowest MSE: Gaussian; lowest MAE: Gaussian.

## test / nigeria / modwt_garch

ARMA(3,1), GARCH(1,1). Common held-out dates: 745. Fit origin(s): 2012-01-11; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 4141.61 | -8277.21 | -8262.42 | 3.67602e-08 | 9.32498e-05 | 100.00 | Yes |
| Student-t | 4159.68 | -8311.36 | -8291.64 | 3.63771e-08 | 9.44958e-05 | 100.00 | Yes |
| GED | 4159.63 | -8311.25 | -8291.53 | 3.65923e-08 | 9.37614e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -1.042%; GED -0.457%. Lowest MSE: Student-t; lowest MAE: Gaussian.

## test / nigeria / raw_garch

ARMA(0,3), GARCH(1,1). Common held-out dates: 745. Fit origin(s): 2012-01-11; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 3437.42 | -6868.84 | -6854.05 | 3.5797e-08 | 9.35666e-05 | 100.00 | Yes |
| Student-t | 3455.58 | -6903.17 | -6883.44 | 3.55447e-08 | 9.48402e-05 | 100.00 | Yes |
| GED |  3456.3 | -6904.6 | -6884.87 | 3.5726e-08 | 9.4073e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -0.705%; GED -0.198%. Lowest MSE: Student-t; lowest MAE: Gaussian.

## test / south_africa / dwt_garch

ARMA(2,2), GARCH(1,1). Common held-out dates: 749. Fit origin(s): 2011-12-30; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1461.81 | -2917.62 | -2904.91 | 6.99308e-08 | 0.000201153 | 100.00 | Yes |
| Student-t | 1464.97 | -2921.93 | -2904.99 | 6.93016e-08 | 0.000199979 | 100.00 | Yes |
| GED | 1465.01 | -2922.02 | -2905.07 | 6.96159e-08 | 0.000200672 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -0.900%; GED -0.450%. Lowest MSE: Student-t; lowest MAE: Student-t.

## test / south_africa / modwt_garch

ARMA(3,2), GARCH(1,1). Common held-out dates: 749. Fit origin(s): 2011-12-30; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 3661.71 | -7317.42 | -7302.63 | 1.79394e-08 | 7.46173e-05 | 100.00 | Yes |
| Student-t | 3662.24 | -7316.48 | -7296.76 | 1.79269e-08 | 7.44327e-05 | 100.00 | Yes |
| GED | 3662.29 | -7316.58 | -7296.85 | 1.79309e-08 | 7.45039e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -0.070%; GED -0.048%. Lowest MSE: Student-t; lowest MAE: Student-t.

## test / south_africa / raw_garch

ARMA(3,1), GARCH(1,1). Common held-out dates: 749. Fit origin(s): 2011-12-30; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian |  2955.8 | -5905.61 | -5890.81 | 1.80257e-08 | 7.5e-05 | 100.00 | Yes |
| Student-t | 2956.17 | -5904.34 | -5884.61 | 1.80128e-08 | 7.48354e-05 | 100.00 | Yes |
| GED | 2956.18 | -5904.36 | -5884.63 | 1.80166e-08 | 7.49018e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -0.072%; GED -0.050%. Lowest MSE: Student-t; lowest MAE: Student-t.

## test / tunisia / dwt_garch

ARMA(2,3), GARCH(1,1). Common held-out dates: 745. Fit origin(s): 2012-01-13; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian |  1953.6 | -3901.21 | -3888.5 | 1.07159e-08 | 5.37469e-05 | 100.00 | Yes |
| Student-t |  2004.3 | -4000.6 | -3983.65 | 9.02667e-09 | 4.98061e-05 | 100.00 | Yes |
| GED | 1996.78 | -3985.56 | -3968.62 | 9.26904e-09 | 4.90972e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -15.764%; GED -13.502%. Lowest MSE: Student-t; lowest MAE: GED.

## test / tunisia / modwt_garch

ARMA(2,1), GARCH(1,1). Common held-out dates: 745. Fit origin(s): 2012-01-13; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian |  4578.1 | -9150.21 | -9135.42 | 4.98529e-09 | 2.54489e-05 | 100.00 | Yes |
| Student-t | 4641.22 | -9274.44 | -9254.72 | 4.91758e-09 | 2.51724e-05 | 100.00 | Yes |
| GED | 4630.38 | -9252.77 | -9233.04 | 4.93253e-09 | 2.5073e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -1.358%; GED -1.058%. Lowest MSE: Student-t; lowest MAE: GED.

## test / tunisia / raw_garch

ARMA(2,0), GARCH(1,1). Common held-out dates: 745. Fit origin(s): 2012-01-13; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 3873.46 | -7740.92 | -7726.13 | 5.00655e-09 | 2.5518e-05 | 100.00 | Yes |
| Student-t | 3936.18 | -7864.36 | -7844.63 | 4.89677e-09 | 2.52021e-05 | 100.00 | Yes |
| GED | 3926.01 | -7844.02 | -7824.3 | 4.92217e-09 | 2.51151e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -2.193%; GED -1.685%. Lowest MSE: Student-t; lowest MAE: GED.

## test / usa_ibm / dwt_garch

ARMA(3,3), GARCH(1,1). Common held-out dates: 754. Fit origin(s): 2012-01-25; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1427.45 | -2848.89 | -2836.18 | 4.57308e-07 | 0.000392103 | 100.00 | Yes |
| Student-t |  1435.8 | -2863.59 | -2846.65 | 4.60851e-07 | 0.000394358 | 100.00 | Yes |
| GED | 1435.33 | -2862.65 | -2845.71 | 4.55199e-07 | 0.000389055 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +0.775%; GED -0.461%. Lowest MSE: GED; lowest MAE: GED.

## test / usa_ibm / modwt_garch

ARMA(2,3), GARCH(1,1). Common held-out dates: 754. Fit origin(s): 2012-01-25; fit n: 1023.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 3590.91 | -7175.81 | -7161.02 | 1.71352e-07 | 0.000153351 | 100.00 | Yes |
| Student-t | 3620.01 | -7232.02 | -7212.3 | 1.71392e-07 | 0.000152851 | 100.00 | Yes |
| GED | 3614.84 | -7221.67 | -7201.95 | 1.71125e-07 | 0.000150798 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +0.023%; GED -0.132%. Lowest MSE: GED; lowest MAE: GED.

## test / usa_ibm / raw_garch

ARMA(2,2), GARCH(1,1). Common held-out dates: 751. Fit origin(s): 2012-01-25; fit n: 1024.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 2889.98 | -5773.96 | -5759.16 | 1.70567e-07 | 0.000152453 | 99.60 | No |
| Student-t | 2918.11 | -5828.21 | -5808.49 | 1.71001e-07 | 0.000152596 | 99.60 | No |
| GED | 2913.11 | -5818.23 | -5798.5 | 1.70538e-07 | 0.000150299 | 99.60 | No |

MSE change relative to Gaussian: Student-t +0.255%; GED -0.017%. Lowest MSE: GED; lowest MAE: GED.

## Interpretation and limitations

GED has the lowest MSE in 13 of 27 groups and the lowest MAE in 18; Student-t has the lowest MSE in 12 and the lowest MAE in 5; Gaussian has the lowest MSE in 2 and the lowest MAE in 4.
Alternative innovations can improve fit and/or forecasting performance for individual series and specifications. Fit rankings and forecasting rankings can differ, and MSE and MAE can favor different distributions.
These point comparisons establish neither significance nor a universal winner. The Gaussian specification remains the primary baseline. The two-step Gaussian mean, optimizer starts, numerical guards and retrospective status of the later period are documented in ../../README.md.
baseline_reproduction.csv verifies the existing Gaussian and Student-t forecast paths; baseline_integrity.csv verifies every protected file remained unchanged.

90 failed refit attempts came from the ARMA mean step; 0 came from other fitting errors. Inspect each pipeline's fit_attempts.csv for dates and messages.
