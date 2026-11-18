"""Storage. Uses a hosted Postgres (Neon etc.) when DATABASE_URL is set, otherwise a local SQLite file.

DATABASE_URL is read from Streamlit secrets or the environment. Queries use `?` placeholders
and quoted column aliases (as "Worker") so the same SQL works on both databases.
"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, inspect, text

SQLITE = Path(__file__).with_name("ledger.db")


def _url():
    try:
        u = st.secrets.get("DATABASE_URL")
    except Exception:
        u = None
    u = u or os.environ.get("DATABASE_URL")
    if not u:
        return f"sqlite:///{SQLITE}"
    for old in ("postgres://", "postgresql://"):
        if u.startswith(old):
            return "postgresql+psycopg://" + u[len(old):]
    return u


@st.cache_resource
def engine():
    return create_engine(_url(), pool_pre_ping=True, pool_recycle=300)


def _bind(sql, p):
    parts = sql.split("?")
    out, params = parts[0], {}
    for i, part in enumerate(parts[1:]):
        v = p[i]
        params[f"p{i}"] = v.item() if hasattr(v, "item") else v
        out += f":p{i}" + part
    return text(out), params


def run(sql, p=()):
    stmt, params = _bind(sql, p)
    with engine().begin() as c:
        c.execute(stmt, params)


def q(sql, p=()):
    stmt, params = _bind(sql, p)
    with engine().connect() as c:
        return pd.read_sql_query(stmt, c, params=params)


def init():
    pk = "serial primary key" if engine().dialect.name == "postgresql" else "integer primary key"
    for ddl in (
        f"create table if not exists workers(id {pk}, name text, level text, active int default 1, skills text, phone text)",
        f"create table if not exists items(id {pk}, category text, name text, method text, "
        "rate_exp double precision, rate_beg double precision, active int default 1)",
        f"create table if not exists entries(id {pk}, date text, worker_id int, item_id int, qty int, "
        "rate double precision, remark text, unique(date, worker_id, item_id))",
        f"create table if not exists payments(id {pk}, month text, worker_id int, amount double precision, "
        "note text, paid_on text)",
    ):
        run(ddl)
    insp = inspect(engine())
    for table, col in (("workers", "skills"), ("workers", "phone"), ("entries", "remark")):
        if col not in [c["name"] for c in insp.get_columns(table)]:
            run(f"alter table {table} add column {col} text")
    if int(q("select count(*) as n from items")["n"].iloc[0]) == 0:
        seed = [("Blouse", "Golgala Dori", 5.5, 4.5), ("Blouse", "Chokogola Dori", 5.5, 4.5),
                ("Blouse", "Golgola Plain", 4.5, 3.5), ("Blouse", "Chokogola Plain", 4.5, 3.5),
                ("Blouse", "Color", 4.5, 3.5)]
        seed += [("Petticoat", n, 0, 0) for n in
                 ["A-36-plain", "A-40-plain", "A-40-kuchi", "A-40-6Cut", "B-36-plain", "B-40-plain"]]
        seed += [("Bag", n, 0, 0) for n in ["10x12-side", "12x15-side", "15x17-basta"]]
        for cat, name, re_, rb in seed:
            run("insert into items(category,name,method,rate_exp,rate_beg) values(?,?,'Machine',?,?)",
                (cat, name, re_, rb))


def money(n):
    return f"₹{n:,.2f}"


def all_cats():
    return list(dict.fromkeys(q("select category from items order by id")["category"]))


def skills_of(raw):
    """Categories a worker does; empty or unset means all."""
    got = [x for x in raw.split(",") if x] if isinstance(raw, str) else []
    return got or all_cats()
