import streamlit as st
from rdflib import Graph, Namespace, RDFS
import os
from src.wiki_browser import show_wiki
from src.sparql_console import show_console

EX = Namespace("http://example.org/gpu/")
SCHEMA = Namespace("https://schema.org/")

st.set_page_config(layout="wide", page_title="GPU-LD Hub")

@st.cache_resource
def load_graph():
    g = Graph()
    base_path = os.path.dirname(os.path.abspath(__file__))
    ttl_path = os.path.join(base_path, "data", "gpu_data.ttl")
    g.parse(ttl_path, format="turtle")
    return g

g = load_graph()

st.sidebar.title("GPU-LD Hub")
page = st.sidebar.radio("Navigace:", ["SPARQL Endpoint", "GPU Encyclopedia"])

if page == "GPU Encyclopedia":
    show_wiki(g, EX, SCHEMA)
else:
    show_console(g)