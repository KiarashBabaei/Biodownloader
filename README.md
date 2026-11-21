# BioDownloader
 
Fetch **GEO**, **SRA** and **ENA** metadata as pandas DataFrames and link them into one table: which sequencing run (SRR) belongs to which sample (GSM) and condition.
 
It downloads **metadata and links only**, not the FASTQ files themselves.
 
## Requirements
 
| Item | Needed |
|---|---|
| Python | 3.9 or newer |
| Packages | `pandas`, `requests` (installed automatically) |
| Internet | Yes (NCBI GEO, NCBI SRA, EBI ENA) |
| Accounts / API keys | None |
 
## Installation
 
```bash
pip install biodownloader
python -c "import biodownloader; print(biodownloader.__version__)"
```
 
## Quick start: from a GSE to a run table
 
You need two accessions for the same study:
 
| Accession | Example | Where to find it |
|---|---|---|
| GEO series (GSE) | `GSE181294` | The paper or the GEO page |
| BioProject (PRJNA...) | `PRJNA751490` | GEO page, section **Relations**, line **BioProject** |
 
```python
from biodownloader import fetch_and_merge_geo_sra
 
merged = fetch_and_merge_geo_sra("GSE181294", "PRJNA751490", how="left")
print(merged[["GSM", "title", "Run"]].head())
```
 
Result: one row per sequencing run. A sample sequenced in several runs appears once per run.
 
For `GSE181294` + `PRJNA751490` this gives 168 rows (51 samples, 168 runs).
 
### Finding the BioProject automatically
 
```python
import re, requests
 
def find_bioproject(gse):
    url = ("https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?"
           "targ=self&form=text&view=quick&acc=" + gse)
    text = requests.get(url, timeout=120).text
    m = re.search(r"!Series_relation\s*=\s*BioProject:.*?(PRJ[A-Z]+\d+)", text)
    return m.group(1) if m else None   # None: microarray or no SRA data
```
 
### Typical next steps
 
```python
# Split sample conditions stored in the free-text "characteristics" column
def parse(text):
    out = {}
    for part in str(text).split("; "):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out
 
import pandas as pd
meta = merged["characteristics"].apply(parse).apply(pd.Series)
merged = pd.concat([merged, meta], axis=1)
print(merged["condition"].value_counts())      # keys depend on the dataset
 
# FASTQ links from ENA (for downloading with wget / curl / aria2)
from biodownloader import fetch_ena_accession
ena = fetch_ena_accession("PRJNA751490")
urls = ["ftp://" + u for cell in ena["fastq_ftp"].dropna() for u in cell.split(";")]
```
 
## Functions
 
All functions return a pandas `DataFrame`. `limit` caps the number of rows; `timeout` is in seconds (default 30; use 120-180 for large series).
 
| Function | Input | Returns |
|---|---|---|
| `fetch_geo_series(gse_id, limit=None, timeout=30)` | `GSE...` | One row per GSM sample |
| `fetch_sra_bioproject(accession, limit=None, timeout=30)` | `PRJNA...`, `SRP...` or SRA search term | SRA RunInfo, one row per run |
| `fetch_ena_accession(accession, limit=None, timeout=30)` | Run `SRR/ERR/DRR`, study `PRJ...`/`SRP...`, experiment `SRX...`, sample `SAMN...`/`SRS...` | ENA read-run records |
| `merge_geo_sra(geo_df, sra_df, how="inner", geo_gsm_col=None, sra_gsm_col=None)` | Tables from the two functions above | Linked table |
| `fetch_and_merge_geo_sra(gse_id, sra_term, geo_limit=None, sra_limit=None, how="inner")` | GSE + BioProject | Linked table (fetch + merge) |
 
## Output columns
 
| Source | Columns |
|---|---|
| GEO | `GSE`, `GSM`, `title`, `organism`, `source_name`, `characteristics`, `BioSample`, `SRX` |
| SRA (main) | `Run`, `BioProject`, `BioSample`, `Experiment`, `SampleName`, `LibraryStrategy`, `LibraryLayout`, `Platform`, `Model`, `spots`, `bases`, `size_MB`, `download_path` |
| ENA | `run_accession`, `study_accession`, `secondary_study_accession`, `sample_accession`, `experiment_accession`, `scientific_name`, `library_strategy`, `instrument_platform`, `fastq_ftp`, `description` |
 
## How the merge links samples
 
Each SRA run is linked to a GEO sample in this order:
 
1. GSM found in the SRA `SampleName` column
2. SRA `BioSample` = GEO `BioSample`
3. SRA `Experiment` = GEO `SRX`
Passing `sra_gsm_col` restricts the link to that column only.
 
| `how` | Meaning |
|---|---|
| `inner` | Only samples that have an SRA run (warns if nothing matches) |
| `left` | All GEO samples; samples without a run have empty SRA columns |
| `right` | All SRA runs |
| `outer` | Everything |
 
Avoid `geo_limit` / `sra_limit` when you need a complete merge: each side is cut independently, so the first N rows may not overlap.
 
## Command line (`biofetch`)
 
```bash
biofetch --source geo   --id GSE181294   --limit 10 --out geo.csv
biofetch --source sra   --id PRJNA751490 --limit 20 --out sra.csv
biofetch --source ena   --id PRJNA751490 --limit 5  --out ena.tsv
biofetch --source merge --geo GSE181294 --sra PRJNA751490 --how left --out merged.csv
```
 
| Option | Meaning |
|---|---|
| `--source` | `geo`, `sra`, `ena` or `merge` |
| `--id` | Accession (for `geo`, `sra`, `ena`) |
| `--geo`, `--sra` | Accessions for `merge` |
| `--how` | `inner` (default), `left`, `right`, `outer` |
| `--limit` | Row limit (`geo`, `sra`, `ena`) |
| `--geo-limit`, `--sra-limit` | Row limits for `merge` |
| `--out` | `.csv` = comma, `.tsv`/`.txt` = tab; without it a preview is printed |
 
## Known limitations
 
| Limitation | Details |
|---|---|
| BioProject is not auto-detected | You supply the PRJNA/SRP; use the helper above. A wrong pair gives an empty merge and a warning. |
| Microarray or no SRA data | Nothing to link: `SRX` is empty and the SRA table is empty. |
| No automatic retry | A slow NCBI response can raise `ReadTimeout`; raise `timeout` and retry. |
| One channel only | GEO parsing reads `*_ch1` fields, so channel 2 of two-color arrays is ignored. |
| Rate limits | NCBI may throttle many consecutive requests without an API key. |
| Not exhaustively tested | Checked on 8 public GEO series (6 with SRA: 100% of samples linked, from 12 to 1,600 samples). |
 
## Tests
 
```bash
pip install -e . pytest
python -m pytest -q tests/
```
 
Some tests query NCBI and ENA live and need internet.
 
## License
 
MIT. Issues: https://github.com/KiarashBabaei/Biodownloader/issues
 
