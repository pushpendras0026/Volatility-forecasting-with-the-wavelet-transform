# Innovation distribution sensitivity results

The primary Gaussian pipeline is unchanged. These are descriptive robustness results.

The held-out comparison contains 27 dataset/pipeline/period groups (81 distribution rows).
Historical test: 2012–2014 for six series; later evaluation: 2015–2025 for three stocks.
All three distributions in a group use common successful dates (the distribution-trio sample) and the existing project metrics.
The main run core table matches raw/DWT/MODWT instead, so Gaussian MSEs can differ slightly from it; sample_reconciliation_distribution.csv lists both samples and n.

| Distribution | Lowest MSE groups | Lowest MAE groups |
|---|---:|---:|
| Gaussian | 4 | 3 |
| Student-t | 13 | 6 |
| GED | 10 | 18 |

Wins count groups equally and are descriptive; they do not measure statistical significance or the size of an improvement.
The full CSV also reports RMSE, predictive R2, MAPE, masked MAPE, independent coverage and parameters.
No single distribution is assumed to replace the Gaussian baseline. Inspect both metrics and improvement sizes below.

Across all replayed periods (including validation): 7206 fit attempts, 111 failed attempts, 0 GED shape-guard flags.
Held-out forecasts: 111 failed rows out of 114588 requested rows.

LogLik/AIC/BIC below describe the first successful refit within each period, conditional on fixed ARMA residuals. They are not joint ARMA-GARCH criteria.
The fitting origin and residual sample size are shown. Lower AIC/BIC and higher LogLik describe that fit; lower MSE/MAE describe held-out forecasts.
MAPE is undefined when the target crosses the existing threshold; the CSV retains the project's masked MAPE and exclusion counts.

## later / google_class_a / dwt_garch

ARMA(2,2), GARCH(1,1). Common held-out dates: 2763. Fit origin(s): 2015-01-05; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian |  1420.3 | -2834.6 | -2821.89 | 8.64318e-07 | 0.000385009 | 99.89 | No |
| Student-t | 1472.16 | -2936.31 | -2919.37 | 8.46355e-07 | 0.000388415 | 99.89 | No |
| GED | 1458.54 | -2909.07 | -2892.12 | 8.48033e-07 | 0.00038318 | 99.89 | No |

MSE change relative to Gaussian: Student-t -2.078%; GED -1.884%. Lowest MSE: Student-t; lowest MAE: GED.

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

ARMA(3,2), GARCH(1,1). Common held-out dates: 2714. Fit origin(s): 2015-01-12; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1318.96 | -2631.92 | -2619.21 | 8.97378e-07 | 0.000334221 | 99.93 | No |
| Student-t | 1416.35 | -2824.69 | -2807.75 | 9.09649e-07 | 0.000334966 | 99.93 | No |
| GED | 1404.15 | -2800.29 | -2783.35 | 9.26172e-07 | 0.00032652 | 99.93 | No |

MSE change relative to Gaussian: Student-t +1.367%; GED +3.209%. Lowest MSE: Gaussian; lowest MAE: GED.

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

ARMA(3,3), GARCH(1,1). Common held-out dates: 2763. Fit origin(s): 2015-01-05; fit n: 511.

| Distribution | LogLik | AIC | BIC | MSE | MAE | Coverage % | All refits converged |
|---|---:|---:|---:|---:|---:|---:|---|
| Gaussian | 1575.66 | -3145.32 | -3132.61 | 6.89813e-07 | 0.000284525 | 99.89 | No |
| Student-t |  1592.3 | -3176.59 | -3159.64 | 6.80666e-07 | 0.000300912 | 99.89 | No |
| GED | 1590.39 | -3172.78 | -3155.84 | 6.75072e-07 | 0.000282838 | 99.89 | No |

