# BioDownloader

**What does it do?**
You give it the ID of a public RNA-seq study (like `GSE181294`). It gives you back **one table** that tells you, for every sequencing file (run):

- which **sample** it belongs to,
- what that sample is (tumor, control, treated...),
- where to **download** the raw FASTQ files.

It downloads **only the table (metadata and links)**, not the big sequencing files.

---

## 1. Words you will see

| Word | Meaning | Example |
|---|---|---|
| **GEO** | NCBI database of experiments | ncbi.nlm.nih.gov/geo |
| **GSE** | One study (series) in GEO | `GSE181294` |
| **GSM** | One sample in a study | `GSM5494366` |
| **BioProject (PRJNA...)** | The same study, as named in the sequencing database | `PRJNA751490` |
| **SRR** | One sequencing run (the actual raw data) | `SRR23080515` |
| **FASTQ** | The raw sequencing file you later analyse | `SRR23080515_1.fastq.gz` |

One sample can have several runs, so the final table has one row per run.

---

## 2. What you need before starting

| You need | Details |
|---|---|
| A computer with **Python 3.9 or newer** | Check: `python3 --version` |
| **Internet** | The tool reads NCBI and EBI websites |
| A **GSE** number | From your paper or from the GEO website |
| The matching **PRJNA** number | Step 4 below shows how to find it |

No account, no password, no API key.

---

## 3. Install (once)

Open a terminal and run:

```bash
pip install biodownloader
```

Check that it works:

```bash
python3 -c "import biodownloader; print(biodownloader.__version__)"
```

You should see a version number such as `0.2.6`.

---

## 4. Find the PRJNA number of your GSE

**Manual way:** open `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE181294`, scroll to **Relations**, and copy the number after **BioProject** (it starts with `PRJNA`).

**Automatic way:** save this as `find_prj.py`:

```python
import re, requests

def find_bioproject(gse):
    url = ("https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?"
           "targ=self&form=text&view=quick&acc=" + gse)
    text = requests.get(url, timeout=120).text
    m = re.search(r"!Series_relation\s*=\s*BioProject:.*?(PRJ[A-Z]+\d+)", text)
    return m.group(1) if m else None

print(find_bioproject("GSE181294"))
```

Run it: `python3 find_prj.py` → prints `PRJNA751490`.
If it prints `None`, the study has no sequencing data (for example a microarray study), and this tool cannot link it.

---

## 5. Get your table

Save this as `get_table.py`:

```python
from biodownloader import fetch_and_merge_geo_sra

merged = fetch_and_merge_geo_sra("GSE181294", "PRJNA751490", how="left")

print(merged.shape)                          # (168, 55)
print(merged[["GSM", "title", "Run"]].head())
merged.to_csv("my_table.csv", index=False)   # open it in Excel
```

Run it: `python3 get_table.py`

For big studies it can take 1-2 minutes. Please wait.

### What you get

| Column | What it tells you |
|---|---|
| `GSM` | Sample ID |
| `title` | Sample name given by the authors |
| `characteristics` | Conditions (tissue, treatment, age...) as text |
| `organism` | Species |
| `Run` | Sequencing run ID (SRR) |
| `LibraryStrategy` | For example RNA-Seq |
| `Platform` / `Model` | Sequencer, for example ILLUMINA |
| `BioSample`, `SRX` | Extra IDs used for linking |

(55 columns in total; the ones above are the most useful.)

---

## 6. Get the FASTQ download links

```python
from biodownloader import fetch_ena_accession

ena = fetch_ena_accession("PRJNA751490")
urls = ["ftp://" + u for cell in ena["fastq_ftp"].dropna() for u in cell.split(";")]

with open("fastq_urls.txt", "w") as f:
    f.write("\n".join(urls))
```

Then download all files with:

```bash
wget -i fastq_urls.txt
```

(FASTQ files are large, often many GB. Make sure you have disk space.)

---

## 7. Turn "characteristics" into proper columns (optional)

```python
import pandas as pd

def parse(text):
    out = {}
    for part in str(text).split("; "):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out

meta = merged["characteristics"].apply(parse).apply(pd.Series)
merged = pd.concat([merged, meta], axis=1)
print(meta.columns.tolist())      # the new column names depend on the study
```

---

## 8. Without Python: command line

```bash
biofetch --source merge --geo GSE181294 --sra PRJNA751490 --how left --out merged.csv
biofetch --source geo --id GSE181294 --out samples.csv
biofetch --source sra --id PRJNA751490 --out runs.csv
biofetch --source ena --id PRJNA751490 --out ena.tsv
```

`--out file.csv` saves a comma file, `--out file.tsv` saves a tab file. Without `--out` it just prints a preview. Add `--limit 10` to test quickly.

---

## 9. Common problems

| Problem | What to do |
|---|---|
| `ReadTimeout` | NCBI was slow. Run again. In Python add `timeout=180`. |
| Empty table / "no rows matched" warning | GSE and PRJNA are not from the same study. Check step 4. |
| `command not found: biofetch` | Close and reopen the terminal, or use `python3 -m pip install biodownloader` and retry. |
| No `Run` values for a GSE | It has no sequencing data (microarray). Nothing to link. |

---

## 10. Honest limits

- You must give the BioProject yourself (step 4 helps).
- Only the first channel of two-color microarrays is read.
- No automatic retry yet.
- Tested on 8 public studies (12 to 1,600 samples); all sequencing ones linked 100%.

---

## Functions (for programmers)

| Function | Input | Output |
|---|---|---|
| `fetch_geo_series(gse_id, limit=None, timeout=30)` | GSE | one row per sample |
| `fetch_sra_bioproject(accession, limit=None, timeout=30)` | PRJNA / SRP | one row per run |
| `fetch_ena_accession(accession, limit=None, timeout=30)` | SRR, PRJNA, SRP, SRX, SAMN | ENA run records incl. `fastq_ftp` |
| `merge_geo_sra(geo_df, sra_df, how="inner")` | the two tables above | linked table |
| `fetch_and_merge_geo_sra(gse_id, sra_term, how="inner")` | GSE + PRJNA | linked table |

`how`: `inner` = only samples with runs, `left` = all GEO samples, `right` = all runs, `outer` = everything.

## License

MIT. Questions or bugs: https://github.com/KiarashBabaei/Biodownloader/issues
