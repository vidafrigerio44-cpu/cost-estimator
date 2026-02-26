import streamlit as st
import pandas as pd
import re

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTjdju-TasHTpDjxdIRqNpQ1AyiVQF7j0XVFbDBIe-8dDB5HiW_DD87QoR9y1h7CvD_lq452CJVXr9/pub?gid=1299182262&single=true&output=csv"

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="The Next Event | Cost Estimator",
    page_icon="assets/favicon.png",
    layout="centered",
)

# ------------------------------------------------
# LOAD JOST FONT (robust method)
# ------------------------------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Jost:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"]  {
    font-family: 'Jost', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# CENTERED LOGO (Streamlit layout, not CSS)
# ------------------------------------------------
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("assets/logo.png", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------
# TITLES
# ------------------------------------------------
st.markdown(
    "<h1 style='text-align:center;'>Cost Estimator</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center; color:#6c757d;'>Calcolo automatico costo unitario medio pesato</p>",
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------
# HELPERS
# ------------------------------------------------
def parse_euro(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    s = s.replace("€", "").replace(" ", "")
    s = s.replace(".", "")
    s = s.replace(",", ".")
    s = re.sub(r"[^0-9.]", "", s)
    try:
        return float(s) if s else None
    except:
        return None

@st.cache_data(ttl=60)
def load_db(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]

    df["Item"] = df["Item"].astype(str).str.strip()
    df["Quantità"] = pd.to_numeric(df["Quantità"], errors="coerce")
    df["Costo_unitario"] = df["Costo_unitario"].apply(parse_euro)

    df = df.dropna(subset=["Item", "Quantità", "Costo_unitario"])
    df["Scaglione_calc"] = df["Quantità"].apply(lambda q: "1-300" if q <= 300 else "300+")
    return df

df = load_db(CSV_URL)

# ------------------------------------------------
# INPUTS
# ------------------------------------------------
items = sorted(df["Item"].unique().tolist())

item = st.selectbox("Item", items)
qty = st.number_input("Quantità richiesta", min_value=1, step=1)

bucket = "1-300" if qty <= 300 else "300+"
filtered = df[(df["Item"] == item) & (df["Scaglione_calc"] == bucket)]

# ------------------------------------------------
# CALCULATION
# ------------------------------------------------
if st.button("Calcola"):
    if filtered.empty:
        st.warning("Nessun dato storico disponibile.")
    else:
        weighted_avg = (
            (filtered["Costo_unitario"] * filtered["Quantità"]).sum()
            / filtered["Quantità"].sum()
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div style="
                background-color:#ea3b33;
                padding:28px;
                border-radius:14px;
                text-align:center;
                color:white;">
                <div style="font-size:30px; font-weight:600;">
                    € {weighted_avg:.2f}
                </div>
                <div style="font-size:14px; opacity:0.85; margin-top:6px;">
                    Scaglione: {bucket} · Record: {len(filtered)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
