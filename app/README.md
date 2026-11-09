# Wavelet-GARCH volatility forecasting: interactive application

Streamlit application accompanying the DA-3041 (Group 9, IIT Guwahati) study of volatility forecasting with the
wavelet transform and GARCH models. It is written for readers who have not read the original paper.

| Page | Content |
|---|---|
| Overview | Problem statement, empirical illustration, heavy tails, study design |
| Concepts | Definitions, formulas and interactive plots for every term used |
| The paper | Summary and critical reading of Ismail, Audu and Tumala (2016) |
| Architecture navigator | Block diagram, equations, training protocol and saved results of every model |
| Results explorer | Saved out-of-sample results, extensions (Student-t, GED, ensembles, MLP) and diagnostics |
| Parameter lab | Python implementation for varying orders, window length, refit cadence and innovation distribution |
| Team and reproducibility | Authors, repository layout and commands to reproduce the R results |

All reported results are read from the saved R output in `data_corrected/` (see `data/SOURCES.md` for provenance).
The Parameter lab is a Python re-implementation intended for exploration; `VALIDATION.md` documents its agreement
with the R forecasts.

## Run locally

```bash
cd app
pip install -r requirements.txt
streamlit run Overview.py
```

Python 3.12 or 3.13 is supported.

## Deployment

The application is deployed on Streamlit Community Cloud from this repository
(main file path `app/Overview.py`, branch `main`).

## Colour scheme

Raw `#1F5FA8`, DWT `#D95F02`, MODWT `#1B9E77`, paper `#B8322A`.
