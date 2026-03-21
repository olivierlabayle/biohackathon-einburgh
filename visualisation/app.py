import cobra
import streamlit as st
import os
from cobra.io import read_sbml_model
import time
import pandas as pd
from build_model import create_carve_model
from model_engine import load_fungal_model, run_fba_simulation, get_sensitivity_data
from visuals import plot_growth_bar, plot_sensitivity
from optimise import run_optimization, optimize_model
from media import MEDIA


MODEL_DIR = "/app/data/models"
FASTA_DIR = "/app/data/fastas"

os.path.isdir(MODEL_DIR) or os.makedirs(MODEL_DIR)
os.path.isdir(FASTA_DIR) or os.makedirs(FASTA_DIR)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="BioOptimize: Fungi Edition",
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

# --- SIDEBAR: CONFIGURATION ---
with st.sidebar:
    st.title("🍄 BioOptimize Fungi")
    st.markdown("Automated GEM Generation & Media Optimization")
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
                "GCF_000182925.2"
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
        else:
            st.info("Please upload a file to proceed.")


    st.divider()

    st.subheader("2. Run Pipeline")
    if st.button("🚀 Build Metabolic Model"):
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

                baseline_solution = model.optimize()
                st.session_state.model = model
                st.session_state.last_solution = baseline_solution
                st.session_state.sensitivity_df = get_sensitivity_data(model, "EX_glc__D_e")
                st.session_state.model_built = True
                st.session_state.build_error = None
                st.success("Model loaded and baseline simulation completed.")
            except Exception as exc:
                st.session_state.model_built = False
                st.session_state.model = None
                st.session_state.last_solution = None
                st.session_state.sensitivity_df = pd.DataFrame()
                st.session_state.build_error = str(exc)
                st.error(f"Model build failed: {exc}")

# --- MAIN DASHBOARD ---
st.title("Media Optimization Workspace")
st.markdown("""
**Welcome to BioOptimize.** Genome-Scale Metabolic Models (GEMs) act like a digital twin of your microbe.
By mapping out every metabolic reaction, we can computationally predict which nutrients will boost growth or target production—saving you weeks of trial-and-error in the wet lab.
""")

# --- TABS ---
tab_overview, tab_optimizer, tab_report = st.tabs([
    "📊 Model Overview",
    "🧪 Media Optimizer",
    "📝 Final Report"
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
        col1, col2 = st.columns(2)
        with col1:
            selected_reaction_name = st.selectbox("Select a reaction to optimize:", options=[None] + [rxn.name for rxn in model.reactions], index=0, key="reaction_select")
        with col2:
            selected_minimal_growth_rate = st.number_input("Minimum growth rate constraint (h⁻¹)", min_value=0.0, max_value=2.0, value=0.7,help="Set a minimum growth rate to ensure viability while optimizing for the selected reaction.")

        # Find the minimum media for the selected reaction and growth rate
        if selected_reaction_name and selected_minimal_growth_rate:
            selected_reaction_id = next(rxn.id for rxn in model.reactions if rxn.name == selected_reaction_name)
            selected_reaction = model.reactions.get_by_id(selected_reaction_id)
            st.write(f"**Reaction ID:** {selected_reaction.id}")
            st.write(f"**Equation:** {selected_reaction.build_reaction_string()}")
            st.write(f"**Associated Genes:** {', '.join(gene.id for gene in selected_reaction.genes) if selected_reaction.genes else 'None'}")
            
            minimum_medium = cobra.medium.minimal_medium(model, selected_minimal_growth_rate)

            st.dataframe(minimum_medium)

            st.success(f"Model successfully optmized for reaction: **{selected_reaction_name}: {growth_rate:.3f} h⁻¹**")
        
            st.plotly_chart(plot_growth_bar(growth_rate), use_container_width=True)

        st.subheader("Network Confidence")
        st.write("Overview of key exchange reactions available in the reconstructed model.")

        exchange_reactions = [rxn.id for rxn in model.exchanges]
        exchange_df = pd.DataFrame({"Exchange Reactions": exchange_reactions})
        st.dataframe(exchange_df, use_container_width=True)


    else:
        if st.session_state.build_error:
            st.error(f"Last build error: {st.session_state.build_error}")
        st.info("👈 Please select a strain or upload a genome in the sidebar, then click 'Build Metabolic Model'.")

# --- TAB 2: MEDIA OPTIMIZER (Placeholder for Phase 3) ---
with tab_optimizer:
    if st.session_state.model_built:
        st.subheader("Interactive Media Formulation")
        st.write("Adjust glucose uptake. Growth and sensitivity update automatically.")

        glucose_uptake = st.slider(
            "Glucose uptake limit (EX_glc__D_e, mmol/gDW/h)",
            min_value=0.0,
            max_value=20.0,
            value=10.0,
            step=0.5,
            help="Higher values allow more glucose import. Internal model lower bound is set to the negative of this value."
        )

        new_solution = run_fba_simulation(
            st.session_state.model,
            {"EX_glc__D_e": -glucose_uptake}
        )
        st.session_state.last_solution = new_solution
        sensitivity_max = max(2, int(glucose_uptake * 2))
        st.session_state.sensitivity_df = get_sensitivity_data(
            st.session_state.model,
            "EX_glc__D_e",
            max_flux=sensitivity_max,
            step=2
        )

        current_solution = st.session_state.last_solution
        if current_solution is not None and getattr(current_solution, "status", "") == "optimal":
            st.metric("Current Predicted Growth", f"{float(current_solution.objective_value):.3f} h⁻¹")
        else:
            st.warning("No optimal solution found for current media setup.")

        st.subheader("Sensitivity Scan (Glucose)")
        sensitivity_fig = plot_sensitivity(st.session_state.sensitivity_df, "Glucose")
        st.plotly_chart(sensitivity_fig, use_container_width=True)
    else:
        st.warning("You must build a model first to unlock the Media Optimizer.")

# --- TAB 3: FINAL REPORT (Placeholder for Phase 4) ---
with tab_report:
    if st.session_state.model_built:
        st.subheader("Optimization Summary Report")
        st.write("A plain-english summary of the optimal media conditions will appear here once you finish tuning in the Optimizer tab.")
    else:
        st.warning("Generate a model and tune your media to unlock the Final Report.")