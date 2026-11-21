"""
BioDownloader: Python tools for downloading and structuring
GEO / SRA / ENA metadata.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

from .geo import fetch_geo_series
from .sra import fetch_sra_bioproject
from .ena import fetch_ena_accession
from .integrate import merge_geo_sra, fetch_and_merge_geo_sra

try:
    __version__ = _pkg_version("biodownloader")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "unknown"

__all__ = [
    "fetch_geo_series",
    "fetch_sra_bioproject",
    "fetch_ena_accession",
    "merge_geo_sra",
    "fetch_and_merge_geo_sra",
    "__version__",
]
