#!/usr/bin/env python3
"""
Script Name  : 02-fastspecfit-fits-inspector.py
Description  : Lists column names from METADATA and SPECPHOT HDUs of FastSpecFit FITS files
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-07-14
Phase        : Phase 01 - Catalog Acquisition
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
A utility to definitively list all column names from the METADATA and SPECPHOT
HDUs of a single FastSpecFit FITS file. Used to determine ground truth column
names and structure for the ETL pipeline. Outputs sorted column lists for
easy reference during schema design.

Usage
-----
    python 02-fastspecfit-fits-inspector.py <path_to_fits_file>

Examples
--------
    python 02-fastspecfit-fits-inspector.py ./data/fastspecfit/fastspec-iron-main-bright-nside1-hp00.fits
        Inspects the specified FastSpecFit file and prints column names.
"""

# =============================================================================
# Imports
# =============================================================================

import sys

from astropy.io import fits

# =============================================================================
# Functions
# =============================================================================


def inspect_columns(file_path: str) -> None:
    """
    Open a FITS file and print column names for key HDUs.
    
    FastSpecFit organizes data into two HDUs:
      - METADATA: Targeting info from DESI (TARGETID, RA, DEC, Z)
      - SPECPHOT: Derived physical properties from spectral fitting
                  (stellar mass, SFR, age, metallicity, spectral indices)
    
    This separation reflects the data provenance: METADATA comes from the
    upstream redshift catalog, SPECPHOT from FastSpecFit's own analysis.

    Parameters
    ----------
    file_path : str
        Path to the FastSpecFit FITS file.
    """
    try:
        with fits.open(file_path, memmap=True) as hdul:
            print(f"--- Inspecting File: {file_path} ---")

            if "METADATA" in hdul:
                print("\n[ METADATA HDU Columns ]")
                print("--------------------------")
                print(sorted(hdul["METADATA"].columns.names))
            else:
                print("\n[ METADATA HDU NOT FOUND ]")

            if "SPECPHOT" in hdul:
                print("\n[ SPECPHOT HDU Columns ]")
                print("------------------------")
                print(sorted(hdul["SPECPHOT"].columns.names))
            else:
                print("\n[ SPECPHOT HDU NOT FOUND ]")

    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)


def main() -> int:
    """Entry point for script execution."""
    if len(sys.argv) < 2:
        print("Usage: python 02-fastspecfit-fits-inspector.py <path_to_fits_file>")
        print("\nExample:")
        print(
            "  python 02-fastspecfit-fits-inspector.py "
            "./data/fastspecfit/fastspec-iron-main-bright-nside1-hp00.fits"
        )
        return 1

    inspect_columns(sys.argv[1])
    return 0


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
