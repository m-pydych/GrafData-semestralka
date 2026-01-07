import streamlit as st
import pandas as pd

def show_console(g):
    st.subheader("💻 SPARQL Endpoint (Simulation)")
    st.write("Zde můžete simulovat dotazy, které by na tento hub posílaly jiné LD služby.")

    # Předdefinované šablony
    templates = {
        "Všechny GPU značky NVIDIA": "SELECT ?gpu ?name WHERE {\n  ?gpu <https://schema.org/manufacturer> <http://example.org/gpu/NVIDIA> ;\n       <https://schema.org/name> ?name .\n} LIMIT 10",
        "Karty s nejvyšším TDP": "SELECT ?name ?tdp WHERE {\n  ?gpu <http://example.org/gpu/tdpWatts> ?tdp ;\n       <https://schema.org/name> ?name .\n} ORDER BY DESC(?tdp) LIMIT 10",
        "Počet karet podle roku": "SELECT ?year (COUNT(?gpu) AS ?count) WHERE {\n  ?gpu <http://example.org/gpu/releaseYear> ?year .\n} GROUP BY ?year ORDER BY ?year"
    }

    selected_template = st.selectbox("Vyberte ukázkový dotaz:", list(templates.keys()))
    
    # Text area pro dotaz
    query_input = st.text_area("SPARQL dotaz:", templates[selected_template], height=200)

    if st.button("Spustit dotaz ⚡"):
        try:
            results = g.query(query_input)
            
            # Převod výsledků do tabulky
            res_list = []
            for row in results:
                res_list.append(row.asdict())
            
            if res_list:
                df_res = pd.DataFrame(res_list)
                st.success(f"Nalezeno {len(df_res)} výsledků.")
                st.dataframe(df_res, use_container_width=True)
                
                # Sémantický export
                st.download_button(
                    "Stáhnout výsledky jako JSON",
                    df_res.to_json(orient="records"),
                    "results.json",
                    "application/json"
                )
            else:
                st.info("Dotaz nevrátil žádné výsledky.")
        except Exception as e:
            st.error(f"Chyba v dotazu: {e}")