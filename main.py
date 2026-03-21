import os
import subprocess


def main():
    print("Hello from biohackathon-einburgh!")

def create_model(file_or_ref="GCF_000182925.2", output_file="model.GCF_000182925.2.xml"):
    if  os.path.isfile(file_or_ref):
        subprocess.run(["carve", file_or_ref, "-o", output_file], check=True)
    else:
        subprocess.run(["carve", "--refseq", file_or_ref, "-o", output_file], check=True)

if __name__ == "__main__":
    main()
