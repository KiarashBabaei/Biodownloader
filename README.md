# BioDownloader

A lightweight Python toolkit for programmatic retrieval of structured metadata from **GEO**, **SRA**, and **ENA**. The package provides a clean Python API and a command-line interface (`biofetch`) for downloading, parsing, and exporting metadata required for downstream RNA‑seq and NGS workflows.

---

## Features

* Retrieve **GEO Series metadata** (GSE/GSM) directly via NCBI GEO API.
* Fetch **SRA RunInfo tables** using SRA's RunInfo interface.
* Query **ENA run‑level annotations** using ENA XML/TSV endpoints.
* Unified schema normalization for cross‑database consistency.
* Optional **GEO–SRA merged metadata** for integrated analyses.
* Command‑line client (`biofetch`) for quick export to CSV/TSV.
* Fully pure‑Python (no external tools required).

---

## Installation

BioDownloader is available on PyPI:

```bash
pip install biodownloader
```

Verify installation:

```bash
python3 -c "import biodownloader; print(biodownloader.__version__)"
```

---

## Command‑Line Usage (CLI: `biofetch`)

BioDownloader includes a CLI for rapid metadata extraction.

### GEO

```bash
biofetch --source geo --id GSE181294 --limit 10 --out geo_metadata.csv
```

### SRA (BioProject)

```bash
biofetch --source sra --id PRJNA730495 --limit 20 --out sra_runinfo.csv
```

### ENA

```bash
biofetch --source ena --id SRR23080510 --limit 5 --out ena_meta.tsv
```

### GEO–SRA Merge

```bash
biofetch --source merge --geo GSE181294 --sra PRJNA730495 --out merged.csv
```

---

## Python API Usage

BioDownloader exposes simple, high‑level functions.

### GEO Metadata

```python
from biodownloader import fetch_geo_series

df = fetch_geo_series("GSE181294", limit=5)
print(df.head())
```

### SRA RunInfo

```python
from biodownloader import fetch_sra_bioproject

df = fetch_sra_bioproject("PRJNA730495", limit=10)
print(df[["Run", "SampleName"]].head())
```

### ENA Run‑Level Metadata

```python
from biodownloader import fetch_ena_accession

df = fetch_ena_accession("SRR23080510", limit=3)
print(df)
```

### GEO–SRA Integrated Table

```python
from biodownloader import fetch_and_merge_geo_sra

merged = fetch_and_merge_geo_sra(
    geo_id="GSE181294",
    sra_id="PRJNA730495",
    geo_limit=None,
    sra_limit=50,
    how="inner",
)

print(merged.head())
```

---

## Normalized Output Schema

### GEO Output Columns

* `GSE`, `GSM`, `title`, `organism`, `source_name`, `characteristics`

### SRA Output Columns (subset)

* `Run`, `SampleName`, `BioProject`, `LibraryStrategy`, `Platform`, `Model`, `download_path`, `size_MB`, `avgLength`, `spots`

### ENA Output Columns

* `run_accession`, `description`, `accession`

### Merged GEO–SRA Columns

Includes all normalized columns from both data sources, joined on `SampleName` / GSM.

---

## Project Structure

```
biodownloader/
 ├── geo.py            # GEO metadata retrieval
 ├── sra.py            # SRA RunInfo fetcher
 ├── ena.py            # ENA metadata fetcher
 ├── integrate.py      # GEO–SRA merging
 ├── cli.py            # biofetch CLI
 ├── __init__.py       # public API exports
```

---

## Tests

Contains minimal integration tests (CSV comparison / schema validation):

```
tests/
 ├── test_geo.py
 ├── test_sra.py
 ├── test_ena.py
 ├── test_merge.py
```

Run tests:

```bash
pytest -q
```

---

## Versioning

Follows semantic versioning (SemVer):

* MAJOR: breaking API changes
* MINOR: new features
* PATCH: bug fixes

---

## License

MIT License.

---

## Contact

For issues or feature requests, open a GitHub Issue.

Repository:
[https://github.com/KiarashBabaei/BioDownloader](https://github.com/KiarashBabaei/BioDownloader)

PyPI:
[https://pypi.org/project/biodownloader/](https://pypi.org/project/biodownloader/)

