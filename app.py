import streamlit as st
import pandas as pd
import re

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTjdju-TasHTpDjxdIRqNpQ1AyiVQF7j0XVFbDBIe-8dDB5HiW_DD87QoR9y1h7CvD_lq452CJVXr9/pub?gid=1299182262&single=true&output=csv"

st.set_page_config(page_title="Cost Estimator", layout="centered")
st.title("Calcolatore costo unitario (pesato)")

@st.cache_data(ttl=60)
def load_db(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]

    # Colonne attese (come nel tuo sheet)
    required = {"Item", "Quantità", "Costo_unitario"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Mancano colonne nel Database: {missing}")

    df["Item"] = df["Item"].astype(str).str.strip()

    # Quantità -> numero
    df["Quantità"] = pd.to_numeric(df["Quantità"], errors="coerce")

    # Costo_unitario: pulizia "1,80 €" -> 1.80
    def parse_euro(x):
        if pd.isna(x):
            return None
        s = str(x).strip()
        s = s.replace("€", "").replace(" ", "")
        s = s.replace(".", "")           # se mai ci fossero separatori migliaia
        s = s.replace(",", ".")          # virgola decimale -> punto
        s = re.sub(r"[^0-9.]", "", s)    # lascia solo cifre e punto
        try:
            return float(s) if s != "" else None
        except:
            return None

    df["Costo_unitario"] = df["Costo_unitario"].apply(parse_euro)

    # Togli righe incomplete
    df = df.dropna(subset=["Item", "Quantità", "Costo_unitario"])

    # Scaglione calcolato internamente (ignoro la tua colonna Scaglione)
    df["Scaglione_calc"] = df["Quantità"].apply(lambda x: "1-300" if x <= 300 else "300+")
    return df

df = load_db(CSV_URL)

items = sorted(df["Item"].unique().tolist())
item = st.selectbox("Item", items)
qty = st.number_input("Quantità richiesta", min_value=1, step=1)

bucket = "1-300" if qty <= 300 else "300+"
filtered = df[(df["Item"] == item) & (df["Scaglione_calc"] == bucket)]

st.caption(f"Scaglione usato: {bucket}")

if st.button("Calcola"):
    if filtered.empty:
        st.warning("Nessun dato storico per questo item/scaglione.")
    else:
        weighted_avg = (filtered["Costo_unitario"] * filtered["Quantità"]).sum() / filtered["Quantità"].sum()
        st.success(f"Costo unitario medio (pesato): € {weighted_avg:.4f}")
        st.write(f"Record usati: {len(filtered)}")
