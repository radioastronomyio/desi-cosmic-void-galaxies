#!/usr/bin/env python3
"""
Script Name  : 02-process-desi-batch.py
Description  : Single-process resumable batch processor for DESI FITS→Parquet
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-09-01
Phase        : Phase 03 - Spectral Tile Pipeline
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
A simple, single-process, resumable script to download DESI FITS files via
HTTP, convert them to Parquet, and clean up. Space-aware with configurable
disk threshold. Logs download speeds and maintains state for resumption.

Usage
-----
    python 02-process-desi-batch.py [--count N]

Examples
--------
    python 02-process-desi-batch.py --count 100
        Process 100 tiles then stop.

    python 02-process-desi-batch.py
        Process until disk space threshold reached.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

STATE_DIR = os.path.join(PROJECT_ROOT, "state")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
RAW_FITS_DIR = os.path.join(PROJECT_ROOT, "raw_fits")
PARQUET_DIR = os.path.join(PROJECT_ROOT, "parquet_output")
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")

ALL_TILES_FILE = os.path.join(STATE_DIR, "all_tiles.txt")
COMPLETED_TILES_FILE = os.path.join(STATE_DIR, "completed_tiles.txt")

DISK_SPACE_THRESHOLD_GB = 50
URL_BASE = "https://data.desi.lbl.gov/public/dr1/spectro/redux/iron/healpix/main/dark"

# =============================================================================
# Functions
# =============================================================================


def setup_logging() -> None:
    """Sets up logging to both console and a file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_filename = os.path.join(
        LOG_DIR, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_filename),
        ],
    )


def get_tiles_to_process() -> list:
    """Reads state files and returns a list of tile IDs that need processing."""
    if not os.path.exists(ALL_TILES_FILE):
        logging.error(f"FATAL: Master tile list '{ALL_TILES_FILE}' not found.")
        sys.exit(1)

    with open(ALL_TILES_FILE, "r") as f:
        all_tiles = {int(line.strip()) for line in f if line.strip()}

    if os.path.exists(COMPLETED_TILES_FILE):
        with open(COMPLETED_TILES_FILE, "r") as f:
            completed_tiles = {int(line.strip()) for line in f if line.strip()}
    else:
        completed_tiles = set()

    tiles_to_do = sorted(list(all_tiles - completed_tiles))
    logging.info(
        f"Found {len(all_tiles)} total tiles, {len(completed_tiles)} completed. "
        f"{len(tiles_to_do)} remaining."
    )
    return tiles_to_do


def check_disk_space() -> bool:
    """Checks if there is enough free disk space to continue."""
    total, used, free = shutil.disk_usage(PROJECT_ROOT)
    free_gb = free / (1024**3)
    if free_gb < DISK_SPACE_THRESHOLD_GB:
        logging.warning(
            f"Stopping: Free disk space ({free_gb:.2f} GB) is below threshold "
            f"({DISK_SPACE_THRESHOLD_GB} GB)."
        )
        return False
    return True


def download_tile_files(tile_id: int) -> bool:
    """
    Downloads coadd and redrock files for a given tile and logs speed.
    
    DESI organizes spectral data by HEALPix pixel ID. The URL structure uses
    a "pixgroup" (tile_id // 100) to limit directory sizes to ~100 tiles each.
    """
    # AI NOTE: pixgroup = tile_id // 100 is DESI's directory sharding convention.
    # This mirrors the S3 bucket structure. Changing this calculation breaks
    # URL construction for all tiles.
    pixgroup = tile_id // 100
    tile_dir = os.path.join(RAW_FITS_DIR, str(tile_id))
    os.makedirs(tile_dir, exist_ok=True)

    files_to_download = [
        f"coadd-main-dark-{tile_id}.fits",
        f"redrock-main-dark-{tile_id}.fits",
    ]

    for filename in files_to_download:
        url = f"{URL_BASE}/{pixgroup}/{tile_id}/{filename}"
        try:
            logging.info(f"Downloading: {url}")
            result = subprocess.run(
                ["wget", "-O", os.path.join(tile_dir, filename), url],
                check=True,
                timeout=300,
                capture_output=True,
                text=True,
            )

            speed_match = re.search(r"\(([^)]+)\)\s+-\s+.*saved", result.stderr)
            if speed_match:
                speed = speed_match.group(1)
                logging.info(f"Download speed for {filename}: {speed}")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logging.error(f"Download failed for {url}: {e}")
            if hasattr(e, "stderr") and e.stderr:
                logging.error(f"WGET STDERR: {e.stderr}")
            shutil.rmtree(tile_dir)
            return False
    return True


def process_tile(tile_id: int) -> bool:
    """Runs the Parquet conversion script as a subprocess."""
    input_dir = os.path.join(RAW_FITS_DIR, str(tile_id))
    conversion_script = os.path.join(SCRIPTS_DIR, "extract_qso_tile_to_parquet.py")

    try:
        logging.info(f"Running conversion script for tile {tile_id}...")
        subprocess.run(
            [
                sys.executable,
                conversion_script,
                "--data-dir",
                input_dir,
                "--output-dir",
                PARQUET_DIR,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Parquet conversion failed for tile {tile_id}.")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        return False
    return True


def cleanup_fits_files(tile_id: int) -> None:
    """Deletes the raw FITS directory to save space."""
    dir_to_delete = os.path.join(RAW_FITS_DIR, str(tile_id))
    if os.path.exists(dir_to_delete):
        shutil.rmtree(dir_to_delete)
        logging.info(f"Cleaned up raw files for tile {tile_id}.")


def update_state_completed(tile_id: int) -> None:
    """Appends a tile ID to the completed file."""
    with open(COMPLETED_TILES_FILE, "a") as f:
        f.write(f"{tile_id}\n")


def main() -> int:
    """Main orchestrator function."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Process DESI data in batches.")
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Limit the number of files to process in this run.",
    )
    args = parser.parse_args()

    for d in [STATE_DIR, LOG_DIR, RAW_FITS_DIR, PARQUET_DIR, SCRIPTS_DIR]:
        os.makedirs(d, exist_ok=True)

    tiles_to_process = get_tiles_to_process()

    if not tiles_to_process:
        logging.info("🎉 All tiles have been processed. Nothing to do.")
        return 0

    if args.count is not None:
        logging.info(f"Processing a limited batch of {args.count} tiles as requested.")
        tiles_to_process = tiles_to_process[: args.count]

    processed_count = 0
    for tile_id in tiles_to_process:
        if not check_disk_space():
            break

        logging.info(
            f"--- Starting Tile {tile_id} ({processed_count + 1}/{len(tiles_to_process)}) ---"
        )

        if download_tile_files(tile_id):
            if process_tile(tile_id):
                cleanup_fits_files(tile_id)
                update_state_completed(tile_id)
                processed_count += 1
            else:
                cleanup_fits_files(tile_id)

        logging.info(f"--- Finished Tile {tile_id} ---")

    logging.info(f"✅ Run finished. Processed {processed_count} tiles in this session.")
    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
