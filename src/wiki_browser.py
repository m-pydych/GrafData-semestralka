import streamlit as st
import pandas as pd
from rdflib import URIRef

def show_wiki(g, EX, SCHEMA):
    st.subheader("GPU Encyclopedia")
    
    # 1. architecture selection
    q_archs = """
    SELECT DISTINCT ?arch ?name WHERE {
        ?arch a <http://example.org/gpu/GPUArchitecture> ;
              <https://schema.org/name> ?name 
    } ORDER BY ?name
    """
    arch_options = {str(r.name): str(r.arch) for r in g.query(q_archs)}
    
    selected_arch_name = st.selectbox("Vyberte architekturu pro analýzu:", list(arch_options.keys()))
    selected_arch_uri = arch_options[selected_arch_name]

    # 2. load cards in selected architecture
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
            "Name": str(r.name),
            "Year": int(r.year) if r.year else None,
            "Performance (GFLOPS)": float(r.perf) if r.perf else None
        })
    
    df = pd.DataFrame(data)

    if not df.empty:
        st.info(f"Analyzing {len(df)} cards in architecture {selected_arch_name}")
        
        perf_df = df[df["Performance (GFLOPS)"] > 0].sort_values("Performance (GFLOPS)")
        
        if len(perf_df) >= 3:
            st.write("### Statistics")
            cols = st.columns(3)
            
            worst = perf_df.iloc[0] # worst
            Median = perf_df.iloc[len(perf_df)//2] # median
            best = perf_df.iloc[-1] # best

            cols[0].metric(worst['Name'])
            cols[0].caption("The best", f"{worst['Performance (GFLOPS)']} GFLOPS")
            
            cols[1].metric(Median['Name'])
            cols[1].caption("Middle", f"{Median['Performance (GFLOPS)']} GFLOPS")
            
            cols[2].metric(best['Name'])
            cols[2].caption("The worst", f"{best['Performance (GFLOPS)']} GFLOPS")
            
        else:
            st.warning("not enough data to show statistics.")

        # all cards
        st.write("### all cards in this architecture")
        st.dataframe(df.drop(columns=["uri"]), use_container_width=True)
    else:
        st.write("For this architecture, no cards were found.")