# DESI DR1 Analysis-Ready Dataset — Project Roadmap

Last Updated: 2025-12-28  
Current Phase: 04 (Repository Standardization & Planning)  
Roadmap Terminus: Phase 06 (ARD Validation)

---

## Project Overview

### Objective

Build a comprehensive Analysis-Ready Dataset (ARD) from DESI Data Release 1 that serves as upstream infrastructure for three downstream research projects:

1. Cosmic Void Galaxies & Environmental Quenching — Primary science case
2. Quasar Anomaly Detection — ML-driven spectral outlier identification
3. Quasar Outflow Energetics — BAL physics and feedback mechanisms

### Architecture

The ARD follows a tiered materialization strategy:

- Tier 1: Direct joins from 9 DESI Value-Added Catalogs (VACs)
- Tier 2: Derived computations (Lick indices, k-NN density, DisPerSE filaments, Spender embeddings)

This roadmap covers Tier 1 materialization through validation. Tier 2 computations are deferred to Phase 07+.

### Data Scale

| Component | Rows | Storage |
|-----------|------|---------|
| Galaxy Catalog (FastSpecFit) | 6.4M | ~15 GB |
| QSO Sample | 1.6M | ~3 GB |
| Void Catalog (DESIVAST) | ~10.7K | <100 MB |
| Spectral Tiles (Parquet) | 12,207 tiles | 108 GB |

### Infrastructure

| Resource | Role |
|----------|------|
| proj-pg01 | PostgreSQL materialization engine |
| proj-fs02 | Network storage (spectral tiles, Parquet exports) |
| radio-gpu01 | GPU compute (Tier 2, future) |

---

## Completed Phases

### Phase 01: Catalog Acquisition ✓

- Downloaded DESIVAST void catalogs (4 algorithms × 2 hemispheres)
- Downloaded FastSpecFit galaxy properties (12 HEALPix files)
- FITS → Parquet conversion for spectral tiles (98.6% compression)

### Phase 02: Database Foundation ✓

- PostgreSQL schema design (`raw_catalogs`, `science_analysis`)
- FastSpecFit ingestion: 6.4M rows in `raw_catalogs.fastspecfit_galaxies`
- DESIVAST ingestion: ~10.7K voids in `raw_catalogs.desivast_voids`
- Galaxy-void environmental assignments materialized

### Phase 03: Spectral Pipeline ✓

- FITS → Parquet conversion pipeline
- 12,207 tile directories processed
- Schema: `target_id`, `ra`, `dec`, `z`, `wavelength`, `flux`, `ivar`, `mask_array`
- Network storage configuration on proj-fs02

---

## Current Phase

### Phase 04: Repository Standardization & Planning

Status: In Progress

| Milestone | Description | Status |
|-----------|-------------|--------|
| 04.1 | ARD Schema consolidation (v2.0) | ✓ Complete |
| 04.2 | Data Dictionary (v2.0) | ✓ Complete |
| 04.3 | Sprint planning (Phase 05-06) | ✓ Complete |
| 04.4 | Repository documentation update | In Progress |

Key Outputs:

- `docs/ARD-SCHEMA-v2.md` — 70+ column schema with Tier assignments
- `docs/ARD-DATA-DICTIONARY-v2.md` — Implementation specifications
- Updated `ROADMAP.md` (this document)

---

## Upcoming Phases

### Phase 05: VAC ETL Sprint

Objective: Ingest all remaining Value-Added Catalogs and materialize unified ARD tables.

#### New VACs to Ingest

| VAC | Science Case | Target Table |
|-----|--------------|--------------|
| PROVABGS | Galaxy quenching | `raw_catalogs.provabgs` |
| Gfinder Group Catalog | Environment | `raw_catalogs.gfinder_groups` |
| AGN/QSO Summary | Anomaly + Outflows | `raw_catalogs.agnqso_summary` |
| CIV Absorber | Outflows | `raw_catalogs.civ_absorbers` |
| MgII Absorber | Outflows | `raw_catalogs.mgii_absorbers` |
| BHMass | Outflows | `raw_catalogs.bhmass` |

#### Milestones

| Milestone | Description | Deliverable |
|-----------|-------------|-------------|
| 05.1 | VAC Acquisition | All FITS downloaded, Parquet conversion if needed |
| 05.2 | Galaxy VAC ETL | `provabgs`, `gfinder_groups` tables populated |
| 05.3 | QSO VAC ETL | 4 QSO-related tables populated |
| 05.4 | Join Orchestration | `ard.galaxy_ard`, `ard.qso_ard` materialized |
| 05.5 | Light Validation & Export | Row counts, null rates, Parquet export |

#### Dependencies

