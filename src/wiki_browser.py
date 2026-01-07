import streamlit as st
import pandas as pd
from rdflib import Graph, URIRef

def show_wiki(g, EX, SCHEMA):
    st.subheader("GPU Encyclopedia")

    # --- 1. UI for filtering ---
    st.write("### Filter settings")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        filter_type = st.selectbox("Filter by:", ["All", "Brand", "Architecture", "Release Year"])
    
    # Dynamically show filter value input based on selected filter type
    with col_f2:
        filter_value = None
        if filter_type == "Brand":
            q_brands = "SELECT DISTINCT ?name WHERE { ?b a <https://schema.org/Organization> ; <https://schema.org/name> ?name . }"
            brands = [str(r.name) for r in g.query(q_brands)]
            filter_value = st.selectbox("Select brand:", sorted(brands))
        elif filter_type == "Architecture":
            q_archs = "SELECT DISTINCT ?name WHERE { ?a a <http://example.org/gpu/GPUArchitecture> ; <https://schema.org/name> ?name . }"
            archs = [str(r.name) for r in g.query(q_archs)]
            filter_value = st.selectbox("Select architecture:", sorted(archs))
        elif filter_type == "Release Year":
            filter_value = st.slider("Minimum year:", 1995, 2025, 2010)

    with col_f3:
        rank_by = st.selectbox("Ranking criteria:", 
                               ["Performance (GFLOPS)", "TDP (W)", "Price ($)", "Number of cores"])
        
    # --- 2. Dynamic query building ---
    # Map ranking criteria to predicates
    rank_map = {
        "Performance (GFLOPS)": "ex:fp32GFlops",
        "TDP (W)": "ex:tdpWatts",
        "Price ($)": "schema:price",
        "Number of cores": "ex:shadingUnits"
    }
    target_predicate = rank_map[rank_by]

    # Build filter clause
    filter_clause = ""
    if filter_type == "Brand":
        filter_clause = f'?brand_uri <https://schema.org/name> "{filter_value}" .'
    elif filter_type == "Architecture":
        filter_clause = f'?arch_uri <https://schema.org/name> "{filter_value}" .'
    elif filter_type == "Release Year":
        filter_clause = f'FILTER(?year >= {filter_value})'

    # Final query
    main_query = f"""
    PREFIX ex: <http://example.org/gpu/>
    PREFIX schema: <https://schema.org/>
    SELECT DISTINCT ?gpu ?name ?val ?year WHERE {{
        ?gpu a schema:Product ;
             schema:name ?name ;
             {target_predicate} ?val .
        
        # Volitelné vazby pro filtry
        OPTIONAL {{ ?gpu schema:manufacturer ?brand_uri }}
        OPTIONAL {{ ?gpu ex:hasArchitecture ?arch_uri }}
        OPTIONAL {{ ?gpu ex:releaseYear ?year }}
        
        {filter_clause}
    }} ORDER BY ?val
    """

    # --- 3. Query execution ---
    @st.cache_data(hash_funcs={Graph: id})
    def run_dynamic_query(query_str):
        res = g.query(query_str)
        return [{"Name": str(r.name), "Value": float(r.val), "Year": int(r.year) if r.year else None} for r in res]

    results_list = run_dynamic_query(main_query)
    df = pd.DataFrame(results_list)

    # --- 4. Displaying Results ---
    if not df.empty:
        st.info(f"{len(df)} GPUs found matching the criteria.")
        
        # Statistiky
        st.write(f"### Statistics: {rank_by}")
        cols = st.columns(3)
        
        worst = df.iloc[0]
        median = df.iloc[len(df)//2]
        best = df.iloc[-1]

        cols[0].metric(label="Best", value=best['Name'])
        cols[0].caption(f"{best['Value']} {rank_by.split()[-1]}")
        
        cols[1].metric(label="Median", value=median['Name'])
        cols[1].caption(f"{median['Value']} {rank_by.split()[-1]}")
        
        cols[2].metric(label="Worst", value=worst['Name'])
        cols[2].caption(f"{worst['Value']} {rank_by.split()[-1]}")

        st.write("### Results:")
        st.dataframe(df.rename(columns={"Value": rank_by}), use_container_width=True)
    else:
        st.warning("For this combination of filters and criteria, no results were found in the graph.")
        st.code(main_query, language="sparql") # Show the query so we can see what failed