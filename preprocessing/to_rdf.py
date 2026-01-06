import pandas as pd
from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.namespace import XSD, OWL

# 1. Namespace definitions
EX = Namespace("http://example.org/gpu/")
SCHEMA = Namespace("https://schema.org/")

def create_rdf():
    try:
        df = pd.read_csv('data/gpu_info_cleaned.csv')
    except FileNotFoundError:
        print("Error: File 'data/gpu_info_cleaned.csv' not found.")
        return

    g = Graph()

    g.bind("ex", EX)
    g.bind("schema", SCHEMA)
    g.bind("owl", OWL)

    # Brand -> Organization
    unique_brands = df[['brand', 'brand_uri_id']].dropna().drop_duplicates()
    for _, row in unique_brands.iterrows():
        brand_uri = EX[row['brand_uri_id']]
        g.add((brand_uri, RDF.type, SCHEMA.Organization))
        g.add((brand_uri, SCHEMA.name, Literal(row['brand'])))

    # Architecture -> GPUArchitecture
    unique_archs = df[['architecture', 'arch_uri_id']].dropna().drop_duplicates()
    for _, row in unique_archs.iterrows():
        arch_uri = EX[row['arch_uri_id']]
        g.add((arch_uri, RDF.type, EX.GPUArchitecture))
        g.add((arch_uri, SCHEMA.name, Literal(row['architecture'])))

    # GPU Product
    for _, row in df.iterrows():
        
        gpu_uri = EX[row['product_uri_id']]

        g.add((gpu_uri, RDF.type, SCHEMA.Product))
        g.add((gpu_uri, SCHEMA.name, Literal(row['product_name'])))
        
        # GPU -> manufacturer (Brand)
        brand_uri = EX[row['brand_uri_id']]
        g.add((gpu_uri, SCHEMA.manufacturer, brand_uri))

        # GPU -> architecture
        if pd.notna(row['arch_uri_id']):
            arch_uri = EX[row['arch_uri_id']]
            g.add((gpu_uri, EX.hasArchitecture, arch_uri))

        # XSD typed literals for numeric properties
        if pd.notna(row['tdp_watts']):
            g.add((gpu_uri, EX.tdpWatts, Literal(int(row['tdp_watts']), datatype=XSD.integer)))
        
        if pd.notna(row['mem_size_kb']):
            g.add((gpu_uri, EX.memorySizeKB, Literal(int(row['mem_size_kb']), datatype=XSD.integer)))

        if pd.notna(row['fp32_gflops']):
            g.add((gpu_uri, EX.fp32GFLOPS, Literal(float(row['fp32_gflops']), datatype=XSD.decimal)))

    # Save to Turtle file
    output_file = "data/gpu_data.ttl"
    g.serialize(destination=output_file, format="turtle")
    print(f"Transformace dokončena. Soubor uložen jako: {output_file}")

if __name__ == "__main__":
    create_rdf()