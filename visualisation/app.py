import tempfile

import cobra
import re
import streamlit as st
import os
from cobra.io import read_sbml_model, write_sbml_model
import time
import pandas as pd
from build_model import create_carve_model
from model_engine import load_fungal_model, run_fba_simulation, get_sensitivity_data
from visuals import plot_growth_bar, plot_sensitivity
from optimise import run_optimization, optimize_model, compute_try
from media import MEDIA
from add_oxygen import add_oxygen_to_model
from network import show_graph, cobra_to_bipartite_graph, extract_k_hop_subgraph
from sequence_utils import (
    detect_sequence_type,
    render_download_button,
    translate_dna_to_protein,
)


MODEL_DIR = "/app/data/models"
FASTA_DIR = "/app/data/fastas"

if not os.path.isdir(MODEL_DIR):
    os.makedirs(MODEL_DIR)

if not os.path.isdir(FASTA_DIR):
    os.makedirs(FASTA_DIR)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GEmtimize",
    page_icon="🍄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #2e7b5b; /* Biotech Green */
        color: white;
        font-weight: bold;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'model_built' not in st.session_state:
    st.session_state.model_built = False
if 'model' not in st.session_state:
    st.session_state.model = None
if 'last_solution' not in st.session_state:
    st.session_state.last_solution = None
if 'sensitivity_df' not in st.session_state:
    st.session_state.sensitivity_df = pd.DataFrame()
if 'build_error' not in st.session_state:
    st.session_state.build_error = None
if 'model_file' not in st.session_state:
    st.session_state.model_file = None

