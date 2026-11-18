import datetime as dt
import html

import streamlit as st

import db, ui
from settings import ICON

E = html.escape
ui.title("Daily entry", "Count the pieces each worker stitched today. Totals add up by themselves.")
workers = db.q("select * from workers where active=1 order by name")

with st.container(border=True):
    c1, c2 = st.columns([1, 2], gap="medium")
    d = c1.date_input("Date", dt.date.today(), format="DD/MM/YYYY")
    if workers.empty:
        c2.info("Add a worker in the Workers page first.")
        wname = None
    else:
        wname = c2.pills("Worker", list(workers["name"]), selection_mode="single", key="w_pick")

main, side = st.columns([3, 2], gap="large")

# ---------- item boxes ----------
with main:
    if wname:
        w = workers[workers["name"] == wname].iloc[0]
        wid, beg = int(w["id"]), w["level"] == "Beginner"
        mine = db.skills_of(w["skills"])
        items = db.q("select * from items where active=1 order by id")
        items = items[items["category"].isin(mine)]
        ex = db.q("select item_id, qty, remark from entries where date=? and worker_id=?", (str(d), wid))
        exmap = {int(x): int(y) for x, y in zip(ex["item_id"], ex["qty"])}
        exrem = {int(x): (y if isinstance(y, str) else "") for x, y in zip(ex["item_id"], ex["remark"])}
        st.caption(f"**{wname}** · {w['level']} rates · {', '.join(mine)}")
        if items.empty:
            st.info("No items for this worker. Set what they work on in the Workers page.")
        elif (items[["rate_exp", "rate_beg"]].min(axis=1) == 0).any():
            st.warning("Some items have a ₹0 rate. Set them in the Rates page before paying.")

        vals, rates, rems = {}, {}, {}
        with st.container(key="grid"):
            for cat, grp in items.groupby("category", sort=False):
                st.markdown(f"<div class='cat'>{ICON.get(cat, '🧵')} {E(cat)}</div>", unsafe_allow_html=True)
                for i in range(0, len(grp), 3):
                    cols = st.columns(3)
                    for col, (_, it) in zip(cols, grp.iloc[i:i + 3].iterrows()):
                        iid = int(it["id"])
                        rates[iid] = float(it["rate_beg"] if beg else it["rate_exp"])
                        with col, st.container(border=True, key=f"box_{iid}"):
                            st.markdown(f"<div class='ib-t'>{E(it['name'])}</div>"
                                        f"<div class='ib-r'>₹{rates[iid]:g} per piece · {it['method']}</div>",
                                        unsafe_allow_html=True)
                            vals[iid] = st.number_input(it["name"], 0, 5000, exmap.get(iid, 0),
                                                        key=f"q_{d}_{wid}_{iid}", label_visibility="collapsed")
                            rems[iid] = st.text_input("Remark", exrem.get(iid, ""), key=f"r_{d}_{wid}_{iid}",
                                                      placeholder="Remark (optional)", label_visibility="collapsed")
            hot = ",".join(f".st-key-box_{i}" for i, v in vals.items() if v > 0)
            if hot:
                st.markdown(f"<style>{hot}{{border-color:var(--accent)!important;background:var(--accent-soft)!important}}</style>",
                            unsafe_allow_html=True)
        ui.stats([("Pieces", sum(vals.values())), ("Amount", db.money(sum(v * rates[i] for i, v in vals.items())))])
        if st.button("Save entries", type="primary", icon=":material/check:", width="stretch"):
            for iid, qty in vals.items():
                key = (str(d), wid, iid)
                if qty == 0:
                    db.run("delete from entries where date=? and worker_id=? and item_id=?", key)
                elif iid in exmap:
                    db.run("update entries set qty=?, remark=? where date=? and worker_id=? and item_id=?",
                           (qty, rems[iid].strip(), *key))
                else:
                    db.run("insert into entries(date,worker_id,item_id,qty,rate,remark) values(?,?,?,?,?,?)",
                           (*key, qty, rates[iid], rems[iid].strip()))
            st.toast("Saved")
            st.rerun()
    elif not workers.empty:
        st.markdown("<div class='empty'>Pick a worker above to start counting pieces.</div>", unsafe_allow_html=True)

# ---------- entry book ----------
with side, st.container(border=True, key="book"):
    day = db.q("""select e.id, w.name as "Worker", i.category as "Category", i.name as "Item", i.method as "Method",
                  e.qty as "Pcs", e.rate as "Rate", e.qty*e.rate as "Amount", e.remark as "Remark"
                  from entries e join workers w on w.id=e.worker_id join items i on i.id=e.item_id
                  where e.date=? order by w.name, i.id""", (str(d),))
    cat = st.pills("Category", ["All"] + list(dict.fromkeys(day["Category"])), default="All",
                   key="cat_f", label_visibility="collapsed") or "All"
    who = st.selectbox("Worker", ["All workers"] + sorted(day["Worker"].unique()), label_visibility="collapsed")
    if cat != "All":
        day = day[day["Category"] == cat]
    if who != "All workers":
        day = day[day["Worker"] == who]
    rows = "".join(
        f"<tr><td>{E(r.Worker)}</td><td>{E(r.Item)}<div>{ui.chip(r.Category)}"
        f"{ui.chip(r.Method, 'hand' if r.Method == 'Hand' else 'mach')}</div>"
        f"{f'<div class=rmk>{E(r.Remark)}</div>' if isinstance(r.Remark, str) and r.Remark else ''}</td>"
        f"<td class='n b'>{r.Pcs}</td><td class='n m'>₹{r.Rate:.2f}</td><td class='n b'>₹{r.Amount:.2f}</td></tr>"
        for r in day.itertuples()) or "<tr><td colspan=5 class='empty'>No entries for this day.</td></tr>"
    st.markdown(f"<div class='bk-h'><div><h3>Entry book</h3><div class='dt'>{d:%d %b %Y}</div></div></div>",
                unsafe_allow_html=True)
    ui.stats([("Pieces", int(day["Pcs"].sum())), ("Amount", db.money(day["Amount"].sum()))])
    st.markdown(f"<div class='tbl'><table><tr><th>Worker</th><th>Item</th><th class='n'>Pcs</th><th class='n'>Rate</th>"
                f"<th class='n'>Amount</th></tr>{rows}</table></div>", unsafe_allow_html=True)
    if not day.empty:
        with st.popover("Remove an entry", icon=":material/delete:"):
            pick = st.selectbox("Entry", list(day["id"]), index=None, format_func=lambda i: (
                lambda r: f"{r.Worker} · {r.Item} · {r.Pcs} pcs")(day[day["id"] == i].iloc[0]))
            if pick is not None and st.button("Delete this entry"):
                db.run("delete from entries where id=?", (int(pick),))
                st.rerun()
