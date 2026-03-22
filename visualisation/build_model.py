import os
import subprocess
from cobra.io import read_sbml_model

def create_carve_model(ref="GCF_000182925.2", fasta_file=None, output_file="model.GCF_000182925.2.xml"):
    if fasta_file is not None:
        subprocess.run(["carve", fasta_file, "-o", output_file], check=True)
    else:
        subprocess.run(["carve", "--refseq", ref, "-o", output_file], check=True)
    return read_sbml_model(output_file)
