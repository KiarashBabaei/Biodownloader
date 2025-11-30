import argparse
import sys

from .geo import fetch_geo_series
from .sra import fetch_sra_bioproject
from .ena import fetch_ena_accession


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="biofetch",
        description="Fetch GEO / SRA / ENA metadata and export as CSV."
    )

    parser.add_argument(
        "--source",
        choices=["geo", "sra", "ena"],
        required=True,
        help="Which database to query: GEO, SRA or ENA."
    )

    parser.add_argument(
        "--id",
        required=True,
        help="Accession ID (e.g. GSE181294, PRJNA123456, ERR1234567)."
    )

    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV file path. If not provided, prints a preview to stdout."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of records (for safety/testing)."
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.source == "geo":
        df = fetch_geo_series(args.id, limit=args.limit)
    elif args.source == "sra":
        df = fetch_sra_bioproject(args.id, limit=args.limit)
    elif args.source == "ena":
        df = fetch_ena_accession(args.id, limit=args.limit)
    else:
        parser.error("Unknown source")
        return 1

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} records to {args.out}")
    else:
        # فقط چند رکورد برای preview
        print(df.head())
        print(f"\nTotal records: {len(df)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

