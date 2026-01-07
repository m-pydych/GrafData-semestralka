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
    
    # 1. Zjistíme, kde leží tento skript (app.py)
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Sestavíme cestu k souboru (předpokládám, že je ve stejné složce jako app.py)
    # Pokud ho máš ve složce 'data', změň to na os.path.join(base_path, "data", "gpu_data.ttl")
    ttl_path = os.path.join(base_path, "gpu_data.ttl")
    
    try:
        g.parse(ttl_path, format="turtle")
        # st.success(f"Data úspěšně načtena z: {ttl_path}") # Volitelné pro kontrolu
    except Exception as e:
        st.error(f"Chyba při načítání dat: {e}")
        st.info(f"Hledal jsem na cestě: {ttl_path}")
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
    # --- ODCHOZÍ VAZBY (Vlastnosti objektu) ---
    st.subheader("📄 Vlastnosti")
    q_out = f"SELECT ?p ?o WHERE {{ <{curr}> ?p ?o . }}"
    for p, o in g.query(q_out):
        p_label = short_id(p)
        if isinstance(o, URIRef):
            o_label = get_label(o)
            if st.button(f"{p_label} ⮕ {o_label}", key=f"out_{o}_{p}"):
                st.session_state.current_uri = str(o)
                st.rerun()
        else:
            st.write(f"**{p_label}:** {o}")

    # --- PŘÍCHOZÍ VAZBY (Kdo na toto odkazuje) ---
    # Tohle je klíčové pro tvé nové uzly (např. kdo všechno má 8GB)
    st.divider()
    st.subheader("🔗 Odkazováno z")
    q_in = f"SELECT ?s ?p WHERE {{ ?s ?p <{curr}> . FILTER(isIRI(?s)) }}"
    in_results = list(g.query(q_in))
    
    if in_results:
        for s, p in in_results[:15]: # Limit abychom nezahltili UI
            s_label = get_label(s)
            p_label = short_id(p)
            if st.button(f"{s_label} (přes {p_label})", key=f"in_{s}_{p}"):
                st.session_state.current_uri = str(s)
                st.rerun()
        if len(in_results) > 15:
            st.info(f"A dalších {len(in_results)-15} uzlů...")
    else:
        st.write("Žádné příchozí vazby.")

with col2:
    st.subheader("🕸️ Mapa sousedů")
    
    nodes = []
    edges = []
    
    # Centrální uzel
    nodes.append(Node(id=str(curr), label=node_label, size=35, color="#FF4B4B"))
    
    # Najdeme okolí (ven i dovnitř)
    q_graph = f"""
    SELECT ?s ?p ?o WHERE {{
        {{ <{curr}> ?p ?o . FILTER(isIRI(?o)) BIND(<{curr}> AS ?s) }}
        UNION
        {{ ?s ?p <{curr}> . FILTER(isIRI(?s)) BIND(<{curr}> AS ?o) }}
    }} LIMIT 30
    """
    
    seen_nodes = {str(curr)}
    for s, p, o in g.query(q_graph):
        s_str, o_str = str(s), str(o)
        
        # Přidání uzlů, pokud ještě nejsou v seznamu
        for uri, label in [(s, get_label(s)), (o, get_label(o))]:
            if str(uri) not in seen_nodes:
                nodes.append(Node(id=str(uri), label=label, size=20))
                seen_nodes.add(str(uri))
        
        # Přidání hrany
        edges.append(Edge(source=s_str, target=o_str, label=short_id(p)))

    config = Config(width=800, height=650, directed=True, nodeHighlightBehavior=True, physics=True)
    clicked = agraph(nodes=nodes, edges=edges, config=config)
    
    if clicked and clicked != st.session_state.current_uri:
        st.session_state.current_uri = clicked
        st.rerun()