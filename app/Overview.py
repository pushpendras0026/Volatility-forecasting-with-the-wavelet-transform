"""Entry point: top navigation bar with one tab per page."""
import streamlit as st

st.set_page_config(page_title="Wavelet GARCH", page_icon=":material/show_chart:", layout="wide")

pages = [
    st.Page("views/overview.py", title="Overview", icon=":material/home:", default=True),
    st.Page("views/lessons.py", title="Video lessons", icon=":material/play_circle:"),
    st.Page("views/concepts.py", title="Concepts", icon=":material/menu_book:"),
    st.Page("views/glossary.py", title="Glossary", icon=":material/translate:"),
    st.Page("views/paper.py", title="The paper", icon=":material/article:"),
    st.Page("views/architecture.py", title="Architectures", icon=":material/account_tree:"),
    st.Page("views/results.py", title="Results", icon=":material/bar_chart:"),
    st.Page("views/lab.py", title="Parameter lab", icon=":material/science:"),
    st.Page("views/team.py", title="Team", icon=":material/groups:"),
]
st.navigation(pages, position="top").run()
