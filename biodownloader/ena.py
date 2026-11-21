from __future__ import annotations

import io
from typing import Optional

import pandas as pd
import requests

# ENA Browser API base URL
ENA_BASE_URL = "https://www.ebi.ac.uk/ena/portal/api/search"

# accession prefix -> searchable field of the ENA "read_run" result
_PREFIX_TO_FIELD = (
    (("SRR", "ERR", "DRR"), "run_accession"),
    (("PRJ",), "study_accession"),
    (("SRP", "ERP", "DRP"), "secondary_study_accession"),
    (("SRX", "ERX", "DRX"), "experiment_accession"),
    (("SAMN", "SAME", "SAMD"), "sample_accession"),
    (("SRS", "ERS", "DRS"), "secondary_sample_accession"),
)


def _field_for_accession(accession: str) -> Optional[str]:
    """Return the ENA read_run field that matches this accession type, or None."""
    acc = accession.strip().upper()
    for prefixes, field in _PREFIX_TO_FIELD:
        if acc.startswith(prefixes):
            return field
    return None


def _ena_query(
    query: str,
    result: str = "read_run",
    limit: Optional[int] = None,
    timeout: int = 30,
) -> pd.DataFrame:
    """
    Internal helper to query ENA and return a DataFrame.
    """
    params = {
        "result": result,
        "query": query,
        "format": "tsv",
        "limit": limit if limit is not None else 0,  # 0 => no server-side limit
        "fields": (
            "run_accession,study_accession,secondary_study_accession,"
            "sample_accession,experiment_accession,scientific_name,"
            "library_strategy,instrument_platform,fastq_ftp,description"
        ),
    }

    resp = requests.get(ENA_BASE_URL, params=params, timeout=timeout)
    resp.raise_for_status()

    text = resp.text
    if not text.strip():
        return pd.DataFrame()

    # ENA returns a TSV header even if there are 0 rows; pandas can read it.
    df = pd.read_csv(io.StringIO(text), sep="\t")

    if limit is not None:
        df = df.head(limit)

    return df


def fetch_ena_accession(
    accession: str,
    limit: Optional[int] = None,
    timeout: int = 30,
) -> pd.DataFrame:
    """
    Fetch ENA metadata for a given accession (run, study, etc.) using the ENA portal API.

    Parameters
    ----------
    accession : str
        ENA accession such as:
        - Run:      ERR..., SRR..., DRR...
        - Study:    PRJEB..., PRJNA...
        - Sample:   SAMEA..., SAMN...
        Any valid ENA-supported accession is accepted.
    limit : int, optional
        If provided, only the first `limit` rows are returned.
    timeout : int
        HTTP timeout in seconds.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with ENA metadata in tabular form.
        Returns an empty DataFrame if no records are found.

    Raises
    ------
    ValueError
        If accession is empty.
    requests.HTTPError
        If ENA returns a non-200 status code.
    """
    accession = accession.strip()
    if not accession:
        raise ValueError("accession cannot be empty (e.g., 'SRR23080510' or 'PRJEB12345').")

    field = _field_for_accession(accession)

    df = pd.DataFrame()
    if field is not None:
        df = _ena_query(f'{field}="{accession}"', result="read_run", limit=limit, timeout=timeout)

    # Fallback: generic accession query (kept for backward compatibility)
    if df.empty:
        df = _ena_query(f"accession={accession}", result="read_run", limit=limit, timeout=timeout)

    return df
