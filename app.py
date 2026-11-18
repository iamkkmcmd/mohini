"""Run with:  streamlit run app.py"""
import streamlit as st

from settings import BUSINESS

st.set_page_config(page_title=f"{BUSINESS} Ledger", page_icon="🧵", layout="wide")

import db, ui  # noqa: E402  (after set_page_config)

db.init()
pages = [
    st.Page("views/entry.py", title="Entry", icon=":material/edit_note:", url_path="entry", default=True),
    st.Page("views/workers.py", title="Workers", icon=":material/group:", url_path="workers"),
    st.Page("views/items.py", title="Items", icon=":material/checkroom:", url_path="items"),
    st.Page("views/rates.py", title="Rates", icon=":material/currency_rupee:", url_path="rates"),
    st.Page("views/report.py", title="Report", icon=":material/receipt_long:", url_path="report"),
]
nav = st.navigation(pages, position="hidden")
ui.load_css()
ui.header(pages)
nav.run()
