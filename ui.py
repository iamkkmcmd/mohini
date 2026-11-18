"""Shared look: CSS loading, header, navigation and small HTML helpers."""
import datetime as dt
import html
from pathlib import Path

import streamlit as st

from settings import BUSINESS, OWNER

STYLES = Path(__file__).with_name("styles")


def load_css():
    try:
        dark = st.context.theme.type == "dark"
    except Exception:
        dark = False
    css = (STYLES / ("dark.css" if dark else "light.css")).read_text() + (STYLES / "base.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def header(pages):
    st.markdown(
        f"""<div class="top"><div class="brand"><span class="logo">{html.escape(BUSINESS[:1])}</span>
        <div><div class="name">{html.escape(BUSINESS)}</div><div class="tag">Stitching ledger</div></div></div>
        <div class="meta"><div class="own">{html.escape(OWNER)}</div>
        <div class="today">{dt.date.today():%a, %d %b %Y}</div></div></div>""", unsafe_allow_html=True)
    with st.container(key="nav"):
        for p in pages:
            st.page_link(p)


def title(text, sub=""):
    st.markdown(f"<h1 class='pt'>{html.escape(text)}</h1><p class='sub'>{html.escape(sub)}</p>", unsafe_allow_html=True)


def stats(pairs):
    st.markdown("<div class='stats'>" + "".join(
        f"<div class='stat'><span>{html.escape(str(k))}</span><b>{html.escape(str(v))}</b></div>" for k, v in pairs)
        + "</div>", unsafe_allow_html=True)


def chip(text, kind="cat"):
    return f"<span class='chip {kind}'>{html.escape(text)}</span>"


def phone_digits(raw):
    """Digits only; a 10-digit Indian number gets the 91 country code."""
    d = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if len(d) == 10:
        d = "91" + d
    elif len(d) == 11 and d.startswith("0"):
        d = "91" + d[1:]
    return d


def call_buttons(raw):
    d = phone_digits(raw)
    if len(d) < 11:
        return "<span class='nophone'>No number yet</span>"
    return (f"<a class='abtn call' href='tel:+{d}'>Call</a>"
            f"<a class='abtn wa' href='https://wa.me/{d}' target='_blank' rel='noopener'>WhatsApp</a>")
