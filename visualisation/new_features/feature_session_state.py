"""
feature_session_state.py
------------------------
Centralised session-state initialisation for BioOptimize / GEMtimise.

The enhanced app.py adds several new keys beyond the four used in code1.py.
This module provides a single _init_state() call that sets all of them safely.

HOW TO INTEGRATE into code1.py (app):
  1. Import at top:
        from feature_session_state import init_state
  2. Call once, before any other UI code:
        init_state()
  3. Remove the existing manual session-state block in code1.py:
        # (the block that assigns st.session_state.model_built etc.)

Original keys (code1.py):
    model_built, model_obj, last_solution, sensitivity_df, build_error

New keys added by the enhanced app:
    display_label      — human-readable name shown in UI after build
    model_source       — 'template' | 'user_gem' | None
    ncbi_hits          — list of dicts returned by ncbi_client.search_assemblies
    protein_fasta_ok   — bool: last protein FASTA passed validation
    protein_fasta_meta — ProteinFastaValidation dataclass or None
"""

import pandas as pd
import streamlit as st


def init_state() -> None:
    """
    Safely initialise all session-state keys used by the app.
    Call this once at the very start of your Streamlit script.
    """
    defaults = {
        # ── Original keys (code1.py) ──────────────────────────────────────
        "model_built": False,
        "model_obj": None,
        "last_solution": None,
        "sensitivity_df": pd.DataFrame(),
        "build_error": None,
        # ── New keys (enhanced app) ───────────────────────────────────────
        "display_label": "",
        "model_source": None,       # 'template' | 'user_gem' | None
        "ncbi_hits": [],
        "protein_fasta_ok": False,
        "protein_fasta_meta": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
