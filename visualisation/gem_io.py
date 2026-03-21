"""
Load user-uploaded genome-scale metabolic models (SBML/XML, JSON).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import cobra


def load_user_gem(uploaded_file) -> cobra.Model:
    """
    Load a COBRA model from a Streamlit UploadedFile-like object (name + getvalue/read).
    Supports .xml, .sbml, .json.
    """
    name = (uploaded_file.name or "model").lower()
    if hasattr(uploaded_file, "getvalue"):
        data = uploaded_file.getvalue()
    else:
        data = uploaded_file.read()

    lower = name.lower()
    if lower.endswith(".json"):
        suffix = ".json"
    elif lower.endswith(".sbml") or lower.endswith(".xml"):
        suffix = ".xml"
    else:
        suffix = ".json" if b"{" in data[:200] else ".xml"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        if suffix == ".json":
            model = cobra.io.load_json_model(tmp_path)
        else:
            model = cobra.io.read_sbml_model(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return model


def sniff_gem_format(filename: str) -> str:
    """Return 'json' or 'sbml'."""
    lower = (filename or "").lower()
    if lower.endswith(".json"):
        return "json"
    return "sbml"
