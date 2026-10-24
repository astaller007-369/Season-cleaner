import pandas as pd
import streamlit as st

from cleaner import clean_season, detect_dayfirst, sort_by_date

st.set_page_config(page_title="Season Cleaner", layout="wide")
st.title("Season Cleaner")
st.caption("Unify the season column to 2026/27 and sort by date.")

uploaded = st.file_uploader("Choose a CSV file", type=["csv", "txt"])

with st.sidebar:
    st.header("Options")
    pivot = st.number_input(
        "Two-digit year cutoff",
        min_value=0, max_value=99, value=70,
        help="In 26/27 the '26' could be 1926 or 2026. Values at or above the cutoff "
             "become 19xx, values below become 20xx. With 70: 26/27 -> 2026/27, 85/86 -> 1985/86.",
    )
    date_order = st.radio("Date order", ["Auto-detect", "Day first (31/12/2026)", "Month first (12/31/2026)"])

if uploaded is None:
    st.info("Upload a CSV to begin.")
    st.stop()

try:
    df = pd.read_csv(uploaded, dtype=str, keep_default_na=False, sep=None,
                     engine="python", encoding="utf-8-sig")
except Exception as e:
    st.error(f"Could not read that file as CSV: {e}")
    st.stop()

cols = list(df.columns)


def guess(name: str) -> int:
    for i, c in enumerate(cols):
        if c.strip().lower() == name:
            return i
    for i, c in enumerate(cols):
        if name in c.lower():
            return i
    return 0


c1, c2, c3 = st.columns(3)
season_col = c1.selectbox("Season column", cols, index=guess("season"))
date_col = c2.selectbox("Date column", cols, index=guess("date"))
order = c3.radio("Sort by date", ["Ascending", "Descending"], horizontal=True)

if date_order.startswith("Auto"):
    dayfirst = detect_dayfirst(df[date_col])
else:
    dayfirst = date_order.startswith("Day")

original = df[season_col].copy()
out = df.copy()
out[season_col] = out[season_col].map(lambda v: clean_season(v, int(pivot)))
out = sort_by_date(out, date_col, ascending=(order == "Ascending"), dayfirst=dayfirst)

changed = (original != df[season_col].map(lambda v: clean_season(v, int(pivot)))).sum()
unrecognised = df[season_col].map(lambda v: clean_season(v, int(pivot))).loc[
    lambda s: (s != "") & ~s.str.match(r"^\d{4}/\d{2}$")
]

m1, m2, m3 = st.columns(3)
m1.metric("Rows", len(out))
m2.metric("Seasons changed", int(changed))
m3.metric("Unrecognised seasons", len(unrecognised))

if len(unrecognised):
    st.warning("Left unchanged: " + ", ".join(sorted(set(unrecognised.astype(str)))[:15]))

with st.expander("See what changed"):
    mapping = (
        pd.DataFrame({"Before": original, "After": df[season_col].map(lambda v: clean_season(v, int(pivot)))})
        .query("Before != After").drop_duplicates().sort_values("After")
    )
    st.dataframe(mapping, hide_index=True, use_container_width=True)

st.dataframe(out, use_container_width=True, hide_index=True)

base = (uploaded.name.rsplit(".", 1)[0]) or "data"
st.download_button(
    "Download cleaned CSV",
    data=out.to_csv(index=False).encode("utf-8"),
    file_name=f"{base}_cleaned.csv",
    mime="text/csv",
    type="primary",
)
