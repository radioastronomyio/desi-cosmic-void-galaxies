<!--
---
title: "Phase 03: Spectral Tile Pipeline"
description: "FITS→Parquet conversion pipeline for DESI DR1 spectral tiles"
author: "VintageDon"
date: "2025-09-03"
version: "1.0"
status: "Complete"
tags:
  - type: worklog
  - domain: data-engineering
  - phase: acquisition
  - tech: [python, parquet, s3, fits, boto3]
related_documents:
  - "[Previous Phase](../02-catalog-validation/README.md)"
  - "[Next Phase](../04-ard-materialization/README.md)"
---
-->

# Phase 03: Spectral Tile Pipeline

## Summary

| Attribute | Value |
|-----------|-------|
| Status | ✅ Complete |
| Sessions | 4 (Sept 1-3, 2025) |
| Artifacts | 7 scripts, 2 production logs |

**Objective:** Download 12,207 DESI DR1 HEALPix tiles from S3, convert fragmented FITS files to unified Parquet format, achieving laptop-queryable spectral data.

**Outcome:** 10,800+ tiles converted successfully. 98.6% compression (2.3TB FITS → ~32GB Parquet). 61-hour unattended production run with zero manual intervention.

---

## 1. Contents

```
03-spectral-tile-pipeline/
├── 01-benchmark-downloads.py           # HTTP concurrency testing
├── 01-benchmark-s3.py                  # S3 worker count optimization
├── 01-correct-s3-paths.py              # Inventory path normalization
├── 02-extract-qso-tile-to-parquet.py   # Core FITS→Parquet converter
├── 02-process-desi-batch.py            # Local batch processor
├── 03-dry-run_20250901_040950.log.txt  # 40-tile validation run
├── 03-process-desi-s3-batch.py         # S3 batch downloader + converter
├── 03-production_20250901_043529.log.txt  # Full 12,207 tile run
├── 04-analyze-parquet-output.py        # Output validation
└── README.md
```

---

## 2. Scripts

| Script | Purpose | Key Output |
|--------|---------|------------|
| `01-benchmark-s3.py` | Test 1-16 S3 workers, find optimal concurrency | 8 workers optimal (38.5 MB/s) |
| `01-benchmark-downloads.py` | HTTP concurrency ceiling detection | Rate limit threshold identification |
| `01-correct-s3-paths.py` | Normalize S3 object keys from DESI manifest | Corrected inventory |
| `02-extract-qso-tile-to-parquet.py` | Multi-file fusion FITS→Parquet converter | Unified QSO records per tile |
| `02-process-desi-batch.py` | Queue-based local tile processing | Batch execution with cleanup |
| `03-process-desi-s3-batch.py` | Resumable S3 download + conversion orchestrator | Production logs |
| `04-analyze-parquet-output.py` | Validate output schema, row counts, compression | Validation report |

---

## 3. Validation

### Dry Run (40 tiles)

| Check | Status | Result |
|-------|--------|--------|
| Batch completion | ✅ Pass | 5/5 batches, 40/40 tiles |
| Compression ratio | ✅ Pass | 98.6% avg (7.7GB FITS → 106MB Parquet) |
| Throughput | ✅ Pass | 34.2 MB/s average |
| Resume capability | ✅ Pass | Checkpoint recovery tested |

### Production Run (12,207 tiles)

| Check | Status | Result |
|-------|--------|--------|
| Tiles processed | ✅ Pass | 10,800+ successful (~88.5%) |
| Zero-QSO tiles | ✅ Expected | ~1.7% (valid nulls from ZWARN filter) |
| Pending analysis | ⚠️ Deferred | ~10% require categorization |
| Runtime | ✅ Pass | 60h 57m (within 3-day estimate) |
| Manual interventions | ✅ Pass | Zero |

---

## 4. Key Metrics

| Metric | Value |
|--------|-------|
| Total FITS downloaded | ~2.3 TB |
| Total Parquet output | ~32 GB |
| Compression ratio | 98.6% |
| Sustained throughput | 34 MB/s (8 workers) |
| Optimal worker count | 8 (diminishing returns above 10) |

---

## 5. Technical Approach

### Multi-File Fusion

Each HEALPix tile has 4 FITS file types:
- `redrock` — redshift fits
- `coadd` — combined spectra (B/R/Z arms)
- `emline` — emission line measurements
- `rdetails` — fit quality metrics

Converter merges all 4 into single Parquet record per QSO.

### Wavelength Compression

- Masked to science range: 3600-9800Å
- Removes low-S/N edges
- Precision: 6 decimal places (preserves S/N~5 measurements)

### Output Schema

```
target_id: int64
ra, dec, z: float64
wavelength: list<float>   # ~3000 elements (3600-9800Å)
flux: list<float>
ivar: list<float>
mask_array: list<int>
rr_chi2: float64          # optional
```

---

## 6. Findings

### Key Results

- **S3 sweet spot:** 8 workers = 95% of max throughput with 0% failure rate
- **Zero-output tiles valid:** 37.5% of tiles have no ZWARN==0 QSOs (sparse sky regions)
- **DESI archive stability:** 61 hours sustained load, no throttling

### Issues Encountered

| Issue | Resolution |
|-------|------------|
| Rate limiting above 10 workers | Benchmark-driven optimization to 8 workers |
| Memory overflow on large tiles | Streaming FITS access with HDU-level reads |
| Disk space during run | Aggressive cleanup: delete FITS after Parquet conversion |

---

## 7. Next Phase

**Handoff:** Parquet tiles on proj-fs02 network share. DuckDB-queryable spectral data ready for cross-match with catalog.

**Next Steps:**

1. Categorize pending ~1,200 tiles (missing source vs zero-QSO vs errors)
2. Build cross-match linkage index (catalog ↔ spectral tiles)
3. Begin ARD materialization

---

## 8. Provenance

| | |
|---|---|
| Compute | edge01 (downloads, conversion) |
| Storage | proj-fs02 network share (2x10G LACP) |
| Data Source | DESI DR1 S3: `s3://desi-public/dr1/spectro/redux/fuji/healpix/` |
| Date Range | 2025-09-01 04:35 to 2025-09-03 17:32 |
