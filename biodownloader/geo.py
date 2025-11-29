from __future__ import annotations

import re
from typing import List, Dict, Optional

import pandas as pd
import requests


GEO_BASE_URL = (
    "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?"
    "targ=all&form=text&view=quick&acc="
)


def _parse_geo_soft_quick(raw_text: str, gse_id: str, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Parse the GEO 'quick' SOFT text into a tidy sample-level DataFrame.

    Parameters
    ----------
    raw_text : str
        The full SOFT/quick text returned by GEO.
    gse_id : str
        The GSE accession (for adding as a column).
    limit : int, optional
        Optional maximum number of samples to parse.

    Returns
    -------
    pandas.DataFrame
        Rows: GSM samples
        Columns: GSE, GSM, title, organism, source_name, characteristics
    """
    samples: List[Dict[str, str]] = []

    current: Dict[str, List[str]] | None = None
    current_gsm: Optional[str] = None

    # regex to detect the start of a new sample block
    sample_start_re = re.compile(r"^\^SAMPLE\s=\s(GSM\d+)")

    # iterate line by line over the SOFT text
    for line in raw_text.splitlines():
        line = line.rstrip("\n")

        # start of a new sample
        m = sample_start_re.match(line)
        if m:
            # if we had a previous sample, finalize and store it
            if current is not None and current_gsm is not None:
                samples.append(_finalize_sample_dict(current, current_gsm, gse_id))

                if limit is not None and len(samples) >= limit:
                    break

            # initialize container for a new sample
            current = {
                "title": [],
                "organism": [],
                "source_name": [],
                "characteristics": [],
            }
            current_gsm = m.group(1)
            continue

        if current is None:
            # we have not entered any SAMPLE block yet
            continue

        # handle the !Sample_* lines
        if line.startswith("!Sample_title ="):
            value = line.split("=", 1)[1].strip()
            current["title"].append(value)
        elif line.startswith("!Sample_organism_ch1 ="):
            value = line.split("=", 1)[1].strip()
            current["organism"].append(value)
        elif line.startswith("!Sample_source_name_ch1 ="):
            value = line.split("=", 1)[1].strip()
            current["source_name"].append(value)
        elif line.startswith("!Sample_characteristics_ch1 ="):
            value = line.split("=", 1)[1].strip()
            current["characteristics"].append(value)

    # finalize and append the last sample if present
    if current is not None and current_gsm is not None:
        samples.append(_finalize_sample_dict(current, current_gsm, gse_id))

    if not samples:
        return pd.DataFrame(
            columns=["GSE", "GSM", "title", "organism", "source_name", "characteristics"]
        )

    return pd.DataFrame(samples)


def _finalize_sample_dict(
    raw_dict: Dict[str, List[str]],
    gsm: str,
    gse_id: str
) -> Dict[str, str]:
    """Helper: convert lists to strings and attach GSM/GSE identifiers."""
    def join_or_empty(values: List[str]) -> str:
        if not values:
            return ""
        # if there are multiple values, join them with ";"
        return "; ".join(values)

    return {
        "GSE": gse_id,
        "GSM": gsm,
        "title": join_or_empty(raw_dict.get("title", [])),
        "organism": join_or_empty(raw_dict.get("organism", [])),
        "source_name": join_or_empty(raw_dict.get("source_name", [])),
        "characteristics": join_or_empty(raw_dict.get("characteristics", [])),
    }


def fetch_geo_series(gse_id: str, limit: int | None = None, timeout: int = 30) -> pd.DataFrame:
    """
    Fetch metadata for a GEO series (GSE*) and return a tidy sample-level table.

    Parameters
    ----------
    gse_id : str
        GEO Series accession (e.g. "GSE181294").
    limit : int, optional
        Optional maximum number of samples to parse (useful for testing).
    timeout : int, optional
        HTTP timeout in seconds.

    Returns
    -------
    pandas.DataFrame
        One row per GSM sample with at least the following columns:
        - GSE
        - GSM
        - title
        - organism
        - source_name
        - characteristics

    Raises
    ------
    ValueError
        If the GSE ID does not look valid.
    requests.HTTPError
        If the GEO server returns an error status code.
    """
    gse_id = gse_id.strip()

    if not gse_id.upper().startswith("GSE"):
        raise ValueError(f"Expected a GEO Series accession starting with 'GSE', got: {gse_id!r}")

    url = GEO_BASE_URL + gse_id
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()

    text = resp.text

    # if GEO returns nothing useful or a weird response, fall back to an empty DataFrame
    if "Series" not in text and "^SAMPLE" not in text:
        # be conservative and return an empty DataFrame with the expected columns
        return pd.DataFrame(
            columns=["GSE", "GSM", "title", "organism", "source_name", "characteristics"]
        )

    return _parse_geo_soft_quick(text, gse_id=gse_id, limit=limit)

