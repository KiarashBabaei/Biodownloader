import pandas as pd
import pytest

import biodownloader
from biodownloader import cli


def test_version_is_a_string():
    assert isinstance(biodownloader.__version__, str)


def test_cli_requires_id_for_geo():
    with pytest.raises(SystemExit):
        cli.main(["--source", "geo"])


def test_cli_merge_requires_both_accessions():
    with pytest.raises(SystemExit):
        cli.main(["--source", "merge", "--geo", "GSE1"])


def test_cli_writes_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "fetch_geo_series", lambda acc, limit=None: pd.DataFrame({"GSM": ["GSM1"]}))
    out = tmp_path / "geo.csv"
    assert cli.main(["--source", "geo", "--id", "GSE1", "--out", str(out)]) == 0
    assert out.read_text().startswith("GSM")


def test_cli_tsv_uses_tabs(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "fetch_ena_accession", lambda acc, limit=None: pd.DataFrame({"a": [1], "b": [2]}))
    out = tmp_path / "ena.tsv"
    cli.main(["--source", "ena", "--id", "SRR1", "--out", str(out)])
    assert "a\tb" in out.read_text()


def test_cli_merge_calls_wrapper(monkeypatch):
    seen = {}

    def fake(gse, sra, geo_limit=None, sra_limit=None, how="inner"):
        seen.update(gse=gse, sra=sra, how=how)
        return pd.DataFrame({"GSM": ["GSM1"]})

    monkeypatch.setattr(cli, "fetch_and_merge_geo_sra", fake)
    assert cli.main(["--source", "merge", "--geo", "GSE1", "--sra", "PRJNA1", "--how", "left"]) == 0
    assert seen == {"gse": "GSE1", "sra": "PRJNA1", "how": "left"}
