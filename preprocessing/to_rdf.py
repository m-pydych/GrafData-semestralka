import pandas as pd
from rdflib import Graph, Literal, RDF, Namespace, URIRef, RDFS
from rdflib.namespace import XSD, OWL
from config import PROCESSED_CSV_PATH, OUTPUT_RDF_PATH
from linkset import BRAND_LINKS, ARCH_LINKS

# 1. Namespace definitions
EX = Namespace("http://example.org/gpu/")
SCHEMA = Namespace("https://schema.org/")

# 2. RDF Property definitions

RDF_PROPERTIES = {
    EX.hasArchitecture: (
        "has architecture",
        EX.GPUArchitecture,
        "The underlying microarchitecture on which the GPU is based (e.g., Ada Lovelace, Turing)."
    ),
    EX.tdpWatts: (
        "TDP (Watts)",
        XSD.integer,
        "Thermal Design Power represents the maximum amount of heat the cooling system is designed to dissipate."
    ),
    EX.memorySizeKB: (
        "Memory Size (KB)",
        XSD.integer,
        "The total amount of dedicated video memory available on the graphics card, measured in kilobytes."
    ),
    EX.gpuCodename: (
        "GPU Codename",
        XSD.string,
        "The internal development codename used by the manufacturer for the GPU chip (e.g., AD102, Navi 31)."
    ),
    EX.memoryType: (
        "Memory Type",
        XSD.string,
        "The type of video memory used by the GPU (e.g., GDDR6, GDDR6X, HBM2)."
    ),
    EX.releaseYear: (
        "Release Year",
        XSD.integer,
        "The calendar year in which the graphics card or GPU was officially released."
    ),
    EX.releaseMonth: (
        "Release Month",
        XSD.integer,
        "The calendar month in which the graphics card or GPU was officially released."
    ),
    EX.shadingUnits: (
        "Shading Units",
        XSD.integer,
        "The number of programmable processing units responsible for shading and compute tasks (e.g., CUDA cores or Stream Processors)."
    ),
    EX.memoryBusBits: (
        "Memory Bus (bits)",
        XSD.integer,
        "The width of the memory interface between the GPU and its video memory, measured in bits."
    ),
    EX.fp32GFlops: (
        "FP32 Performance (GFLOPS)",
        XSD.float,
        "Theoretical peak single-precision (FP32) floating-point performance of the GPU, measured in GFLOPS."
    ),
    EX.baseClockMHz: (
        "Base Clock (MHz)",
        XSD.integer,
        "The base operating frequency of the GPU core under normal workload conditions."
    ),
    EX.boostClockMHz: (
        "Boost Clock (MHz)",
        XSD.integer,
        "The maximum clock frequency the GPU can reach under boost conditions, depending on power and thermal limits."
    ),
    EX.maxClockMHz: (
        "Max Clock (MHz)",
        XSD.integer,
        "The maximum achievable clock frequency of the GPU core as specified by the manufacturer."
    ),
}



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
    g.bind("rdfs", RDFS)

    g.add((EX.GPUArchitecture, RDF.type, RDFS.Class))
    g.add((EX.GPUArchitecture, RDFS.label, Literal("GPU Architecture", lang="en")))

    # Define RDF properties
    for prop, (label, dtype, comment) in RDF_PROPERTIES.items():
        g.add((prop, RDF.type, RDF.Property))
        g.add((prop, RDFS.label, Literal(label, lang="en")))
        g.add((prop, RDFS.range, dtype))
        g.add((prop, RDFS.comment, Literal(comment, lang="en")))


    # Brand -> Organization
    unique_brands = df[['brand', 'brand_uri_id']].dropna().drop_duplicates()
    for _, row in unique_brands.iterrows():
        brand_name = row['brand']
        brand_uri = EX[row['brand_uri_id']]
        
        g.add((brand_uri, RDF.type, SCHEMA.Organization))
        g.add((brand_uri, SCHEMA.name, Literal(brand_name, lang='en')))

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
        g.add((arch_uri, SCHEMA.name, Literal(arch_name, lang='en')))

        # wikidata links
        if arch_name in ARCH_LINKS and ARCH_LINKS[arch_name]:
            external_uri = URIRef(ARCH_LINKS[arch_name])
            g.add((arch_uri, OWL.sameAs, external_uri))

    # GPU Product 
    for _, row in df.iterrows():
        
        gpu_uri = EX[row['product_uri_id']]

        g.add((gpu_uri, RDF.type, SCHEMA.Product))
        g.add((gpu_uri, SCHEMA.name, Literal(row['product_name'], lang="en")))

        if pd.notna(row['gpu_codename']):
            g.add((gpu_uri, EX.gpuCodename, Literal(row['gpu_codename'], lang="en")))

        if pd.notna(row['mem_type']):
            g.add((gpu_uri, EX.memoryType, Literal(row['mem_type'], lang="en")))

        if pd.notna(row['shading_units']):
            g.add((gpu_uri, EX.shadingUnits, Literal(int(row['shading_units']), datatype=XSD.integer)))

        if pd.notna(row['mem_bus_bits']):
            g.add((gpu_uri, EX.memoryBusBits, Literal(int(row['mem_bus_bits']), datatype=XSD.integer)))

        if pd.notna(row['fp32_gflops']):
            g.add((gpu_uri, EX.fp32GFlops, Literal(float(row['fp32_gflops']), datatype=XSD.float)))

        if pd.notna(row['launch_price']):
            g.add((gpu_uri, SCHEMA.price, Literal(int(row['launch_price']), datatype=XSD.integer)))

        if pd.notna(row['base_clock']):
            g.add((gpu_uri, EX.baseClockMHz, Literal(int(row['base_clock']), datatype=XSD.integer)))

        if pd.notna(row['boost_clock']):
            g.add(( gpu_uri, EX.boostClockMHz, Literal(int(row['boost_clock']), datatype=XSD.integer)))

        if pd.notna(row['max_clock_mhz']):
            g.add((gpu_uri, EX.maxClockMHz, Literal(int(row['max_clock_mhz']), datatype=XSD.integer)))
        
        # GPU -> manufacturer (Brand) predicate
        brand_uri = EX[row['brand_uri_id']]
        g.add((gpu_uri, SCHEMA.manufacturer, brand_uri))

        # GPU -> architecture predicate
        if pd.notna(row['arch_uri_id']):
            arch_uri = EX[row['arch_uri_id']]
            g.add((gpu_uri, EX.hasArchitecture, arch_uri))

        # Release date to XSD date format (YYYY-MM-DD)
        if 'release_date_xsd' in row and pd.notna(row['release_date_xsd']):
            g.add((gpu_uri, SCHEMA.releaseDate, Literal(row['release_date_xsd'], datatype=XSD.date)))

        # Year to integer
        if 'release_year' in row and pd.notna(row['release_year']):
            g.add((gpu_uri, EX.releaseYear, Literal(int(row['release_year']), datatype=XSD.integer)))

        # Month to integer
        if 'release_month' in row and pd.notna(row['release_month']):
            g.add((gpu_uri, EX.releaseMonth, Literal(int(row['release_month']), datatype=XSD.integer)))

        # XSD typed literals for numeric properties
        if pd.notna(row['tdp_watts']):
            g.add((gpu_uri, EX.tdpWatts, Literal(int(row['tdp_watts']), datatype=XSD.integer)))
        
        if pd.notna(row['mem_size_kb']):
            g.add((gpu_uri, EX.memorySizeKB, Literal(int(row['mem_size_kb']), datatype=XSD.integer)))

    # Save to Turtle file
    g.serialize(destination=OUTPUT_RDF_PATH, format="turtle")
    print(f"Saved to: {OUTPUT_RDF_PATH}")

if __name__ == "__main__":
    create_rdf()
    print("\nto rdf - all done\n")