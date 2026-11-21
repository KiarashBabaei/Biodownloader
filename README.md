# BioDownloader

A lightweight Python toolkit that fetches structured metadata from **GEO**, **SRA** and **ENA** as pandas DataFrames, links GEO samples to SRA runs, and ships a command-line client (`biofetch`) for RNA-seq / NGS workflows.

## Features

* **GEO series metadata**: one row per GSM sample, including the BioSample and SRX links.
* **SRA RunInfo tables** via NCBI E-utilities (BioProject, SRP study or any SRA search term).
* **ENA read-run records** for run, study, experiment or sample accessions.
* **GEO-SRA merge** that links samples by GSM, BioSample or experiment (SRX).
* **`biofetch` CLI** exporting CSV or TSV.
* Pure Python (pandas + requests); Python 3.9+.

## Installation

```bash
pip install biodownloader
python -c "import biodownloader; print(biodownloader.__version__)"
```

## Python API

Every function returns a pandas `DataFrame`. `limit` caps the number of rows and `timeout` is the HTTP timeout in seconds (default 30).

### GEO

```python
from biodownloader import fetch_geo_series

df = fetch_geo_series("GSE181294", limit=5)
print(df[["GSM", "title", "BioSample", "SRX"]])
```

Columns: `GSE`, `GSM`, `title`, `organism`, `source_name`, `characteristics`, `BioSample`, `SRX`.

### SRA

```python
from biodownloader import fetch_sra_bioproject

df = fetch_sra_bioproject("PRJNA751490", limit=10)
print(df[["Run", "SampleName", "BioSample", "Experiment"]].head())
```

Accepts a BioProject (`PRJNA...`), an SRA study (`SRP...`) or a general SRA term. Returns the RunInfo table (`Run`, `BioProject`, `BioSample`, `Experiment`, `SampleName`, `LibraryStrategy`, `LibraryLayout`, `Platform`, `Model`, `spots`, `bases`, `size_MB`, `download_path`, ...).

### ENA

```python
from biodownloader import fetch_ena_accession

df = fetch_ena_accession("PRJNA751490", limit=3)
print(df[["run_accession", "sample_accession", "fastq_ftp"]])
```

Accepted accessions: runs (`SRR`/`ERR`/`DRR`), studies (`PRJ...`, `SRP`/`ERP`/`DRP`), experiments (`SRX`/`ERX`/`DRX`) and samples (`SAMN`/`SAME`/`SAMD`, `SRS`/`ERS`/`DRS`).

Columns: `run_accession`, `study_accession`, `secondary_study_accession`, `sample_accession`, `experiment_accession`, `scientific_name`, `library_strategy`, `instrument_platform`, `fastq_ftp`, `description`.

### GEO-SRA integrated table

```python
from biodownloader import fetch_and_merge_geo_sra

merged = fetch_and_merge_geo_sra("GSE181294", "PRJNA751490", how="left")
print(merged.shape)  # (168, 55): 51 samples, 168 runs
```

* The GSE and the SRA accession must belong to the same study. If an `inner` merge finds no overlap, a warning is raised.
* Each SRA run is linked to a GEO sample by GSM (`SampleName`), then by `BioSample`, then by experiment (`SRX`).
* A sample sequenced in several runs appears once per run.
* Use `how="left"` to keep GEO samples that have no SRA run.
* `geo_limit` and `sra_limit` cut each table independently, so the first N rows of each side may not overlap. Avoid them when you need a complete merge.

For existing tables use `merge_geo_sra(geo_df, sra_df, how="inner", geo_gsm_col=None, sra_gsm_col=None)`. Passing `sra_gsm_col` restricts the link to that column only.

## Command-line usage (`biofetch`)

```bash
biofetch --source geo   --id GSE181294    --limit 10 --out geo_metadata.csv
biofetch --source sra   --id PRJNA751490  --limit 20 --out sra_runinfo.csv
biofetch --source ena   --id PRJNA751490  --limit 5  --out ena_meta.tsv
biofetch --source merge --geo GSE181294 --sra PRJNA751490 --how left --out merged.csv
```

* `--out` ending in `.tsv` or `.txt` writes tab-separated output, anything else is comma-separated. Without `--out` a preview is printed.
* `--limit` applies to `geo`, `sra` and `ena`; `--geo-limit` and `--sra-limit` apply to `merge`.

## Project structure

```
biodownloader/
 |-- geo.py          # GEO metadata retrieval
 |-- sra.py          # SRA RunInfo fetcher
 |-- ena.py          # ENA metadata fetcher
 |-- integrate.py    # GEO-SRA merging
 |-- cli.py          # biofetch CLI
 |-- __init__.py     # public API exports
tests/
 |-- test_regression.py   # parser, merge, ENA and live-data regression tests
 |-- test_cli.py          # offline CLI tests
```

## Tests

```bash
pip install -e . pytest
python -m pytest -q tests/
```

Some tests query NCBI and ENA live and need an internet connection.

## Versioning

Semantic versioning: MAJOR for breaking API changes, MINOR for new features, PATCH for bug fixes.

## License

MIT License.

## Contact

Issues and feature requests: https://github.com/KiarashBabaei/Biodownloader/issues

PyPI: https://pypi.org/project/biodownloader/
