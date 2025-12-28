#!/usr/bin/env python3
"""
Script Name  : 01-correct-s3-paths.py
Description  : Normalizes S3 object keys from DESI inventory for aws s3 cp
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-09-01
Phase        : Phase 03 - Spectral Tile Pipeline
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Reads the original 'complete_desi_inventory.csv' and creates a new
's3_desi_inventory.csv' with corrected S3 object keys. Removes the
'https://data.desi.lbl.gov/public/' prefix to produce valid S3 keys.

Usage
-----
    python 01-correct-s3-paths.py

Examples
--------
    python 01-correct-s3-paths.py
        Reads complete_desi_inventory.csv, outputs s3_desi_inventory.csv.
"""

# =============================================================================
# Imports
# =============================================================================

import csv
import sys

# =============================================================================
# Configuration
# =============================================================================

INPUT_CSV = "complete_desi_inventory.csv"
OUTPUT_CSV = "s3_desi_inventory.csv"
# DESI serves the same data via HTTPS (data.desi.lbl.gov) and S3 (s3://desidata).
# The S3 bucket mirrors the HTTPS path structure, so we strip the URL prefix
# to get valid S3 object keys.
URL_PREFIX_TO_REMOVE = "https://data.desi.lbl.gov/public/"

# =============================================================================
# Functions
# =============================================================================


def main() -> int:
    """Main function to execute the script logic."""
    print(f"🔍 Reading original inventory from '{INPUT_CSV}'...")

    try:
        with open(INPUT_CSV, mode="r", encoding="utf-8") as infile, open(
            OUTPUT_CSV, mode="w", encoding="utf-8", newline=""
        ) as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            header = next(reader)
            try:
                url_index = header.index("url")
            except ValueError:
                print(f"❌ ERROR: 'url' column not found in the header of '{INPUT_CSV}'")
                return 1

            new_header = header + ["s3_key"]
            writer.writerow(new_header)

            count = 0
            for row in reader:
                original_url = row[url_index]
                if original_url.startswith(URL_PREFIX_TO_REMOVE):
                    s3_key = original_url.replace(URL_PREFIX_TO_REMOVE, "")
                    row.append(s3_key)
                    writer.writerow(row)
                    count += 1
                else:
                    row.append("")
                    writer.writerow(row)

    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found: '{INPUT_CSV}'")
        return 1
    except IOError as e:
        print(f"❌ ERROR: Could not write to output file '{OUTPUT_CSV}'. Details: {e}")
        return 1

    print(
        f"✅ Successfully processed {count} rows and created '{OUTPUT_CSV}' "
        f"with corrected S3 keys."
    )
    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