# --- SIDEBAR: CONFIGURATION ---
with st.sidebar:
    st.markdown(
        "<h1><span style='color: orange; font-weight: bold;'>GEM</span><span style='color: black; font-weight: bold;'>timize</span></h1>",
        unsafe_allow_html=True
    )
    st.markdown("Automated GEM Generation and Media Optimisation")
    st.divider()
    st.subheader("1. Select Strain Data")
    input_method = st.radio(
        "Choose your input method:",
        ["Library Strains", "Custom Upload"],
        help="Select a pre-loaded reference genome or upload your own sequencing data."
    )

    selected_strain_name = "Custom Strain"

    if input_method == "Library Strains":
        selected_strain_name = st.selectbox(
            "Select a default fungal strain:",
            [
                "NC12",
                "Rhimi",
                "Aspory",
                "Aspni"
            ]
        )
        fasta_file = None
        st.success(f"Ready to load: **{selected_strain_name.split(' ')[0]}**")

    else:
        st.info("Otherwise, upload your own genome file in FASTA format below.")
        selected_strain_name = st.text_input("Strain Name", value="Custom_Strain")
        uploaded_file = st.file_uploader(
            "Upload Genome (Required)",
            type=["fasta", "faa", "fna"],
            help="Drag and drop your .fasta or .gbk file here."
        )

        fasta_file = f"{FASTA_DIR}/{selected_strain_name}.fasta"

        if uploaded_file is not None:
            with open(fasta_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("File uploaded and saved!")
            raw_bytes = uploaded_file.getbuffer().tobytes()
            try:
                kind = detect_sequence_type(raw_bytes)
                custom_upload_sequence_kind = kind
                protein_bytes = (
                    translate_dna_to_protein(raw_bytes) if kind == "dna" else raw_bytes
                )
                safe = re.sub(r"[^\w\-.]+", "_", selected_strain_name.strip()) or "strain"
                st.caption(
                    f"Sequence type: **{kind.upper()}** — CarveMe uses protein FASTA (.faa)."
                )
                render_download_button(
                    "Download protein FASTA (.faa)",
                    f"{safe}.faa",
                    protein_bytes,
                )
            except ValueError as err:
                st.warning(str(err))
        else:
            st.info("Please upload a file to proceed.")


    st.divider()

    st.subheader("2. Run Pipeline")
    if st.button("Build Metabolic Model"):
        if (
            input_method == "Custom Upload"
            and custom_upload_sequence_kind == "dna"
        ):
            st.info(
                "This is a BETA feature currently being tested, expected to be "
                "integrated into the GEMtimize web app soon."
            )
        else:
            with st.spinner(f"Reconstructing metabolic network for {selected_strain_name}..."):
                # Simulating the backend GEM pipeline processing time
                time.sleep(2.5)
                try:
                    model_file = f"{MODEL_DIR}/model.{selected_strain_name}.xml"
                    if os.path.exists(model_file):
                        st.info("Model already exists. Loading from disk...")
                        model = read_sbml_model(model_file)
                    else:
                        st.info("Model not found. Creating a new one...")
                        model = create_carve_model(selected_strain_name, fasta_file, model_file)

                    add_oxygen_to_model(model)

                    baseline_solution = model.optimize()
                    st.session_state.model = model
                    st.session_state.last_solution = baseline_solution
                    st.session_state.sensitivity_df = get_sensitivity_data(model, "EX_glc__D_e")
                    st.session_state.model_built = True
                    st.session_state.build_error = None
                    st.session_state.model_file = model_file
                    st.session_state.custom_medium = {}
                    st.success("Model loaded and baseline simulation completed.")
                except Exception as exc:
                    st.session_state.model_built = False
                    st.session_state.model = None
                    st.session_state.last_solution = None
                    st.session_state.model_file = None
                    st.session_state.sensitivity_df = pd.DataFrame()
                    st.session_state.build_error = str(exc)
                    st.session_state.custom_medium = {}
                    st.error(f"Model build failed: {exc}")

# --- MAIN DASHBOARD ---
st.title("Media Optimization Workspace")
st.markdown("""
**Welcome to GEMtimize.** Genome-Scale Metabolic Models (GEMs) act like a digital twin of your microbe.
By mapping out every metabolic reaction, we can computationally predict which nutrients will boost growth or target production—saving you weeks of trial-and-error in the wet lab.
""")

# --- TABS ---
tab_overview, tab_network, tab_report = st.tabs([
    "📊 Model Overview",
    "🔬 Network Visualization",
    "📝 Downloads"
])

# --- TAB 1: MODEL OVERVIEW ---
with tab_overview:
    if st.session_state.model_built:
        st.success(f"Metabolic Model successfully generated for: **{selected_strain_name}**")

        model = st.session_state.model

        solution = st.session_state.last_solution
        growth_rate = 0.0
        if solution is not None and getattr(solution, "status", "") == "optimal":
            growth_rate = float(solution.objective_value)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Metabolic Reactions", f"{len(model.reactions):,}")
        col2.metric("Metabolites", f"{len(model.metabolites):,}")
        col3.metric("Genes Mapped", f"{len(model.genes):,}")
        col4.metric("Predicted Max Growth", f"{growth_rate:.3f} h⁻¹", "Maximum Theroretical Growth Rate")

        # Select a Reaction and Minimum Growth Rate for Media Optimization
        st.markdown("""**Obtain a minimal medium for your reaction**""")
        selected_reaction_name = st.selectbox("Select a reaction to optimise:", options=[None] + [rxn.name for rxn in model.reactions], index=0, key="objective_select")
        

        # Find the minimum media for the selected reaction and growth rate
        if selected_reaction_name:
            # Get objective info
            selected_reaction_id = next(rxn.id for rxn in model.reactions if rxn.name == selected_reaction_name)
            selected_reaction = model.reactions.get_by_id(selected_reaction_id)

            st.write(f"**Reaction ID:** {selected_reaction.id}")
            st.write(f"**Equation:** {selected_reaction.build_reaction_string()}")
            st.write(model.objective)

            st.markdown("""**Build a media recipe**""")
            # --- Input Row ---
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                selected_exchange_name = st.selectbox("Select an exchange reaction:", options=[None] + [rxn.name for rxn in model.exchanges], index=0, key="exchanges_select")

            with col2:
                flux_value = st.number_input("Uptake Rate:", min_value=-1000.0, value=10.0, step=1.0)
            
            with col3:
                if st.button("Add to Medium"):
                    # Convert reaction name to reaction ID for proper medium handling
                    if selected_exchange_name:
                        exchange_reaction = next((rxn for rxn in model.exchanges if rxn.name == selected_exchange_name), None)
                        if exchange_reaction:
                            st.session_state.custom_medium[exchange_reaction.id] = flux_value
                        else:
                            st.error(f"Exchange reaction '{selected_exchange_name}' not found")

            with col4:
                if st.button("Infinite Media"):
                    st.session_state.custom_medium = {exchange.id: 1000.0 for exchange in model.exchanges}
                    st.rerun()
            

            # --- Display and Apply Medium ---
            if st.session_state.custom_medium:
                st.markdown("### **Current Recipe**")
                
                # Create sliders for each component
                updated_medium = {}
                for rxn_id, current_flux in st.session_state.custom_medium.items():
                    try:
                        rxn = model.reactions.get_by_id(rxn_id)
                        display_name = rxn.name
                    except:
                        display_name = rxn_id
                    
                    # Create two columns for name and slider
                    name_col, slider_col = st.columns([1, 2])
                    
                    with name_col:
                        st.write(f"**{display_name}**")
                    
                    with slider_col:
                        new_flux = st.slider(
                            f"Flux for {rxn_id}",
                            min_value=0.0,
                            max_value=1000.0,
                            value=current_flux,
                            step=1.0,
                            key=f"slider_{rxn_id}",
                            label_visibility="collapsed"
                        )
                        updated_medium[rxn_id] = new_flux
                
                # Update the session state with new slider values
                st.session_state.custom_medium = updated_medium
                
                if st.button("Clear Medium", type="secondary"):
                    st.session_state.custom_medium = {}
                    st.rerun()
                
                # Run optimisation automatically when media changes
                if st.session_state.custom_medium:
                    with st.spinner("Running optimisation..."):
                        optimized_model, optimized_growth = optimize_model(model, medium=st.session_state.custom_medium, objective=selected_reaction_id, direction="max")
                        st.write(f"**Growth Rate (Growth Rate):** {optimized_growth:.4f}")
                        st.success(f"Model successfully optimized for reaction: **{selected_reaction_name}: {optimized_growth:.3f} h⁻¹**")
                        
                        # Store optimized model in session state for TRY computation
                        st.session_state.optimized_model = optimized_model.copy()
                        st.session_state.optimized_growth = optimized_growth


            curr_model, prev_model = st.tabs([
                "Current model",
                "Best model"
            ])

            # --- TAB 1: MODEL OVERVIEW ---
            with curr_model:
                # -- Benchmarking TRY --
                # Compute TRY metrics (Titer, Rate, Yield) for the optimized model
                if st.session_state.model_built and 'optimized_model' in st.session_state:
            

                    # User input for biomass concentration
                    st.subheader("📊 TRY Benchmarking Metrics")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown("**Biomass Concentration (gDW/L):**")
                    with col2:
                        st.session_state.biomass_concentration = st.slider(
                            "Biomass", 
                            min_value=0.01, 
                            max_value=50.0, 
                            value=0.5, 
                            step=0.1, 
                            format="%.2f",
                            label_visibility="collapsed"
                        )
                        
                    # Compute TRY metrics - re-optimize model to ensure correct fluxes
                    temp_model = st.session_state.optimized_model.copy()
                    temp_model.medium = st.session_state.custom_medium
                    temp_model.objective = selected_reaction_id
                    temp_model.objective_direction = "max"
                    solution = temp_model.optimize()
                    
                    yield_val, rate, titer = compute_try(
                        temp_model, 
                        selected_reaction_id, 
                        st.session_state.custom_medium, 
                        st.session_state.biomass_concentration
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Yield", 
                            f"{yield_val:.4f} mol/mol",
                            help="Product produced per substrate consumed"
                        )
                    
                    with col2:
                        st.metric(
                            "Rate", 
                            f"{rate:.4f} mmol/gDW/h",
                            help="Productivity of the cell factory"
                        )
                    
                    with col3:
                        st.metric(
                            "Titer (1h)", 
                            f"{titer:.4f} mmol/L",
                            help="Product concentration after 1 hour"
                        )
                    
                    # TRY explanation
                    with st.expander("ℹ️ About TRY Metrics"):
                        st.markdown("""
                        **TRY** metrics evaluate production costs in microbial biotechnology:
                        
                        - **Yield**: Amount of product produced per amount of substrate used (mol/mol)
                        - **Rate**: Productivity of the cell factory (mmol/gDW/h)  
                        - **Titer**: Final concentration of product in fermentation (mmol/L)
                        
                        *Reference: Konzock & Nielsen, Trends in Biotechnology, 2024*
                        """)

                    st.markdown("### **Best Recipe**")
                    # Generate minimal medium using the optimized model
                    try:
                        minimal_medium = cobra.medium.minimal_medium(temp_model, st.session_state.optimized_growth)
                        if minimal_medium is None or minimal_medium.empty:
                            st.error("Cannot generate optimized medium. Please try again.")
                            st.session_state.optimized_medium = {}
                        else:
                            st.session_state.optimized_medium = minimal_medium
                            # Convert to DataFrame and sort, then convert reaction IDs to names for display
                            optimal_df = minimal_medium.reset_index()
                            optimal_df.columns = ['Exchange Reaction', 'Flux']
                            # Convert reaction IDs to names for better display
                            optimal_df['Exchange Reaction'] = optimal_df['Exchange Reaction'].apply(
                                lambda rxn_id: model.reactions.get_by_id(rxn_id).name if rxn_id in [r.id for r in model.reactions] else rxn_id
                            )
                            optimal_df = optimal_df.sort_values(by='Flux', ascending=False)
                            st.table(optimal_df[['Exchange Reaction', 'Flux']])
                    except Exception as e:
                        st.error(f"Error generating minimal medium: {e}")
                        st.session_state.optimized_medium = {}


                    if st.button("Save as Best Model"):
                        st.session_state.prev_model = temp_model.copy()
                        st.session_state.prev_medium = st.session_state.optimized_medium.copy()
                        st.session_state.prev_growth = st.session_state.optimized_growth
                        st.rerun()
                else:
                    st.info("👈 Build and optimize a model to see TRY benchmarking metrics.")
                    
            with prev_model:
                # -- Benchmarking TRY --
                # Compute TRY metrics (Titer, Rate, Yield) for the optimized model
                if st.session_state.model_built and 'prev_model' in st.session_state:
                    
                    # Re-optimize the previous model to ensure correct fluxes
                    temp_prev_model = st.session_state.prev_model.copy()
                    temp_prev_model.medium = st.session_state.prev_medium
                    temp_prev_model.objective = selected_reaction_id
                    temp_prev_model.objective_direction = "max"
                    prev_solution = temp_prev_model.optimize()
                    
                    prev_yield, prev_rate, prev_titer = compute_try(
                        temp_prev_model, 
                        selected_reaction_id, 
                        st.session_state.prev_medium, 
                        st.session_state.biomass_concentration
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Yield", 
                            f"{prev_yield:.4f} mol/mol",
                            help="Product produced per substrate consumed"
                        )
                    
                    with col2:
                        st.metric(
                            "Rate", 
                            f"{prev_rate:.4f} mmol/gDW/h",
                            help="Productivity of the cell factory"
                        )
                    
                    with col3:
                        st.metric(
                            "Titer (1h)", 
                            f"{prev_titer:.4f} mmol/L",
                            help="Product concentration after 1 hour"
                        )
                    
                    # TRY explanation
                    with st.expander("ℹ️ About TRY Metrics"):
                        st.markdown("""
                        **TRY** metrics evaluate production costs in microbial biotechnology:
                        
                        - **Yield**: Amount of product produced per amount of substrate used (mol/mol)
                        - **Rate**: Productivity of the cell factory (mmol/gDW/h)  
                        - **Titer**: Final concentration of product in fermentation (mmol/L)
                        
                        *Reference: Konzock & Nielsen, Trends in Biotechnology, 2024*
                        """)

                    st.markdown("### **Best Recipe**")
                    
                    if st.session_state.prev_medium is None or (hasattr(st.session_state.prev_medium, 'empty') and st.session_state.prev_medium.empty):
                        st.error("No best medium available. Please save a model first.")
                    else:
                        # Convert to DataFrame and sort, then convert reaction IDs to names for display
                        prev_optimal_df = st.session_state.prev_medium.reset_index()
                        prev_optimal_df.columns = ['Exchange Reaction', 'Flux']
                        # Convert reaction IDs to names for better display
                        prev_optimal_df['Exchange Reaction'] = prev_optimal_df['Exchange Reaction'].apply(
                            lambda rxn_id: model.reactions.get_by_id(rxn_id).name if rxn_id in [r.id for r in model.reactions] else rxn_id
                        )
                        prev_optimal_df = prev_optimal_df.sort_values(by='Flux', ascending=False)
                        st.table(prev_optimal_df[['Exchange Reaction', 'Flux']])
                else:
                    st.info("👈 Build and optimize another model to see TRY benchmarking metrics of the best model.")

    else:
        if st.session_state.build_error:
            st.error(f"Last build error: {st.session_state.build_error}")
        st.info("👈 Please select a strain or upload a genome in the sidebar, then click 'Build Metabolic Model'.")

# --- TAB 2: Network visualization ---
with tab_network:
    if st.session_state.model_built:
        st.subheader("Metabolic Network Visualization")
        st.write("Explore the metabolic network around your selected reaction.")

        model = st.session_state.model
        G = cobra_to_bipartite_graph(model)

        reaction_tab, metabolite_tab = st.columns([1, 1])
        with reaction_tab:
            network_reaction_name = st.selectbox(
                "Select a reaction to visualize its local network:",
                options=[None] + [rxn.name for rxn in model.reactions],
                index=0,
                key="network_reaction_select"   
            )
        with metabolite_tab:
            network_metabolite_name = st.selectbox(
                "Or, select a metabolite to visualize its local network:",
                options=[None] + [met.name for met in model.metabolites],
                index=0,
                key="network_metabolite_select"   
            )


        k = st.number_input("Select a distance to explore", min_value=0, max_value=10, value=2, step=1)

        if network_reaction_name or network_metabolite_name:
            if network_reaction_name:
                center_node = next((rxn.id for rxn in model.reactions if rxn.name == network_reaction_name), None)
            else:
                center_node = next((met.id for met in model.metabolites if met.name == network_metabolite_name), None)

            st.write(f"Selected node: {center_node}")
            subgraph = extract_k_hop_subgraph(G, center_node, k=k)
            show_graph(subgraph)
        else:
            st.info("Select a reaction or metabolite from the dropdown in the Model Overview tab to visualize its local network.")
    else:
        st.info("👈 Build a model in the sidebar and select a reaction in the Model Overview tab to visualize the metabolic network.")

# --- TAB 2: MEDIA OPTIMIZER ---
# with tab_optimizer:
#     if st.session_state.model_built:
#         st.subheader("Interactive Media Formulation")
#         st.write("Adjust glucose uptake. Growth and sensitivity update automatically.")

#         glucose_uptake = st.slider(
#             "Glucose uptake limit (EX_glc__D_e, mmol/gDW/h)",
#             min_value=0.0,
#             max_value=20.0,
#             value=10.0,
#             step=0.5,
#             help="Higher values allow more glucose import. Internal model lower bound is set to the negative of this value."
#         )

#         new_solution = run_fba_simulation(
#             st.session_state.model,
#             {"EX_glc__D_e": -glucose_uptake}
#         )
#         st.session_state.last_solution = new_solution
#         sensitivity_max = max(2, int(glucose_uptake * 2))
#         st.session_state.sensitivity_df = get_sensitivity_data(
#             st.session_state.model,
#             "EX_glc__D_e",
#             max_flux=sensitivity_max,
#             step=2
#         )

#         current_solution = st.session_state.last_solution
#         if current_solution is not None and getattr(current_solution, "status", "") == "optimal":
#             st.metric("Current Predicted Growth", f"{float(current_solution.objective_value):.3f} h⁻¹")
#         else:
#             st.warning("No optimal solution found for current media setup.")

#         st.subheader("Sensitivity Scan (Glucose)")
#         sensitivity_fig = plot_sensitivity(st.session_state.sensitivity_df, "Glucose")
#         st.plotly_chart(sensitivity_fig, use_container_width=True)
#     else:
#         st.warning("You must build a model first to unlock the Media Optimizer.")

# --- TAB 3: FINAL REPORT ---
with tab_report:
    if st.session_state.model_built:
        st.subheader("Download Inital GEM")
        with open(st.session_state.model_file, "r") as f:
            st.download_button(
                label="Download GEM",
                data=f,
                file_name="GEM.xml",
                mime="text/plain"
            )
    else:
        st.warning("Generate a model and tune your media to unlock the Final Report.")


    if 'prev_model' in st.session_state and st.session_state.prev_model is not None:
        st.subheader("Download Optimized GEM")
        best_model_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        best_model_filename = best_model_file.name  # get the filename
        best_model_file.close() 
        write_sbml_model(st.session_state.prev_model, best_model_filename)

        with open(best_model_filename, "r") as f:
            st.download_button(
                label="Download Optimized GEM",
                data=f,
                file_name="Optimized_GEM.xml",
                mime="text/plain"
            )
