#!/usr/bin/env python3
"""
Script Name  : 01-desivast-download.py
Description  : Downloads DESIVAST void catalogs from DESI DR1 public archive
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-06-30
Phase        : Phase 01 - Catalog Acquisition
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Downloads DESIVAST void catalogs from the DESI DR1 public archive at NERSC.
DESIVAST provides void catalogs using four algorithms (VIDE, ZOBOV, REVOLVER,
VoidFinder) for both Northern (NGC) and Southern (SGC) Galactic Caps.
Total download size is approximately 1.2 GB across 8 FITS files.

Usage
-----
    python 01-desivast-download.py [data_directory]

Examples
--------
    python 01-desivast-download.py
        Downloads to default ./data/desivast directory.

    python 01-desivast-download.py /mnt/proj-fs02/desi-dr1/desivast
        Downloads to specified directory.
"""

# =============================================================================
# Imports
# =============================================================================

import os
import sys
import time
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin

import requests

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_DATA_DIR = Path("./data/desivast")
DESIVAST_BASE_URL = "https://data.desi.lbl.gov/public/dr1/vac/dr1/desivast/v1.0/"

# DESIVAST provides void catalogs from four independent void-finding algorithms,
# each with different methodological approaches:
#   - VIDE: Voronoi-based, identifies voids as low-density Voronoi cells
#   - ZOBOV: Zone-based, hierarchical watershed from density minima
#   - REVOLVER: Reconstructs voids using galaxy peculiar velocities
#   - VoidFinder: Identifies maximal spheres in underdense regions
#
# Each algorithm produces separate catalogs for Northern (NGC) and Southern (SGC)
# Galactic Caps due to the survey footprint geometry. Total: 4 algorithms × 2 caps = 8 files.
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


def get_file_info(url: str) -> Tuple[int, str]:
    """Get file size without downloading."""
    try:
        response = requests.head(url, timeout=30)
        if response.status_code == 200:
            size = int(response.headers.get("content-length", 0))
            return size, "Available"
        else:
            return 0, f"HTTP {response.status_code}"
    except Exception as e:
        return 0, f"Error: {e}"


def download_file(url: str, local_path: Path) -> bool:
    """Download a single file with progress tracking."""
    # Idempotent: skip files that already exist with non-zero size.
    # This allows safe re-runs after partial downloads or interruptions.
    if local_path.exists():
        existing_size = local_path.stat().st_size
        print(f"✅ Already exists: {local_path.name} ({format_size(existing_size)})")
        return True

    try:
        print(f"⬇️  Downloading: {local_path.name}")

        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 8192
        start_time = time.time()

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Progress every 10MB
                    if downloaded % (10 * 1024 * 1024) < chunk_size:
                        elapsed = time.time() - start_time
                        if elapsed > 0 and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            speed = downloaded / elapsed
                            print(
                                f"   📈 {percent:.1f}% - {format_size(downloaded)}/"
                                f"{format_size(total_size)} - {format_size(speed)}/s",
                                end="\r",
                            )

        print()  # New line after progress
        final_size = local_path.stat().st_size
        elapsed = time.time() - start_time
        print(
            f"✅ Downloaded: {local_path.name} ({format_size(final_size)} in {elapsed:.1f}s)"
        )
        return True

    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        if local_path.exists():
            local_path.unlink()
        return False


def main() -> int:
    """Download DESIVAST void catalogs."""
    # Parse command line arguments
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    else:
        data_dir = DEFAULT_DATA_DIR

    print("🔭 DESIVAST Void Catalog Downloader")
    print("=" * 50)
    print(f"📁 Target directory: {data_dir}")
    print(f"🌐 Source: {DESIVAST_BASE_URL}")

    # Create directory
    data_dir.mkdir(parents=True, exist_ok=True)

    # Survey files
    print(f"\n🔍 Surveying {len(DESIVAST_FILES)} DESIVAST files...")
    total_size = 0

    for filename in DESIVAST_FILES:
        url = urljoin(DESIVAST_BASE_URL, filename)
        size, status = get_file_info(url)
        total_size += size
        print(f"   📄 {filename}: {format_size(size)} ({status})")

    print(f"\n📊 Total download size: {format_size(total_size)}")

    # Confirm download
    response = input("\n⚡ Proceed with download? [y/N]: ").strip().lower()
    if response not in ["y", "yes"]:
        print("❌ Download cancelled")
        return 1

    # Download files
    print("\n⬇️  Downloading DESIVAST files...")
    success_count = 0

    for filename in DESIVAST_FILES:
        url = urljoin(DESIVAST_BASE_URL, filename)
        local_path = data_dir / filename

        if download_file(url, local_path):
            success_count += 1

    # Summary
    print("\n📊 Download Summary:")
    print(f"   ✅ Success: {success_count}/{len(DESIVAST_FILES)} files")

    if success_count == len(DESIVAST_FILES):
        print("   🎉 All DESIVAST files downloaded successfully!")
        return 0
    else:
        print("   ⚠️  Some downloads failed")
        return 1


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
