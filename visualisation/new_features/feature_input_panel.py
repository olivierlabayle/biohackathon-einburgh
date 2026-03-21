"""
feature_input_panel.py
----------------------
Enhanced input panel replacing the original sidebar approach in code1.py.

Three new input modes (vs. the original two):
  1. Library strain      — curated dropdown (uses strains.py)
  2. Search NCBI         — live Entrez assembly search (uses ncbi_client.py)
  3. Custom protein FASTA — drag-and-drop upload with validation (uses genome_validate.py)
  4. Upload GEM model    — SBML / JSON COBRA model (uses gem_io.py via model_engine.py)

HOW TO INTEGRATE into code1.py (app):
  1. Install new deps:
        biopython>=1.81   (already in requirements.txt)
  2. Add new module files to project:
        strains.py, ncbi_client.py, genome_validate.py, gem_io.py,
        feature_input_panel.py
  3. Replace the sidebar input block in code1.py with:

        from feature_input_panel import render_input_panel
        panel = render_input_panel()
        # panel keys: input_mode, genome_submode, selected_label,
        #             gem_file, protein_file, ncbi_selected

  4. In the "Build Model" button handler, branch on panel['input_mode'] and
     panel['genome_submode'] to call the right loader
     (see feature_model_loaders.py for the updated pipeline helpers).

Dependencies (must be importable):
    streamlit, strains, ncbi_client, genome_validate
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from genome_validate import validate_protein_fasta_bytes
from ncbi_client import search_assemblies
from strains import LIBRARY_LABELS, strain_by_label


def render_input_panel() -> dict[str, Any]:
    """
    Renders the full input configuration section.

    Returns a dict:
        {
            "input_mode":     str,   # "Genome (protein FASTA)" | "Upload GEM model"
            "genome_submode": str,   # "Library strain" | "Search NCBI" | "Custom protein FASTA"
            "selected_label": str,   # human-readable name for the chosen input
            "gem_file":       UploadedFile | None,
            "protein_file":   UploadedFile | None,
            "ncbi_selected":  dict | None,  # hit dict from ncbi_client
        }
    """
    st.subheader("Configure input")
    st.markdown("---")

    input_mode = st.radio(
        "Choose input source",
        ["Genome (protein FASTA)", "Upload GEM model"],
        help=(
            "Library / NCBI search / custom protein FASTA, "
            "or load your own SBML/JSON GEM."
        ),
        horizontal=True,
    )

    selected_label = "Not selected"
    gem_file = None
    protein_file = None
    ncbi_selected = None
    genome_submode = "Library strain"

    # ── Branch 1: genome / protein FASTA ──────────────────────────────────────
    if input_mode == "Genome (protein FASTA)":
        genome_submode = st.radio(
            "Genome source",
            ["Library strain", "Search NCBI", "Custom protein FASTA"],
            help="Library: curated strains. NCBI: assembly search. Custom: your protein FASTA.",
            horizontal=True,
        )

        # 1a. Library strain -------------------------------------------------------
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

        # 1b. Search NCBI ----------------------------------------------------------
        elif genome_submode == "Search NCBI":
            q = st.text_input(
                "Search genome / assembly name",
                placeholder="e.g. Aspergillus nidulans",
                help=(
                    "Queries the NCBI Entrez `assembly` database. "
                    "Set NCBI_EMAIL in Streamlit secrets for policy compliance."
                ),
            )
            if st.button("Search NCBI"):
                try:
                    st.session_state.ncbi_hits = search_assemblies(q)
                    if not st.session_state.ncbi_hits:
                        st.warning("No assemblies found. Try different keywords.")
                except Exception as exc:
                    st.error(f"NCBI search failed: {exc}")
                    st.session_state.ncbi_hits = []

            hits = st.session_state.get("ncbi_hits") or []
            if hits:
                options = [h["display"] for h in hits]
                pick = st.selectbox("Select a result", options, key="ncbi_pick")
                idx = options.index(pick)
                ncbi_selected = hits[idx]
                selected_label = ncbi_selected["display"]
            else:
                selected_label = "Search NCBI (no selection yet)"

        # 1c. Custom protein FASTA -------------------------------------------------
        else:
            st.caption(
                "Upload **one** protein sequence FASTA (e.g. `.faa`, `.fa`). "
                "Not for raw DNA FASTA."
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

    # ── Branch 2: Upload GEM model ────────────────────────────────────────────
    else:
        st.caption("Standard formats: **SBML** (`.xml`, `.sbml`) or **COBRA JSON** (`.json`).")
        gem_file = st.file_uploader(
            "Upload GEM (SBML / JSON)",
            type=["xml", "sbml", "json"],
            accept_multiple_files=False,
        )
        selected_label = gem_file.name if gem_file else "GEM upload (no file yet)"

    return {
        "input_mode": input_mode,
        "genome_submode": genome_submode,
        "selected_label": selected_label,
        "gem_file": gem_file,
        "protein_file": protein_file,
        "ncbi_selected": ncbi_selected,
    }
