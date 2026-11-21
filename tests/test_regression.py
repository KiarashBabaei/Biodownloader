import pandas as pd
import pytest
import biodownloader as bd
from biodownloader.ena import _field_for_accession


def test_merge_fallback_biosample():
    geo = pd.DataFrame({"GSM": ["GSM1", "GSM2"], "BioSample": ["SAMN1", "SAMN2"], "SRX": ["SRX1", "SRX2"]})
    sra = pd.DataFrame({
        "Run": ["SRR1", "SRR2", "SRR3"],
        "SampleName": ["GSM1", "SAMN2", "SAMN2"],
        "BioSample": ["SAMN1", "SAMN2", "SAMN2"],
        "Experiment": ["SRX1", "SRX2", "SRX2"],
    })
    out = bd.merge_geo_sra(geo, sra, how="inner")
    assert len(out) == 3
    assert out["GSM"].nunique() == 2


def test_merge_fallback_experiment_only():
    geo = pd.DataFrame({"GSM": ["GSM1"], "SRX": ["SRX1"]})
    sra = pd.DataFrame({"Run": ["SRR1"], "Experiment": ["SRX1"]})
    out = bd.merge_geo_sra(geo, sra, how="inner")
    assert len(out) == 1 and out.loc[0, "GSM"] == "GSM1"


def test_merge_explicit_columns():
    geo = pd.DataFrame({"GSM": ["GSM1", "GSM2"], "title": ["a", "b"]})
    sra = pd.DataFrame({"SampleName": ["GSM1", "GSM2"], "Run": ["SRR1", "SRR2"]})
    out = bd.merge_geo_sra(geo, sra, geo_gsm_col="GSM", sra_gsm_col="SampleName")
    assert len(out) == 2 and "Run" in out.columns


def test_merge_left_keeps_all_geo():
    geo = pd.DataFrame({"GSM": ["GSM1", "GSM2"]})
    sra = pd.DataFrame({"SampleName": ["GSM1"], "Run": ["SRR1"]})
    assert len(bd.merge_geo_sra(geo, sra, how="left")) == 2


def test_merge_outer_keeps_unmatched_sra():
    geo = pd.DataFrame({"GSM": ["GSM1"]})
    sra = pd.DataFrame({"SampleName": ["GSM1", "GSM9"], "Run": ["SRR1", "SRR9"]})
    out = bd.merge_geo_sra(geo, sra, how="outer")
    assert len(out) == 2
    assert out["GSM"].notna().all()


def test_merge_empty_inner_warns():
    geo = pd.DataFrame({"GSM": ["GSM1"]})
    sra = pd.DataFrame({"SampleName": ["GSM9"], "Run": ["SRR1"]})
    with pytest.warns(UserWarning):
        out = bd.merge_geo_sra(geo, sra, how="inner")
    assert out.empty


def test_merge_no_link_raises():
    with pytest.raises(ValueError):
        bd.merge_geo_sra(pd.DataFrame({"GSM": ["GSM1"]}), pd.DataFrame({"Run": ["SRR1"], "x": ["a"]}))


def test_merge_no_gsm_columns_raises():
    with pytest.raises(ValueError):
        bd.merge_geo_sra(pd.DataFrame({"x": [1]}), pd.DataFrame({"y": [2]}))


def test_wrapper_empty_does_not_crash(monkeypatch):
    import biodownloader.integrate as integ
    monkeypatch.setattr(integ, "fetch_geo_series", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(integ, "fetch_sra_bioproject", lambda *a, **k: pd.DataFrame({"Run": ["SRR1"]}))
    assert integ.fetch_and_merge_geo_sra("GSE1", "PRJNA1").empty


@pytest.mark.parametrize("acc,field", [
    ("SRR23080545", "run_accession"),
    ("PRJNA751490", "study_accession"),
    ("PRJEB1787", "study_accession"),
    ("SRP320091", "secondary_study_accession"),
    ("SRX19033464", "experiment_accession"),
    ("SAMN20520006", "sample_accession"),
    ("SRS9000934", "secondary_sample_accession"),
    ("XYZ123", None),
])
def test_ena_field_selection(acc, field):
    assert _field_for_accession(acc) == field


@pytest.mark.parametrize("limit", [1, 3, 5])
def test_geo_limit_exact_and_unique(limit):
    df = bd.fetch_geo_series("GSE120575", limit=limit, timeout=120)
    assert len(df) == limit
    assert df["GSM"].is_unique


def test_ena_study_returns_runs():
    assert len(bd.fetch_ena_accession("PRJNA751490", limit=3, timeout=120)) == 3


def test_merge_covers_all_samples():
    df = bd.fetch_and_merge_geo_sra("GSE181294", "PRJNA751490", how="inner")
    assert df["GSM"].nunique() == 51
    assert len(df) == 168
