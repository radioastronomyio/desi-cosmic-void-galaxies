<!--
---
title: "Phase 01: Catalog Acquisition"
description: "DESIVAST and FastSpecFit catalog download, inspection, and PostgreSQL ingestion"
author: "VintageDon"
date: "2025-07-14"
version: "1.0"
status: "Complete"
tags:
  - type: worklog
  - domain: data-engineering
  - phase: acquisition
  - tech: [python, postgresql, fits, astropy]
related_documents:
  - "[Next Phase](../02-catalog-validation/README.md)"
  - "[Data Dictionary](../../docs/DATA_DICTIONARY.md)"
---
-->

# Phase 01: Catalog Acquisition

## Summary

| Attribute | Value |
|-----------|-------|
| Status | ✅ Complete |
| Sessions | 3 (July 2, July 14, 2025) |
| Artifacts | 5 scripts |

**Objective:** Acquire DESIVAST void catalogs and FastSpecFit galaxy catalogs from DESI DR1, inspect FITS structure, and ingest into PostgreSQL for downstream analysis.

**Outcome:** 10,752 voids (4 algorithms) and 6.4M galaxies loaded into PostgreSQL on proj-pg01. COPY-based ingestion achieved 150k rows/sec throughput.

---

## 1. Contents

```
01-catalog-acquisition/
├── 01-desivast-download.py           # Download DESIVAST FITS from NERSC
├── 01-desivast-fits-inspector.py     # Inspect DESIVAST HDU structure
├── 02-fastspecfit-fits-inspector.py  # Inspect FastSpecFit HDU structure
├── 03-etl-desivast-postgresql.py     # Ingest DESIVAST to PostgreSQL
├── 03-etl-fastspecfit-postgresql.py  # Ingest FastSpecFit to PostgreSQL
└── README.md
```

---

## 2. Scripts

| Script | Purpose | Key Output |
|--------|---------|------------|
| `01-desivast-download.py` | Download 8 DESIVAST FITS files (~1.2GB) from DESI public archive | FITS files in data directory |
| `01-desivast-fits-inspector.py` | Scan FITS HDUs, extract column metadata, sample values | JSON schema manifests |
| `02-fastspecfit-fits-inspector.py` | Inspect FastSpecFit healpix FITS structure | Column type inference |
| `03-etl-desivast-postgresql.py` | COPY-based ingestion of void catalogs | `desi_void_desivast` database |
| `03-etl-fastspecfit-postgresql.py` | COPY-based ingestion of 6.4M galaxies | `desi_void_fastspecfit` database |

---

## 3. Validation

| Check | Status | Evidence |
|-------|--------|----------|
| DESIVAST file count | ✅ Pass | 8/8 FITS files downloaded (all 4 algorithms × NGC/SGC) |
| Void count | ✅ Pass | 10,752 voids across algorithms |
| FastSpecFit row count | ✅ Pass | 6,445,927 galaxies ingested |
| Coordinate coverage | ✅ Pass | RA [0°, 360°], DEC [-35°, 90°] matches DESI footprint |
| Redshift range | ✅ Pass | z ∈ [0.001, 0.45] consistent with BGS sample |

---

## 4. Findings

### Key Results

- **HDU structure varies by algorithm:** VoidFinder uses "VOIDS_DATA", ZOBOV uses "MAXIMAL" — inspector handles dynamically
- **COPY vs INSERT:** 150k rows/sec vs 5k rows/sec on proj-pg01. 30x throughput gain.
- **Galactic cap encoding:** NGC/SGC split encoded in filenames, not FITS columns. Parsed during ingestion.

### Issues Encountered

| Issue | Resolution |
|-------|------------|
| HDU index assumption | Used `hdul.info()` to discover structure dynamically |
| Header typo ("Pxomox") | Documented for provenance; doesn't affect data |
| Plaintext credentials in config.ini | Flagged for migration to `.env` |

---

## 5. Data Products

| Database | Table | Rows | Description |
|----------|-------|------|-------------|
| `desi_void_desivast` | `voids` | 10,752 | Void catalog (all 4 algorithms) |
| `desi_void_fastspecfit` | `galaxies` | 6,445,927 | Galaxy properties (stellar mass, SFR, z) |

---

## 6. Next Phase

**Handoff:** PostgreSQL tables ready for validation queries on proj-pg01.

**Next Steps:**

1. Run Stage 1 integrity validation (row counts, PK uniqueness, null rates)
2. Run Stage 2 physical plausibility checks (redshift distributions, mass-SFR relations)

---

## 7. Provenance

| | |
|---|---|
| Compute | proj-dp01 (download, inspection), proj-pg01 (PostgreSQL) |
| Data Source | DESI DR1 public archive (NERSC) |
| Date Range | 2025-07-02 to 2025-07-14 |
