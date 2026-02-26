import streamlit as st
import pandas as pd
import re

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTjdju-TasHTpDjxdIRqNpQ1AyiVQF7j0XVFbDBIe-8dDB5HiW_DD87QoR9y1h7CvD_lq452CJVXr9/pub?gid=1299182262&single=true&output=csv"

st.set_page_config(page_title="The Next Event | Cost Estimator", layout="centered")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Jost:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'Jost', sans-serif; }
body { background-color: #f5f5f5; }

.logo-container { text-align: center; margin-bottom: 40px; }
.main-title { font-size: 36px; font-weight: 600; text-align: center; margin-bottom: 10px; }
.subtitle { text-align: center; color: #6c757d; margin-bottom: 40px; }

.result-box { background-color: #ea3b33; padding: 30px; border-radius: 14px; text-align: center; margin-top: 30px; }
.result-text { color: white; font-size: 30px; font-weight: 600; }

.stButton > button { background-color: #ea3b33; color: white; border-radius: 10px; border: none; padding: 10px 25px; font-weight: 600; }
.stButton > button:hover { background-color: #c8322b; color: white; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image("assets/logo.png", width=230)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">Cost Estimator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Calcolo automatico costo unitario medio pesato</div>', unsafe_allow_html=True)

def parse_euro(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    s = s.replace("€", "").replace(" ", "")
    s = s.replace(".", "")          # separatore migliaia
    s = s.replace(",", ".")         # decimali
    s = re.sub(r"[^0-9.]", "", s)   # lascia solo numeri e punto
    try:
        return float(s) if s else None
    except:
        return None

@st.cache_data(ttl=60)
def load_db(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]

    required = {"Item", "Quantità", "Costo_unitario"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Mancano colonne nel Database: {missing}")

    df["Item"] = df["Item"].astype(str).str.strip()
    df["Quantità"] = pd.to_numeric(df["Quantità"], errors="coerce")
    df["Costo_unitario"] = df["Costo_unitario"].apply(parse_euro)

    df = df.dropna(subset=["Item", "Quantità", "Costo_unitario"])
    df["Scaglione_calc"] = df["Quantità"].apply(lambda q: "1-300" if q <= 300 else "300+")
    return df

try:
    df = load_db(CSV_URL)
except Exception as e:
    st.error(f"Errore lettura database: {e}")
    st.stop()

items = sorted(df["Item"].unique().tolist())
item = st.selectbox("Item", items)
qty = st.number_input("Quantità richiesta", min_value=1, step=1)

bucket = "1-300" if qty <= 300 else "300+"
filtered = df[(df["Item"] == item) & (df["Scaglione_calc"] == bucket)]

if st.button("Calcola"):
    if filtered.empty:
        st.warning("Nessun dato storico disponibile per questo item/scaglione.")
    else:
        weighted_avg = (filtered["Costo_unitario"] * filtered["Quantità"]).sum() / filtered["Quantità"].sum()
        st.markdown(
            f'<div class="result-box"><div class="result-text">€ {weighted_avg:.4f}</div></div>',
            unsafe_allow_html=True
        )
