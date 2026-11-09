"""Team, code links and how to reproduce."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ on the path when run standalone

import pandas as pd
import streamlit as st

from lib import common as C

C.setup("Team and reproducibility")
REPO = "https://github.com/pushpendras0026/Volatility-forecasting-with-the-wavelet-transform"

st.title("Team and reproducibility")
st.markdown("**DA-3041, Group 9, IIT Guwahati**")
st.dataframe(pd.DataFrame({"Name": ["Neeharika", "Pratyaksha Jha", "Pushpendra Singh", "Somita Agarwal"],
                           "Roll number": ["240150008", "240150025", "240150026", "240150035"]}),
             hide_index=True, width="content")

st.header("Source code")
st.markdown(f"Repository: [{REPO}]({REPO})")
st.markdown(
    """
| Component | Location in the repository |
|---|---|
| Model implementation (R 4.6, base R and `nnet`) | `R/` (`engine.R`, `models.R`, `wavelets.R`, `ensemble.R`, `mlp.R`, `metrics.R`, `data.R`) |
| Settings and model grid | `config/experiment.R` |
| Results of the final run | `results/<run id>/` (`SUMMARY.md`, `tables/`, per-origin forecasts) |
| Innovation-distribution extension | `Distribution/` |
| Prepared data and provenance | `data/` (`manifest.csv`, `issues.csv`) |
| Report | `report/` |
| This application | `app/` (`Overview.py`, `pages/`, `lib/`, `tools/`) |
    """)

st.header("Reproducing the results")
st.code("""Rscript run_all.R --workers 16

# or step by step
Rscript tests/run_tests.R
Rscript run.R --workers 16
Rscript tools/analyze.R
Rscript tools/figures.R
Rscript Distribution/tests.R
Rscript Distribution/innovation_distribution_robustness.R --workers 12
Rscript Distribution/report.R""", language="bash")
st.markdown("The worker count affects run time only. Completed jobs are reused only when the code, data and configuration "
            "fingerprint is unchanged.")

st.header("Running this application locally")
st.code("""cd app
pip install -r requirements.txt
streamlit run Overview.py""", language="bash")
man = C.read_csv("SYNC_MANIFEST.csv")
st.markdown(f"The `data_corrected` folder holds {len(man)} result files ({man.bytes.sum() / 1e6:.1f} MB) copied from the R run. "
            "`data/SOURCES.md` maps each file to its origin.")
with st.expander("List of bundled files"):
    st.dataframe(man, hide_index=True, width="stretch")

st.header("References")
st.markdown("""
* Ismail, M. T., Audu, B. and Tumala, M. M. (2016). Volatility forecasting with the wavelet transformation algorithm GARCH model:
  Evidence from African stock markets. *J. Finance and Data Science* 2, 125-135. doi:10.1016/j.jfds.2016.09.002
* Rubio, L. et al. (2023). Forecasting volatility by using wavelet transform, ARIMA and GARCH models. *Eurasian Economic Review* 13, 803-830.
* Engle, R. F. (1982). Autoregressive conditional heteroscedasticity. *Econometrica* 50(4), 987-1007.
* Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. *J. Econometrics* 31(3), 307-327.
* Percival, D. B. and Walden, A. T. (2000). *Wavelet Methods for Time Series Analysis*. Cambridge University Press.
""")
