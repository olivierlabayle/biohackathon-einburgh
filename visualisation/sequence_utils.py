# =============================================================================
# sequence_utils.py
# NEW FEATURE — currently being integrated into the GEMtimize web app (app.py)
#
# Planned integration points in app.py:
#   1. In the "Custom Upload" block (sidebar): call prepare_fasta_for_carveme()
#      instead of writing the raw upload bytes directly.  The returned faa_path
#      should be passed as fasta_file to create_carve_model(), replacing the
#      plain .fasta path that is used today.
#   2. After the file-upload success message: show the detected sequence type
#      (DNA / protein) and, when DNA was detected, confirm translation occurred.
#   3. Offer a download button (render_download_button) so users can retrieve
#      the translated protein FASTA before kicking off the model build.
# =============================================================================

from __future__ import annotations

import os
import re
from io import StringIO
from typing import Literal

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

try:
    import streamlit as st
except ImportError:
    st = None  # Allow module to be imported outside a Streamlit context

__all__ = [
    "detect_sequence_type",
    "translate_dna_to_protein",
    "prepare_fasta_for_carveme",
    "render_download_button",
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Letters that appear only in protein sequences (never in IUPAC nucleotides)
_PROTEIN_ONLY = frozenset("EFILPQ")

# Full IUPAC nucleotide alphabet (DNA + RNA + ambiguity codes)
_DNA_IUPAC = frozenset("ACGTUNRYSWKMBDHV")


def _fasta_text_io(data: bytes) -> StringIO:
    """Convert raw FASTA bytes to a text-mode StringIO.

    Biopython's SeqIO.parse expects a text-mode handle, not a binary BytesIO.
    """
    return StringIO(data.decode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_sequence_type(data: bytes) -> Literal["dna", "protein"]:
    """Classify a FASTA file as DNA or protein by inspecting its residues.

    Parameters
    ----------
    data:
        Raw bytes of a FASTA file (nucleotide or amino-acid).

    Returns
    -------
    ``"dna"`` or ``"protein"``.

    Raises
    ------
    ValueError
        If the file contains no parseable sequence data.
    """
    letters = [
        c.upper()
        for record in SeqIO.parse(_fasta_text_io(data), "fasta")
        for c in str(record.seq)
        if c.isalpha()
    ]

    if not letters:
        raise ValueError("No sequence data found — check your FASTA file.")

    # Heuristic 1: any protein-exclusive letters present at >4 % → protein
    if sum(c in _PROTEIN_ONLY for c in letters) / len(letters) > 0.04:
        return "protein"

    # Heuristic 2: ≥85 % IUPAC nucleotide characters → DNA
    if sum(c in _DNA_IUPAC for c in letters) / len(letters) >= 0.85:
        return "dna"

    return "protein"


def translate_dna_to_protein(data: bytes, table: int = 1) -> bytes:
    """Translate every record in a DNA FASTA to its protein sequence.

    Translation uses BioPython with the specified NCBI genetic code *table*
    (default 1 = standard code).  Stop codons are stripped from the C-terminus.

    Parameters
    ----------
    data:
        Raw bytes of a DNA FASTA file.
    table:
        NCBI translation table number (e.g. 1 = standard, 4 = mycoplasma).

    Returns
    -------
    UTF-8 encoded bytes of the translated protein FASTA.

    Raises
    ------
    ValueError
        If the FASTA contained no records.
    """
    records = []
    for rec in SeqIO.parse(_fasta_text_io(data), "fasta"):
        prot_seq = rec.seq.translate(table=table).rstrip("*")  # strip stop codon
        records.append(
            SeqRecord(prot_seq, id=rec.id, description=rec.description)
        )

    if not records:
        raise ValueError("FASTA contained no records.")

    buf = StringIO()
    SeqIO.write(records, buf, "fasta")
    return buf.getvalue().encode("utf-8")


def _safe_filename(name: str) -> str:
    """Sanitise a strain name so it can be used safely as a filename."""
    return re.sub(r"[^\w\-.]+", "_", name.strip()) or "strain"


def prepare_fasta_for_carveme(
    raw_bytes: bytes,
    strain_name: str,
    out_dir: str,
    *,
    genetic_code: int = 1,
    save_original: bool = True,
) -> tuple[str, bytes, Literal["dna", "protein"]]:
    """Detect molecule type, translate if needed, and write a .faa for CarveMe.

    This is the primary entry-point for the app.py integration.  It handles the
    full pre-processing pipeline for a user-uploaded genome file:

    1. Detect whether the upload is DNA or protein.
    2. Translate DNA → protein if required (using *genetic_code*).
    3. Write the protein FASTA to *out_dir* with extension ``.faa``.
    4. Optionally preserve the original upload alongside it.

    Parameters
    ----------
    raw_bytes:
        Raw bytes from ``st.file_uploader`` (``uploaded_file.getbuffer()``).
    strain_name:
        User-supplied strain label; used to derive output filenames.
    out_dir:
        Directory in which to write the processed files (created if absent).
    genetic_code:
        NCBI genetic code table for translation (default 1 = standard).
    save_original:
        If ``True``, also save the unmodified upload as ``<strain>_upload.fasta``.

    Returns
    -------
    (faa_path, protein_bytes, kind)
        *faa_path* — absolute path to the written ``.faa`` file.
        *protein_bytes* — UTF-8 encoded protein FASTA bytes (useful for the
        download button without a second disk read).
        *kind* — ``"dna"`` or ``"protein"`` as detected from the input.
    """
    os.makedirs(out_dir, exist_ok=True)
    safe = _safe_filename(strain_name)

    kind = detect_sequence_type(raw_bytes)
    protein_bytes = (
        translate_dna_to_protein(raw_bytes, table=genetic_code)
        if kind == "dna"
        else raw_bytes
    )

    faa_path = os.path.join(out_dir, f"{safe}.faa")
    with open(faa_path, "wb") as fh:
        fh.write(protein_bytes)

    if save_original:
        original_path = os.path.join(out_dir, f"{safe}_upload.fasta")
        with open(original_path, "wb") as fh:
            fh.write(raw_bytes)

    return faa_path, protein_bytes, kind


def render_download_button(label: str, file_name: str, data: bytes) -> None:
    """Render a Streamlit download button for a protein FASTA file.

    Parameters
    ----------
    label:
        Button label shown in the UI (e.g. ``"Download protein FASTA"``).
    file_name:
        Suggested filename for the downloaded file (e.g. ``"MyStrain.faa"``).
    data:
        Raw bytes to serve (typically *protein_bytes* from
        :func:`prepare_fasta_for_carveme`).

    Raises
    ------
    ImportError
        If Streamlit is not installed in the current environment.
    """
    if st is None:
        raise ImportError(
            "streamlit is required to call render_download_button. "
            "Install it with: pip install streamlit"
        )
    st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime="text/plain",
    )
