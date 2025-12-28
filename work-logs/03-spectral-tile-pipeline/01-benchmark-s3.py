#!/usr/bin/env python3
"""
Script Name  : 01-benchmark-s3.py
Description  : Tests concurrent download performance from DESI AWS S3 bucket
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-09-01
Phase        : Phase 03 - Spectral Tile Pipeline
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Tests concurrent download performance from the DESI AWS S3 public bucket using
aws s3 cp in a thread pool. Determines optimal worker count for production runs.
Requires aws-cli configured with dummy credentials.

Usage
-----
    python 01-benchmark-s3.py

Examples
--------
    python 01-benchmark-s3.py
        Tests worker counts [1, 2, 4, 8, 12, 16, 24, 32] using 25 coadd files.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import logging
import random
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

# Test a range of concurrency levels to find the throughput plateau.
# S3 handles high concurrency well, but local I/O and network may bottleneck.
WORKER_COUNTS = [1, 2, 4, 8, 12, 16, 24, 32]
# 25 files balances statistical significance with benchmark runtime.
FILES_FOR_BENCHMARK = 25
BENCHMARK_DIR = Path("./s3_benchmark_temp")
INPUT_CSV = Path("./s3_desi_inventory.csv")
# DESI public data bucket — requires --no-sign-request flag.
S3_BUCKET_URI = "s3://desidata"

# =============================================================================
# Functions
# =============================================================================


def setup_logging() -> None:
    """Sets up basic logging to the console."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_random_file_info(count: int) -> list:
    """Gets a random sample of S3 object keys from the corrected inventory CSV."""
    if not INPUT_CSV.exists():
        logging.error(f"FATAL: Corrected inventory file '{INPUT_CSV}' not found.")
        logging.error("Please run '01-correct-s3-paths.py' first.")
        sys.exit(1)

    all_coadd_files = []
    with open(INPUT_CSV, mode="r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            if row["file_type"] == "coadd" and row["s3_key"]:
                all_coadd_files.append(
                    {"s3_key": row["s3_key"], "filename": row["filename"]}
                )

    if len(all_coadd_files) < count:
        logging.warning(
            f"Warning: Not enough 'coadd' files in inventory. Using all {len(all_coadd_files)}."
        )
        return all_coadd_files

    return random.sample(all_coadd_files, count)


def download_worker(s3_key: str, dest_path: Path) -> int:
    """Worker function to download a single file using aws s3 cp."""
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
        subprocess.run(command, check=True, timeout=300, capture_output=True)
        return dest_path.stat().st_size
    except subprocess.CalledProcessError as e:
        logging.error(f"Download failed for {s3_uri} with exit code {e.returncode}.")
        logging.error(f"STDERR: {e.stderr.decode('utf-8')}")
        return 0
    except subprocess.TimeoutExpired:
        logging.error(f"Download timed out for {s3_uri}.")
        return 0


def run_benchmark(worker_count: int, files_to_download: list) -> dict:
    """Runs a benchmark for a given number of workers using a pre-selected file list."""
    logging.info(f"\n--- Running Benchmark: {worker_count} concurrent workers ---")

    test_dir = BENCHMARK_DIR / f"test_{worker_count}_workers"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)

    tasks = [
        {"s3_key": f_info["s3_key"], "path": test_dir / f_info["filename"]}
        for f_info in files_to_download
    ]
    total_bytes_downloaded = 0
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_task = {
            executor.submit(download_worker, task["s3_key"], task["path"]): task
            for task in tasks
        }

        for i, future in enumerate(as_completed(future_to_task), 1):
            try:
                file_size = future.result()
                total_bytes_downloaded += file_size
                print(f"\r  Progress: {i}/{len(tasks)} files downloaded...", end="")
            except Exception as exc:
                logging.error(f"A download task generated an exception: {exc}")

    end_time = time.perf_counter()
    print("\n  Downloads complete.")

    elapsed_time = end_time - start_time
    total_mb = total_bytes_downloaded / (1024 * 1024)
    throughput_mb_s = (total_mb / elapsed_time) if elapsed_time > 0 else 0

    logging.info(f"  - Total time: {elapsed_time:.2f} seconds")
    logging.info(f"  - Total downloaded: {total_mb:.2f} MB")
    logging.info(f"  - Aggregate throughput: {throughput_mb_s:.2f} MB/s")

    return {
        "workers": worker_count,
        "throughput_mbs": throughput_mb_s,
        "time_sec": elapsed_time,
        "data_mb": total_mb,
    }


def main() -> int:
    """Main function to orchestrate the benchmark tests."""
    setup_logging()
    logging.info("🚀 Starting DESI S3 download benchmark...")

    if BENCHMARK_DIR.exists():
        shutil.rmtree(BENCHMARK_DIR)

    logging.info(
        f"Selecting {FILES_FOR_BENCHMARK} random 'coadd' files for the test set..."
    )
    files_for_all_tests = get_random_file_info(FILES_FOR_BENCHMARK)
    logging.info("File set selected. Beginning benchmark runs.")

    results = []
    for worker_count in WORKER_COUNTS:
        result = run_benchmark(worker_count, files_for_all_tests)
        results.append(result)

    print("\n\n--- Benchmark Summary Report ---\n")
    print(
        f"{'Workers' : <10} | {'Throughput (MB/s)' : <20} | "
        f"{'Total Time (s)' : <18} | {'Data (MB)' : <15}"
    )
    print("-" * 70)
    for res in results:
        print(
            f"{res['workers'] : <10} | {res['throughput_mbs'] : <20.2f} | "
            f"{res['time_sec'] : <18.2f} | {res['data_mb'] : <15.2f}"
        )
    print("-" * 70)

    if results:
        best_result = max(results, key=lambda x: x["throughput_mbs"])
        logging.info(
            f"\n🏆 Optimal performance found at {best_result['workers']} workers "
            f"with {best_result['throughput_mbs']:.2f} MB/s."
        )

    logging.info(f"\nCleaning up temporary directory: {BENCHMARK_DIR}")
    shutil.rmtree(BENCHMARK_DIR)
    logging.info("✅ Benchmark complete.")

    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
