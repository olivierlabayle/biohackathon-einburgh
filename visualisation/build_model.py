
import os
import subprocess
from cobra.io import read_sbml_model

def create_carve_model(file_or_ref="GCF_000182925.2", output_file="model.GCF_000182925.2.xml"):
    if  os.path.isfile(file_or_ref):
        subprocess.run(["carve", file_or_ref, "-o", output_file], check=True)
    else:
        subprocess.run(["carve", "--refseq", file_or_ref, "-o", output_file], check=True)
    return read_sbml_model(output_file)