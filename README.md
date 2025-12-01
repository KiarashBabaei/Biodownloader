BioDownloader – README Files
Below are two complete README versions: one optimized for GitHub, and one optimized for PyPI. You can copy each into the appropriate platform without modification.
 
 README (GitHub Version – Full, Rich, Detailed)
BioDownloader
A lightweight Python toolkit for downloading and integrating GEO, SRA, and ENA metadata.
BioDownloader provides: - 🔍 GEO metadata extraction (GSE/GSM) - 🎛 SRA RunInfo retrieval (via NCBI SRA API) - 🌐 ENA run‑level metadata queries - 🔗 Optional GEO–SRA auto‑merge (best‑effort GSM matching) - 🧪 CLI tool (biofetch) for terminal‑based data retrieval
The library is designed to be simple, pure‑Python, API‑driven, and easily integrable within downstream RNA‑seq workflows.
 
Features
GEO
from biodownloader import fetch_geo_series
geo_df = fetch_geo_series("GSE181294")
Retrieves GSM metadata (title, organism, characteristics, etc.).
SRA
from biodownloader import fetch_sra_bioproject
sra_df = fetch_sra_bioproject("PRJNA730495")
Downloads real SRA RunInfo tables directly from NCBI.
ENA
from biodownloader import fetch_ena_accession
ena_df = fetch_ena_accession("SRR23080510")
Fetches ENA run‑level metadata via the ENA Portal API.
 
 GEO–SRA Auto‑Merge
BioDownloader attempts to auto‑detect GSM‑like fields and merge GEO and SRA tables:
from biodownloader import fetch_and_merge_geo_sra
merged = fetch_and_merge_geo_sra("GSE181294", "PRJNA730495")
Important: automatic merging is dataset‑dependent.
If GSM identifiers do not match (e.g., different GEO series), the merged table will be empty — this is expected behavior.
You can override detection manually:
from biodownloader import merge_geo_sra
merged = merge_geo_sra(
    geo_df,
    sra_df,
    geo_gsm_col="GSM",
    sra_gsm_col="SampleName",
)
 
 Command‑Line Interface (CLI)
BioDownloader installs a command‑line tool called biofetch.
GEO example
biofetch --source geo --id GSE181294 --limit 10 --out geo_meta.csv
SRA example
biofetch --source sra --id PRJNA730495 --out sra_meta.csv
ENA example
biofetch --source ena --id SRR23080510 --out ena_meta.tsv
 
Installation
pip install biodownloader
or from source (development mode):
pip install -e .
 
  Project Structure
biodownloader/
│── __init__.py
│── geo.py
│── sra.py
│── ena.py
│── integrate.py
│── cli.py
└── pyproject.toml
 
 Limitations
•	Auto‑merge depends entirely on GSM IDs present in both GEO + SRA.
If they come from unrelated datasets, merge will be empty.
•	GEO API sometimes changes HTML formatting → parser may need updates.
•	ENA result structure may vary depending on accession type.
 
License
MIT License.
