import pandas as pd
from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.namespace import XSD, OWL
from config import PROCESSED_CSV_PATH, OUTPUT_RDF_PATH
from linkset import BRAND_LINKS, ARCH_LINKS

# 1. Namespace definitions
EX = Namespace("http://example.org/gpu/")
SCHEMA = Namespace("https://schema.org/")

def create_rdf():
    try:
        df = pd.read_csv(PROCESSED_CSV_PATH)
    except FileNotFoundError:
        print(f"Error: File {PROCESSED_CSV_PATH} not found.")
        return

    g = Graph()

    g.bind("ex", EX)
    g.bind("schema", SCHEMA)
    g.bind("owl", OWL)
    
    # Brand -> Organization
    unique_brands = df[['brand', 'brand_uri_id']].dropna().drop_duplicates()
    for _, row in unique_brands.iterrows():
        brand_name = row['brand']
        brand_uri = EX[row['brand_uri_id']]
        
        g.add((brand_uri, RDF.type, SCHEMA.Organization))
        g.add((brand_uri, SCHEMA.name, Literal(brand_name)))

        # wikidata links
        if brand_name in BRAND_LINKS and BRAND_LINKS[brand_name]:
            external_uri = URIRef(BRAND_LINKS[brand_name])
            g.add((brand_uri, OWL.sameAs, external_uri))


    # Architecture -> GPUArchitecture
    unique_archs = df[['architecture', 'arch_uri_id']].dropna().drop_duplicates()
    for _, row in unique_archs.iterrows():
        arch_name = row['architecture']
        arch_uri = EX[row['arch_uri_id']]
        
        g.add((arch_uri, RDF.type, EX.GPUArchitecture))
        g.add((arch_uri, SCHEMA.name, Literal(arch_name)))

        # wikidata links
        if arch_name in ARCH_LINKS and ARCH_LINKS[arch_name]:
            external_uri = URIRef(ARCH_LINKS[arch_name])
            g.add((arch_uri, OWL.sameAs, external_uri))




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
    g.serialize(destination=OUTPUT_RDF_PATH, format="turtle")
    print(f"Saved to: {OUTPUT_RDF_PATH}")

if __name__ == "__main__":
    create_rdf()
    print("\nto rdf - all done\n")