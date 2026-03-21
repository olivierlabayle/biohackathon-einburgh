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

##### Input
**Genome fasta file**
1) Default option: four strains in the library. Already in the code; The user can also just search the genome name (need API added to our website), find matched genome;
2) Customised genome. The users can also upload their own genome, the genome format should be protein sequence fasta file. Add a hint about the genome format should be protein sequence fasta file. Only allow one file each time.
3) For the "uploading genome" interface, put the button in the middle, the user can simply drag their genome to upload it.
  
**GEM Engine**
1) already integrated in the website. The user only need to click the button to run it.  
2) the user can also upload their GEM modelThe interface accepts standard metabolic model formats (SBML/XML, JSON).

**Output & Features:**
- Interactive UI: Built with Streamlit for a seamless, browser-based experience.
- Real-time FBA Simulation: Dynamic sliders allow users to adjust media components (Glucose, Oxygen, Nitrogen) and see the Predicted Growth Rate update instantly via Plotly visualizations.
Sensitivity Analysis: Automated charts showing how specific nutrient ranges impact biomass yield, helping to narrow down "wet-lab" experimental space.
Bioprocess Report: An automated plain-English summary of optimal media conditions, exportable for laboratory use.
