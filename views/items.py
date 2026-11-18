import streamlit as st

import db, ui
from settings import ICON, METHODS

ui.title("Items", "Everything you stitch, grouped by category.")
it = db.q("select id, category, name, method, active from items order by id")
for cat, g in it[it["active"] == 1].groupby("category", sort=False):
    st.markdown(f"**{ICON.get(cat, '🧵')} {cat}:** " + " · ".join(g["name"]))
cats = list(dict.fromkeys(it["category"])) or ["Blouse"]


def add_item():
    s = st.session_state
    cat = s["ic"] if s["ic"] != "New category" else s.get("icn", "").strip()
    nm = s.get("inm", "").strip()
    if cat and nm:
        db.run("insert into items(category,name,method,rate_exp,rate_beg) values(?,?,?,0,0)", (cat, nm, s["im"]))
        s["inm"] = ""
        s["icn"] = ""


with st.container(border=True):
    st.markdown("### Add an item")
    a, b = st.columns(2)
    sel = a.selectbox("Category", cats + ["New category"], key="ic")
    b.selectbox("Method", METHODS, key="im")
    if sel == "New category":
        st.text_input("New category name", key="icn")
    st.text_input("Item name (e.g. A-40-kuchi)", key="inm")
    st.button("Add item", type="primary", on_click=add_item)
    st.caption("New items start at ₹0. Set the rate on the Rates page.")

it["active"] = it["active"].astype(bool)
ed = st.data_editor(it, hide_index=True, width="stretch", disabled=["id"], key="ied", column_config={
    "method": st.column_config.SelectboxColumn("Method", options=METHODS),
    "active": st.column_config.CheckboxColumn("Active")})
if st.button("Save item changes"):
    for _, r in ed.iterrows():
        db.run("update items set category=?, name=?, method=?, active=? where id=?",
               (r["category"], r["name"], r["method"], int(r["active"]), int(r["id"])))
    st.toast("Saved")
    st.rerun()
st.caption("Untick Active to hide an item from the entry page. Old entries are kept.")
