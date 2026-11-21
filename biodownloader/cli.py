from __future__ import annotations

import argparse
from typing import List, Optional

import pandas as pd

from .geo import fetch_geo_series
from .sra import fetch_sra_bioproject
from .ena import fetch_ena_accession
from .integrate import fetch_and_merge_geo_sra


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="biofetch",
        description="Fetch GEO / SRA / ENA metadata and export it as CSV or TSV.",
    )

    parser.add_argument(
        "--source",
        choices=["geo", "sra", "ena", "merge"],
        required=True,
        help="Which database to query: geo, sra, ena, or merge (GEO + SRA).",
    )

    parser.add_argument(
        "--id",
        default=None,
        help="Accession for --source geo/sra/ena (e.g. GSE181294, PRJNA751490, SRR23080510).",
    )

    parser.add_argument("--geo", default=None, help="GEO series accession (merge only).")
    parser.add_argument("--sra", default=None, help="SRA/BioProject accession (merge only).")
    parser.add_argument(
        "--how",
        choices=["inner", "left", "right", "outer"],
        default="inner",
        help="Merge mode (merge only, default: inner).",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of records (geo/sra/ena).",
    )
    parser.add_argument("--geo-limit", type=int, default=None, help="Maximum GEO samples (merge only).")
    parser.add_argument("--sra-limit", type=int, default=None, help="Maximum SRA runs (merge only).")

    parser.add_argument(
        "--out",
        default=None,
        help="Output file (.csv, or .tsv/.txt for tab-separated). If omitted, prints a preview.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.source == "merge":
        if not (args.geo and args.sra):
            parser.error("--source merge requires both --geo and --sra.")
        df = fetch_and_merge_geo_sra(
            args.geo,
            args.sra,
            geo_limit=args.geo_limit,
            sra_limit=args.sra_limit,
            how=args.how,
        )
    else:
        if not args.id:
            parser.error(f"--id is required for --source {args.source}.")
        fetch = {
            "geo": fetch_geo_series,
            "sra": fetch_sra_bioproject,
            "ena": fetch_ena_accession,
        }[args.source]
        df = fetch(args.id, limit=args.limit)

    if args.out:
        sep = "\t" if args.out.lower().endswith((".tsv", ".txt")) else ","
        df.to_csv(args.out, index=False, sep=sep)
        print(f"Saved {len(df)} records to {args.out}")
    else:
        with pd.option_context("display.max_columns", None, "display.width", 200):
            print(df.head())
        print(f"\nTotal records: {len(df)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
