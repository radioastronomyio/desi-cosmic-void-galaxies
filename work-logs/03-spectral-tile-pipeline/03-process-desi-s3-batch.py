#!/usr/bin/env python3
"""
Script Name  : 03-process-desi-s3-batch.py
Description  : Parallel S3 batch processor for DESI DR1 spectral tiles
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-09-01
Phase        : Phase 03 - Spectral Tile Pipeline
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
A resilient, parallel script to process the DESI DR1 dataset from the AWS S3
public bucket. Downloads tiles in parallel (8 workers), converts to Parquet
(4 workers), and operates in small resumable batches with automatic cleanup.
Logs effective throughput and compression ratios per batch.

Usage
-----
    python 03-process-desi-s3-batch.py [--count N]

Examples
--------
    python 03-process-desi-s3-batch.py --count 2
        Process 2 batches (16 tiles) then stop.

    python 03-process-desi-s3-batch.py
        Full production run until all tiles processed.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import csv
import logging
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path.cwd()
STATE_DIR = PROJECT_ROOT / "state"
LOG_DIR = PROJECT_ROOT / "logs"
RAW_FITS_DIR = PROJECT_ROOT / "raw_fits"
PARQUET_DIR = PROJECT_ROOT / "parquet_output"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
INVENTORY_CSV = PROJECT_ROOT / "s3_desi_inventory.csv"
COMPLETED_TILES_FILE = STATE_DIR / "completed_tiles.txt"

# Worker counts tuned via 01-benchmark-s3.py testing.
# 8 download workers saturates typical network bandwidth without overwhelming S3.
# 4 process workers balances CPU-bound Parquet conversion with I/O wait.
DOWNLOAD_WORKERS = 8
PROCESS_WORKERS = 4
BATCH_SIZE = DOWNLOAD_WORKERS
DISK_SPACE_THRESHOLD_GB = 50
# DESI public data bucket — no authentication required (--no-sign-request).
S3_BUCKET_URI = "s3://desidata"

# =============================================================================
# Functions
# =============================================================================


def setup_logging() -> None:
    """Sets up detailed, timestamped logging."""
    LOG_DIR.mkdir(exist_ok=True)
    log_filename = LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
    """Builds the list of tiles to process from inventory and state files."""
    if not INVENTORY_CSV.exists():
        logging.error(f"FATAL: S3 inventory file not found: '{INVENTORY_CSV}'")
        sys.exit(1)

    completed_tiles = set()
    if COMPLETED_TILES_FILE.exists():
        with open(COMPLETED_TILES_FILE, "r", encoding="utf-8") as f:
            completed_tiles = {int(line.strip()) for line in f if line.strip()}

    all_coadd_files = {}
    with open(INVENTORY_CSV, mode="r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            if row["file_type"] == "coadd":
                tile_id = int(row["pixel"])
                if tile_id not in completed_tiles:
                    # AI NOTE: Redrock filename is derived by replacing "coadd" with
                    # "redrock" in the coadd filename. This assumes DESI's standard
                    # naming convention (coadd-main-dark-XXXXX.fits → redrock-main-dark-XXXXX.fits).
                    # If DESI changes naming conventions in future releases, this breaks.
                    all_coadd_files[tile_id] = {
                        "tile_id": tile_id,
                        "s3_key_coadd": row["s3_key"],
                        "filename_coadd": row["filename"],
                        "s3_key_redrock": row["s3_key"].replace("coadd", "redrock"),
                        "filename_redrock": row["filename"].replace("coadd", "redrock"),
                    }

    tiles_to_do = list(all_coadd_files.values())
    logging.info(f"Found {len(completed_tiles)} completed tiles.")
    logging.info(f"Discovered {len(tiles_to_do)} tiles remaining to be processed.")
    return tiles_to_do


def check_disk_space() -> bool:
    """Checks for sufficient free disk space."""
    _, _, free = shutil.disk_usage(PROJECT_ROOT)
    free_gb = free / (1024**3)
    if free_gb < DISK_SPACE_THRESHOLD_GB:
        logging.warning(
            f"Stopping: Free disk space ({free_gb:.2f} GB) is below threshold."
        )
        return False
    return True


def download_worker(s3_key: str, dest_path: Path) -> dict:
    """Worker to download a single file via aws s3 cp."""
    s3_uri = f"{S3_BUCKET_URI}/{s3_key}"
    command = [
        "aws",
        "s3",
        "cp",
        s3_uri,
        str(dest_path),
        "--no-sign-request",
        "--quiet",
    ]
    try:
        subprocess.run(command, check=True, timeout=600, capture_output=True)
        return {"success": True, "size_bytes": dest_path.stat().st_size, "path": dest_path}
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error(f"Download failed for {s3_uri}: {e}")
        return {"success": False, "size_bytes": 0, "path": dest_path}


def process_worker(tile_id: int, coadd_file: str, redrock_file: str) -> dict:
    """Worker to run the Parquet conversion, passing specific filenames."""
    input_dir = RAW_FITS_DIR / str(tile_id)
    conversion_script = SCRIPTS_DIR / "extract_qso_tile_to_parquet.py"
    command = [
        sys.executable,
        str(conversion_script),
        "--data-dir",
        str(input_dir),
        "--output-dir",
        str(PARQUET_DIR),
        "--coadd-file",
        coadd_file,
        "--redrock-file",
        redrock_file,
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=600)
        output_tile_dir = PARQUET_DIR / f"tile_{str(tile_id).zfill(5)}"
        parquet_files = list(output_tile_dir.glob("*.parquet"))
        parquet_size = parquet_files[0].stat().st_size if parquet_files else 0
        return {"success": True, "parquet_size_bytes": parquet_size, "tile_id": tile_id}
    except subprocess.CalledProcessError as e:
        logging.error(f"Parquet conversion failed for tile {tile_id}.")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        return {"success": False, "parquet_size_bytes": 0, "tile_id": tile_id}


def log_batch_summary(batch_results: list, elapsed_time: float) -> None:
    """Calculates and logs a detailed summary for a completed batch."""
    total_fits_bytes = sum(res.get("fits_size_bytes", 0) for res in batch_results)
    total_parquet_bytes = sum(res.get("parquet_size_bytes", 0) for res in batch_results)
    reduction = (
        (1 - (total_parquet_bytes / total_fits_bytes)) * 100
        if total_fits_bytes > 0
        else 0
    )

    effective_speed_mbs = (
        (total_fits_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
    )

    logging.info("--- Batch Summary ---")
    for res in sorted(batch_results, key=lambda x: x["tile_id"]):
        fits_mb = res.get("fits_size_bytes", 0) / (1024 * 1024)
        parquet_mb = res.get("parquet_size_bytes", 0) / (1024 * 1024)
        logging.info(
            f"  Tile {res['tile_id']}: FITS Size={fits_mb:.2f} MB, "
            f"Parquet Size={parquet_mb:.2f} MB"
        )

    logging.info(f"Total FITS Downloaded : {total_fits_bytes / (1024*1024):.2f} MB")
    logging.info(f"Total Parquet Created: {total_parquet_bytes / (1024*1024):.2f} MB")
    logging.info(f"Data Reduction        : {reduction:.2f}%")
    logging.info(f"Effective Batch Speed : {effective_speed_mbs:.2f} MB/s")
    logging.info("---------------------")


def main() -> int:
    """Main orchestrator function."""
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Process DESI S3 data in parallel batches."
    )
    parser.add_argument(
        "--count", type=int, help="Limit the number of BATCHES to process."
    )
    args = parser.parse_args()

    for d in [STATE_DIR, LOG_DIR, RAW_FITS_DIR, PARQUET_DIR, SCRIPTS_DIR]:
        d.mkdir(exist_ok=True)

    all_tiles_to_process = get_tiles_to_process()
    if not all_tiles_to_process:
        logging.info("🎉 All tiles processed.")
        return 0

    batches = [
        all_tiles_to_process[i : i + BATCH_SIZE]
        for i in range(0, len(all_tiles_to_process), BATCH_SIZE)
    ]
    if args.count:
        batches = batches[: args.count]

    logging.info(
        f"Ready to process {len(batches)} batches of up to {BATCH_SIZE} tiles each."
    )

    for i, batch in enumerate(batches):
        if not check_disk_space():
            break
        batch_num = i + 1
        logging.info(f"--- Starting Batch {batch_num}/{len(batches)} ---")
        start_time = time.perf_counter()

        download_tasks, download_results = [], {}
        for tile in batch:
            tile_dir = RAW_FITS_DIR / str(tile["tile_id"])
            tile_dir.mkdir(exist_ok=True)
            download_tasks.append({
                "s3_key": tile["s3_key_coadd"],
                "dest": tile_dir / tile["filename_coadd"],
            })
            download_tasks.append({
                "s3_key": tile["s3_key_redrock"],
                "dest": tile_dir / tile["filename_redrock"],
            })

        with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
            future_to_task = {
                executor.submit(download_worker, t["s3_key"], t["dest"]): t
                for t in download_tasks
            }
            for future in as_completed(future_to_task):
                res = future.result()
                if res["success"]:
                    tile_id = int(res["path"].parent.name)
                    download_results[tile_id] = (
                        download_results.get(tile_id, 0) + res["size_bytes"]
                    )

        tiles_to_process_in_batch = [
            t for t in batch if t["tile_id"] in download_results
        ]
        batch_final_results = []
        with ThreadPoolExecutor(max_workers=PROCESS_WORKERS) as executor:
            future_to_tile = {
                executor.submit(
                    process_worker,
                    t["tile_id"],
                    t["filename_coadd"],
                    t["filename_redrock"],
                ): t["tile_id"]
                for t in tiles_to_process_in_batch
            }
            for future in as_completed(future_to_tile):
                res = future.result()
                if res["success"]:
                    res["fits_size_bytes"] = download_results.get(res["tile_id"], 0)
                    batch_final_results.append(res)

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        log_batch_summary(batch_final_results, elapsed_time)

        for res in batch_final_results:
            tile_id = res["tile_id"]
            shutil.rmtree(RAW_FITS_DIR / str(tile_id))
            with open(COMPLETED_TILES_FILE, "a", encoding="utf-8") as f:
                f.write(f"{tile_id}\n")

        logging.info(
            f"--- Finished Batch {batch_num}/{len(batches)} in {elapsed_time:.2f} seconds ---"
        )

    logging.info("✅ Run finished.")
    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