```markdown
05.1 VAC Acquisition
 │
 ├──────────────────┐
 │                  │
 ▼                  ▼
05.2 Galaxy ETL    05.3 QSO ETL
 │                  │
 └────────┬─────────┘
          │
          ▼
      05.4 Join Orchestration
          │
          ▼
      05.5 Light Validation
```

#### ARD Table Strategy

Two separate ARD products (Option C from design review):

- `ard.galaxy_ard` — Foundation + Galaxy Physics + Environment layers
- `ard.qso_ard` — Foundation + QSO Physics layers

Rationale: Science cases are distinct; avoids 70% null columns when querying galaxies.

---

### Phase 06: ARD Validation

Objective: Full scientific validation before any downstream analysis. The ARD is the foundation for three papers — errors here propagate everywhere.

#### Milestones

| Milestone | Description | Deliverable |
|-----------|-------------|-------------|
| 06.1 | Completeness Audit | Join success rates, TARGETID coverage, missing data patterns |
| 06.2 | Statistical Distributions | Mass function, z distribution, SFR-M* relation, D4000 histogram |
| 06.3 | Environment Sanity Checks | Void fraction (~40% expected), group membership rates, density distribution |
| 06.4 | QSO Diagnostics | BAL fraction, BH mass distribution, absorber detection rates |
| 06.5 | Cross-VAC Consistency | PROVABGS vs FastSpecFit SFR, redshift agreement, flag reconciliation |
| 06.6 | Validation Report | Document with figures, known issues, caveats |

#### Validation Gate

No downstream work begins until Phase 06 is complete and the ARD is certified.

---

## Deferred Phases (Post-Roadmap)

These phases are scoped but not scheduled. They begin after Phase 06 validation.

### Phase 07: Tier 2 Computations

| Component | Method | Hardware |
|-----------|--------|----------|
| Lick Indices (HδA, Mgb, Fe) | pPXF at Lick resolution | CPU cluster |
| k-NN Density (Σ₅) | cKDTree on volume-limited sample | CPU cluster |
| Filament Distance | DisPerSE (3σ persistence) | CPU cluster |
| Spectral Embeddings | Spender autoencoder (16-D) | GPU (A4000) |
| Derived Classifications | BPT, EVOL_STAGE, BURST_RATIO | SQL |

### Phase 08+: Science Analysis

Individual analysis phases per downstream paper:

- Void galaxy quenching analysis
- QSO anomaly detection pipeline
- Outflow energetics calculations

---

## VAC Inventory

### Currently Ingested

| VAC | Table | Rows | Status |
|-----|-------|------|--------|
| FastSpecFit | `raw_catalogs.fastspecfit_galaxies` | 6.4M | ✓ Complete |
| DESIVAST | `raw_catalogs.desivast_voids` | ~10.7K | ✓ Complete |
| — | `galaxy_void_assignments` | 6.4M | ✓ Complete |

### Phase 05 Targets

| VAC | Table | Est. Rows | Status |
|-----|-------|-----------|--------|
| PROVABGS | `raw_catalogs.provabgs` | ~6M | Pending |
| Gfinder | `raw_catalogs.gfinder_groups` | ~2M | Pending |
| AGN/QSO Summary | `raw_catalogs.agnqso_summary` | ~1.6M | Pending |
| CIV Absorber | `raw_catalogs.civ_absorbers` | ~100K | Pending |
| MgII Absorber | `raw_catalogs.mgii_absorbers` | ~200K | Pending |
| BHMass | `raw_catalogs.bhmass` | ~1M | Pending |

### Excluded (Anti-Portfolio)

| VAC | Reason |
|-----|--------|
| Lyman-α Forest Catalogs | Cosmology focus, terabyte scale, not object-level |
| EMFit | Redundant with FastSpecFit |
| Stellar Catalog | Milky Way, not extragalactic |

---

## Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| ARD Schema v2.0 | `docs/ARD-SCHEMA-v2.md` | Column specifications, Tier assignments |
| Data Dictionary v2.0 | `docs/ARD-DATA-DICTIONARY-v2.md` | Implementation details, formulas, validation |
| Work Logs | `work-logs/` | Phase-by-phase progress documentation |

---

## Design Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Embedding architecture | Spender (16-D) | Fits 16GB GPU, no image I/O |
| Void source | DESIVAST (no recompute) | Authoritative, 4 algorithms |
| Stellar mass source | PROVABGS | Non-parametric SFH, +0.1-0.2 dex in quiescent |
| Fiber vs total SFR | Both (BURST_RATIO metric) | Avoids aperture bias |
| ARD table structure | Separate Galaxy + QSO | Clean science separation |
| Filament finding | DisPerSE @ 3σ | Validated for BGS density |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-28 | Major rewrite: ARD-first architecture, 9 VACs, Phases 04-06 defined |
| 2025-10-04 | Initial roadmap (direct-to-analysis approach, superseded) |
