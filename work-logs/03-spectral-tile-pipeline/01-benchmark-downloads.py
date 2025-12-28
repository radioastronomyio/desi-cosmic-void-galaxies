#!/usr/bin/env python3
"""
Script Name  : 01-benchmark-downloads.py
Description  : Tests concurrent HTTP download performance from DESI data server
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-09-01
Phase        : Phase 03 - Spectral Tile Pipeline
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Tests concurrent download performance from the DESI data server to determine
the optimal number of worker threads. Uses a fixed set of coadd files for
fair apples-to-apples comparison across worker counts.

Usage
-----
    python 01-benchmark-downloads.py

Examples
--------
    python 01-benchmark-downloads.py
        Tests worker counts [1, 2, 4, 8, 12, 16, 24, 32] and reports optimal.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import logging
import os
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
# Too few workers underutilizes bandwidth; too many may trigger rate limiting
# or create contention overhead.
WORKER_COUNTS = [1, 2, 4, 8, 12, 16, 24, 32]
# 15 files provides statistically meaningful timing without excessive runtime.
FILES_FOR_BENCHMARK = 15
BENCHMARK_DIR = Path("./download_benchmark_temp")
INPUT_CSV = Path("./complete_desi_inventory.csv")

# =============================================================================
# Functions
# =============================================================================


def setup_logging() -> None:
    """Sets up basic logging to the console."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_random_file_info(count: int) -> list:
    """Gets a random sample of file information (URL, filename) from the master CSV."""
    if not INPUT_CSV.exists():
        logging.error(f"FATAL: Master inventory file '{INPUT_CSV}' not found.")
        sys.exit(1)

    all_files = []
    with open(INPUT_CSV, mode="r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            if row["file_type"] == "coadd":
                all_files.append({"url": row["url"], "filename": row["filename"]})

    if len(all_files) < count:
        logging.warning(
            f"Warning: Not enough 'coadd' files in inventory. Using all {len(all_files)} files."
        )
        return all_files

    return random.sample(all_files, count)


def download_worker(url: str, dest_path: Path) -> int:
    """Worker function to download a single file using wget."""
    try:
        subprocess.run(
            ["wget", "-q", "-O", str(dest_path), url], check=True, timeout=300
        )
        return dest_path.stat().st_size
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error(f"Download failed for {url}: {e}")
        return 0


def run_benchmark(worker_count: int, files_to_download: list) -> dict:
    """Runs a benchmark for a given number of workers using a pre-selected file list."""
    logging.info(f"\n--- Running Benchmark: {worker_count} concurrent workers ---")

    test_dir = BENCHMARK_DIR / f"test_{worker_count}_workers"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)

    tasks = [
        {"url": f_info["url"], "path": test_dir / f_info["filename"]}
        for f_info in files_to_download
    ]
    total_bytes_downloaded = 0
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_url = {
            executor.submit(download_worker, task["url"], task["path"]): task["url"]
            for task in tasks
        }

        for i, future in enumerate(as_completed(future_to_url), 1):
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
    logging.info("🚀 Starting DESI download benchmark...")

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
