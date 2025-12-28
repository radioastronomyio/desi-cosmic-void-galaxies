#!/usr/bin/env python3
"""
Script Name  : 03-etl-desivast-postgresql.py
Description  : Extracts DESIVAST void data from FITS and loads into PostgreSQL
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-07-14
Phase        : Phase 01 - Catalog Acquisition
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Extracts void data from all DESIVAST FITS files (REVOLVER, VIDE, ZOBOV,
VoidFinder), transforms the data to fit a unified schema, and loads it into
the 'raw_catalogs.desivast_voids' table in PostgreSQL. Uses high-performance
COPY-based ingestion achieving ~150k rows/sec throughput. Truncates target
table before load for idempotent re-runs.

Usage
-----
    python 03-etl-desivast-postgresql.py [--dry-run]

Examples
--------
    python 03-etl-desivast-postgresql.py
        Loads all DESIVAST files into PostgreSQL.

    python 03-etl-desivast-postgresql.py --dry-run
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


def process_desivast_files(
    base_path: str, db_name: str, dry_run: bool = False
) -> None:
    """
    Process all DESIVAST FITS files and load into unified voids table.
    
    Unifies output from four void-finding algorithms into a single table with
    a superset schema. Algorithm-specific columns are NULLable; common columns
    (ra, dec, redshift, radius) are populated for all records.

    Parameters
    ----------
    base_path : str
        Directory containing DESIVAST FITS files.
    db_name : str
        Target database name.
    dry_run : bool, optional
        If True, skip actual database writes. Default is False.
    """
    print("\n--- Starting DESIVAST Ingestion ---")
    target_table = "raw_catalogs.desivast_voids"

    # Truncate-before-load pattern ensures idempotent re-runs.
    # Each execution produces identical results regardless of prior state.
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

    files = sorted(glob.glob(os.path.join(base_path, "DESIVAST_*.fits")))
    if not files:
        print(f"Error: No DESIVAST files found in '{base_path}'.", file=sys.stderr)
        return

    unified_columns = [
        "algorithm",
        "original_void_index",
        "ra",
        "dec",
        "x_mpc_h",
        "y_mpc_h",
        "z_mpc_h",
        "radius_mpc_h",
        "edge_flag",
        "redshift",
        "depth",
        "tot_area",
        "edge_area",
        "gal",
        "out_flag",
        "void0",
        "void1",
        "x1",
        "y1",
        "z1",
        "x2",
        "y2",
        "z2",
        "x3",
        "y3",
        "z3",
        "zone",
        "target",
        "g2v",
        "g2v2",
        "gid",
        "n_x",
        "n_y",
        "n_z",
        "p1_x",
        "p1_y",
        "p1_z",
        "p2_x",
        "p2_y",
        "p2_z",
        "p3_x",
        "p3_y",
        "p3_z",
        "r_eff",
        "r_eff_uncert",
        "galactic_cap",
        "source_file",
    ]

    for f_path in files:
        file_name = os.path.basename(f_path)
        print(f"Processing file: {file_name} ...")

        # AI NOTE: VoidFinder uses "MAXIMALS" HDU, not "VOIDS". This reflects
        # its algorithmic approach: VoidFinder identifies maximal empty spheres,
        # while other algorithms use hierarchical zone-based void definitions.
        # Do not normalize HDU names without understanding this distinction.
        if "REVOLVER" in file_name:
            algorithm, hdu_name = "REVOLVER", "VOIDS"
        elif "VIDE" in file_name:
            algorithm, hdu_name = "VIDE", "VOIDS"
        elif "ZOBOV" in file_name:
            algorithm, hdu_name = "ZOBOV", "VOIDS"
        elif "VoidFinder" in file_name:
            algorithm, hdu_name = "VoidFinder", "MAXIMALS"
        else:
            print(
                f"Warning: Skipping unrecognized file format: {file_name}",
                file=sys.stderr,
            )
            continue

        galactic_cap = "SGC" if "SGC" in file_name else "NGC"

        try:
            with fits.open(f_path, memmap=True) as hdul:
                if hdu_name not in hdul:
                    print(
                        f"Warning: Expected HDU '{hdu_name}' not found in {file_name}. Skipping.",
                        file=sys.stderr,
                    )
                    continue

                df = Table(hdul[hdu_name].data).to_pandas()

                df.rename(
                    columns={
                        "RA": "ra",
                        "DEC": "dec",
                        "RADIUS": "radius_mpc_h",
                        "X": "x_mpc_h",
                        "Y": "y_mpc_h",
                        "Z": "z_mpc_h",
                        "EDGE": "edge_flag",
                        "VOID": "original_void_index",
                        "REDSHIFT": "redshift",
                        "DEPTH": "depth",
                        "TOT_AREA": "tot_area",
                        "EDGE_AREA": "edge_area",
                        "GAL": "gal",
                        "OUT": "out_flag",
                        "VOID0": "void0",
                        "VOID1": "void1",
                        "X1": "x1",
                        "Y1": "y1",
                        "Z1": "z1",
                        "X2": "x2",
                        "Y2": "y2",
                        "Z2": "z2",
                        "X3": "x3",
                        "Y3": "y3",
                        "Z3": "z3",
                        "ZONE": "zone",
                        "TARGET": "target",
                        "G2V": "g2v",
                        "G2V2": "g2v2",
                        "GID": "gid",
                        "N_X": "n_x",
                        "N_Y": "n_y",
                        "N_Z": "n_z",
                        "P1_X": "p1_x",
                        "P1_Y": "p1_y",
                        "P1_Z": "p1_z",
                        "P2_X": "p2_x",
                        "P2_Y": "p2_y",
                        "P2_Z": "p2_z",
                        "P3_X": "p3_x",
                        "P3_Y": "p3_y",
                        "P3_Z": "p3_z",
                        "R_EFF": "r_eff",
                        "R_EFF_UNCERT": "r_eff_uncert",
                    },
                    inplace=True,
                )

                initial_rows = len(df)
                df.dropna(subset=["ra"], inplace=True)
                if len(df) < initial_rows:
                    print(
                        f"  > Cleaned {initial_rows - len(df)} rows with missing RA values."
                    )

                df["algorithm"] = algorithm
                df["galactic_cap"] = galactic_cap
                df["source_file"] = file_name

                # AI NOTE: Column order in df_unified must match unified_columns
                # exactly. PostgreSQL COPY is positional — column name list in the
                # COPY command maps to CSV column positions, not header names.
                df_unified = pd.DataFrame()
                for col in unified_columns:
                    if col in df:
                        df_unified[col] = df[col]
                    else:
                        df_unified[col] = None

                copy_from_stringio(df_unified, db_name, target_table, dry_run=dry_run)
                if not dry_run:
                    print(f"  > Loaded {len(df_unified)} rows into {target_table}.")

        except Exception as e:
            print(f"Error processing file {file_name}: {e}", file=sys.stderr)
            continue

    print("--- DESIVAST Ingestion Complete ---")


def main() -> int:
    """Entry point for script execution."""
    parser = argparse.ArgumentParser(
        description="DESIVAST FITS to PostgreSQL ETL Pipeline.",
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

    process_desivast_files(
        paths["desivast_dir"], db_conf["dbname_desivast"], dry_run=args.dry_run
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
