import streamlit as st
import pandas as pd
from rdflib import Graph, Namespace, URIRef, RDFS
from streamlit_agraph import agraph, Node, Edge, Config
import os

# 1. NASTAVENÍ NAMESPACŮ
EX = Namespace("http://example.org/gpu/")
SCHEMA = Namespace("https://schema.org/")

st.set_page_config(layout="wide", page_title="GPU Knowledge Explorer")

# 2. NAČTENÍ DAT
@st.cache_resource
def load_gpu_graph():
    g = Graph()
    g.bind("ex", EX)
    g.bind("schema", SCHEMA)
    g.bind("rdfs", RDFS)
    
    # Zjistíme, kde leží tento skript (app.py)
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # TADY JE TA OPRAVA: přidali jsme "data" do cesty
    ttl_path = os.path.join(base_path, "data", "gpu_data.ttl")
    
    try:
        g.parse(ttl_path, format="turtle")
    except Exception as e:
        st.error(f"Chyba při načítání dat: {e}")
        st.info(f"Hledal jsem na cestě: {ttl_path}")
        st.warning("Ujistěte se, že soubor gpu_data.ttl je v GitHubu ve složce 'data'.")
    return g

g = load_gpu_graph()

# 3. POMOCNÉ FUNKCE
def get_label(uri):
    """Získá rdfs:label nebo schema:name, jinak vrátí zkrácené ID."""
    # Zkusíme najít label nebo jméno
    query = f"""
    SELECT ?label WHERE {{
        <{uri}> (rdfs:label|schema:name) ?label .
    }} LIMIT 1
    """
    res = list(g.query(query))
    if res:
        return str(res[0][0])
    return str(uri).replace(str(EX), "").replace(str(SCHEMA), "")

def short_id(uri):
    return str(uri).replace(str(EX), "ex:").replace(str(SCHEMA), "schema:")

# --- SESSION STATE ---
if 'current_uri' not in st.session_state:
    st.session_state.current_uri = str(EX.NVIDIA)

# --- SIDEBAR: VYHLEDÁVÁNÍ ---
st.sidebar.header("🔍 Vyhledávání")
search_query = st.sidebar.text_input("Najít uzel (GPU, Značka, Arch...):")

if search_query:
    q_search = f"""
    SELECT ?node ?name WHERE {{
        ?node (schema:name|rdfs:label) ?name .
        FILTER (CONTAINS(LCASE(?name), LCASE("{search_query}")))
    }} LIMIT 8
    """
    res = g.query(q_search)
    for r in res:
        if st.sidebar.button(f"👉 {r.name}", key=f"search_{r.node}"):
            st.session_state.current_uri = str(r.node)
            st.rerun()

# --- HLAVNÍ PLOCHA ---
curr = URIRef(st.session_state.current_uri)
node_label = get_label(curr)

st.title(f"📍 {node_label}")
st.caption(f"URI: {short_id(curr)}")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📄 Seznam a filtrace")
    
    # --- NASTAVENÍ FILTRŮ A ŘAZENÍ ---
    sort_by = st.selectbox("Řadit podle:", ["Názvu", "Roku vydání", "Velikosti VRAM"])
    sort_order = st.radio("Pořadí:", ["Vzestupně", "Sestupně"], horizontal=True)
    
    # --- SPARQL: Získání sousedů s metadaty ---
    # Tento dotaz najde vše, co odkazuje na aktuální uzel, a vytáhne k tomu detaily
    q_neighbors_full = f"""
    SELECT DISTINCT ?target ?name ?year ?vram WHERE {{
        ?target ?p <{curr}> .
        ?target (schema:name|rdfs:label) ?name .
        OPTIONAL {{ ?target ex:releaseYear ?year }}
        OPTIONAL {{ ?target ex:memorySizeKB ?vram }}
        FILTER(isIRI(?target))
    }}
    """
    
    neighbor_data = []
    for row in g.query(q_neighbors_full):
        neighbor_data.append({
            "uri": str(row.target),
            "Názvu": str(row.name),
            "Roku vydání": int(row.year) if row.year else 0,
            "Velikosti VRAM": int(row.vram) if row.vram else 0
        })
    
    df_neighbors = pd.DataFrame(neighbor_data)

    if not df_neighbors.empty:
        # --- LOGIKA ŘAZENÍ ---
        ascending = (sort_order == "Vzestupně")
        df_neighbors = df_neighbors.sort_values(by=sort_by, ascending=ascending).reset_index(drop=True)
        
        # Omezení počtu zobrazených prvků v mapě (např. top 30), aby nezkolabovala
        max_nodes = 30
        df_visible = df_neighbors.head(max_nodes)
        
        # --- VÝPIS OČÍSLOVANÉHO SEZNAMU ---
        for i, row in df_visible.iterrows():
            idx = i + 1
            label = f"{idx}. {row['Názvu']}"
            meta = f"({row['Roku vydání']}, {row['Velikosti VRAM'] // 1024} MB)" if row['Roku vydání'] > 0 else ""
            
            if st.button(f"{label} {meta}", key=f"list_{row['uri']}"):
                st.session_state.current_uri = row['uri']
                st.rerun()
        
        if len(df_neighbors) > max_nodes:
            st.info(f"Zobrazeno prvních {max_nodes} z {len(df_neighbors)} výsledků.")
    else:
        st.write("Žádné příchozí vazby pro tento uzel.")

with col2:
    st.subheader("🕸️ Mapa (číslo odpovídá seznamu vlevo)")
    
    nodes = []
    edges = []
    
    # Centrální uzel (stále s textem, aby bylo jasné, kde jsme)
    nodes.append(Node(id=str(curr), label=node_label, size=35, color="#FF4B4B"))
    
    if not df_neighbors.empty:
        for i, row in df_visible.iterrows():
            idx = i + 1
            # TADY JE TA ZMĚNA: label je jen číslo
            nodes.append(Node(
                id=row['uri'], 
                label=str(idx), 
                size=20, 
                color="#2196F3", # Modrá pro sousedy
                title=row['Názvu'] # Tooltip po najetí myší
            ))
            edges.append(Edge(source=row['uri'], target=str(curr), label=""))

    config = Config(width=800, height=650, directed=True, nodeHighlightBehavior=True, physics=True)
    clicked = agraph(nodes=nodes, edges=edges, config=config)
    
    if clicked and clicked != st.session_state.current_uri:
        st.session_state.current_uri = clicked
        st.rerun()