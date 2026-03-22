"""Thin facade so app.py imports a stable module name; implementation lives in dna_to_protein_fasta."""

from dna_to_protein_fasta import (
    detect_sequence_type,
    prepare_fasta_for_carveme,
    render_download_button,
    translate_dna_to_protein,
)

__all__ = [
    "detect_sequence_type",
    "translate_dna_to_protein",
    "prepare_fasta_for_carveme",
    "render_download_button",
]