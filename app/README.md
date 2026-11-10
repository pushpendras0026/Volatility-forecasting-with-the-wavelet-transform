# Wavelet-GARCH volatility forecasting: interactive application

Streamlit application accompanying the DA-3041 (Group 9, IIT Guwahati) study of volatility forecasting with the
wavelet transform and GARCH models. It is written for readers who have not read the original paper.

| Tab (top bar) | Content |
|---|---|
| Overview | Problem statement, empirical illustration, heavy tails, study design |
| Video lessons | 17 short narrated 3Blue1Brown-style animations with captions, transcripts and self-check questions |
| Concepts | Definitions, formulas and interactive plots for every term used |
| Glossary | Searchable definitions of every term, linked to the lesson that explains it |
| The paper | Summary and critical reading of Ismail, Audu and Tumala (2016) |
| Architectures | Block diagram, equations, training protocol and saved results of every model |
| Results | Saved out-of-sample results, extensions (Student-t, GED, ensembles, MLP), diagnostics and a model-vs-model head-to-head |
| Parameter lab | Python implementation for varying orders, window length, refit cadence and innovation distribution |
| Team | Authors, repository layout and commands to reproduce the R results |

Every chart has a "How to read this" note, the relevant lesson clip sits next to its topic, and result tables can be
downloaded as CSV. The clips in `media/clips/` are 720p re-encodes of `video/final/parts/` (captions from `audio/timings.json`).
The 17 long lessons appear only in the Video lessons tab. Eleven short narrated derivation clips with burned-in captions
(`media/micro/`; sources and numeric checks in `video/micro/`) sit beside the topic they prove: log-likelihoods and parameter
effects for the Gaussian, Student-t and GED, AIC/BIC, the target proxy, GARCH long-run variance, Haar reconstruction and
the ensemble identity. Concepts also has a profile-likelihood fit of the tail shape on real returns.
The app uses a dark theme (`.streamlit/config.toml`) and top navigation (`st.navigation(position="top")` in `Overview.py`).

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

## Themes

A switcher at the top right of every page offers three looks: **Midnight** (softened dark), **Daylight** (clean light) and
**Executive** (warm paper with serif headings). The choice applies to the page chrome, Plotly charts and tables and is kept
while you move between tabs. Series colours keep their meaning (raw blue, DWT orange, MODWT green) in every theme; only the shade
changes for contrast. Definitions are in `lib/common.py` (`THEMES`).
