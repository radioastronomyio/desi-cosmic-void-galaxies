#!/usr/bin/env python3
"""
Script Name  : 02-extract-qso-tile-to-parquet.py
Description  : Core FITS→Parquet converter for DESI HEALPix tiles
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-09-01
Phase        : Phase 03 - Spectral Tile Pipeline
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Extracts QSO data from DESI HEALPix tile FITS files (coadd + redrock) and
writes unified Parquet records. Filters for ZWARN==0 QSOs, merges B/R/Z
spectral arms, and applies wavelength masking to science range (3600-9800Å).

Usage
-----
    python 02-extract-qso-tile-to-parquet.py --data-dir <dir> --output-dir <dir> \
        --coadd-file <file> --redrock-file <file>

Examples
--------
    python 02-extract-qso-tile-to-parquet.py \
        --data-dir ./raw_fits/12345 \
        --output-dir ./parquet_output \
        --coadd-file coadd-main-dark-12345.fits \
        --redrock-file redrock-main-dark-12345.fits
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import os
import sys

import numpy as np
import pandas as pd
from astropy.io import fits

# =============================================================================
# Configuration
# =============================================================================

# DESI spectrograph science wavelength range.
# B arm: 3600-5800Å, R arm: 5760-7620Å, Z arm: 7520-9824Å
# We clip to 3600-9800Å to exclude noisy edges and ensure consistent array lengths.
# AI NOTE: These bounds are instrument-specific. Changing them affects downstream
# analysis that assumes fixed wavelength grids. Update MIN_WAVE/MAX_WAVE together
# and verify array length consistency across the full tile set.
MIN_WAVE = 3600
MAX_WAVE = 9800

# =============================================================================
# Functions
# =============================================================================


def main(data_dir: str, output_dir: str, coadd_file: str, redrock_file: str) -> int:
    """Main ETL logic for a single HEALPix tile."""
    try:
        tile_id = "".join(filter(str.isdigit, os.path.basename(coadd_file)))
        print(f"Processing Tile ID: {tile_id}")
    except (ValueError, AttributeError):
        print(f"❌ ERROR: Could not determine Tile ID from filename: {coadd_file}")
        return 1

    tile_output_dir = os.path.join(output_dir, f"tile_{tile_id.zfill(5)}")
    os.makedirs(tile_output_dir, exist_ok=True)

    # Load redrock data — contains redshift fitting results.
    # Redrock is DESI's template-fitting pipeline that classifies spectra
    # and measures redshifts. The REDSHIFTS HDU has one row per target.
    redrock_path = os.path.join(data_dir, redrock_file)
    if not os.path.exists(redrock_path):
        print(f"❌ Required file not found: {redrock_path}")
        return 2

    with fits.open(redrock_path) as rr:
        rr_data = rr["REDSHIFTS"].data
        # ZWARN==0 means the redshift fit passed all quality checks.
        # Non-zero ZWARN indicates potential issues (low S/N, ambiguous fits,
        # edge effects). We filter to ZWARN==0 for science-grade redshifts.
        qso_targets = {
            int(row["TARGETID"]): {"z": float(row["Z"]), "ra": None, "dec": None}
            for row in rr_data
            if row["SPECTYPE"] == "QSO" and row["ZWARN"] == 0
        }

    if not qso_targets:
        print("✅ No valid QSO targets found in this tile. Exiting gracefully.")
        open(os.path.join(tile_output_dir, "_SUCCESS_NO_QSO"), "a").close()
        return 0

    # Load coadd data
    coadd_path = os.path.join(data_dir, coadd_file)
    if not os.path.exists(coadd_path):
        print(f"❌ Required file not found: {coadd_path}")
        return 2

    with fits.open(coadd_path) as coadd:
        fibermap = coadd["FIBERMAP"].data
        id_index = {}
        for i, row in enumerate(fibermap):
            tid = int(row["TARGETID"])
            if tid in qso_targets:
                qso_targets[tid]["ra"] = float(row["TARGET_RA"])
                qso_targets[tid]["dec"] = float(row["TARGET_DEC"])
                id_index[tid] = i

        # DESI spectra are split across three arms covering different wavelength ranges:
        #   B (blue):  3600-5800Å — covers [OII], Hδ, Hγ, Hβ
        #   R (red):   5760-7620Å — covers [OIII], Hα, [NII], [SII]
        #   Z (near-IR): 7520-9824Å — covers Ca triplet, atmospheric features
        # AI NOTE: Arrays MUST be concatenated in B→R→Z order to maintain
        # monotonically increasing wavelength. Changing this order breaks
        # wavelength-flux alignment silently.
        flux_data = [
            coadd["B_FLUX"].data,
            coadd["R_FLUX"].data,
            coadd["Z_FLUX"].data,
        ]
        wave_data = [
            coadd["B_WAVELENGTH"].data,
            coadd["R_WAVELENGTH"].data,
            coadd["Z_WAVELENGTH"].data,
        ]
        # IVAR = inverse variance, DESI's native uncertainty representation.
        # Convert to error via: error = 1/sqrt(ivar) where ivar > 0.
        ivar_data = [
            coadd["B_IVAR"].data,
            coadd["R_IVAR"].data,
            coadd["Z_IVAR"].data,
        ]
        mask_data = [
            coadd["B_MASK"].data,
            coadd["R_MASK"].data,
            coadd["Z_MASK"].data,
        ]
        full_wave = np.concatenate(wave_data)

    # Build records
    records = []
    for tid, meta in qso_targets.items():
        idx = id_index.get(tid)
        if idx is None:
            continue

        flux_brz = np.concatenate([f[idx, :] for f in flux_data]).astype(np.float32)
        ivar_brz = np.concatenate([i[idx, :] for i in ivar_data]).astype(np.float32)
        mask_brz = np.concatenate([m[idx, :] for m in mask_data]).astype(np.int32)

        mask = (full_wave >= MIN_WAVE) & (full_wave <= MAX_WAVE)

        records.append({
            "target_id": tid,
            "ra": round(meta["ra"], 6),
            "dec": round(meta["dec"], 6),
            "z": round(meta["z"], 6),
            "wavelength": full_wave[mask].astype(np.float32).tolist(),
            "flux": flux_brz[mask].tolist(),
            "ivar": ivar_brz[mask].tolist(),
            "mask_array": mask_brz[mask].tolist(),
        })

    file_name = f"qso_data_TILE{tile_id.zfill(5)}_{len(records)}_qsos.parquet"
    out_path = os.path.join(tile_output_dir, file_name)
    print(f"💾 Writing {len(records)} records to: {out_path}")
    pd.DataFrame(records).to_parquet(out_path, index=False, engine="pyarrow")
    print("✅ Extraction complete.")

    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extracts QSO data from a DESI tile."
    )
    parser.add_argument("--data-dir", required=True, help="Directory containing FITS files")
    parser.add_argument("--output-dir", required=True, help="Output directory for Parquet")
    parser.add_argument("--coadd-file", required=True, help="Filename of the coadd FITS file")
    parser.add_argument("--redrock-file", required=True, help="Filename of the redrock FITS file")
    args = parser.parse_args()

    sys.exit(main(args.data_dir, args.output_dir, args.coadd_file, args.redrock_file))
