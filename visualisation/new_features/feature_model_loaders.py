"""
feature_model_loaders.py
------------------------
Updated GEM pipeline helpers that power the enhanced "Run GEM engine" button.

These replace / extend the simple `create_carve_model` + `load_fungal_model`
calls in code1.py / code2.py with three new loading paths:

  load_from_gem_upload()   — loads a user-supplied SBML/JSON COBRA model
  run_template_pipeline()  — placeholder reconstruction from a label string
                             (used for library strain, NCBI hit, protein FASTA)

HOW TO INTEGRATE into code1.py (app):
  1. Import:
        from feature_model_loaders import run_template_pipeline, load_from_gem_upload
  2. In your "Run GEM engine" button handler, replace the existing try/except block
     with the appropriate call:

        # For library strain / NCBI / protein FASTA:
        run_template_pipeline(label_string)

        # For uploaded GEM:
        load_from_gem_upload(uploaded_file_object)

     Both functions write directly into st.session_state and call st.spinner /
     st.error internally, so no extra wrapping is needed.

Dependencies (must be importable):
    streamlit, model_engine (gem_io transitively), pandas
"""

from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from model_engine import (
    get_sensitivity_data,
    load_model_from_gem_upload,
    load_template_model,
    run_fba_simulation,
)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _set_sensitivity_or_empty(model) -> None:
    """Populate sensitivity_df if EX_glc__D_e exists, else store empty DF."""
    if model.reactions.has_id("EX_glc__D_e"):
        st.session_state.sensitivity_df = get_sensitivity_data(model, "EX_glc__D_e")
    else:
        st.session_state.sensitivity_df = pd.DataFrame()


def _fail_build(msg: str) -> None:
    """Reset all model-related session state and record the error."""
    st.session_state.model_built = False
    st.session_state.model_obj = None
    st.session_state.last_solution = None
    st.session_state.sensitivity_df = pd.DataFrame()
    st.session_state.build_error = msg
    st.session_state.model_source = None


# ── Public API ────────────────────────────────────────────────────────────────

def run_template_pipeline(label: str) -> None:
    """
    Loads the COBRApy textbook demo network and tags it with `label`.
    Used for: library strain, NCBI assembly hit, custom protein FASTA.

    Writes into st.session_state:
        model_obj, last_solution, sensitivity_df, model_built,
        model_source ('template'), display_label, build_error
    """
    with st.spinner(f"Running GEM pipeline for {label[:60]}..."):
        time.sleep(1.0)
        try:
            model = load_template_model(label)
            sol = run_fba_simulation(model, {})
            st.session_state.model_obj = model
            st.session_state.last_solution = sol
            st.session_state.model_source = "template"
            st.session_state.display_label = label
            _set_sensitivity_or_empty(model)
            st.session_state.model_built = True
            st.session_state.build_error = None
        except Exception as exc:
            _fail_build(str(exc))
            st.error(f"GEM engine failed: {exc}")


def load_from_gem_upload(uploaded_file) -> None:
    """
    Loads a user-provided SBML/XML or COBRA JSON model.

    Writes into st.session_state:
        model_obj, last_solution, sensitivity_df, model_built,
        model_source ('user_gem'), display_label, build_error
    """
    with st.spinner("Loading your GEM..."):
        time.sleep(0.2)
        try:
            model = load_model_from_gem_upload(uploaded_file)
            sol = run_fba_simulation(model, {})
            st.session_state.model_obj = model
            st.session_state.last_solution = sol
            st.session_state.model_source = "user_gem"
            st.session_state.display_label = uploaded_file.name
            _set_sensitivity_or_empty(model)
            st.session_state.model_built = True
            st.session_state.build_error = None
        except Exception as exc:
            _fail_build(str(exc))
            st.error(f"GEM engine failed: {exc}")
