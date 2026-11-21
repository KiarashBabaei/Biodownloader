from __future__ import annotations

import re
import warnings
from typing import Optional

import pandas as pd

from biodownloader.geo import fetch_geo_series
from biodownloader.sra import fetch_sra_bioproject


GSM_PATTERN = re.compile(r"GSM\d+")
_KEY = "__gsm_key__"


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
    for col in df.select_dtypes(include=["object", "string"]).columns:
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
    for col in df.select_dtypes(include=["object", "string"]).columns:
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

    When `sra_gsm_col` is not given, each SRA run is linked to a GEO sample in
    this order:
      1. a GSM ID found in the SRA GSM-like column (e.g. 'SampleName')
      2. SRA 'BioSample' == GEO 'BioSample'
      3. SRA 'Experiment' == GEO 'SRX'

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
        If None, an automatic detection is attempted (with BioSample and
        Experiment fallbacks). If given, only this column is used.

    Returns
    -------
    pandas.DataFrame
        Merged table with suffixes '_geo' and '_sra' where needed.

    Raises
    ------
    ValueError
        If no suitable GSM-like columns can be detected.
    """
    auto_sra = sra_gsm_col is None

    if geo_gsm_col is None:
        geo_gsm_col = _detect_geo_gsm_column(geo_df)
    if sra_gsm_col is None:
        sra_gsm_col = _detect_sra_gsm_column(sra_df)

    if geo_gsm_col is None:
        raise ValueError(
            "Could not detect GSM-like columns automatically. "
            "Please provide 'geo_gsm_col' and 'sra_gsm_col' explicitly."
        )

    sra = sra_df.copy()

    # Step 1: direct GSM match through the SRA GSM-like column
    if sra_gsm_col is not None:
        if auto_sra:
            key = sra[sra_gsm_col].astype(str).str.extract(r"(GSM\d+)", expand=False)
        else:
            key = sra[sra_gsm_col].copy()
    else:
        key = pd.Series(pd.NA, index=sra.index, dtype="object")

    # Steps 2-3: fallback through BioSample, then Experiment (SRX)
    fallback_used = False
    if auto_sra:
        geo_ids = geo_df[geo_gsm_col].astype(str).str.extract(r"(GSM\d+)", expand=False)
        for geo_col, sra_col in (("BioSample", "BioSample"), ("SRX", "Experiment")):
            if geo_col in geo_df.columns and sra_col in sra.columns:
                fallback_used = True
                mapping = {}
                for value, gsm in zip(geo_df[geo_col], geo_ids):
                    if pd.isna(value) or pd.isna(gsm):
                        continue
                    value = str(value).strip()
                    if value and value.lower() != "nan":
                        mapping.setdefault(value, gsm)
                key = key.fillna(sra[sra_col].astype(str).str.strip().map(mapping))

    if sra_gsm_col is None and not fallback_used:
        raise ValueError(
            "Could not detect GSM-like columns automatically. "
            "Please provide 'geo_gsm_col' and 'sra_gsm_col' explicitly."
        )

    sra[_KEY] = key
    merged = geo_df.merge(
        sra,
        left_on=geo_gsm_col,
        right_on=_KEY,
        how=how,
        suffixes=("_geo", "_sra"),
    )
    if how in ("right", "outer") and geo_gsm_col in merged.columns:
        merged[geo_gsm_col] = merged[geo_gsm_col].fillna(merged[_KEY])
    merged = merged.drop(columns=[_KEY])

    if how == "inner" and merged.empty:
        warnings.warn(
            "merge_geo_sra: no GEO sample could be linked to an SRA run. "
            "Check that the GSE and the SRA accession belong to the same study.",
            stacklevel=2,
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
        (e.g. "PRJNA751490" or "SRP320091").
    geo_limit : int, optional
        Maximum number of GEO samples to fetch (None = no limit).
    sra_limit : int, optional
        Maximum number of SRA runs to fetch (None = no limit).
    how : str
        Merge mode ('inner', 'left', etc.).

    Returns
    -------
    pandas.DataFrame
        Merged GEO-SRA metadata table. Empty if either side has no records.
    """
    geo_df = fetch_geo_series(gse_id, limit=geo_limit)
    sra_df = fetch_sra_bioproject(sra_term, limit=sra_limit)

    if geo_df.empty or sra_df.empty:
        return pd.DataFrame()

    return merge_geo_sra(geo_df, sra_df, how=how)
