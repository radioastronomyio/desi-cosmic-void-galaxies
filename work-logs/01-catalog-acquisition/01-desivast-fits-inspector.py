#!/usr/bin/env python3
"""
Script Name  : 01-desivast-fits-inspector.py
Description  : Inspects DESIVAST void catalog FITS files to understand HDU structure
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-06-30
Phase        : Phase 01 - Catalog Acquisition
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Inspects DESIVAST void catalog FITS files to understand structure and schema
requirements. Analyzes all 8 DESIVAST files across different algorithms
(VIDE, ZOBOV, REVOLVER, VoidFinder) and galactic caps (NGC/SGC). Outputs
column analysis showing common vs algorithm-specific columns and row counts.

Usage
-----
    python 01-desivast-fits-inspector.py [data_directory]

Examples
--------
    python 01-desivast-fits-inspector.py
        Inspects files in default ./data/desivast directory.

    python 01-desivast-fits-inspector.py /mnt/proj-fs02/desi-dr1/desivast
        Inspects files in specified directory.
"""

# =============================================================================
# Imports
# =============================================================================

import sys
from pathlib import Path
from typing import Dict, List, Set

try:
    import numpy as np
    from astropy.io import fits
    from astropy.table import Table
except ImportError:
    print("❌ Error: astropy is required for FITS inspection")
    print("   Install with: pip install astropy")
    sys.exit(1)

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_DATA_DIR = Path("./data/desivast")

DESIVAST_FILES = [
    "DESIVAST_BGS_VOLLIM_V2_REVOLVER_NGC.fits",
    "DESIVAST_BGS_VOLLIM_V2_REVOLVER_SGC.fits",
    "DESIVAST_BGS_VOLLIM_V2_VIDE_NGC.fits",
    "DESIVAST_BGS_VOLLIM_V2_VIDE_SGC.fits",
    "DESIVAST_BGS_VOLLIM_V2_ZOBOV_NGC.fits",
    "DESIVAST_BGS_VOLLIM_V2_ZOBOV_SGC.fits",
    "DESIVAST_BGS_VOLLIM_VoidFinder_NGC.fits",
    "DESIVAST_BGS_VOLLIM_VoidFinder_SGC.fits",
]

# =============================================================================
# Functions
# =============================================================================


def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def extract_algorithm(filename: str) -> str:
    """Extract algorithm name from filename."""
    if "REVOLVER" in filename:
        return "REVOLVER"
    elif "VIDE" in filename:
        return "VIDE"
    elif "ZOBOV" in filename:
        return "ZOBOV"
    elif "VoidFinder" in filename:
        return "VoidFinder"
    else:
        return "Unknown"


def extract_galactic_cap(filename: str) -> str:
    """Extract galactic cap from filename."""
    if "NGC" in filename:
        return "NGC"
    elif "SGC" in filename:
        return "SGC"
    else:
        return "Unknown"


def inspect_fits_file(file_path: Path) -> Dict:
    """
    Inspect a single FITS file and return structure info.
    
    FITS files contain multiple Header Data Units (HDUs). HDU 0 is always the
    Primary HDU containing only headers (no tabular data). The science data
    lives in extension HDUs (index 1+), typically as binary tables.
    """
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        file_size = file_path.stat().st_size
        algorithm = extract_algorithm(file_path.name)
        galactic_cap = extract_galactic_cap(file_path.name)

        with fits.open(file_path) as hdul:
            info = {
                "filename": file_path.name,
                "algorithm": algorithm,
                "galactic_cap": galactic_cap,
                "file_size": file_size,
                "num_hdus": len(hdul),
                "hdus": [],
            }

            # Inspect each HDU
            for i, hdu in enumerate(hdul):
                hdu_info = {"index": i, "type": type(hdu).__name__, "name": hdu.name}

                # Get header info
                if hasattr(hdu, "header"):
                    hdu_info["header_cards"] = len(hdu.header)

                # Get data info for table HDUs
                # Binary table HDUs have a .columns attribute containing schema info.
                # Image HDUs have .data with shape/dtype but no columns.
                if hasattr(hdu, "data") and hdu.data is not None:
                    if hasattr(hdu.data, "columns"):  # Binary table
                        hdu_info["num_columns"] = len(hdu.data.columns)
                        hdu_info["num_rows"] = len(hdu.data)
                        hdu_info["columns"] = []

                        for col in hdu.data.columns:
                            col_info = {
                                "name": col.name,
                                "format": col.format,
                                "dtype": str(col.dtype)
                                if hasattr(col, "dtype")
                                else "unknown",
                            }
                            if hasattr(col, "unit") and col.unit:
                                col_info["unit"] = str(col.unit)
                            hdu_info["columns"].append(col_info)

                    elif hasattr(hdu.data, "shape"):  # Image data
                        hdu_info["data_shape"] = hdu.data.shape
                        hdu_info["data_dtype"] = str(hdu.data.dtype)

                info["hdus"].append(hdu_info)

            return info

    except Exception as e:
        return {"error": f"Error reading {file_path}: {e}"}


