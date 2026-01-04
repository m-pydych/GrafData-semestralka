import streamlit as st
import pandas as pd

st.title("GPU Semantic Comparator")

gpu_name = st.text_input("Jaká grafická karta vás zajímá?", "RTX 4090")

if gpu_name:
    st.write(f"Hledám informace o: {gpu_name}")
    data = {
        "Parametr": ["VRAM", "Výrobce", "TDP"],
        "Hodnota": ["24 GB", "NVIDIA", "450W"]
    }
    df = pd.DataFrame(data)
    st.table(df)



