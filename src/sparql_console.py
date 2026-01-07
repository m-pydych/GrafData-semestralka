import streamlit as st
import pandas as pd

def show_console(g):
    st.subheader("SPARQL Endpoint")
    st.write("manually run SPARQL queries against the database.")

    # Předdefinované šablony
    templates = {
        "All GPUs made by NVIDIA": "SELECT ?gpu ?name WHERE {\n  ?gpu <https://schema.org/manufacturer> <http://example.org/gpu/NVIDIA> ;\n       <https://schema.org/name> ?name .\n} LIMIT 10",
        "Top 10 GPUs by TDP": "SELECT ?name ?tdp WHERE {\n  ?gpu <http://example.org/gpu/tdpWatts> ?tdp ;\n       <https://schema.org/name> ?name .\n} ORDER BY DESC(?tdp) LIMIT 10",
        "Count of GPUs by year": "SELECT ?year (COUNT(?gpu) AS ?count) WHERE {\n  ?gpu <http://example.org/gpu/releaseYear> ?year .\n} GROUP BY ?year ORDER BY ?year",


    }

    selected_template = st.selectbox("sample query:", list(templates.keys()))
    
    # Text area pro dotaz
    query_input = st.text_area("SPARQL query:", templates[selected_template], height=200)

    if st.button("Run Query"):
        try:
            results = g.query(query_input)
            
            # Převod výsledků do tabulky
            res_list = []
            for row in results:
                res_list.append({str(k): (v.toPython() if hasattr(v, 'toPython') else str(v)) for k, v in row.asdict().items()})
            
            if res_list:
                df_res = pd.DataFrame(res_list)
                st.success(f"{len(df_res)} results returned.")
                st.dataframe(df_res, use_container_width=True)
                
                # Sémantický export
                st.download_button(
                    "dowload results as JSON",
                    df_res.to_json(orient="records"),
                    "results.json",
                    "application/json"
                )
            else:
                st.info("No results returned.")
        except Exception as e:
            st.error(f"Error in query: {e}")