import streamlit as st
import pandas as pd
import re

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTjdju-TasHTpDjxdIRqNpQ1AyiVQF7j0XVFbDBIe-8dDB5HiW_DD87QoR9y1h7CvD_lq452CJVXr9/pub?gid=1299182262&single=true&output=csv"

# -----------------------
# Page setup
# -----------------------
st.set_page_config(
    page_title="The Next Event | Cost Estimator",
    layout="centered",
)

# -----------------------
# Brand styling (Jost + CSS)
# -----------------------
css = """
<link href="https://fonts.googleapis.com/css2?family=Jost:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'Jost', sans-serif; }
body { background-color: #f5f5f5; }

.logo-container { text-align: center; margin-bottom: 26px; }
.main-title { font-size: 38px; font-weight: 600; text-align: center; margin: 0 0 6px 0; letter-spacing: -0.5px; }
.subtitle { text-align: center; color: #6c757d; margin: 0 0 34px 0; }

.result-box { background-color: #ea3b33; padding: 28px; border-radius: 14px; text-align: center; margin-top: 22px; }
.result-text { color: #ffffff; font-size: 30px; font-weight: 700; letter-spacing: -0.3px; }
.result-meta { color: rgba(255,255,255,0.85); font-size: 14px; margin-top: 8px; }

.stButton > button { background-color: #ea3b33; color: #ffffff; border-radius: 10px; border: none; padding: 10px 22px; font-weight: 600; }
.stButton > button:hover { background-color: #c8322b; color: #ffffff; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# -----------------------
# Header (logo + title)
# -----------------------
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image("assets/logo.png", width=240)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="main-title">Cost Estimator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Calcolo automatico costo unitario medio pesato</div>', unsafe_allow_html=True)


# -----------------------
# Helpers
# -----------------------
def parse_euro(x):
    """
    Converts values like '1,80 €' or '1.234,50 €' into float (1.80 / 1234.50).
    """
    if pd.isna(x):
        return None
    s = str(x).strip()
    s = s.replace("€", "").replace(" ", "")
    s = s.replace(".", "")          # remove thousands separators if present
    s = s.replace(",", ".")         # decimal comma -> dot
    s = re.sub(r"[^0-9.]", "", s)   # keep digits + dot only
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

    # Keep only valid rows
    df = df.dropna(subset=["Item", "Quantità", "Costo_unitario"])

    # Bucket computed internally
    df["Scaglione_calc"] = df["Quantità"].apply(lambda q: "1-300" if q <= 300 else "300+")
    return df


# -----------------------
# Load data
# -----------------------
try:
    df = load_db(CSV_URL)
except Exception as e:
    st.error(f"Errore lettura database: {e}")
    st.stop()

items = sorted(df["Item"].unique().tolist())

# -----------------------
# UI inputs
# -----------------------
item = st.selectbox("Item", items)
qty = st.number_input("Quantità richiesta", min_value=1, step=1)

bucket = "1-300" if qty <= 300 else "300+"
filtered = df[(df["Item"] == item) & (df["Scaglione_calc"] == bucket)]

# -----------------------
# Action
# -----------------------
if st.button("Calcola"):
    if filtered.empty:
        st.warning("Nessun dato storico disponibile per questo item/scaglione.")
    else:
        weighted_avg = (filtered["Costo_unitario"] * filtered["Quantità"]).sum() / filtered["Quantità"].sum()

        st.markdown(
            f"""
            <div class="result-box">
              <div class="result-text">€ {weighted_avg:.4f}</div>
              <div class="result-meta">Scaglione: {bucket} · Record: {len(filtered)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
