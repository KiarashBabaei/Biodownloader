BioDownloader
Lightweight Python tools for retrieving structured metadata from GEO, SRA, and ENA.
 
Features
•	Fetch GEO metadata (GSE/GSM)
•	Retrieve SRA RunInfo via NCBI API
•	Access ENA run‑level metadata
•	Optional automated GEO–SRA merging
•	Includes a command‑line client (biofetch)
 
Installation
pip install biodownloader
 
Usage Examples
GEO
from biodownloader import fetch_geo_series
geo = fetch_geo_series("GSE181294")
SRA
from biodownloader import fetch_sra_bioproject
sra = fetch_sra_bioproject("PRJNA730495")
ENA
from biodownloader import fetch_ena_accession
ena = fetch_ena_accession("SRR23080510")
GEO–SRA merge
from biodownloader import fetch_and_merge_geo_sra
merged = fetch_and_merge_geo_sra("GSE181294", "PRJNA730495")
 
CLI
biofetch --source geo --id GSE181294 --out output.csv
biofetch --source sra --id PRJNA730495 --out sra.csv
biofetch --source ena --id SRR23080510 --out ena.tsv
 
Limitations
•	When GSM identifiers do not match between GEO and SRA, merged tables may be empty.
•	GEO HTML structures may evolve and require parser updates.
 
License
MIT License.
