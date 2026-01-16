import streamlit as st
import pandas as pd
from rdflib import Graph, URIRef

def show_wiki(g, EX, SCHEMA):
    st.subheader("GPU Encyclopedia")

    if "rank_by_key" not in st.session_state:
        st.session_state.rank_by_key = "None"


    # --- 1. UI outside form ---
    st.write("### Filter settings")
    filter_type = st.selectbox("Filter by:", 
        ["All", "Brand", "Architecture", "Release Year", "Memory Size", "Memory Type", "Memory Bus"])


    # --- 2. Form ---
    with st.form("wiki_filter_form"):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            filter_value = None
            if filter_type == "Brand":
                q_brands = "SELECT DISTINCT ?name WHERE { ?gpu <https://schema.org/manufacturer> ?b . ?b <https://schema.org/name> ?name . }"
                brands = [str(r.name) for r in g.query(q_brands)]
                filter_value = st.selectbox("Select brand:", sorted(brands))
            elif filter_type == "Architecture":
                q_archs = "SELECT DISTINCT ?name WHERE { ?gpu <http://example.org/gpu/hasArchitecture> ?a . ?a <https://schema.org/name> ?name . }"
                archs = [str(r.name) for r in g.query(q_archs)]
                filter_value = st.selectbox("Select architecture:", sorted(archs))
            elif filter_type == "Release Year":
                q_years = "SELECT DISTINCT ?year WHERE { ?gpu <http://example.org/gpu/releaseYear> ?year . }"
                years = [str(r.year) for r in g.query(q_years)]
                filter_value = st.selectbox("Select year:", sorted(years))

            elif filter_type == "Memory Size":
                q_m_sizes = """
                SELECT DISTINCT ?label WHERE { 
                    ?gpu <http://example.org/gpu/memorySize> ?ms . 
                    OPTIONAL { ?ms <https://schema.org/name> ?name }
                    BIND(COALESCE(STR(?name), STR(?ms)) AS ?label)
                }"""
                m_sizes = [str(r.label).split('/')[-1].split('#')[-1] for r in g.query(q_m_sizes)]
                filter_value = st.selectbox("Select VRAM:", sorted(list(set(m_sizes))))

            elif filter_type == "Memory Type":
                q_m_types = "SELECT DISTINCT ?type WHERE { ?gpu <http://example.org/gpu/memoryType> ?type . }"
                m_types = [str(r.type) for r in g.query(q_m_types)]
                filter_value = st.selectbox("Select memory type:", sorted(m_types))

            elif filter_type == "Memory Bus":
                # Oprava: Hledáme, co mají karty v ex:memBus
                q_m_buses = """
                SELECT DISTINCT ?label WHERE { 
                    ?gpu <http://example.org/gpu/memBus> ?mb . 
                    OPTIONAL { ?mb <https://schema.org/name> ?name }
                    BIND(COALESCE(STR(?name), STR(?mb)) AS ?label)
                }"""
                m_buses = [str(r.label).split('/')[-1].split('#')[-1] for r in g.query(q_m_buses)]
                filter_value = st.selectbox("Select bus width:", sorted(list(set(m_buses))))

            else:
                st.write("No additional settings needed.")


        with col_f2:
            rank_by = st.selectbox("Ranking criteria:", 
                                   ["None", "Performance (GFLOPS)", "TDP (W)", "Price ($)", "Number of cores"],
                                   key="rank_by_key")

        # submit button
        submitted = st.form_submit_button("Show results")

    # --- 3. Logic and display (executes only after submission) ---
    if submitted:
        rank_map = {
            "Performance (GFLOPS)": "ex:fp32GFlops",
            "TDP (W)": "ex:tdpWatts",
            "Price ($)": "schema:price",
            "Number of cores": "ex:shadingUnits"
        }
        is_ranking = rank_by != "None"
        target_predicate = rank_map[rank_by] if is_ranking else "schema:name"

        # Build filter clause
        filter_clause = ""
        if filter_type == "Brand":
            filter_clause = f'?brand_uri <https://schema.org/name> ?bn . FILTER(STR(?bn) = "{filter_value}")'
        elif filter_type == "Architecture":
            filter_clause = f'?arch_uri <https://schema.org/name> ?an . FILTER(STR(?an) = "{filter_value}")'
        elif filter_type == "Release Year":
            filter_clause = f'FILTER(?year = {filter_value})'
        elif filter_type == "Memory Size":
            filter_clause = f'?gpu <http://example.org/gpu/memorySize> ?ms . FILTER(CONTAINS(STR(?ms), "{filter_value}"))'
        elif filter_type == "Memory Type":
            filter_clause = f'?gpu <http://example.org/gpu/memoryType> ?mt . FILTER(STR(?mt) = "{filter_value}")'
        elif filter_type == "Memory Bus":
            filter_clause = f'?gpu <http://example.org/gpu/memBus> ?mb . FILTER(CONTAINS(STR(?mb), "{filter_value}"))'

        main_query = f"""
        PREFIX ex: <http://example.org/gpu/>
        PREFIX schema: <https://schema.org/>
        SELECT DISTINCT ?gpu ?name ?val ?year WHERE {{
            ?gpu a schema:Product ;
                 schema:name ?name ;
                 {target_predicate} ?val .
            
            OPTIONAL {{ ?gpu schema:manufacturer ?brand_uri }}
            OPTIONAL {{ ?gpu ex:hasArchitecture ?arch_uri }}
            OPTIONAL {{ ?gpu ex:releaseYear ?year }}
            {filter_clause}
        }} ORDER BY ?val
        """

        @st.cache_data(hash_funcs={Graph: id})
        def run_dynamic_query(query_str, ranking_active):
            res = g.query(query_str)
            data = []
            for r in res:
                row = {
                    "Name": str(r.name),
                    "Year": int(r.year.toPython()) if r.year and hasattr(r.year, 'toPython') else (int(r.year) if r.year else None)
                }
                if ranking_active:
                    row["Value"] = float(r.val.toPython()) if hasattr(r.val, 'toPython') else float(r.val)
                else:
                    row["Value"] = str(r.val)
                data.append(row)
            return data

        results_list = run_dynamic_query(main_query, is_ranking)
        df = pd.DataFrame(results_list)




        if not df.empty:
            st.success(f"{len(df)} GPUs found.")

            if is_ranking:
                st.write(f"### Statistics: {rank_by}")
                cols = st.columns(3)
                worst, median, best = df.iloc[0], df.iloc[len(df)//2], df.iloc[-1]

                cols = st.columns(3)
                worst, median, best = df.iloc[0], df.iloc[len(df)//2], df.iloc[-1]
                cols[0].metric(label="Highest", value=best['Name'])
                cols[0].caption(f"{best['Value']} {rank_by.split()[-1]}")
                cols[1].metric(label="Median", value=median['Name'])
                cols[1].caption(f"{median['Value']} {rank_by.split()[-1]}")
                cols[2].metric(label="Lowest", value=worst['Name'])
                cols[2].caption(f"{worst['Value']} {rank_by.split()[-1]}")
            
            display_df = df.copy()
            if is_ranking:
                display_df = display_df.rename(columns={"Value": rank_by})
            else:
                display_df = display_df.drop(columns=["Value"])
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("No results found.")
            if is_ranking:
                st.info(f"The criteria '{rank_by}' might be missing for these cards (common for older GPUs).")
                if st.button("Remove ranking criteria (set to None)"):
                    st.session_state.rank_by_key = "None"
                    st.rerun()