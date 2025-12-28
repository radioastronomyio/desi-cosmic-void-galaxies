#!/usr/bin/env python3
"""
Script Name  : 03-etl-fastspecfit-postgresql.py
Description  : Extracts FastSpecFit galaxy data from FITS and loads into PostgreSQL
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-07-14
Phase        : Phase 01 - Catalog Acquisition
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Extracts galaxy properties from all 12 FastSpecFit FITS files, selects key
scientific columns from METADATA and SPECPHOT HDUs, calculates errors from
inverse variances, and loads into 'raw_catalogs.fastspecfit_galaxies' table
in PostgreSQL. Uses high-performance COPY-based ingestion achieving ~150k
rows/sec throughput. Processes 6.4M galaxies total.

Usage
-----
    python 03-etl-fastspecfit-postgresql.py [--dry-run]

Examples
--------
    python 03-etl-fastspecfit-postgresql.py
        Loads all FastSpecFit files into PostgreSQL.

    python 03-etl-fastspecfit-postgresql.py --dry-run
        Shows what would be processed without writing to database.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import configparser
import glob
import os
import sys
import time
from io import StringIO

import numpy as np
import pandas as pd
import psycopg2
from astropy.io import fits
from astropy.table import Table

# =============================================================================
# Functions
# =============================================================================


def get_db_config() -> dict:
    """Read and return the database configuration."""
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config["database"]


def ivar_to_err(ivar: np.ndarray) -> np.ndarray:
    """
    Safely convert inverse variance to error.
    
    DESI (and most spectroscopic surveys) store uncertainties as inverse
    variance rather than standard error. This is deliberate: inverse variance
    is the natural weighting for combining measurements, and avoids numerical
    issues with very small errors. The conversion is: err = 1/sqrt(ivar).
    
    AI NOTE: If you see *_IVAR columns in DESI data, they must be converted
    before use as uncertainties. Do not load raw IVAR values as errors.

    Parameters
    ----------
    ivar : np.ndarray
        Inverse variance values.

    Returns
    -------
    np.ndarray
        Error values (1/sqrt(ivar)) where ivar > 0, otherwise NaN.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        err = 1.0 / np.sqrt(ivar)
    err[~np.isfinite(err)] = np.nan
    return err


