import streamlit as st
import pandas as pd
from rdflib import Graph, Namespace

EX = Namespace("http://example.org/gpu/")
SCHEMA = Namespace("https://schema.org/")

st.title("GPU Semantic Comparator 🖥️")

@st.cache_resource
def load_gpu_graph():
    g = Graph()
    g.parse("data/gpu_data.ttl", format="turtle")
    return g

g = load_gpu_graph()


gpu_search = st.text_input("Zadejte název grafické karty:", "GeForce RTX 4090")

if gpu_search:
    query = f"""
    PREFIX schema: <https://schema.org/>
    PREFIX ex: <http://example.org/gpu/>

    SELECT ?name ?brandName ?tdp ?vram ?archName
    WHERE {{
        ?gpu a schema:Product ;
             schema:name ?name ;
             schema:manufacturer ?brand .
        
        ?brand schema:name ?brandName .
        
        OPTIONAL {{ ?gpu ex:tdpWatts ?tdp }}
        OPTIONAL {{ ?gpu ex:memorySizeKB ?vram }}
        OPTIONAL {{ 
            ?gpu ex:hasArchitecture ?arch .
            ?arch schema:name ?archName .
        }}

        FILTER (CONTAINS(LCASE(?name), LCASE("{gpu_search}")))
    }}
    LIMIT 5
    """

    results = g.query(query)

    if len(results) > 0:
        st.write(f"Nalezené výsledky pro: **{gpu_search}**")
        
        output_data = []
        for row in results:
            output_data.append({
                "Model": str(row.name),
                "Výrobce": str(row.brandName),
                "Architektura": str(row.archName) if row.archName else "Neznámo",
                "TDP (W)": str(row.tdp) if row.tdp else "-",
                "VRAM (MB)": int(row.vram) // 1024 if row.vram else "-"
            })
        
        st.table(pd.DataFrame(output_data))
    else:
        st.warning("Žádná taková karta nebyla v grafu nalezena.")