import time

import pandas as pd
import streamlit as st

from genome_validate import validate_protein_fasta_bytes
from model_engine import (
    get_sensitivity_data,
    load_model_from_gem_upload,
    load_template_model,
    run_fba_simulation,
)
from ncbi_client import search_assemblies
from strains import LIBRARY_LABELS, strain_by_label
from visuals import plot_growth_bar, plot_sensitivity


def _init_state():
    defaults = {
        "model_built": False,
        "model_obj": None,
        "last_solution": None,
        "sensitivity_df": pd.DataFrame(),
        "build_error": None,
        "display_label": "",
        "model_source": None,
        "ncbi_hits": [],
        "protein_fasta_ok": False,
        "protein_fasta_meta": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _fail_build(msg: str):
    st.session_state.model_built = False
    st.session_state.model_obj = None
    st.session_state.last_solution = None
    st.session_state.sensitivity_df = pd.DataFrame()
    st.session_state.build_error = msg
    st.session_state.model_source = None


def _set_sensitivity_or_empty(model):
    if model.reactions.has_id("EX_glc__D_e"):
        st.session_state.sensitivity_df = get_sensitivity_data(model, "EX_glc__D_e")
    else:
        st.session_state.sensitivity_df = pd.DataFrame()


def _run_template_pipeline(label: str):
    with st.spinner(f"Running placeholder GEM pipeline for {label[:60]}..."):
        time.sleep(1.0)
        model = load_template_model(label)
        sol = run_fba_simulation(model, {})
        st.session_state.model_obj = model
        st.session_state.last_solution = sol
        st.session_state.model_source = "template"
        st.session_state.display_label = label
        _set_sensitivity_or_empty(model)
        st.session_state.model_built = True
        st.session_state.build_error = None


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GEMtimise",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remote logo (black artwork); inverted in dark mode for white-on-black.
_HEADER_LOGO_URL = (
    "https://www.ingredientsnetwork.com/COLOR%20LOGO-BLACK-comp324183.png"
)


def _theme_css(theme: str) -> str:
    is_dark = theme == "dark"
    bg = "#000000" if is_dark else "#ffffff"
    surface = "#111111" if is_dark else "#f5f5f5"
    border = "#333333" if is_dark else "#d4d4d4"
    text = "#ffffff" if is_dark else "#000000"
    logo_filter = "invert(1)" if is_dark else "none"
    return f"""
<style>
    :root {{
        --gem-bg: {bg};
        --gem-surface: {surface};
        --gem-text: {text};
        --gem-orange: #f97316;
        --gem-border: {border};
        --fs-section-title: 1.725rem;
        --fs-base: 1.4025rem;
        --fs-caption: 1.254rem;
        --fs-tagline: 1.452rem;
        --fs-accent: 1.452rem;
        --fs-brand: clamp(3.9rem, 7.8vw, 5.07rem);
    }}
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        background-color: var(--gem-bg) !important;
        color: var(--gem-text) !important;
    }}
    .main .block-container {{
        padding-top: 2rem;
        padding-left: 8% !important;
        padding-right: 8% !important;
        color: var(--gem-text);
        font-size: var(--fs-base);
        line-height: 1.5;
    }}
    .main .block-container h1, .main .block-container h2, .main .block-container h3, .main .block-container h4 {{
        font-size: var(--fs-section-title) !important;
        line-height: 1.3 !important;
        font-weight: 600 !important;
        color: var(--gem-text) !important;
    }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ background-color: var(--gem-bg) !important; }}
    header[data-testid="stHeader"] button {{
        color: var(--gem-text) !important;
    }}
    .main .block-container strong {{ color: var(--gem-text) !important; }}
    .main .block-container .stMarkdown, .main .block-container label,
    .main .block-container p:not(.brand-title):not(.tagline):not(.drag-hint-text) {{
        color: var(--gem-text) !important;
    }}
    .main .block-container a {{ color: var(--gem-orange) !important; }}
    .stCaption, [data-testid="stCaption"] {{
        color: var(--gem-text) !important;
        font-size: var(--fs-caption) !important;
    }}
    .stMetric {{
        background-color: var(--gem-surface) !important;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid var(--gem-border);
        box-shadow: none;
        font-size: var(--fs-base) !important;
        color: var(--gem-text) !important;
    }}
    [data-testid="stMetric"] label, [data-testid="stMetric"] [data-testid="stMarkdownContainer"] p {{
        color: var(--gem-text) !important;
    }}
    .stButton > button {{
        width: 100%;
        border-radius: 8px;
        min-height: 2.75rem;
        font-weight: 600;
        font-size: var(--fs-base) !important;
        background-color: var(--gem-surface) !important;
        color: var(--gem-text) !important;
        border: 1px solid var(--gem-border) !important;
    }}
    .stButton > button:hover {{
        border-color: var(--gem-orange) !important;
        color: var(--gem-text) !important;
    }}
    .header-banner {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem 0 1.5rem;
        min-height: 12vh;
    }}
    .header-logo {{
        max-height: 110px;
        width: auto;
        height: auto;
        display: block;
        filter: {logo_filter};
    }}
    .brand-title {{
        font-family: inherit;
        font-size: clamp(5rem, 10vw, 7rem);
        font-weight: 700;
        text-align: center;
        margin: 0.5rem 0 0.5rem 0;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }}
    .brand-title .gem {{ color: var(--gem-orange) !important; }}
    .brand-title .timise {{ color: var(--gem-text) !important; }}
    .tagline {{
        text-align: center;
        color: var(--gem-text) !important;
        margin: 0 0 2rem 0;
        font-size: clamp(1.4rem, 2.8vw, 2rem);
        font-weight: 500;
        line-height: 1.45;
    }}
    .drag-hint-text {{
        text-align: center;
        color: var(--gem-orange) !important;
        font-size: var(--fs-accent);
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: 0.02em;
    }}
    section[data-testid="stFileUploader"] label p {{
        font-size: var(--fs-accent) !important;
        font-weight: 700 !important;
        color: var(--gem-text) !important;
    }}
    [data-baseweb="radio"] label, [data-baseweb="select"] label {{ color: var(--gem-text) !important; }}
    div[data-baseweb="select"] > div {{
        background-color: var(--gem-surface) !important;
        border-color: var(--gem-border) !important;
        color: var(--gem-text) !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{ background-color: transparent !important; gap: 0.5rem; }}
    .stTabs [data-baseweb="tab"] {{ color: var(--gem-text) !important; font-size: var(--fs-base) !important; }}
    .stTabs [aria-selected="true"] {{ color: var(--gem-orange) !important; border-bottom-color: var(--gem-orange) !important; }}
    [data-testid="stExpander"] {{ background-color: var(--gem-surface); border: 1px solid var(--gem-border); border-radius: 8px; }}
    [data-testid="stAlert"] {{
        background-color: var(--gem-surface) !important;
        color: var(--gem-text) !important;
        border: 1px solid var(--gem-border) !important;
    }}
    [data-testid="stAlert"] p, [data-testid="stAlert"] div, [data-testid="stAlert"] span {{
        color: var(--gem-text) !important;
    }}
    [data-testid="stAlert"][data-baseweb="notification"] {{ border-left-width: 4px !important; }}
    div[data-testid="stSuccessNotification"] {{ border-left-color: #22c55e !important; }}
    div[data-testid="stErrorNotification"] {{ border-left-color: #ef4444 !important; }}
    div[data-testid="stWarningNotification"] {{ border-left-color: var(--gem-orange) !important; }}
    div[data-testid="stInfoNotification"] {{ border-left-color: #38bdf8 !important; }}

    /* Force all text strictly white (dark) / black (light) — no grey */
    .stApp, .stApp *, [data-testid="stAppViewContainer"] *,
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stText, label, p, span, div, li, td, th {{
        color: var(--gem-text) !important;
    }}
    /* Orange stays orange in both modes */
    .gem, .brand-title .gem,
    .stTabs [aria-selected="true"],
    .drag-hint-text,
    .stApp a {{ color: var(--gem-orange) !important; }}

    /* FIX 1: Radio dot orange — NO background highlight on selected label */
    /* Remove any background/highlight Streamlit adds to selected radio option */
    [data-baseweb="radio"] [aria-checked="true"],
    [data-baseweb="radio"] [role="radio"][aria-checked="true"],
    [data-baseweb="radio"] [aria-checked="true"] > div:first-child {{
        background-color: transparent !important;
        box-shadow: none !important;
    }}
    /* Orange outer ring on checked radio */
    [data-baseweb="radio"] [aria-checked="true"] div[class] {{
        border-color: var(--gem-orange) !important;
    }}
    /* Orange filled inner dot */
    [data-baseweb="radio"] [aria-checked="true"] div[class] > div,
    [data-baseweb="radio"] input:checked ~ div div div {{
        background-color: var(--gem-orange) !important;
    }}
    /* SVG circle fill for baseweb radio */
    [data-baseweb="radio"] [aria-checked="true"] svg circle {{
        fill: var(--gem-orange) !important;
        stroke: var(--gem-orange) !important;
    }}

    /* FIX 2: Horizontal rule (st.markdown "---") — white in dark mode, grey in light */
    hr {{
        border: none !important;
        border-top: 1.5px solid {("#ffffff" if is_dark else "#cccccc")} !important;
        opacity: 1 !important;
        margin: 1rem 0 !important;
    }}

    /* Run GEM Engine primary button — solid orange always */
    button[data-testid="baseButton-primary"],
    button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
        background-color: var(--gem-orange) !important;
        color: #0a0a0a !important;
        border: none !important;
        box-shadow: 0 4px 24px rgba(249, 115, 22, 0.35) !important;
        min-height: 3.25rem !important;
        font-size: var(--fs-accent) !important;
        font-weight: 700 !important;
    }}
    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {{
        background-color: #ea580c !important;
        color: #0a0a0a !important;
    }}
    button[data-testid="baseButton-primary"] *,
    button[data-testid="baseButton-primary"] p {{
        color: #0a0a0a !important;
    }}

    /* FIX 3: Theme toggle — fixed top-RIGHT */
    div[data-testid="stRadio"]:has(input[name="display_mode"]) {{
        position: fixed !important;
        top: 0.55rem !important;
        right: 1.5rem !important;
        left: auto !important;
        z-index: 9999 !important;
        background: transparent !important;
        width: auto !important;
    }}
    div[data-testid="stRadio"]:has(input[name="display_mode"]) label,
    div[data-testid="stRadio"]:has(input[name="display_mode"]) p {{
        font-size: 1.35rem !important;
    }}

    /* FIX 4: Bigger header section — logo, brand title, tagline */
    .header-banner {{
        padding: 2rem 0 1.5rem !important;
        min-height: 12vh;
    }}
    .header-logo {{
        max-height: 110px !important;
        width: auto !important;
    }}
    .brand-title {{
        font-size: clamp(5rem, 10vw, 7rem) !important;
        margin: 0.5rem 0 0.5rem 0 !important;
        letter-spacing: -0.03em;
        line-height: 1.1 !important;
    }}
    .tagline {{
        font-size: clamp(1.4rem, 2.8vw, 2rem) !important;
        margin: 0 0 2rem 0 !important;
        font-weight: 500 !important;
    }}
</style>
"""


_init_state()

_mode = st.radio("🌙 / ☀️", ["🌙", "☀️"], horizontal=True, key="display_mode", label_visibility="collapsed")
_ui_theme = "dark" if _mode == "🌙" else "light"
st.markdown(_theme_css(_ui_theme), unsafe_allow_html=True)
# --- Header banner (logo inverted for dark background; URL may change over time) ---
st.markdown(
    f'<div class="header-banner"><img src="{_HEADER_LOGO_URL}" alt="Brand logo" class="header-logo" loading="lazy" /></div>',
    unsafe_allow_html=True,
)

# --- MAIN: centered input panel ---
st.markdown(
    '<p class="brand-title"><span class="gem">GEM</span><span class="timise">timise</span></p>'
    '<p class="tagline">Automated GEM generation and media optimization</p>',
    unsafe_allow_html=True,
)

st.subheader("Configure input")
st.markdown("---")

input_mode = st.radio(
    "Choose input source",
    ["Genome (protein FASTA)", "Upload GEM model"],
    help="Library / NCBI search / custom protein FASTA, or load your own SBML/JSON GEM.",
    horizontal=True,
)

selected_label = "Not selected"
gem_file = None
protein_file = None
ncbi_selected = None
genome_submode = "Library strain"

if input_mode == "Genome (protein FASTA)":
    genome_submode = st.radio(
        "Genome source",
        ["Library strain", "Search NCBI", "Custom protein FASTA"],
        help="Library: curated strains. NCBI: assembly search. Custom: your protein FASTA.",
        horizontal=True,
    )

    if genome_submode == "Library strain":
        choice = st.selectbox(
            "Select a fungal strain",
            LIBRARY_LABELS,
            key="library_strain_choice",
        )
        meta = strain_by_label(choice)
        selected_label = meta["label"]
        st.markdown(f"**NCBI:** [Open assembly record]({meta['ncbi_url']})")
        st.caption(f"Short name: {meta['short']}")

    elif genome_submode == "Search NCBI":
        q = st.text_input(
            "Search genome / assembly name",
            placeholder="e.g. Aspergillus nidulans",
            help="NCBI Entrez `assembly` database. Set NCBI_EMAIL in secrets for compliance.",
        )
        if st.button("Search NCBI"):
            try:
                st.session_state.ncbi_hits = search_assemblies(q)
                if not st.session_state.ncbi_hits:
                    st.warning("No assemblies found. Try different keywords.")
            except Exception as exc:
                st.error(f"NCBI search failed: {exc}")
                st.session_state.ncbi_hits = []

        hits = st.session_state.ncbi_hits or []
        if hits:
            options = [h["display"] for h in hits]
            pick = st.selectbox("Select a result", options, key="ncbi_pick")
            idx = options.index(pick)
            ncbi_selected = hits[idx]
            selected_label = ncbi_selected["display"]
        else:
            selected_label = "Search NCBI (no selection yet)"

    else:
        st.caption(
            "Upload **one** protein sequence FASTA (e.g. `.faa`, `.fa`). Not for raw DNA FASTA."
        )
        try:
            upload_box = st.container(border=True)
        except TypeError:
            upload_box = st.container()
        with upload_box:
            st.markdown(
                '<p class="drag-hint-text">Drag your genome file here</p>',
                unsafe_allow_html=True,
            )
            protein_file = st.file_uploader(
                "Upload your genome",
                type=["faa", "fasta", "fa", "fas"],
                accept_multiple_files=False,
                help="Protein FASTA — single file. Drag and drop supported.",
                key="genome_fasta_uploader",
            )

        if protein_file is not None:
            data = protein_file.getvalue()
            check = validate_protein_fasta_bytes(data)
            st.session_state.protein_fasta_ok = check.ok
            st.session_state.protein_fasta_meta = check
            if check.ok:
                st.success(
                    f"Valid protein FASTA: {check.record_count} record(s), "
                    f"{check.total_aa:,} residues."
                )
                selected_label = protein_file.name
            else:
                st.error(check.message)
                selected_label = protein_file.name
        else:
            st.session_state.protein_fasta_ok = False
            st.session_state.protein_fasta_meta = None
            selected_label = "Custom protein FASTA (no file yet)"

else:
    st.caption("Standard formats: **SBML** (`.xml`, `.sbml`) or **COBRA JSON** (`.json`).")
    gem_file = st.file_uploader(
        "Upload GEM (SBML / JSON)",
        type=["xml", "sbml", "json"],
        accept_multiple_files=False,
    )
    if gem_file:
        selected_label = gem_file.name
    else:
        selected_label = "GEM upload (no file yet)"

st.markdown("---")
st.markdown("**GEM engine**")
if st.button("Run GEM engine", type="primary", use_container_width=True):
    if input_mode == "Upload GEM model":
        if not gem_file:
            st.error("Please upload a SBML or JSON model first.")
        else:
            with st.spinner("Loading your GEM..."):
                time.sleep(0.2)
                try:
                    model = load_model_from_gem_upload(gem_file)
                    sol = run_fba_simulation(model, {})
                    st.session_state.model_obj = model
                    st.session_state.last_solution = sol
                    st.session_state.model_source = "user_gem"
                    st.session_state.display_label = gem_file.name
                    _set_sensitivity_or_empty(model)
                    st.session_state.model_built = True
                    st.session_state.build_error = None
                    st.success("GEM loaded and baseline FBA completed.")
                except Exception as exc:
                    _fail_build(str(exc))
                    st.error(f"GEM engine failed: {exc}")

    elif genome_submode == "Custom protein FASTA":
        if not protein_file:
            st.error("Please upload a protein FASTA file.")
        elif not st.session_state.protein_fasta_ok:
            st.error("Protein FASTA validation failed. Fix the file and try again.")
        else:
            try:
                _run_template_pipeline(f"{protein_file.name} (protein FASTA)")
                st.success("Model loaded (demo network) and baseline FBA completed.")
            except Exception as exc:
                _fail_build(str(exc))
                st.error(f"GEM engine failed: {exc}")

    elif genome_submode == "Search NCBI":
        if not st.session_state.ncbi_hits or ncbi_selected is None:
            st.error("Search NCBI and select an assembly first.")
        else:
            try:
                _run_template_pipeline(ncbi_selected["display"])
                st.success("Model loaded (demo network) and baseline FBA completed.")
            except Exception as exc:
                _fail_build(str(exc))
                st.error(f"GEM engine failed: {exc}")

    else:
        choice = st.session_state.get("library_strain_choice", LIBRARY_LABELS[0])
        meta = strain_by_label(choice)
        try:
            _run_template_pipeline(meta["label"])
            st.success("Model loaded (demo network) and baseline FBA completed.")
        except Exception as exc:
            _fail_build(str(exc))
            st.error(f"GEM engine failed: {exc}")

# --- MAIN DASHBOARD (below input) ---
st.markdown("---")
st.subheader("Media Optimization Workspace")
st.markdown(
    """
**Welcome to GEMtimise.** Genome-Scale Metabolic Models (GEMs) act like a digital twin of your microbe.
By mapping out every metabolic reaction, we can computationally predict which nutrients will boost growth or target production.
"""
)

label_for_ui = (
    st.session_state.display_label if st.session_state.model_built else selected_label
)

tab_overview, tab_optimizer, tab_report = st.tabs(
    ["📊 Model Overview", "🧪 Media Optimizer", "📝 Final Report"]
)

with tab_overview:
    if st.session_state.model_built:
        st.success(f"Metabolic Model successfully generated for: **{label_for_ui}**")
        if st.session_state.model_source == "template":
            st.caption("Demo network: full reconstruction from protein FASTA is not implemented yet.")

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
        st.plotly_chart(
            plot_growth_bar(growth_rate, theme=_ui_theme), use_container_width=True
        )

        st.subheader("Network Confidence")
        st.write("Overview of key exchange reactions available in the model.")

        exchange_reactions = [rxn.id for rxn in model.exchanges[:12]]
        exchange_df = pd.DataFrame({"Exchange Reactions (sample)": exchange_reactions})
        st.dataframe(exchange_df, use_container_width=True)

    else:
        if st.session_state.build_error:
            st.error(f"Last build error: {st.session_state.build_error}")
        st.info("Configure input above and click **Run GEM engine**.")

with tab_optimizer:
    if st.session_state.model_built:
        model = st.session_state.model_obj
        if not model.reactions.has_id("EX_glc__D_e"):
            st.warning(
                "This model has no `EX_glc__D_e` exchange reaction. "
                "Glucose slider is disabled for this GEM."
            )
        else:
            st.subheader("Interactive Media Formulation")
            st.write("Adjust glucose uptake. Growth and sensitivity update automatically.")

            glucose_uptake = st.slider(
                "Glucose uptake limit (EX_glc__D_e, mmol/gDW/h)",
                min_value=0.0,
                max_value=20.0,
                value=10.0,
                step=0.5,
            )

            new_solution = run_fba_simulation(
                st.session_state.model_obj,
                {"EX_glc__D_e": -glucose_uptake},
            )
            st.session_state.last_solution = new_solution
            sensitivity_max = max(2, int(glucose_uptake * 2))
            st.session_state.sensitivity_df = get_sensitivity_data(
                st.session_state.model_obj,
                "EX_glc__D_e",
                max_flux=sensitivity_max,
                step=2,
            )

            current_solution = st.session_state.last_solution
            if current_solution is not None and getattr(current_solution, "status", "") == "optimal":
                st.metric("Current Predicted Growth", f"{float(current_solution.objective_value):.3f} h⁻¹")
            else:
                st.warning("No optimal solution found for current media setup.")

            st.subheader("Sensitivity Scan (Glucose)")
            if not st.session_state.sensitivity_df.empty:
                sensitivity_fig = plot_sensitivity(
                    st.session_state.sensitivity_df, "Glucose", theme=_ui_theme
                )
                st.plotly_chart(sensitivity_fig, use_container_width=True)
    else:
        st.warning("You must run the GEM engine first to unlock the Media Optimizer.")

with tab_report:
    if st.session_state.model_built:
        st.subheader("Optimization Summary Report")
        st.write(
            "A plain-english summary of the optimal media conditions will appear here "
            "once you finish tuning in the Optimizer tab."
        )
    else:
        st.warning("Generate a model and tune your media to unlock the Final Report.")