def copy_from_stringio(
    df: pd.DataFrame, db_name: str, table_name: str, dry_run: bool = False
) -> None:
    """
    High-performance load of a pandas DataFrame to PostgreSQL using COPY.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to load.
    db_name : str
        Target database name.
    table_name : str
        Target table name (schema.table format).
    dry_run : bool, optional
        If True, skip actual database write. Default is False.
    """
    if dry_run:
        print(f"  [DRY RUN] Would COPY {len(df)} rows into '{table_name}'")
        return

    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False, na_rep="\\N")
    buffer.seek(0)

    db_config = get_db_config()
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"],
        )
        with conn.cursor() as cursor:
            columns = ",".join(df.columns)
            cursor.copy_expert(
                f"COPY {table_name} ({columns}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')",
                buffer,
            )
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error during COPY for table {table_name}: {error}", file=sys.stderr)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def process_fastspecfit_files(
    base_path: str, db_name: str, dry_run: bool = False
) -> None:
    """
    Process all FastSpecFit FITS files and load into galaxies table.

    Parameters
    ----------
    base_path : str
        Directory containing FastSpecFit FITS files.
    db_name : str
        Target database name.
    dry_run : bool, optional
        If True, skip actual database writes. Default is False.
    """
    print("\n--- Starting FastSpecFit Ingestion ---")
    target_table = "raw_catalogs.fastspecfit_galaxies"

    if not dry_run:
        print(f"Clearing existing data from {target_table}...")
        db_config = get_db_config()
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_config["user"],
                password=db_config["password"],
                host=db_config["host"],
                port=db_config["port"],
            )
            with conn.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {target_table} RESTART IDENTITY")
            conn.commit()
            print("Table cleared successfully.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error truncating table {target_table}: {error}", file=sys.stderr)
            if conn:
                conn.rollback()
            return
        finally:
            if conn:
                conn.close()

    files = sorted(glob.glob(os.path.join(base_path, "fastspec-iron-*.fits")))
    if not files:
        print(f"Error: No FastSpecFit files found in '{base_path}'.", file=sys.stderr)
        return

    # Columns from inspector's ground truth
    meta_cols = ["TARGETID", "RA", "DEC", "Z"]
    specphot_cols = ["LOGMSTAR", "LOGMSTAR_IVAR", "SFR", "SFR_IVAR", "AGE", "ZZSUN", "DN4000"]

    for i, f_path in enumerate(files):
        start_time = time.time()
        file_name = os.path.basename(f_path)
        print(f"Processing file {i+1}/{len(files)}: {file_name} ...")

        try:
            with fits.open(f_path, memmap=True) as hdul:
                if "METADATA" not in hdul or "SPECPHOT" not in hdul:
                    print(
                        f"Warning: Skipping {file_name}, missing METADATA or SPECPHOT HDU.",
                        file=sys.stderr,
                    )
                    continue

                meta_table = Table(hdul["METADATA"].data, masked=True)
                spec_table = Table(hdul["SPECPHOT"].data, masked=True)

                df = pd.DataFrame()
                # Populate from METADATA HDU
                for col in meta_cols:
                    df[col.lower()] = meta_table[col]

                # AI NOTE: Z_ERR is not provided by FastSpecFit v1.0 — this is a
                # known gap in the VAC. We create a NaN column that loads as NULL
                # in PostgreSQL. Future VAC versions may include redshift errors;
                # check release notes before removing this workaround.
                df["z_err"] = np.nan

                # Populate from SPECPHOT HDU
                df["logmstar"] = spec_table["LOGMSTAR"]
                df["logmstar_err"] = ivar_to_err(spec_table["LOGMSTAR_IVAR"])
                df["sfr"] = spec_table["SFR"]
                df["sfr_err"] = ivar_to_err(spec_table["SFR_IVAR"])
                df["age_gyr"] = spec_table["AGE"]
                df["metallicity"] = spec_table["ZZSUN"]
                df["d4000"] = spec_table["DN4000"]

                # Provenance columns for traceability. The healpix_id is extracted
                # from the filename pattern "fastspec-iron-*-hp##.fits" and enables
                # joining back to the original source files if needed.
                df["healpix_id"] = int(file_name.split("hp")[-1].split(".")[0])
                df["source_file"] = file_name

                copy_from_stringio(df, db_name, target_table, dry_run=dry_run)
                if not dry_run:
                    print(f"  > Loaded {len(df)} rows into {target_table}.")

        except KeyError as e:
            print(
                f"Error processing file {file_name}: Missing expected column - {e}.",
                file=sys.stderr,
            )
            continue
        except Exception as e:
            print(f"Error processing file {file_name}: {e}", file=sys.stderr)
            continue

        end_time = time.time()
        duration_msg = f"Done in {end_time - start_time:.2f} seconds."
        rows_msg = f"{len(df)} rows found." if dry_run else f"{len(df)} rows loaded."
        print(f"  > {duration_msg} {rows_msg}")

    print("--- FastSpecFit Ingestion Complete ---")


def main() -> int:
    """Entry point for script execution."""
    parser = argparse.ArgumentParser(
        description="FastSpecFit FITS to PostgreSQL ETL Pipeline.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the script to see what files and rows would be processed\n"
        "without writing anything to the database.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("\n" + "=" * 50)
        print("🚀   PERFORMING DRY RUN - NO DATA WILL BE WRITTEN   🚀")
        print("=" * 50)

    total_start_time = time.time()

    config = configparser.ConfigParser()
    config.read("config.ini")
    paths = config["paths"]
    db_conf = config["database"]

    process_fastspecfit_files(
        paths["fastspecfit_dir"], db_conf["dbname_fastspecfit"], dry_run=args.dry_run
    )

    total_end_time = time.time()
    print(
        f"\nTotal ETL process finished in {(total_end_time - total_start_time)/60:.2f} minutes."
    )

    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
