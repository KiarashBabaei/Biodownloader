from __future__ import annotations

import io
from typing import Optional, Tuple

import pandas as pd
import requests
import xml.etree.ElementTree as ET


# NCBI E-utilities base endpoint
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def _esearch_sra(
    accession: str,
    timeout: int = 30,
) -> Tuple[Optional[str], Optional[str], int]:
    """
    Run NCBI esearch on the SRA database to obtain WebEnv, QueryKey, and count.

    Parameters
    ----------
    accession : str
        PRJNA..., SRP..., or any SRA search term.
    timeout : int
        HTTP timeout in seconds.

    Returns
    -------
    (webenv, query_key, count)
    If count == 0, or WebEnv/QueryKey missing → nothing found.
    """

    params = {
        "db": "sra",
        "term": accession,
        "usehistory": "y",
        "retmode": "xml",
    }

    resp = requests.get(EUTILS_BASE + "esearch.fcgi", params=params, timeout=timeout)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)

    webenv = root.findtext(".//WebEnv")
    query_key = root.findtext(".//QueryKey")
    count_text = root.findtext(".//Count") or "0"

    try:
        count = int(count_text)
    except ValueError:
        count = 0

    if not webenv or not query_key or count == 0:
        return None, None, 0

    return webenv, query_key, count


def fetch_sra_bioproject(
    accession: str,
    limit: Optional[int] = None,
    timeout: int = 30,
) -> pd.DataFrame:
    """
    Fetch SRA RunInfo metadata using NCBI E-utilities (esearch → efetch).

    This replicates the behavior of:
        esearch -db sra -query 'PRJNAxxxx' | efetch -format runinfo

    Parameters
    ----------
    accession : str
        A BioProject (PRJNA...), SRA Study (SRP...), or general SRA term.
    limit : int, optional
        If provided, only the first N rows of RunInfo are returned.
    timeout : int
        HTTP timeout in seconds.

    Returns
    -------
    pandas.DataFrame
        A RunInfo table with columns such as:
            Run, BioProject, BioSample, Experiment, SampleName, LibraryLayout,
            LibraryStrategy, Platform, Model, ScientificName, ReleaseDate, etc.
        Returns an empty DataFrame if no matches found.

    Raises
    ------
    ValueError
        If accession is empty.
    requests.HTTPError
        If NCBI returns a non-200 status.
    """

    accession = accession.strip()
    if not accession:
        raise ValueError("accession cannot be empty (e.g., 'PRJNA730495').")

    # Step 1 — esearch: get WebEnv and QueryKey
    webenv, query_key, count = _esearch_sra(accession, timeout=timeout)
    if not webenv or not query_key or count == 0:
        return pd.DataFrame()  # nothing found

    # Step 2 — efetch: retrieve RunInfo as CSV
    params = {
        "db": "sra",
        "query_key": query_key,
        "WebEnv": webenv,
        "retmode": "text",
        "rettype": "runinfo",
    }

    resp = requests.get(EUTILS_BASE + "efetch.fcgi", params=params, timeout=timeout)
    resp.raise_for_status()

    text = resp.text
    if not text.strip():
        return pd.DataFrame()

    df = pd.read_csv(io.StringIO(text))

    if limit is not None:
        df = df.head(limit)

    return df



