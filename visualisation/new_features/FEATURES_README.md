# BioOptimize — New Feature Files

These files contain **only** the new features from the enhanced app.
Your original files (`code1.py` – `code4.py`) are untouched.
Each feature file is self-contained and can be included selectively.

---

## Feature files at a glance

| File | What it adds | Touches original? |
|---|---|---|
| `feature_theme.py` | Dark / light toggle + full CSS system | No |
| `feature_header.py` | Branded logo banner + GEMtimise title/tagline | No |
| `feature_session_state.py` | Centralised `init_state()` with new keys | No |
| `feature_input_panel.py` | NCBI search, protein FASTA upload, GEM upload | No |
| `feature_model_loaders.py` | Updated pipeline helpers (template + GEM upload) | No |
| `feature_visuals.py` | Theme-aware `plot_growth_bar` / `plot_sensitivity` | No (drop-in) |

Supporting files (already written, copy to project root):

| File | Role |
|---|---|
| `strains.py` | Curated library strain metadata |
| `ncbi_client.py` | NCBI Entrez assembly search |
| `genome_validate.py` | Protein FASTA local validation |
| `gem_io.py` | SBML / JSON COBRA model loader |
| `model_engine.py` | Extended model engine (adds `load_template_model`, `load_model_from_gem_upload`) |

---

## Minimal integration — include everything

Add to the **top** of `code1.py`:

```python
from feature_session_state import init_state
from feature_theme import render_theme_toggle, get_theme_css
from feature_header import render_header
from feature_input_panel import render_input_panel
from feature_model_loaders import run_template_pipeline, load_from_gem_upload
from feature_visuals import plot_growth_bar, plot_sensitivity
from strains import strain_by_label, LIBRARY_LABELS
```

Then in the script body (replacing the current sidebar block):

```python
# 1. Session state
init_state()

# 2. Theme (must come first — injects CSS)
_ui_theme = render_theme_toggle()
st.markdown(get_theme_css(_ui_theme), unsafe_allow_html=True)

# 3. Header
render_header(_ui_theme)

# 4. Input panel
panel = render_input_panel()

# 5. Run button
if st.button("Run GEM engine", type="primary", use_container_width=True):
    if panel["input_mode"] == "Upload GEM model":
        if panel["gem_file"]:
            load_from_gem_upload(panel["gem_file"])
        else:
            st.error("Upload a SBML or JSON model first.")
    elif panel["genome_submode"] == "Custom protein FASTA":
        if panel["protein_file"] and st.session_state.protein_fasta_ok:
            run_template_pipeline(f"{panel['protein_file'].name} (protein FASTA)")
        else:
            st.error("Upload and validate a protein FASTA first.")
    elif panel["genome_submode"] == "Search NCBI":
        if panel["ncbi_selected"]:
            run_template_pipeline(panel["ncbi_selected"]["display"])
        else:
            st.error("Search NCBI and select an assembly first.")
    else:  # Library strain
        choice = st.session_state.get("library_strain_choice", LIBRARY_LABELS[0])
        run_template_pipeline(strain_by_label(choice)["label"])

# 6. In plots, pass theme:
#    plot_growth_bar(growth_rate, theme=_ui_theme)
#    plot_sensitivity(df, "Glucose", theme=_ui_theme)
```

---

## Pick-and-mix — include only what you want

Each feature is independent. Examples:

**Only the dark/light theme:**
```python
from feature_theme import render_theme_toggle, get_theme_css
_ui_theme = render_theme_toggle()
st.markdown(get_theme_css(_ui_theme), unsafe_allow_html=True)
```

**Only the NCBI search input:**
```python
# In your sidebar or main panel:
from ncbi_client import search_assemblies
q = st.text_input("Search assembly")
if st.button("Search"):
    hits = search_assemblies(q)
```

**Only the GEM upload path:**
```python
from gem_io import load_user_gem
gem_file = st.file_uploader("Upload GEM", type=["xml","sbml","json"])
if gem_file:
    model = load_user_gem(gem_file)
```

**Only theme-aware charts (drop-in for code4.py):**
```python
# Replace in code1.py:
from feature_visuals import plot_growth_bar, plot_sensitivity
# Then pass theme= wherever you call them.
```

---

## New `requirements.txt` entries

```
biopython>=1.81   # genome_validate.py, ncbi_client.py
```
All other dependencies are already in your original `requirements.txt`.
