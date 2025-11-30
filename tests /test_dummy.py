from biodownloader import fetch_geo_series, fetch_sra_bioproject, fetch_ena_accession


def test_import_and_empty_frames():
    df_geo = fetch_geo_series("GSE000000")
    df_sra = fetch_sra_bioproject("PRJNA000000")
    df_ena = fetch_ena_accession("ERR000000")

    assert list(df_geo.columns)
    assert list(df_sra.columns)
    assert list(df_ena.columns)
