"""
Validate uploaded files as protein FASTA (local checks only; no NCBI lookup).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional, Tuple

from Bio import SeqIO


# IUPAC protein letters + common ambiguity / stop
_PROTEIN_CHARS = set(
    "ACDEFGHIKLMNPQRSTVWYBXZJUO*"
)


@dataclass
class ProteinFastaValidation:
    ok: bool
    message: str
    record_count: int = 0
    total_aa: int = 0


def _looks_nucleotide(seq: str) -> bool:
    """Heuristic: high fraction of ATGCN only suggests DNA/RNA, not protein."""
    s = seq.upper().replace(" ", "").replace("\n", "")
    if len(s) < 10:
        return False
    nuc = sum(1 for c in s if c in "ATGCUN")
    return (nuc / len(s)) > 0.85


def validate_protein_fasta_bytes(data: bytes) -> ProteinFastaValidation:
    """
    Parse FASTA from bytes; require at least one record and protein-like sequences.
    Rejects empty files and sequences that look nucleotide-only.
    """
    if not data or not data.strip():
        return ProteinFastaValidation(False, "File is empty.")

    try:
        handle = io.BytesIO(data)
        records = list(SeqIO.parse(handle, "fasta"))
    except Exception as exc:
        return ProteinFastaValidation(False, f"Not valid FASTA: {exc}")

    if not records:
        return ProteinFastaValidation(False, "No FASTA records found.")

    total_aa = 0
    for rec in records:
        seq_str = str(rec.seq).upper().replace(" ", "")
        if not seq_str:
            return ProteinFastaValidation(False, f"Empty sequence in record: {rec.id}")
        if _looks_nucleotide(seq_str):
            return ProteinFastaValidation(
                False,
                "Sequence looks like nucleotide (DNA/RNA), not protein. "
                "Upload a protein sequence FASTA (.faa / .fasta).",
            )
        # Allow common protein alphabet; flag if too many unknown chars
        bad = sum(1 for c in seq_str if c not in _PROTEIN_CHARS and not c.isspace())
        if bad / len(seq_str) > 0.3:
            return ProteinFastaValidation(
                False,
                "Sequence does not look like protein (unexpected characters).",
            )
        total_aa += len(seq_str.replace("\n", ""))

    return ProteinFastaValidation(
        True,
        "OK",
        record_count=len(records),
        total_aa=total_aa,
    )


def parse_protein_fasta_records(data: bytes) -> Tuple[Optional[list], Optional[str]]:
    """Return list of SeqRecords or (None, error message)."""
    v = validate_protein_fasta_bytes(data)
    if not v.ok:
        return None, v.message
    try:
        handle = io.BytesIO(data)
        return list(SeqIO.parse(handle, "fasta")), None
    except Exception as exc:
        return None, str(exc)
