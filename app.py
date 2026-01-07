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
    base_path = os.path.dirname(os.path.abspath(__file__))
    ttl_path = os.path.join(base_path, "data", "gpu_data.ttl")
    try:
        g.parse(ttl_path, format="turtle")
    except Exception as e:
        st.error(f"Chyba při načítání dat: {e}")
    return g

g = load_gpu_graph()

# 3. POMOCNÉ FUNKCE
def get_label(uri):
    query = f"SELECT ?label WHERE {{ <{uri}> (rdfs:label|schema:name) ?label . }} LIMIT 1"
    res = list(g.query(query))
    return str(res[0][0]) if res else str(uri).split("/")[-1]

def short_id(uri):
    return str(uri).replace(str(EX), "ex:").replace(str(SCHEMA), "schema:")

# --- SESSION STATE ---
if 'current_uri' not in st.session_state:
    st.session_state.current_uri = str(EX.NVIDIA)

# --- SIDEBAR: VYHLEDÁVÁNÍ ---
st.sidebar.header("🔍 Vyhledávání")
search_query = st.sidebar.text_input("Najít kartu/uzel:")
if search_query:
    q_search = f"""SELECT ?node ?name WHERE {{ ?node (schema:name|rdfs:label) ?name . 
    FILTER (CONTAINS(LCASE(?name), LCASE("{search_query}"))) }} LIMIT 10"""
    for r in g.query(q_search):
        if st.sidebar.button(f"👉 {r.name}", key=f"s_{r.node}"):
            st.session_state.current_uri = str(r.node)
            st.rerun()

# --- HLAVNÍ PLOCHA ---
curr = URIRef(st.session_state.current_uri)
st.title(f"📍 {get_label(curr)}")

col1, col2 = st.columns([1, 2])

with col1:
    # SEKCE A: Vlastnosti aktuálního uzlu
    with st.expander("📄 Technické detaily uzlu", expanded=True):
        q_props = f"SELECT ?p ?o WHERE {{ <{curr}> ?p ?o . }}"
        for p, o in g.query(q_props):
            p_lab = short_id(p)
            if isinstance(o, URIRef):
                if st.button(f"{p_lab} ⮕ {get_label(o)}", key=f"prop_{o}_{p}"):
                    st.session_state.current_uri = str(o)
                    st.rerun()
            else:
                st.write(f"**{p_lab}:** {o}")

    st.divider()

    # SEKCE B: Seznam sousedů (Příchozí vazby)
    st.subheader("🔗 Související položky")
    
    sort_by = st.selectbox("Řadit podle:", ["Názvu", "Roku vydání", "Velikosti VRAM"])
    sort_order = st.radio("Pořadí:", ["Vzestupně", "Sestupně"], horizontal=True)

    # SPARQL pro sousedy
    q_neigh = f"""
    SELECT DISTINCT ?target ?name ?year ?vram WHERE {{
        ?target ?p <{curr}> .
        ?target (schema:name|rdfs:label) ?name .
        OPTIONAL {{ ?target ex:releaseYear ?year }}
        OPTIONAL {{ ?target ex:memorySizeKB ?vram }}
        FILTER(isIRI(?target))
    }}
    """
    
    neighbor_list = []
    for row in g.query(q_neigh):
        neighbor_list.append({
            "uri": str(row.target),
            "Názvu": str(row.name),
            "Roku vydání": int(row.year) if row.year else 0,
            "Velikosti VRAM": int(row.vram) if row.vram else 0
        })
    
    df = pd.DataFrame(neighbor_list)

    if not df.empty:
        df = df.sort_values(by=sort_by, ascending=(sort_order == "Vzestupně")).reset_index(drop=True)
        
        # Filtrování v levém sloupci
        max_nodes = 25
        df_visible = df.head(max_nodes)

        for i, row in df_visible.iterrows():
            idx = i + 1
            meta = f"({row['Roku vydání']})" if row['Roku vydání'] > 0 else ""
            if st.button(f"{idx}. {row['Názvu']} {meta}", key=f"nav_{row['uri']}", use_container_width=True):
                st.session_state.current_uri = row['uri']
                st.rerun()
        
        if len(df) > max_nodes:
            st.caption(f"A dalších {len(df) - max_nodes} uzlů...")
    else:
        st.write("Žádné příchozí vazby.")

with col2:
    st.subheader("🕸️ Interaktivní mapa")
    
    nodes = []
    edges = []
    
    # Centrální uzel (červený)
    nodes.append(Node(id=str(curr), label=get_label(curr), size=35, color="#FF4B4B"))
    
    # Přidání očíslovaných sousedů z DataFrame
    if not df.empty:
        for i, row in df_visible.iterrows():
            idx = i + 1
            nodes.append(Node(
                id=row['uri'], 
                label=str(idx), # Jen číslo!
                size=20, 
                color="#2196F3",
                title=row['Názvu'] # Jméno se ukáže při najetí myší
            ))
            edges.append(Edge(source=row['uri'], target=str(curr)))

    # Také přidáme odchozí vazby do mapy (ty co jsou v Technických detailech)
    q_out = f"SELECT ?p ?o WHERE {{ <{curr}> ?p ?o . FILTER(isIRI(?o)) }}"
    for p, o in g.query(q_out):
        if str(o) not in [n.id for n in nodes]:
            nodes.append(Node(id=str(o), label=get_label(o), size=20, color="#4CAF50"))
        edges.append(Edge(source=str(curr), target=str(o), label=short_id(p)))

    config = Config(width=800, height=700, directed=True, physics=True)
    clicked = agraph(nodes=nodes, edges=edges, config=config)
    
    if clicked and clicked != st.session_state.current_uri:
        st.session_state.current_uri = clicked
        st.rerun()