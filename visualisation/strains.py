"""
Curated library strains with NCBI assembly / genome browser links (static metadata).
"""

LIBRARY_STRAINS = [
    {
        "id": "nc12",
        "label": "Neurospora crassa OR74A (NC12)",
        "ncbi_url": "https://www.ncbi.nlm.nih.gov/assembly/GCF_000182805.1/",
        "short": "Neurospora crassa",
    },
    {
        "id": "rhimi",
        "label": "Rhizopus microsporus ATCC 52814 (Rhimi_ATCC52814_1)",
        "ncbi_url": "https://www.ncbi.nlm.nih.gov/assembly/GCA_003047595.1/",
        "short": "Rhizopus microsporus",
    },
    {
        "id": "aspni",
        "label": "Aspergillus niger ATCC 13496 (Aspni_bvT_1)",
        "ncbi_url": "https://www.ncbi.nlm.nih.gov/assembly/GCA_003388765.1/",
        "short": "Aspergillus niger",
    },
    {
        "id": "asporyz",
        "label": "Aspergillus oryzae RIB40 (ASM18445v3)",
        "ncbi_url": "https://www.ncbi.nlm.nih.gov/assembly/GCA_000184455.2/",
        "short": "Aspergillus oryzae",
    },
]

LIBRARY_LABELS = [s["label"] for s in LIBRARY_STRAINS]


def strain_by_label(label: str) -> dict:
    for s in LIBRARY_STRAINS:
        if s["label"] == label:
            return s
    return LIBRARY_STRAINS[0]