MSE change relative to Gaussian: Student-t -1.326%; GED -2.137%. Lowest MSE: GED; lowest MAE: GED.

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
| Gaussian | 1248.59 | -2491.18 | -2478.47 | 6.04654e-07 | 0.000265449 | 100.00 | Yes |
| Student-t | 1301.89 | -2595.78 | -2578.83 | 6.06949e-07 | 0.000255634 | 100.00 | Yes |
| GED | 1293.08 | -2578.16 | -2561.22 | 6.0563e-07 | 0.00025512 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +0.380%; GED +0.162%. Lowest MSE: Gaussian; lowest MAE: GED.

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
| Gaussian | 1236.65 | -2467.31 | -2454.6 | 6.21698e-06 | 0.000526661 | 99.86 | No |
| Student-t |  1260.5 |   -2513 | -2496.05 | 6.17665e-06 | 0.000506517 | 99.86 | No |
| GED | 1255.31 | -2502.62 | -2485.67 | 6.22808e-06 | 0.000507819 | 99.86 | No |

MSE change relative to Gaussian: Student-t -0.649%; GED +0.179%. Lowest MSE: Student-t; lowest MAE: Student-t.

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
| Gaussian | 1826.15 | -3646.3 | -3633.59 | 3.24529e-08 | 8.43931e-05 | 100.00 | Yes |
| Student-t |  1848.2 | -3688.41 | -3671.46 | 3.27243e-08 | 8.50878e-05 | 100.00 | Yes |
| GED | 1847.92 | -3687.84 | -3670.89 | 3.25509e-08 | 8.45199e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +0.836%; GED +0.302%. Lowest MSE: Gaussian; lowest MAE: Gaussian.

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
| Gaussian | 1461.81 | -2917.62 | -2904.91 | 1.80842e-08 | 7.88028e-05 | 100.00 | Yes |
| Student-t | 1464.97 | -2921.93 | -2904.99 | 1.80854e-08 | 7.87021e-05 | 100.00 | Yes |
| GED | 1465.01 | -2922.02 | -2905.07 | 1.80841e-08 | 7.87249e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +0.007%; GED -0.001%. Lowest MSE: GED; lowest MAE: Student-t.

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
| Gaussian |  1953.6 | -3901.21 | -3888.5 | 4.61089e-09 | 2.74143e-05 | 100.00 | Yes |
| Student-t |  2004.3 | -4000.6 | -3983.65 | 4.30825e-09 | 2.64611e-05 | 100.00 | Yes |
| GED | 1996.78 | -3985.56 | -3968.62 | 4.38544e-09 | 2.60769e-05 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t -6.564%; GED -4.890%. Lowest MSE: Student-t; lowest MAE: GED.

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
| Gaussian | 1427.45 | -2848.89 | -2836.18 | 1.73629e-07 | 0.000164522 | 100.00 | Yes |
| Student-t |  1435.8 | -2863.59 | -2846.65 | 1.74444e-07 | 0.000165075 | 100.00 | Yes |
| GED | 1435.33 | -2862.65 | -2845.71 | 1.73718e-07 | 0.000163667 | 100.00 | Yes |

MSE change relative to Gaussian: Student-t +0.469%; GED +0.051%. Lowest MSE: Gaussian; lowest MAE: GED.

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

GED has the lowest MSE in 10 of 27 groups and the lowest MAE in 18; Student-t has the lowest MSE in 13 and the lowest MAE in 6; Gaussian has the lowest MSE in 4 and the lowest MAE in 3.
Alternative innovations can improve fit and/or forecasting performance for individual series and specifications. Fit rankings and forecasting rankings can differ, and MSE and MAE can favor different distributions.
These point comparisons establish neither significance nor a universal winner. The Gaussian specification remains the primary baseline. The two-step Gaussian mean, optimizer starts, numerical guards and retrospective status of the later period are documented in ../../README.md.
baseline_reproduction.csv verifies the existing Gaussian and Student-t forecast paths; baseline_integrity.csv verifies every protected file remained unchanged.

111 failed refit attempts came from the ARMA mean step; 0 came from other fitting errors. Inspect each pipeline's fit_attempts.csv for dates and messages.
