# GEMitize - GEM Creation and Optimization Platform

A comprehensive web application for creating, optimizing, and visualizing genome-scale metabolic models (GEMs). Built with Streamlit and powered by COBRApy, CarveMe, and advanced metabolic modeling tools.

## Key Features

- **Multiple Input Methods**: Choose from curated strain library, custom protein FASTA upload or
- **Automated GEM Construction**: Uses CarveMe pipeline to generate metabolic models from genome data
- **Advanced Optimization**: Flux Balance Analysis (FBA) with TRY metrics (Titer, Rate, Yield) for production optimization
- **Media Composition**: Custom nutrient media design with sensitivity analysis
- **Interactive Network Visualization**: Bipartite metabolic network graphs with customizable subgraph extraction
- **Professional UI**: Dark/light theme toggle with responsive design
- **Docker Support**: Complete containerization for reproducible deployments


# How to run

## 1. Setup

### Build the Docker Image

```bash
docker build --platform linux/amd64 -t biohackathon-einburgh:latest -f .devcontainer/Dockerfile .
```

### Run the Docker Container

```bash
docker run \
    --platform linux/amd64 \
    -it \
    --rm \
    -p "8501:8501" \
    -v "$(PWD):/app/" \
    -e STREAMLIT_SERVER_PORT=8501 \
    -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    biohackathon-einburgh:latest \
    /bin/bash
```

### Run the Streamlit App

```
uv sync
uv run streamlit run visualisation/app.py
```

## 2. Use GEMitize


### Choose an input genome
- 1) **Default option**: Choose from four strains in the library:
  - Neurospora crassa. OR74A
  - Rhizopus microsporus var. microspores. ATCC 52814
  - Aspergillus niger. ATCC 13496
  - Aspergillus oryzae. RIB40

- 2) **Customed strain/genome**: 


### Build a GEM
- **Automated**: Just click 'Build Metabolic Model': the platform will automatically build a GEM model from the input genome using the selected database. 

### GEM optimization
From the Model Overview tab (default):
- 1. Select reaction to optimize (for example, Biomass reaction)
- 2. Compose your media by adding nutrients.
- 3. Optimize to maximize the selected reaction!
- 4. Display results:
    - TRY (Titer, Rate, Yield) metrics.
    - Minimal media composition required for optimal production.

### Network Visualization
From the Network Visualization tab:
- Visualize the metabolic network
- Interact with the network
- Download the network

### Download 
From the Model Overview tab:
- Download the GEM model

# Tools
- CarveMe: [https://carveme.readthedocs.io/en/latest/installation.html](https://carveme.readthedocs.io/en/latest/installation.html), tool to generate GEMs from genomes
- streamlit: [https://streamlit.io/](https://streamlit.io/), tool to create web applications for data science and machine learning
- Cobrapy: [https://opencobra.github.io/cobrapy/](https://opencobra.github.io/cobrapy/), tool to create web applications for data science and machine learning


