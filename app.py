import streamlit as st
import pandas as pd
from rdflib import Graph, Namespace, URIRef, RDFS
from streamlit_agraph import agraph, Node, Edge, Config
import os

# 1. NASTAVENÍ
EX = Namespace("http://example.org/gpu/")
SCHEMA = Namespace("https://schema.org/")

st.set_page_config(layout="wide", page_title="GPU Knowledge Explorer")

@st.cache_resource
def load_gpu_graph():
    g = Graph()
    g.bind("ex", EX)
    g.bind("schema", SCHEMA)
    g.bind("rdfs", RDFS)
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Uprav cestu k data/gpu_data.ttl pokud je potřeba
    ttl_path = os.path.join(base_path, "data", "gpu_data.ttl")
    try:
        g.parse(ttl_path, format="turtle")
    except Exception as e:
        st.error(f"Chyba při načítání dat: {e}")
    return g

g = load_gpu_graph()

def get_label(uri):
    query = f"SELECT ?label WHERE {{ <{uri}> (rdfs:label|schema:name) ?label . }} LIMIT 1"
    res = list(g.query(query))
    return str(res[0][0]) if res else str(uri).split("/")[-1]

def short_id(uri):
    return str(uri).replace(str(EX), "ex:").replace(str(SCHEMA), "schema:")

if 'current_uri' not in st.session_state:
    st.session_state.current_uri = str(EX.NVIDIA)

# --- SIDEBAR ---
st.sidebar.header("🔍 Vyhledávání")
search_query = st.sidebar.text_input("Najít uzel:")
if search_query:
    q_search = f"""SELECT ?node ?name WHERE {{ ?node (schema:name|rdfs:label) ?name . 
    FILTER (CONTAINS(LCASE(?name), LCASE("{search_query}"))) }} LIMIT 10"""
    for r in g.query(q_search):
        if st.sidebar.button(f"👉 {r.name}", key=f"s_{r.node}"):
            st.session_state.current_uri = str(r.node)
            st.rerun()

# --- DATA PREPARATION ---
curr = URIRef(st.session_state.current_uri)
curr_label = get_label(curr)

# Komplexní SPARQL pro získání všech možných metadat pro řazení
q_neigh = f"""
SELECT DISTINCT ?target ?name ?year ?vram ?tdp ?price ?cores ?bus ?perf WHERE {{
    ?target ?p <{curr}> .
    ?target (schema:name|rdfs:label) ?name .
    OPTIONAL {{ ?target ex:releaseYear ?year }}
    OPTIONAL {{ ?target ex:memorySizeKB ?vram }}
    OPTIONAL {{ ?target ex:tdpWatts ?tdp }}
    OPTIONAL {{ ?target schema:price ?price }}
    OPTIONAL {{ ?target ex:shadingUnits ?cores }}
    OPTIONAL {{ ?target ex:memoryBusBits ?bus }}
    OPTIONAL {{ ?target ex:fp32GFlops ?perf }}
    FILTER(isIRI(?target))
}}
"""

neighbor_list = []
for row in g.query(q_neigh):
    neighbor_list.append({
        "uri": str(row.target),
        "Název": str(row.name),
        "Rok": int(row.year) if row.year else 0,
        "VRAM": int(row.vram) if row.vram else 0,
        "TDP": int(row.tdp) if row.tdp else 0,
        "Cena": float(row.price) if row.price else 0.0,
        "Jádra": int(row.cores) if row.cores else 0,
        "Sběrnice": int(row.bus) if row.bus else 0,
        "Výkon": float(row.perf) if row.perf else 0.0
    })

df = pd.DataFrame(neighbor_list)

# --- UI LAYOUT ---
st.title(f"📍 {curr_label}")
col1, col2 = st.columns([1, 2])

with col1:
    with st.expander("📄 Detaily aktuálního uzlu"):
        for p, o in g.query(f"SELECT ?p ?o WHERE {{ <{curr}> ?p ?o . }}"):
            if isinstance(o, URIRef):
                if st.button(f"{short_id(p)} ⮕ {get_label(o)}", key=f"det_{o}"):
                    st.session_state.current_uri = str(o); st.rerun()
            else: st.write(f"**{short_id(p)}:** {o}")

    st.subheader("🔗 Související položky")
    
    if not df.empty:
        # Dynamické řazení
        sort_col = st.selectbox("Řadit podle:", [c for c in df.columns if c != "uri"])
        sort_dir = st.radio("Směr:", ["Vzestupně", "Sestupně"], horizontal=True)
        
        df = df.sort_values(by=sort_col, ascending=(sort_dir == "Vzestupně")).reset_index(drop=True)
        
        # Omezení pro zobrazení
        max_display = 30
        df_show = df.head(max_display)

        for i, row in df_show.iterrows():
            idx = i + 1
            # Zobrazení hodnoty podle které se řadí pro kontrolu
            val = row[sort_col]
            label = f"**{idx}.** {row['Název']}  \n`{sort_col}: {val}`"
            if st.button(label, key=f"list_{row['uri']}", use_container_width=True):
                st.session_state.current_uri = row['uri']; st.rerun()
        
        if len(df) > max_display:
            st.info(f"Zobrazeno {max_display} z {len(df)} (použijte řazení pro ostatní)")
    else:
        st.write("Žádné příchozí vazby.")

with col2:
    st.subheader("🕸️ Mapa (čísla odpovídají seznamu)")
    nodes = []
    edges = []
    
    # Centrální uzel - bez textu, jen barva
    nodes.append(Node(id=str(curr), label=" ", size=40, color="#FF4B4B", title=f"CENTRUM: {curr_label}"))
    
    # Sousedé - jen čísla
    if not df.empty:
        for i, row in df_show.iterrows():
            nodes.append(Node(
                id=row['uri'], 
                label=str(i+1), # Tady je to očíslování
                size=25, 
                color="#2196F3",
                title=row['Název'] # Jméno uvidíš po najetí myší
            ))
            edges.append(Edge(source=row['uri'], target=str(curr)))

    # Ostatní odchozí vztahy (např. značka/architektura) - zelené bez čísel
    for p, o in g.query(f"SELECT ?p ?o WHERE {{ <{curr}> ?p ?o . FILTER(isIRI(?o)) }}"):
        if str(o) not in [n.id for n in nodes]:
            nodes.append(Node(id=str(o), label=" ", size=20, color="#4CAF50", title=get_label(o)))
        edges.append(Edge(source=str(curr), target=str(o), label=short_id(p)))

    config = Config(width=800, height=750, directed=True, physics=True, hierarchical=False)
    clicked = agraph(nodes=nodes, edges=edges, config=config)
    
    if clicked and clicked != st.session_state.current_uri:
        st.session_state.current_uri = clicked
        st.rerun()