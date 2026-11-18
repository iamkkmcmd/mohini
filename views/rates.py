import streamlit as st

import db, ui

ui.title("Rates", "Payment per piece, for experienced and beginner workers.")
rt = db.q("select id, category, name, rate_exp, rate_beg from items where active=1 order by id")
ed = st.data_editor(rt, hide_index=True, width="stretch", disabled=["id", "category", "name"], key="red",
                    column_config={"category": "Category", "name": "Item",
                                   "rate_exp": st.column_config.NumberColumn("Experienced ₹", format="%.2f", min_value=0),
                                   "rate_beg": st.column_config.NumberColumn("Beginner ₹", format="%.2f", min_value=0)})
if st.button("Save rates", type="primary"):
    for _, r in ed.iterrows():
        db.run("update items set rate_exp=?, rate_beg=? where id=?", (float(r["rate_exp"]), float(r["rate_beg"]), int(r["id"])))
    st.toast("Saved")
    st.rerun()
st.caption("A rate change applies to new entries only. Old entries keep the rate they were saved with.")
