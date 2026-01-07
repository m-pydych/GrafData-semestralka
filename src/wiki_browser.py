import streamlit as st
import pandas as pd
from rdflib import URIRef

def show_wiki(g, EX, SCHEMA):
    st.subheader("📖 GPU Encyclopedia")
    
    # 1. Výběr architektury pro začátek
    q_archs = """
    SELECT DISTINCT ?arch ?name WHERE {
        ?arch a <http://example.org/gpu/GPUArchitecture> ;
              <https://schema.org/name> ?name .
    } ORDER BY ?name
    """
    arch_options = {str(r.name): str(r.arch) for r in g.query(q_archs)}
    
    selected_arch_name = st.selectbox("Vyberte architekturu pro analýzu:", list(arch_options.keys()))
    selected_arch_uri = arch_options[selected_arch_name]

    # 2. Načtení dat o kartách v dané architektuře
    q_cards = f"""
    SELECT ?gpu ?name ?year ?perf WHERE {{
        ?gpu <http://example.org/gpu/hasArchitecture> <{selected_arch_uri}> ;
             <https://schema.org/name> ?name .
        OPTIONAL {{ ?gpu <http://example.org/gpu/releaseYear> ?year }}
        OPTIONAL {{ ?gpu <http://example.org/gpu/fp32GFlops> ?perf }}
    }}
    """
    
    data = []
    for r in g.query(q_cards):
        data.append({
            "uri": str(r.gpu),
            "Název": str(r.name),
            "Rok": int(r.year) if r.year else 0,
            "Výkon (GFLOPS)": float(r.perf) if r.perf else 0.0
        })
    
    df = pd.DataFrame(data)

    if not df.empty:
        # --- STATISTICKÉ HŘIŠTĚ (Decily) ---
        st.info(f"Analyzuji {len(df)} karet v architektuře {selected_arch_name}")
        
        # Filtrujeme jen ty, co mají výkon (aby decily nelhaly)
        perf_df = df[df["Výkon (GFLOPS)"] > 0].sort_values("Výkon (GFLOPS)")
        
        if len(perf_df) >= 3:
            st.write("### 📊 Statistické zajímavosti výkonu")
            cols = st.columns(3)
            
            # Výpočet decilů
            d10 = perf_df.iloc[0] # 10. decil (nejslabší)
            d5 = perf_df.iloc[len(perf_df)//2] # Medián
            d1 = perf_df.iloc[-1] # 1. decil (nejsilnější)
            
            cols[0].metric("Nejsilnější (1. decil)", f"{d1['Výkon (GFLOPS)']} GFLOPS")
            cols[0].caption(d1['Název'])
            
            cols[1].metric("Střed (5. decil)", f"{d5['Výkon (GFLOPS)']} GFLOPS")
            cols[1].caption(d5['Název'])
            
            cols[2].metric("Nejslabší (10. decil)", f"{d10['Výkon (GFLOPS)']} GFLOPS")
            cols[2].caption(d10['Název'])
        else:
            st.warning("Málo dat o výkonu pro výpočet decilů.")

        # --- TABULKA VŠECH KARET ---
        st.write("### 🗃️ Všechny karty v této architektuře")
        st.dataframe(df.drop(columns=["uri"]), use_container_width=True)
    else:
        st.write("Pro tuto architekturu nebyly nalezeny žádné karty.")