# biohackathon-einburgh
Repository for the 2026 Biohackathon in Edinburgh

## Tasks


### 1. Create a genome - chemical reactions map

Contributors: Olivier, Chumeng

Input: 
- Genome
- Database

Output:
- File of chemical reactions as SBML format?

### 2. Create a GEM

Contributors: Daria

Input: 
- chemical reactions as SBML format
- 
Output:
- Potential GEM (cobrapy format?)

### 3. Optimize titer, rate and yield

Contributors: Davide

Input: 
- GEM

Output:
- Realized GEM (cobrapy format?)

### Visualize & Interact: The BioOptimize Interface
Contributors: Anooraag, Kanika, Chumeng

Problem Solved: Genome-Scale Metabolic Models (GEMs) are powerful but often inaccessible to non-specialists due to complex command-line interfaces. We built an interactive bridge that allows bioprocess engineers to "play" with their strain's metabolism without writing a single line of code.

#### Quick start
```
streamlit run app.py
```

Input Logic:

GEM Engine: Powered by COBRApy. The interface accepts standard metabolic model formats (SBML/XML, JSON) generated from the genomic pipeline.

Flexible Data Sources: Users can select from a library of industrial fungal strains (A. niger, N. crassa, etc.) or upload custom FASTA/GFF files.

Output & Features:

Interactive UI: Built with Streamlit for a seamless, browser-based experience.

Real-time FBA Simulation: Dynamic sliders allow users to adjust media components (Glucose, Oxygen, Nitrogen) and see the Predicted Growth Rate update instantly via Plotly visualizations.

Sensitivity Analysis: Automated charts showing how specific nutrient ranges impact biomass yield, helping to narrow down "wet-lab" experimental space.

Bioprocess Report: An automated plain-English summary of optimal media conditions, exportable for laboratory use.
