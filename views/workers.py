import html

import streamlit as st

import db, ui
from settings import LEVELS

E = html.escape
ui.title("Workers", "Who stitches for you, how to reach them, and what they work on.")


def add_worker():
    n = st.session_state.get("wn", "").strip()
    if n:
        db.run("insert into workers(name,level,skills,phone) values(?,?,?,?)",
               (n, st.session_state["wl"], ",".join(st.session_state["wsk"]), st.session_state.get("wp", "").strip()))
        st.session_state["wn"] = ""
        st.session_state["wp"] = ""


with st.container(border=True):
    st.markdown("### Add a worker")
    a, b, c = st.columns(3)
    a.text_input("Name", key="wn")
    b.text_input("Phone number", key="wp", placeholder="98xxxxxxxx")
    c.selectbox("Level", LEVELS, key="wl")
    st.multiselect("Works on", db.all_cats(), default=db.all_cats(), key="wsk")
    st.button("Add worker", type="primary", on_click=add_worker)

ws = db.q("select id, name, level, skills, phone, active from workers order by active desc, name")
if ws.empty:
    st.markdown("<div class='empty'>No workers yet.</div>", unsafe_allow_html=True)
else:
    ws["skills"] = ws["skills"].apply(db.skills_of)
    cards = ""
    for r in ws.itertuples():
        phone = r.phone if isinstance(r.phone, str) else ""
        cards += (f"<div class='wk{'' if r.active else ' off'}'><div><span class='wk-name'>{E(r.name)}</span> "
                  f"{ui.chip(r.level, 'mach')}{'' if r.active else ui.chip('inactive', 'mach')}</div>"
                  f"<div>{''.join(ui.chip(s) for s in r.skills)}</div>"
                  f"<div class='wk-ph'>{E(phone) if phone else '&nbsp;'}</div>"
                  f"<div class='wk-act'>{ui.call_buttons(phone)}</div></div>")
    st.markdown(f"<div class='wlist'>{cards}</div>", unsafe_allow_html=True)

    with st.expander("Edit workers", icon=":material/edit:"):
        ws["active"] = ws["active"].astype(bool)
        ed = st.data_editor(ws, hide_index=True, width="stretch", disabled=["id"], key="wed", column_config={
            "level": st.column_config.SelectboxColumn("Level", options=LEVELS),
            "phone": st.column_config.TextColumn("Phone"),
            "skills": st.column_config.MultiselectColumn("Works on", options=db.all_cats()),
            "active": st.column_config.CheckboxColumn("Active")})
        if st.button("Save worker changes", type="primary"):
            for _, r in ed.iterrows():
                db.run("update workers set name=?, level=?, skills=?, phone=?, active=? where id=?",
                       (r["name"], r["level"], ",".join(r["skills"] or []),
                        (r["phone"] or "") if isinstance(r["phone"], str) else "", int(r["active"]), int(r["id"])))
            st.toast("Saved")
            st.rerun()
        st.caption("Promoting a beginner only changes rates for new entries. Old entries keep the rate they were saved with.")
