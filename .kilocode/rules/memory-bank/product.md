# DESI Cosmic Void Galaxies ARD — Product Overview

## Problems Solved

This project addresses:

- **Fragmented VAC ecosystem:** DESI DR1 has 9+ Value Added Catalogs with different schemas, formats, and access patterns. Researchers must manually join and reconcile data for each analysis.

- **Repeated preprocessing:** Every downstream project (quenching studies, anomaly detection, outflow analysis) independently implements the same VAC joins, quality filters, and derived columns.

- **Missing derived quantities:** Key physics quantities (sSFR, BPT classification, environmental density) require computation from raw VAC columns. Without standardization, each researcher implements their own version.

- **No analysis-ready baseline:** Researchers start from raw FITS files rather than a curated, validated dataset optimized for their science case.

---

## How It Works

The DESI Cosmic Void Galaxies ARD is a materialized dataset built by joining 9 DESI Value Added Catalogs into two science-optimized products: a galaxy ARD (6.4M rows) and a QSO ARD (1.6M rows).

PostgreSQL serves as the materialization engine. VAC FITS files are ingested into `raw_catalogs.*` tables, joined on TARGETID, and materialized into `ard.*` tables with derived columns. The final products are exported to Parquet for distribution.

Key components:

- **VAC ETL Pipeline:** Ingests FITS → PostgreSQL with schema validation
- **Join Orchestration:** Materializes unified ARD tables from 9 source VACs
- **Derived Column Engine:** Computes LOG_sSFR, BPT_CLASS, EVOL_STAGE, BURST_RATIO
- **Validation Suite:** Statistical distributions, cross-VAC consistency, completeness audits
- **Parquet Export:** Distribution-ready columnar format

---

## Goals and Outcomes

### Primary Goals

1. **Unified ARD Product:** Single source of truth joining 9 VACs with 70+ columns
2. **Validated Quality:** Completeness audits, distribution checks, cross-VAC consistency verified
3. **Downstream Enablement:** Three research projects (voids, outflows, anomalies) consume the ARD

### User Experience Goals

- Researchers load one Parquet file instead of joining multiple FITS catalogs
- Derived quantities (sSFR, BPT, environment) are pre-computed and validated
- Schema documentation enables confident column selection
- Quality filters are pre-applied; researchers work with science-ready samples

### Success Metrics

- **Completeness:** >95% TARGETID join success across core VACs
- **Validation:** Statistical distributions match published DESI results
- **Adoption:** All three downstream projects successfully consume ARD
- **Documentation:** Schema and data dictionary enable self-service usage

---

## Science Cases Enabled

### 1. Cosmic Void Galaxies & Environmental Quenching (Primary)

How does the void environment affect galaxy evolution? The ARD provides:
- Void/wall classifications from DESIVAST
- Stellar mass, SFR, and sSFR from PROVABGS
- D4000, HδA indices for stellar population age
- Group membership for isolating environment effects

### 2. Quasar Anomaly Detection

What unusual QSO spectra exist in DESI DR1? The ARD provides:
- Spectral embeddings (Spender 16-D latent vectors)
- Reconstruction error as anomaly metric
- BAL flags and absorption indices for known anomaly types

### 3. Quasar Outflow Energetics

What are the physical properties of QSO outflows? The ARD provides:
- PCA-based systemic redshifts (Z_SYS) for accurate velocity measurements
- CIV and MgII column densities and equivalent widths
- Black hole masses and bolometric luminosities for Eddington normalization
