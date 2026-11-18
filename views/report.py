import datetime as dt

import streamlit as st

import db, ui

ui.title("Monthly report", "Pieces, earnings and payments for each worker.")
e = db.q("""select substr(e.date,1,7) as "Month", e.worker_id, w.name as "Worker", i.name as "Item",
         e.qty as "Pcs", e.qty*e.rate as "Amount" from entries e
         join workers w on w.id=e.worker_id join items i on i.id=e.item_id""")
if e.empty:
    st.info("No entries yet.")
    st.stop()

months = sorted(e["Month"].unique())
a, b = st.columns(2)
m_from = a.selectbox("From month", months, index=max(0, len(months) - 5))
m_to = b.selectbox("To month", months, index=len(months) - 1)
e = e[(e["Month"] >= m_from) & (e["Month"] <= m_to)]
pay = db.q('select month as "Month", worker_id, sum(amount) as "Paid" from payments group by month, worker_id')
s = e.groupby(["Month", "worker_id", "Worker"], as_index=False).agg(Pcs=("Pcs", "sum"), Earned=("Amount", "sum"))
s = s.merge(pay, on=["Month", "worker_id"], how="left").fillna({"Paid": 0})
s["Due"] = s["Earned"] - s["Paid"]
cfg = {k: st.column_config.NumberColumn(format="₹%.2f") for k in ["Earned", "Paid", "Due"]}

t = s.groupby("Worker", as_index=False)[["Pcs", "Earned", "Paid", "Due"]].sum()
st.markdown(f"### {m_from} to {m_to}")
ui.stats([("Pieces", int(t["Pcs"].sum())), ("Earned", db.money(t["Earned"].sum())),
          ("Paid", db.money(t["Paid"].sum())), ("Due", db.money(t["Due"].sum()))])
st.dataframe(t, hide_index=True, width="stretch", column_config=cfg)

for m in months:
    if m_from <= m <= m_to:
        with st.expander(m, expanded=(m == m_to)):
            st.dataframe(s[s["Month"] == m][["Worker", "Pcs", "Earned", "Paid", "Due"]],
                         hide_index=True, width="stretch", column_config=cfg)
            pv = e[e["Month"] == m].pivot_table(index="Worker", columns="Item", values="Pcs", aggfunc="sum", fill_value=0)
            st.caption("Pieces by item")
            st.dataframe(pv, width="stretch")
st.download_button("Download summary (CSV)", s.drop(columns="worker_id").to_csv(index=False),
                   f"payroll_{m_from}_to_{m_to}.csv", "text/csv", icon=":material/download:")

with st.container(border=True):
    st.markdown("### Record a payment")
    with st.form("pay", clear_on_submit=True, border=False):
        c = st.columns(2)
        pw = c[0].selectbox("Worker", sorted(e["Worker"].unique()))
        pm = c[1].selectbox("For month", months, index=len(months) - 1)
        pa = c[0].number_input("Amount ₹", 0.0, step=50.0)
        pn = c[1].text_input("Note (optional)")
        if st.form_submit_button("Save payment", type="primary") and pa > 0:
            wid = int(e.loc[e["Worker"] == pw, "worker_id"].iloc[0])
            db.run("insert into payments(month,worker_id,amount,note,paid_on) values(?,?,?,?,?)",
                   (pm, wid, pa, pn, str(dt.date.today())))
            st.rerun()

ph = db.q("""select p.id, p.paid_on as "Date", p.month as "Month", w.name as "Worker", p.amount as "Amount", p.note as "Note"
             from payments p join workers w on w.id=p.worker_id order by p.id desc""")
if not ph.empty:
    with st.expander("Payment history"):
        st.dataframe(ph, hide_index=True, width="stretch")
        did = st.selectbox("Delete a payment by id", ph["id"], index=None)
        if did is not None and st.button("Delete"):
            db.run("delete from payments where id=?", (int(did),))
            st.rerun()
