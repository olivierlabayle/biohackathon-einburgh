"""
- Check user input: DNA vs protein detection
- Translate DNS sequence into protein sequence
- Provide option for user to download the protein sequence file
- Integrate the function into main script
"""

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
    st = None

__all__ = [
    "detect_sequence_type",
    "translate_dna_to_protein",
    "prepare_fasta_for_carveme",
    "render_download_button",
]

_PROTEIN_ONLY = frozenset("EFILPQ")
_DNA_IUPAC    = frozenset("ACGTUNRYSWKMBDHV")


def _fasta_text_io(data: bytes) -> StringIO:
    """Biopython FASTA I/O expects text-mode handles, not binary BytesIO."""
    return StringIO(data.decode("utf-8", errors="replace"))


def detect_sequence_type(data: bytes) -> Literal["dna", "protein"]:
    """Classify a FASTA file as DNA or protein by inspecting its residues."""
    letters = [
        c.upper()
        for record in SeqIO.parse(_fasta_text_io(data), "fasta")
        for c in str(record.seq)
        if c.isalpha()
    ]
    if not letters:
        raise ValueError("No sequence data found — check your FASTA file.")

    # Any protein-exclusive letters → protein
    if sum(c in _PROTEIN_ONLY for c in letters) / len(letters) > 0.04:
        return "protein"

    # Mostly IUPAC nucleotide characters → DNA
    if sum(c in _DNA_IUPAC for c in letters) / len(letters) >= 0.85:
        return "dna"

    return "protein"


def translate_dna_to_protein(data: bytes, table: int = 1) -> bytes:
    """Translate every record in a DNA FASTA to protein (in-frame, coding sequences)."""
    records = []
    for rec in SeqIO.parse(_fasta_text_io(data), "fasta"):
        prot_seq = rec.seq.translate(table=table).rstrip("*")  # strip stop codon
        records.append(SeqRecord(prot_seq, id=rec.id, description=rec.description))

    if not records:
        raise ValueError("FASTA contained no records.")

    buf = StringIO()
    SeqIO.write(records, buf, "fasta")
    return buf.getvalue().encode("utf-8")


def _safe_filename(name: str) -> str:
    """Sanitise a strain name for use as a filename."""
    return re.sub(r"[^\w\-.]+", "_", name.strip()) or "strain"


def prepare_fasta_for_carveme(
    raw_bytes: bytes,
    strain_name: str,
    out_dir: str,
    *,
    genetic_code: int = 1,
    save_original: bool = True,
) -> tuple[str, bytes, Literal["dna", "protein"]]:
    """
    Detect molecule type, translate if needed, write .faa for CarveMe.
    Returns (protein_faa_path, protein_bytes, kind).
    """
    os.makedirs(out_dir, exist_ok=True)
    safe = _safe_filename(strain_name)

    kind = detect_sequence_type(raw_bytes)
    protein_bytes = translate_dna_to_protein(raw_bytes, table=genetic_code) if kind == "dna" else raw_bytes

    faa_path = os.path.join(out_dir, f"{safe}.faa")
    with open(faa_path, "wb") as f:
        f.write(protein_bytes)

    if save_original:
        with open(os.path.join(out_dir, f"{safe}_upload.fasta"), "wb") as f:
            f.write(raw_bytes)

    return faa_path, protein_bytes, kind


def render_download_button(label: str, file_name: str, data: bytes) -> None:
    """Render a Streamlit download button for a protein FASTA file."""
    if st is None:
        raise ImportError("streamlit is required to call render_download_button")
    st.download_button(label=label, data=data, file_name=file_name, mime="text/plain")
