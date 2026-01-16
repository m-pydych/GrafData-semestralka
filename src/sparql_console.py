import json
import streamlit as st
import pandas as pd

def show_console(g):
    st.subheader("SPARQL Endpoint")
    st.write("manually run SPARQL queries against the database.")

    # Predefined query templates
    templates = {
        "All GPUs made by NVIDIA": "SELECT ?gpu ?name WHERE {\n  ?gpu <https://schema.org/manufacturer> <http://example.org/gpu/NVIDIA> ;\n       <https://schema.org/name> ?name .\n} LIMIT 10",
        "Top 10 GPUs by TDP": "SELECT ?name ?tdp WHERE {\n  ?gpu <http://example.org/gpu/tdpWatts> ?tdp ;\n       <https://schema.org/name> ?name .\n} ORDER BY DESC(?tdp) LIMIT 10",
        "Count of GPUs by year": "SELECT ?year (COUNT(?gpu) AS ?count) WHERE {\n  ?gpu <http://example.org/gpu/releaseYear> ?year .\n} GROUP BY ?year ORDER BY ?year",


    }

    selected_template = st.selectbox("sample query:", list(templates.keys()))
    
    query_input = st.text_area("SPARQL query:", templates[selected_template], height=200)

    if st.button("Run Query"):
        try:
            results = g.query(query_input)
            
            res_list = []
            for row in results:
                res_list.append({str(k): (v.toPython() if hasattr(v, 'toPython') else str(v)) for k, v in row.asdict().items()})
                
            if res_list:
                df_res = pd.DataFrame(res_list)
                
                st.success(f"Query successful! Found {len(df_res)} results.")
                st.dataframe(df_res, use_container_width=True)

                json_ld_data = {
                    "@context": {
                        "name": "https://schema.org/name",
                        "manufacturer": "https://schema.org/manufacturer",
                        "tdp": "http://example.org/gpu/tdpWatts",
                        "year": "http://example.org/gpu/releaseYear",
                        "gpu": "@id"
                    },
                    "@graph": res_list
                }

                st.download_button(
                    "Download results as JSON-LD",
                    json.dumps(json_ld_data, indent=2),
                    "results.jsonld",
                    "application/ld+json"
                )
            else:
                st.info("No results returned.")
        except Exception as e:
            st.error(f"Error in query: {e}")