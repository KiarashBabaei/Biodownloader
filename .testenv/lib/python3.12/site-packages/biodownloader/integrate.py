from __future__ import annotations

import re
from typing import Optional

import pandas as pd

from biodownloader.geo import fetch_geo_series
from biodownloader.sra import fetch_sra_bioproject


GSM_PATTERN = re.compile(r"GSM\d+")


def _detect_geo_gsm_column(df: pd.DataFrame) -> Optional[str]:
    """
    Try to detect the GEO sample ID column (typically 'GSM' or similar).
    """
    # First: explicit candidates
    candidate_names = ["GSM", "Sample", "Sample_ID", "GEO_accession"]
    for col in df.columns:
        if col in candidate_names or col.upper() in ("GSM", "SAMPLE", "GEO_ACCESSION"):
            series = df[col].astype(str)
            if series.str.contains(GSM_PATTERN).any():
                return col

    # Fallback: scan all object columns for GSM-like patterns
    for col in df.select_dtypes(include="object").columns:
        series = df[col].astype(str)
        if series.str.fullmatch(GSM_PATTERN).any():
            return col

    return None


def _detect_sra_gsm_column(df: pd.DataFrame) -> Optional[str]:
    """
    Try to detect the SRA column that contains GEO GSM IDs.
    Often this is 'SampleName' or a similar text field.
    """
    candidate_names = ["SampleName", "sample_name", "GEO_Accession", "geo_accession"]
    for col in df.columns:
        if col in candidate_names or col.lower() in ("samplename", "sample_name", "geo_accession"):
            series = df[col].astype(str)
            if series.str.contains(GSM_PATTERN).any():
                return col

    # Fallback: scan all object columns for a GSM substring
    for col in df.select_dtypes(include="object").columns:
        series = df[col].astype(str)
        if series.str.contains(GSM_PATTERN).any():
            return col

    return None


def merge_geo_sra(
    geo_df: pd.DataFrame,
    sra_df: pd.DataFrame,
    how: str = "inner",
    geo_gsm_col: Optional[str] = None,
    sra_gsm_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Merge GEO and SRA metadata tables on a shared GSM-like identifier.

    Parameters
    ----------
    geo_df : pandas.DataFrame
        Table returned by `fetch_geo_series`.
    sra_df : pandas.DataFrame
        Table returned by `fetch_sra_bioproject`.
    how : str
        Pandas merge 'how' parameter ('inner', 'left', 'right', 'outer').
    geo_gsm_col : str, optional
        Column name in GEO table that contains GSM IDs.
        If None, an automatic detection is attempted.
    sra_gsm_col : str, optional
        Column name in SRA table that contains GSM IDs (or GSM-like text).
        If None, an automatic detection is attempted.

    Returns
    -------
    pandas.DataFrame
        Merged table with suffixes '_geo' and '_sra' where needed.

    Raises
    ------
    ValueError
        If no suitable GSM-like columns can be detected.
    """
    if geo_gsm_col is None:
        geo_gsm_col = _detect_geo_gsm_column(geo_df)
    if sra_gsm_col is None:
        sra_gsm_col = _detect_sra_gsm_column(sra_df)

    if geo_gsm_col is None or sra_gsm_col is None:
        raise ValueError(
            "Could not detect GSM-like columns automatically. "
            "Please provide 'geo_gsm_col' and 'sra_gsm_col' explicitly."
        )

    merged = geo_df.merge(
        sra_df,
        left_on=geo_gsm_col,
        right_on=sra_gsm_col,
        how=how,
        suffixes=("_geo", "_sra"),
    )
    return merged


def fetch_and_merge_geo_sra(
    gse_id: str,
    sra_term: str,
    geo_limit: Optional[int] = None,
    sra_limit: Optional[int] = None,
    how: str = "inner",
) -> pd.DataFrame:
    """
    Convenience wrapper: fetch GEO + SRA metadata and merge them.

    Parameters
    ----------
    gse_id : str
        GEO series accession (e.g. "GSE181294").
    sra_term : str
        SRA search term, typically a BioProject or study accession
        (e.g. "PRJNA730495" or "SRP320091").
    geo_limit : int, optional
        Maximum number of GEO samples to fetch (None = no limit).
    sra_limit : int, optional
        Maximum number of SRA runs to fetch (None = no limit).
    how : str
        Merge mode ('inner', 'left', etc.).

    Returns
    -------
    pandas.DataFrame
        Merged GEO–SRA metadata table.
    """
    geo_df = fetch_geo_series(gse_id, limit=geo_limit)
    sra_df = fetch_sra_bioproject(sra_term, limit=sra_limit)

    if geo_df.empty or sra_df.empty:
        # Return an empty merge with the expected shape,
        # instead of raising an exception.
        return merge_geo_sra(geo_df, sra_df, how=how) if not geo_df.empty and not sra_df.empty else pd.DataFrame()

    merged = merge_geo_sra(geo_df, sra_df, how=how)
    return merged
