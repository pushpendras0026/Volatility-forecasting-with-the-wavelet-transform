"""Video lessons: the narrated 3Blue1Brown-style explainer, one short chapter per topic, with a self-check quiz."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/ on the path when run standalone

import streamlit as st

from lib import common as C

C.setup("Video lessons")
st.markdown('<div class="hero"><h1>Video lessons</h1>'
            "Short narrated animations in the 3Blue1Brown style. Each lesson explains one graph or idea used in the app, "
            "with captions. The numbers in the animations are read from the same result files as the app.</div>",
            unsafe_allow_html=True)

GROUPS = {
    "Foundations": ["s01", "s03", "s04"],
    "Models": ["s05", "s06", "s07", "s08"],
    "The paper and our design": ["s09", "s10"],
    "Results and extensions": ["s11", "s12", "s13", "s14", "s15", "s16"],
}
QUIZ = {
    "s01": ("What does 'volatility clustering' mean?",
            ["Large moves tend to follow large moves, and calm follows calm", "Returns are always positive",
             "Volatility is constant over time"], 0),
    "s03": ("What is the forecasting target y(t+1)?",
            ["The next price", "The squared deviation of tomorrow's return from the recent 20-day mean", "The sign of tomorrow's return"], 1),
    "s04": ("Why do heavy tails matter for a Gaussian model?",
            ["It overestimates extreme days", "It treats extreme days as almost impossible and so underweights them",
             "Tails do not affect estimation"], 1),
    "s06": ("In GARCH(1,1), what does alpha + beta measure?",
            ["Persistence: how slowly a volatility shock fades", "The mean return", "The number of parameters"], 0),
    "s07": ("How does the MODWT differ from the paired DWT?",
            ["It overlaps windows and gives one detail value per day instead of one per two days",
             "It uses a different data set", "It removes outliers"], 0),
    "s11": ("What is RMSE / raw-GARCH RMSE below 1?",
            ["The model is more accurate than raw GARCH", "The model is less accurate", "The models are identical"], 0),
    "s12": ("Why try Student-t or GED innovations?",
            ["They allow heavier tails than a normal distribution", "They make fitting faster", "They remove the ARMA step"], 0),
    "s14": ("What is an equal-weight ensemble?",
            ["The average of several models' forecasts", "The best single model", "A model trained on all datasets"], 0),
}

q = st.text_input("Search lessons", placeholder="e.g. GARCH, wavelet, tails, MLP")
for grp, keys in GROUPS.items():
    keys = [k for k in keys if not q or q.lower() in C.CLIP_TITLES[k].lower()]
    if not keys:
        continue
    st.header(grp)
    cols = st.columns(2)
    for i, k in enumerate(keys):
        with cols[i % 2]:
            st.subheader(f"{int(k[1:])}. {C.CLIP_TITLES[k]}")
            f = C.CLIPS / f"{k}.mp4"
            if f.exists():
                vtt = C.CLIPS / f"{k}.vtt"
                try:
                    st.video(str(f), subtitles=str(vtt) if vtt.exists() else None)
                except TypeError:
                    st.video(str(f))
                with st.expander("Transcript"):
                    if vtt.exists():
                        lines = [l for l in vtt.read_text(encoding="utf-8").splitlines()
                                 if l and not l.startswith("WEBVTT") and "-->" not in l]
                        st.write(" ".join(lines))
            if k in QUIZ:
                qq, opts, ans = QUIZ[k]
                with st.expander("Check yourself"):
                    pick = st.radio(qq, opts, index=None, key=f"quiz_{k}")
                    if pick is not None:
                        (st.success if opts.index(pick) == ans else st.error)(
                            "Correct." if opts.index(pick) == ans else f"Not quite. Answer: {opts[ans]}")