def print_file_summary(info: Dict) -> None:
    """Print summary for a single file."""
    if "error" in info:
        print(f"❌ {info['error']}")
        return

    print(f"📄 {info['filename']}")
    print(f"   🔬 Algorithm: {info['algorithm']}")
    print(f"   🌌 Galactic Cap: {info['galactic_cap']}")
    print(f"   💾 Size: {format_size(info['file_size'])}")
    print(f"   📦 HDUs: {info['num_hdus']}")

    for hdu in info["hdus"]:
        print(f"      [{hdu['index']}] {hdu['type']} '{hdu['name']}'", end="")
        if "num_rows" in hdu:
            print(f" - {hdu['num_rows']} rows, {hdu['num_columns']} columns")
        elif "data_shape" in hdu:
            print(f" - shape: {hdu['data_shape']}")
        else:
            print()


def print_column_analysis(all_info: List[Dict]) -> None:
    """
    Analyze and print column information across all files.
    
    Different void-finding algorithms produce different output columns. This
    analysis identifies which columns are common (safe for unified schema) vs.
    algorithm-specific (require NULLable columns or separate tables).
    """
    print("\n📊 Column Analysis Across All Files:")

    # Collect all columns
    all_columns: Set[str] = set()
    column_info: Dict[str, Dict] = {}

    for info in all_info:
        if "error" in info:
            continue

        for hdu in info["hdus"]:
            if "columns" in hdu:
                for col in hdu["columns"]:
                    col_name = col["name"]
                    all_columns.add(col_name)

                    if col_name not in column_info:
                        column_info[col_name] = {
                            "dtypes": set(),
                            "formats": set(),
                            "units": set(),
                            "files": set(),
                        }

                    column_info[col_name]["dtypes"].add(col.get("dtype", "unknown"))
                    column_info[col_name]["formats"].add(col.get("format", "unknown"))
                    if "unit" in col:
                        column_info[col_name]["units"].add(col["unit"])
                    column_info[col_name]["files"].add(info["algorithm"])

    # Print common columns (present in all algorithms)
    algorithms = set(info["algorithm"] for info in all_info if "error" not in info)
    common_columns = [
        col for col in all_columns if len(column_info[col]["files"]) == len(algorithms)
    ]

    if common_columns:
        print(f"\n✅ Common columns (present in all {len(algorithms)} algorithms):")
        for col in sorted(common_columns):
            info = column_info[col]
            dtype = (
                list(info["dtypes"])[0]
                if len(info["dtypes"]) == 1
                else f"Multiple: {info['dtypes']}"
            )
            units = (
                list(info["units"])[0]
                if len(info["units"]) == 1
                else f"Multiple: {info['units']}"
                if info["units"]
                else "None"
            )
            print(f"   📋 {col}: {dtype} ({units})")

    # Print algorithm-specific columns
    for algorithm in sorted(algorithms):
        algo_columns = [
            col
            for col in all_columns
            if algorithm in column_info[col]["files"]
            and len(column_info[col]["files"]) < len(algorithms)
        ]
        if algo_columns:
            print(f"\n🔧 {algorithm}-specific columns:")
            for col in sorted(algo_columns):
                info = column_info[col]
                dtype = (
                    list(info["dtypes"])[0]
                    if len(info["dtypes"]) == 1
                    else f"Multiple: {info['dtypes']}"
                )
                print(f"   📋 {col}: {dtype}")


def print_row_counts(all_info: List[Dict]) -> None:
    """Print row count analysis."""
    print("\n📊 Row Count Analysis:")

    by_algorithm = {}
    for info in all_info:
        if "error" in info:
            continue

        algorithm = info["algorithm"]
        galactic_cap = info["galactic_cap"]

        if algorithm not in by_algorithm:
            by_algorithm[algorithm] = {}

        # Find main data table (usually HDU 1)
        for hdu in info["hdus"]:
            if "num_rows" in hdu and hdu["index"] > 0:  # Skip primary HDU
                by_algorithm[algorithm][galactic_cap] = hdu["num_rows"]
                break

    for algorithm in sorted(by_algorithm.keys()):
        caps = by_algorithm[algorithm]
        total = sum(caps.values())
        print(f"   🔬 {algorithm}:")
        for cap in ["NGC", "SGC"]:
            if cap in caps:
                print(f"      {cap}: {caps[cap]:,} voids")
        print(f"      Total: {total:,} voids")


def main() -> int:
    """Inspect all DESIVAST FITS files."""
    # Parse command line arguments
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    else:
        data_dir = DEFAULT_DATA_DIR

    print("🔍 DESIVAST FITS Inspector")
    print("=" * 40)
    print(f"📁 Data directory: {data_dir}")

    if not data_dir.exists():
        print(f"❌ Error: Directory {data_dir} does not exist")
        print("   Run the DESIVAST downloader first")
        return 1

    # Inspect all files
    print(f"\n📋 Inspecting {len(DESIVAST_FILES)} DESIVAST files...")
    all_info = []

    for filename in DESIVAST_FILES:
        file_path = data_dir / filename
        info = inspect_fits_file(file_path)
        all_info.append(info)
        print_file_summary(info)
        print()

    # Cross-file analysis
    valid_files = [info for info in all_info if "error" not in info]

    if valid_files:
        print_column_analysis(all_info)
        print_row_counts(all_info)

        print("\n🎉 Inspection complete!")
        print(f"   ✅ Successfully inspected: {len(valid_files)}/{len(DESIVAST_FILES)} files")
    else:
        print("❌ No valid files found. Check that DESIVAST files have been downloaded.")
        return 1

    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
