"""
NCBI Entrez utilities for genome name search (assembly database).
Requires Entrez.email per NCBI policy — set NCBI_EMAIL env or Streamlit secrets.
"""

from __future__ import annotations

import os
import time
from typing import Any, List

# Rate limit between Entrez calls (seconds)
_ENTREZ_DELAY = 0.35


def _get_email() -> str:
    email = os.environ.get("NCBI_EMAIL", "").strip()
    if not email:
        try:
            import streamlit as st

            email = (st.secrets.get("NCBI_EMAIL") or "").strip()
        except Exception:
            pass
    return email or "biooptimize@users.nlm.nih.gov"


def _configure_entrez() -> None:
    from Bio import Entrez

    Entrez.email = _get_email()
    Entrez.tool = "GEMtimise/1.0"


def _flatten_summaries(records) -> List[dict]:
    """Normalize Entrez esummary DocumentSummary to a list of dict-like rows."""
    if records is None:
        return []
    if isinstance(records, list):
        return [r for r in records if isinstance(r, dict)]
    if not isinstance(records, dict):
        return []
    dss = records.get("DocumentSummarySet")
    if dss is None:
        return []
    if isinstance(dss, dict):
        inner = dss.get("DocumentSummary", [])
    else:
        inner = []
    if isinstance(inner, dict):
        return [inner]
    if isinstance(inner, list):
        return [x for x in inner if isinstance(x, dict)]
    return []


def search_assemblies(term: str, retmax: int = 15) -> List[dict[str, Any]]:
    """
    Search NCBI assembly database for `term`. Returns list of dicts with
    assembly_accession, organism_name, assembly_name, uid.
    """
    term = (term or "").strip()
    if not term:
        return []

    _configure_entrez()
    from Bio import Entrez

    time.sleep(_ENTREZ_DELAY)
    handle = Entrez.esearch(db="assembly", term=term, retmax=retmax, sort="relevance")
    search = Entrez.read(handle)
    handle.close()
    id_list = search.get("IdList", [])
    if not id_list:
        return []

    time.sleep(_ENTREZ_DELAY)
    handle = Entrez.esummary(db="assembly", id=",".join(id_list))
    try:
        records = Entrez.read(handle)
    except Exception:
        handle.close()
        return []
    handle.close()

    summaries = _flatten_summaries(records)
    out: List[dict[str, Any]] = []
    for doc in summaries:
        uid = str(doc.get("uid", doc.get("Id", "")))
        accession = doc.get("AssemblyAccession") or doc.get("AssemblyName") or uid
        organism = doc.get("Organism") or doc.get("organism_name") or ""
        asm_name = doc.get("AssemblyName") or ""
        display = f"{accession} — {organism}".strip(" —")
        if len(display) > 200:
            display = display[:197] + "..."
        out.append(
            {
                "uid": uid,
                "assembly_accession": accession,
                "organism_name": organism,
                "assembly_name": asm_name,
                "display": display,
            }
        )
    return out
