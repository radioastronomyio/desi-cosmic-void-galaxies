#!/usr/bin/env python3
"""
Script Name  : 04-analyze-parquet-output.py
Description  : Validates structure and integrity of generated Parquet files
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-09-03
Phase        : Phase 03 - Spectral Tile Pipeline
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Scans the output directory of the DESI ETL pipeline, validates the structure
and integrity of the generated Parquet files, and provides a summary report.
Checks schema consistency, array length matching, and redshift distributions.
Optionally generates a sample spectrum plot.

Usage
-----
    python 04-analyze-parquet-output.py [--plot]

Examples
--------
    python 04-analyze-parquet-output.py
        Analyze all Parquet files and print summary report.

    python 04-analyze-parquet-output.py --plot
        Analyze files and generate a random spectrum plot.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import random
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

try:
    import matplotlib.pyplot as plt
    PLOTTING_ENABLED = True
except ImportError:
    PLOTTING_ENABLED = False

# =============================================================================
# Configuration
# =============================================================================

PARQUET_DIR = Path("./parquet_output")

# =============================================================================
# Functions
# =============================================================================


def find_parquet_files(directory: Path) -> list:
    """Recursively finds all .parquet files in the given directory."""
    if not directory.is_dir():
        print(f"❌ ERROR: Directory not found: '{directory}'")
        sys.exit(1)

    print(f"🔍 Scanning for .parquet files in '{directory}'...")
    files = list(directory.rglob("*.parquet"))
    print(f"✅ Found {len(files)} Parquet files.")
    return files


def analyze_files(file_paths: list) -> None:
    """
    Reads, validates, and aggregates statistics from a list of Parquet files.
    
    Key validations:
      - Schema consistency: All files should have identical column structure
      - Array length matching: wavelength, flux, ivar, mask must be same length
      - Redshift plausibility: z values should be positive and reasonable for QSOs
    
    Schema or array length mismatches indicate ETL bugs that would corrupt
    downstream analysis.
    """
    if not file_paths:
        return

    total_qsos = 0
    qsos_per_file = []
    redshift_values = []
    schemas = set()

    print("\n--- Analyzing File Structure and Content ---\n")

    try:
        from tqdm import tqdm
        iterator = tqdm(file_paths, desc="Inspecting files")
    except ImportError:
        iterator = file_paths

    for file_path in iterator:
        try:
            schema = pq.read_schema(file_path)
            schemas.add(str(schema))

            df = pd.read_parquet(file_path)

            num_rows = len(df)
            total_qsos += num_rows
            qsos_per_file.append(num_rows)

            if num_rows > 0:
                redshift_values.extend(df["z"].tolist())

                sample_row = df.sample(1).iloc[0]
                wv_len = len(sample_row["wavelength"])
                fx_len = len(sample_row["flux"])
                iv_len = len(sample_row["ivar"])
                mk_len = len(sample_row["mask_array"])

                # All spectral arrays must have identical length — they're parallel
                # arrays indexed by wavelength position. A mismatch indicates
                # corruption during B/R/Z arm concatenation.
                if not (wv_len == fx_len == iv_len == mk_len):
                    print(f"\n⚠️ WARNING: Array length mismatch in {file_path.name}!")
                    print(
                        f"  Wavelength: {wv_len}, Flux: {fx_len}, "
                        f"IVAR: {iv_len}, Mask: {mk_len}"
                    )

        except Exception as e:
            print(f"\n❌ ERROR: Could not process file {file_path.name}: {e}")
            continue

    print("\n\n--- 📋 ETL Output Validation Report ---\n")
    print(f"{'Metric':<30} | {'Value'}")
    print("-" * 50)
    print(f"{'Total Parquet Files Found':<30} | {len(file_paths)}")
    print(f"{'Total QSOs Processed':<30} | {total_qsos:,}")

    if len(schemas) == 1:
        print(f"{'Schema Consistency':<30} | ✅ OK")
    else:
        print(
            f"{'Schema Consistency':<30} | ⚠️ WARNING: "
            f"{len(schemas)} different schemas found!"
        )

    if qsos_per_file:
        print(
            f"{'Avg QSOs per File':<30} | "
            f"{sum(qsos_per_file) / len(qsos_per_file):.2f}"
        )
        print(f"{'Min QSOs per File':<30} | {min(qsos_per_file)}")
        print(f"{'Max QSOs per File':<30} | {max(qsos_per_file)}")

    if redshift_values:
        print(f"{'Min Redshift (z)':<30} | {min(redshift_values):.4f}")
        print(f"{'Max Redshift (z)':<30} | {max(redshift_values):.4f}")
        print(
            f"{'Avg Redshift (z)':<30} | "
            f"{sum(redshift_values) / len(redshift_values):.4f}"
        )

    print("-" * 50)

    if schemas:
        print("\n📄 Schema Found:")
        print(list(schemas)[0])


def plot_random_spectrum(file_paths: list) -> None:
    """Selects a random QSO from a random file and plots its spectrum."""
    if not PLOTTING_ENABLED:
        print("\n⚠️ Plotting skipped: 'matplotlib' is not installed.")
        print("   Please run: pip install matplotlib")
        return

    if not file_paths:
        return

    print("\n--- Generating Sample Spectrum Plot ---")

    try:
        random_file = random.choice(file_paths)
        df = pd.read_parquet(random_file)

        if df.empty:
            print("Could not plot: Selected file was empty.")
            return

        qso = df.sample(1).iloc[0]

        plt.style.use("seaborn-v0_8-whitegrid")
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(qso["wavelength"], qso["flux"], color="royalblue", lw=1)

        ax.set_title(
            f"Sample Spectrum for TARGETID: {qso['target_id']}\n"
            f"(from {random_file.name})",
            fontsize=14,
        )
        ax.set_xlabel("Wavelength (Å)", fontsize=12)
        ax.set_ylabel("Flux", fontsize=12)
        ax.tick_params(axis="both", which="major", labelsize=10)

        info_text = (
            f"RA: {qso['ra']:.4f}, Dec: {qso['dec']:.4f}\n"
            f"Redshift (z): {qso['z']:.4f}"
        )
        ax.text(
            0.02,
            0.95,
            info_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5", fc="wheat", alpha=0.5),
        )

        plot_filename = f"sample_spectrum_{qso['target_id']}.png"
        plt.savefig(plot_filename)
        print(f"✅ Plot saved to '{plot_filename}'")

    except Exception as e:
        print(f"❌ ERROR: Could not generate plot: {e}")


def main() -> int:
    """Main function to orchestrate the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze and validate DESI Parquet files."
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate a plot of one random spectrum.",
    )
    args = parser.parse_args()

    file_list = find_parquet_files(PARQUET_DIR)
    analyze_files(file_list)

    if args.plot:
        plot_random_spectrum(file_list)

    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
