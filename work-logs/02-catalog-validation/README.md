<!--
---
title: "Phase 02: Catalog Validation"
description: "Three-stage validation: integrity, physical plausibility, and systematic uncertainty"
author: "VintageDon"
date: "2025-08-05"
version: "1.0"
status: "Complete"
tags:
  - type: worklog
  - domain: data-engineering
  - phase: validation
  - tech: [python, postgresql, matplotlib]
related_documents:
  - "[Previous Phase](../01-catalog-acquisition/README.md)"
  - "[Next Phase](../03-spectral-tile-pipeline/README.md)"
---
-->

# Phase 02: Catalog Validation

## Summary

| Attribute | Value |
|-----------|-------|
| Status | ✅ Complete |
| Sessions | 3 (Aug 4-5, 2025) |
| Artifacts | 3 scripts, 2 logs, 1 summary, 10 figures, 2 SQL files |

**Objective:** Validate ingested catalogs through three stages: (1) data integrity, (2) physical plausibility, and (3) systematic uncertainty analysis across void-finding algorithms.

**Outcome:** 6,342,556 galaxies retained post-cuts (98.4% retention). All validation checks passed. Algorithm comparison confirms consistent quenching signals.

---

## 1. Contents

```
02-catalog-validation/
├── 01-validate-integrity.py          # Stage 1: row counts, PKs, nulls
├── 01-validation-stage1.log.txt      # Stage 1 execution log
├── 02-validate-plausibility.py       # Stage 2: physical distributions
├── 02-validation-stage2.log.txt      # Stage 2 execution log
├── 02-stage2-summary.txt             # Retained sample summary
├── 03-systematic-uncertainty.py      # Stage 3: algorithm comparison
├── 03-phase3-output/                 # Stage 3 outputs
├── figures/                          # Distribution & scaling relation plots
├── sql/                              # Schema export scripts
└── README.md
```

---

## 2. Scripts

| Script | Purpose | Key Output |
|--------|---------|------------|
| `01-validate-integrity.py` | Row counts, PK uniqueness, null rates, type sanity | `01-validation-stage1.log.txt` |
| `02-validate-plausibility.py` | Apply quality cuts, plot distributions, verify scaling relations | `figures/`, `02-stage2-summary.txt` |
| `03-systematic-uncertainty.py` | Compare sSFR distributions across 4 void-finding algorithms | `03-phase3-output/` |

---

## 3. Validation

### Stage 1: Data Integrity

| Check | Status | Result |
|-------|--------|--------|
| FastSpecFit row count | ✅ Pass | 6,445,927 rows |
| DESIVAST void count | ✅ Pass | 10,752 voids |
| PK uniqueness | ✅ Pass | No duplicates |
| Null rates | ✅ Pass | <0.02% on critical columns |

### Stage 2: Physical Plausibility

| Check | Status | Result |
|-------|--------|--------|
| Redshift range | ✅ Pass | z ∈ [0.001, 1.0] |
| Stellar mass range | ✅ Pass | log(M★/M☉) ∈ [6, 13] |
| SFR-mass relation | ✅ Pass | Main sequence visible |
| Mass-z correlation | ✅ Pass | Malmquist bias as expected |
| Sample retention | ✅ Pass | 98.4% retained (6,342,556) |

### Stage 3: Systematic Uncertainty

| Check | Status | Result |
|-------|--------|--------|
| Algorithm agreement | ✅ Pass | sSFR distributions consistent across VIDE, ZOBOV, REVOLVER, VoidFinder |
| Sample size per algorithm | ✅ Pass | Sufficient statistics for all 4 |

---

## 4. Figures

### Distribution Plots

| Figure | Location | Shows |
|--------|----------|-------|
| Redshift distribution | `figures/distributions/redshift_distribution.png` | z histogram, BGS sample characteristics |
| Stellar mass distribution | `figures/distributions/stellar_mass_distribution.png` | log(M★) histogram |
| SFR distribution | `figures/distributions/sfr_distribution.png` | Star formation rate histogram |
| D4000 distribution | `figures/distributions/d4000_distribution.png` | 4000Å break strength |

### Scaling Relations

| Figure | Location | Shows |
|--------|----------|-------|
| Mass vs redshift | `figures/scaling_relations/mass_vs_redshift_critical.png` | Malmquist bias visualization |
| SFR-mass main sequence | `figures/scaling_relations/sfr_mass_main_sequence.png` | Star-forming sequence |
| sSFR vs mass | `figures/scaling_relations/ssfr_vs_mass_quenching.png` | Quenching diagnostic |

### Void Analysis

| Figure | Location | Shows |
|--------|----------|-------|
| Spatial distribution | `figures/void_analysis/void_spatial_distribution.png` | RA/DEC coverage |
| Size distributions | `figures/void_analysis/void_size_distributions.png` | Effective radii by algorithm |
| Galactic cap | `figures/void_analysis/void_galactic_cap_distribution.png` | NGC/SGC split |

---

## 5. Findings

### Key Results

- **98.4% retention:** Quality cuts remove only edge cases, preserving statistical power
- **Mass-z correlation:** Strong Malmquist-like selection effect — expected for magnitude-limited sample
- **Algorithm consistency:** All 4 void-finding algorithms show consistent environmental quenching signal

### Issues Encountered

| Issue | Resolution |
|-------|------------|
| `isfinite()` cast error | Explicit numeric cast: `WHERE isfinite(logmstar::numeric)` |
| First cut run returned zero rows | Fixed cut logic (AND vs OR), re-ran successfully |

---

## 6. Next Phase

**Handoff:** Validated catalog in PostgreSQL. Quality cuts defined. Ready for spectral pipeline integration.

**Next Steps:**

1. Proceed with spectral tile pipeline (FITS→Parquet conversion)
2. Cross-match spectral tiles with validated galaxy catalog

---

## 7. Provenance

| | |
|---|---|
| Compute | proj-dp01 (validation scripts), proj-pg01 (queries) |
| Data Location | PostgreSQL on proj-pg01 |
| Date Range | 2025-08-04 to 2025-08-05 |
