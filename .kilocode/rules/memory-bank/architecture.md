# DESI Cosmic Void Galaxies ARD — Architecture

## Overview

This project implements a tiered materialization architecture for building an Analysis-Ready Dataset from DESI DR1. PostgreSQL serves as the enrichment engine where VAC joins and computations occur. Parquet is the distribution format for downstream consumption.

The ARD separates into two products: `ard.galaxy_ard` for galaxy science (quenching, environment) and `ard.qso_ard` for quasar science (outflows, anomalies). This separation avoids 70% null columns when querying galaxies and keeps science cases cleanly isolated.

---

## Core Components

### PostgreSQL Materialization Engine
**Purpose:** Central database for VAC ingestion, joins, and derived column computation  
**Location:** proj-pg01  
**Key Characteristics:** Schemas `raw_catalogs` (source VACs), `ard` (materialized products), `science_analysis` (query views)

### Parquet Distribution Layer
**Purpose:** Columnar format for efficient downstream queries and distribution  
**Location:** proj-fs02 network share  
**Key Characteristics:** Exported from PostgreSQL after validation, serves as the "release" format

### Spectral Tile Archive
**Purpose:** FITS→Parquet converted spectra for Tier 2 embedding work  
**Location:** proj-fs02 (`/mnt/spectral-tiles/`)  
**Key Characteristics:** 12,207 tiles, 108 GB total, linked to catalog via TARGETID

---

## Structure

```
desi-cosmic-void-galaxies/
├── .kilocode/rules/memory-bank/  # Agent context (this directory)
├── .internal-files/              # Research archives (gitignored)
├── data/                         # Large files (LFS)
├── docs/
│   ├── ARD-SCHEMA-v2.md          # Column specifications
│   ├── ARD-DATA-DICTIONARY-v2.md # Implementation reference
│   └── documentation-standards/  # Templates
├── scratch/                      # Working files, checkpoints, GDR prompts
├── work-logs/
│   ├── 01-catalog-acquisition/   # Phase 01 scripts + outputs
│   ├── 02-catalog-validation/    # Phase 02 scripts + outputs
│   ├── 03-spectral-tile-pipeline/# Phase 03 scripts + outputs
│   └── 04-ard-foundations/       # Phase 04 documentation
├── ROADMAP.md                    # Project phases and planning
└── README.md                     # Project overview
```

---

## Design Patterns and Principles

### Key Patterns

- **Tiered Materialization:** Tier 1 (VAC joins, SQL-only) vs Tier 2 (derived computations, cluster/GPU)
- **Factory-Consumer Model:** This repo is the ARD factory; downstream repos consume the product
- **Schema-First Design:** ARD schema and data dictionary are authoritative; code follows schema
- **Milestone-Based Work Logs:** Each phase is self-contained with scripts, outputs, and documentation

### Design Principles

1. **PostgreSQL first:** Do as much as possible in SQL before resorting to Python/cluster compute
2. **Parquet for distribution:** Export only after validation; Parquet is the release artifact
3. **Separate Galaxy/QSO:** Different science cases get different ARD tables
4. **Provenance tracking:** Every column traces to a source VAC or computation method

---

## Integration Points

### Internal Integrations
- **proj-pg01:** PostgreSQL database, primary materialization engine
- **proj-fs02:** Network storage for spectral tiles and Parquet exports
- **radio-gpu01:** GPU compute for Tier 2 embeddings (future)

### External Integrations
- **DESI Data Portal:** Source for VAC FITS files
- **Downstream repos:** `desi-quasar-outflows`, `desi-qso-anomaly-detection` consume ARD

---

## Data Flow

```
DESI VAC FITS files
       │
       ▼ (Phase 05: ETL)
┌─────────────────────────────┐
│  raw_catalogs.* tables      │
│  (PostgreSQL)               │
└─────────────────────────────┘
       │
       ▼ (Phase 05: Join Orchestration)
┌─────────────────────────────┐
│  ard.galaxy_ard             │
│  ard.qso_ard                │
│  (PostgreSQL)               │
└─────────────────────────────┘
       │
       ▼ (Phase 05: Export)
┌─────────────────────────────┐
│  Parquet files              │
│  (proj-fs02)                │
└─────────────────────────────┘
       │
       ▼ (Phase 06: Validation)
       │
       ▼ (Phase 07+: Tier 2)
┌─────────────────────────────┐
│  Enriched ARD + Embeddings  │
└─────────────────────────────┘
```

---

## Architectural Decisions

### ADR-001: Separate Galaxy and QSO ARD Tables
**Date:** 2025-12-28  
**Decision:** Create `ard.galaxy_ard` and `ard.qso_ard` as separate tables (Option C)  
**Rationale:** Science cases are distinct; avoids 70% null columns when querying galaxies  
**Alternatives Considered:** Single unified table (rejected: too sparse), views over unified (rejected: query complexity)  
**Implications:** ETL produces two products; downstream consumers select appropriate table

### ADR-002: PROVABGS for Stellar Mass
**Date:** 2025-12-28  
**Decision:** Use PROVABGS VAC for LOG_MSTAR instead of FastSpecFit  
**Rationale:** Non-parametric SFH recovers +0.1-0.2 dex in quiescent systems  
**Alternatives Considered:** FastSpecFit (rejected: parametric SFH underestimates quiescent mass)  
**Implications:** Requires PROVABGS ingestion in Phase 05; LOG_SFR_TOTAL also from PROVABGS

### ADR-003: Spender for Spectral Embeddings
**Date:** 2025-12-28  
**Decision:** Use Spender autoencoder with 16-D latent space for embeddings  
**Rationale:** Fits 16GB GPU, no image I/O needed, validated on astronomical spectra  
**Alternatives Considered:** AstroCLIP (rejected: requires image I/O), Universal Spectrum Tokenizer (rejected: less mature)  
**Implications:** Deferred to Tier 2 (Phase 07+); A4000 GPU adequate

---

## Constraints and Limitations

- **Token budget:** Memory-bank files must be concise for agent context windows
- **Network bandwidth:** Spectral tile access assumes 2×10G LACP adequate; NVMe relocation is contingent
- **PostgreSQL capacity:** proj-pg01 has ~32GB allocated; sufficient for catalog-scale work
- **GPU memory:** A4000 (16GB) constrains embedding batch sizes and model complexity

---

## Future Considerations

### Planned Improvements
- Tier 2 computation pipeline (Phase 07)
- Automated validation suite for ARD releases
- CI/CD for schema changes

### Scalability Considerations
- DR2 will be ~10× larger; current architecture should scale with hardware
- Parquet partitioning strategy may need refinement for larger datasets

### Known Technical Debt
- Legacy `DATA_DICTIONARY.md` superseded by v2.0 but not yet removed
- Some Phase 01-03 scripts have placeholder implementations flagged with AI NOTEs
