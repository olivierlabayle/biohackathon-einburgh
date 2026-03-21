import streamlit as st
import os
from cobra.io import read_sbml_model
import time
import pandas as pd
from build_model import create_carve_model
from model_engine import load_fungal_model, run_fba_simulation, get_sensitivity_data
from visuals import plot_growth_bar, plot_sensitivity

MODEL_DIR = "/app/data/models"
FASTA_DIR = "/app/data/fastas"

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
if 'model_obj' not in st.session_state:
    st.session_state.model_obj = None
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
        st.success(f"Ready to load: **{selected_strain_name.split(' ')[0]}**")

    else:
        st.info("Don't have a genome? You can search and download one from [FungiDB](https://fungidb.org/fungidb/app/search/genomic-sequence/SequencesByTaxon).")

        genome_file = st.file_uploader(
            "Upload Genome (Required)",
            type=["fasta", "gbk", "fna"],
            help="Drag and drop your .fasta or .gbk file here."
        )

        annotation_file = st.file_uploader(
            "Upload Annotation (Optional)",
            type=["gff", "tsv"],
            help="Adding gene annotations (.gff) greatly improves the metabolic model's accuracy."
        )

        if genome_file:
            selected_strain_name = genome_file.name

    st.divider()

    st.subheader("2. Run Pipeline")
    if st.button("🚀 Build Metabolic Model"):
        if input_method == "Custom Upload" and not genome_file:
            st.error("Please upload a genome file first!")
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
                        model = create_carve_model(selected_strain_name, model_file)

                    baseline_solution = run_fba_simulation(model, {})
                    st.session_state.model_obj = model
                    st.session_state.last_solution = baseline_solution
                    st.session_state.sensitivity_df = get_sensitivity_data(model, "EX_glc__D_e")
                    st.session_state.model_built = True
                    st.session_state.build_error = None
                    st.success("Model loaded and baseline simulation completed.")
                except Exception as exc:
                    st.session_state.model_built = False
                    st.session_state.model_obj = None
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

        model = st.session_state.model_obj
        solution = st.session_state.last_solution
        growth_rate = 0.0
        if solution is not None and getattr(solution, "status", "") == "optimal":
            growth_rate = float(solution.objective_value)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Metabolic Reactions", f"{len(model.reactions):,}")
        col2.metric("Metabolites", f"{len(model.metabolites):,}")
        col3.metric("Genes Mapped", f"{len(model.genes):,}")
        col4.metric("Predicted Max Growth", f"{growth_rate:.3f} h⁻¹", "Baseline Media")
        st.plotly_chart(plot_growth_bar(growth_rate), use_container_width=True)

        st.subheader("Network Confidence")
        st.write("Overview of key exchange reactions available in the reconstructed model.")

        exchange_reactions = [rxn.id for rxn in model.exchanges[:12]]
        exchange_df = pd.DataFrame({"Exchange Reactions (sample)": exchange_reactions})
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
            st.session_state.model_obj,
            {"EX_glc__D_e": -glucose_uptake}
        )
        st.session_state.last_solution = new_solution
        sensitivity_max = max(2, int(glucose_uptake * 2))
        st.session_state.sensitivity_df = get_sensitivity_data(
            st.session_state.model_obj,
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