import streamlit as st
import pandas as pd

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTjdju-TasHTpDjxdIRqNpQ1AyiVQF7j0XVFbDBIe-8dDB5HiW_DD87QoR9y1h7CvD_lq452CJVXr9/pub?gid=1299182262&single=true&output=csv"

st.set_page_config(page_title="Cost Estimator", layout="centered")
st.title("Calcolatore costo unitario (pesato)")

@st.cache_data(ttl=60)
def load_db(url):
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]

    df["Item"] = df["Item"].astype(str).str.strip()
    df["Quantità"] = pd.to_numeric(df["Quantità"], errors="coerce")
    df["Costo_unitario"] = pd.to_numeric(df["Costo_unitario"], errors="coerce")
    df = df.dropna(subset=["Item", "Quantità", "Costo_unitario"])

    df["Scaglione"] = df["Quantità"].apply(lambda x: "1-300" if x <= 300 else "300+")
    return df

df = load_db(CSV_URL)

items = sorted(df["Item"].unique().tolist())
item = st.selectbox("Item", items)
qty = st.number_input("Quantità richiesta", min_value=1, step=1)

bucket = "1-300" if qty <= 300 else "300+"
filtered = df[(df["Item"] == item) & (df["Scaglione"] == bucket)]

st.caption(f"Scaglione usato: {bucket}")

if st.button("Calcola"):
    if filtered.empty:
        st.warning("Nessun dato storico per questo item/scaglione.")
    else:
        weighted_avg = (filtered["Costo_unitario"] * filtered["Quantità"]).sum() / filtered["Quantità"].sum()
        st.success(f"Costo unitario medio (pesato): € {weighted_avg:.4f}")
        st.write(f"Record usati: {len(filtered)}")
