import streamlit as st
import pandas as pd
from rdflib import Graph, Namespace, URIRef
from streamlit_agraph import agraph, Node, Edge, Config

# 1. NASTAVENÍ NAMESPACŮ (musí odpovídat to_rdf.py)
EX = Namespace("http://example.org/gpu/")
SCHEMA = Namespace("https://schema.org/")

st.set_page_config(layout="wide", page_title="GPU Knowledge Explorer")

# 2. NAČTENÍ DAT (Cachování pro rychlost)
@st.cache_resource
def load_gpu_graph():
    g = Graph()
    # !!! ZDE ZKONTROLUJ CESTU K TVÉMU TTL SOUBORU !!!
    # Pokud ho máš v podsložce data, nechej to takto:
    try:
        g.parse("data/gpu_data.ttl", format="turtle")
    except:
        st.error("Soubor gpu_data.ttl nebyl nalezen. Zkontrolujte cestu v app.py.")
    return g

g = load_gpu_graph()

# 3. LOGIKA NAVIGACE (Session State)
# Pokud uživatel poprvé otevře web, začneme u NVIDIA (nebo jiné značky)
if 'current_uri' not in st.session_state:
    st.session_state.current_uri = str(EX.NVIDIA)

# Pomocná funkce pro zkrácení URI pro hezčí zobrazení
def short_id(uri):
    return str(uri).replace(str(EX), "ex:").replace(str(SCHEMA), "schema:")

# --- SIDEBAR: VYHLEDÁVÁNÍ ---
st.sidebar.header("🔍 Vyhledávání")
search_query = st.sidebar.text_input("Najít kartu podle názvu:")

if search_query:
    # SPARQL dotaz pro vyhledání URI podle jména
    q_search = f"""
    SELECT ?gpu ?name WHERE {{
        ?gpu schema:name ?name .
        FILTER (CONTAINS(LCASE(?name), LCASE("{search_query}")))
    }} LIMIT 5
    """
    res = g.query(q_search)
    for r in res:
        if st.sidebar.button(f"👉 {r.name}", key=str(r.gpu)):
            st.session_state.current_uri = str(r.gpu)
            st.rerun()

# --- HLAVNÍ PLOCHA ---
curr = URIRef(st.session_state.current_uri)
st.title(f"📍 Aktuální uzel: {short_id(curr)}")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📄 Detaily a vlastnosti")
    
    # SPARQL pro získání všech informací o aktuálním uzlu
    q_info = f"SELECT ?p ?o WHERE {{ <{curr}> ?p ?o . }}"
    info_res = g.query(q_info)
    
    for p, o in info_res:
        pred_label = short_id(p)
        if isinstance(o, URIRef):
            # Pokud je hodnota odkaz (URI), uděláme z ní klikací tlačítko
            obj_label = short_id(o)
            if st.button(f"{pred_label} ➡️ {obj_label}", key=f"btn_{o}"):
                st.session_state.current_uri = str(o)
                st.rerun()
        else:
            # Pokud je to text/číslo, jen ho vypíšeme
            st.write(f"**{pred_label}:** {o}")

with col2:
    st.subheader("🕸️ Mapa znalostí (klikni pro navigaci)")
    
    nodes = []
    edges = []
    
    # Přidáme centrální uzel (ten je červený)
    nodes.append(Node(id=str(curr), label=short_id(curr), size=30, color="#FF4B4B"))
    
    # Najdeme sousedy (vše co z uzlu vede nebo do něj vede)
    q_neighbors = f"""
    SELECT ?p ?target WHERE {{
        {{ <{curr}> ?p ?target . FILTER(isIRI(?target)) }}
        UNION
        {{ ?target ?p <{curr}> . FILTER(isIRI(?target)) }}
    }} LIMIT 20
    """
    
    for p, target in g.query(q_neighbors):
        nodes.append(Node(id=str(target), label=short_id(target), size=20))
        # Směr šipky závisí na tom, kdo je subjekt
        edges.append(Edge(source=str(curr), target=str(target), label=short_id(p)))

    # Konfigurace vzhledu grafu
    config = Config(width=800, height=600, directed=True, nodeHighlightBehavior=True, physics=True)
    
    # Vykreslení grafu. Kliknutí vrátí ID uzlu.
    clicked_node = agraph(nodes=nodes, edges=edges, config=config)
    
    if clicked_node and clicked_node != st.session_state.current_uri:
        st.session_state.current_uri = clicked_node
        st.rerun()