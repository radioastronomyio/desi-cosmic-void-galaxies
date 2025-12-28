# DESI DR1 Analysis-Ready Dataset — Project Brief

**Date:** December 28, 2025  
**Purpose:** Onboarding summary for ARD development and downstream research applications

---

## Project Identity

**Repository:** `Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies`  
**Status:** Phase 04 complete, entering Phase 05 (VAC ETL Sprint)

This project transforms DESI DR1 Value Added Catalogs into a deeply enriched Analysis-Ready Dataset (ARD), then releases it to the community. The ARD serves as the shared foundation for three downstream research directions.

---

## Architecture

```
DESI DR1 VACs (9 source catalogs)
         │
         ▼
┌─────────────────────────────────────┐
│   Enrichment Engine (PostgreSQL)   │
│   • Tier 1: VAC joins              │
│   • Tier 2: Derived computations   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   ARD Products                      │
│   • ard.galaxy_ard (6.4M rows)     │
│   • ard.qso_ard (1.6M rows)        │
│   • Parquet distribution format    │
└─────────────────────────────────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
   void-galaxies   quasar-outflows   qso-anomaly
      (paper)         (paper)        (tool/paper)
```

---

## Source Assets

| Asset | Location | Scale | Status |
|-------|----------|-------|--------|
| Galaxy Catalog | PostgreSQL (proj-pg01) | 6.4M rows | ✓ Ingested |
| Void Catalog | PostgreSQL (proj-pg01) | ~10.7K voids | ✓ Ingested |
| Environmental Assignments | PostgreSQL (proj-pg01) | 6.4M rows | ✓ Complete |
| QSO Spectral Tiles | Network share (proj-fs02) | 108 GB / 12,207 tiles | ✓ Converted |
| PROVABGS, Gfinder, QSO VACs | DESI Data Portal | ~10M rows total | Pending (Phase 05) |

---

## VAC Inventory

### Currently Ingested
- FastSpecFit (6.4M galaxies)
- DESIVAST (10.7K voids, 4 algorithms)

### Phase 05 Targets
- PROVABGS (Bayesian stellar mass, SFR)
- Gfinder Group Catalog (group membership, halo mass)
- AGN/QSO Summary (systemic redshift, BAL flags)
- CIV Absorber Catalog (column densities, velocities)
- MgII Absorber Catalog (low-ionization tracers)
- BHMass VAC (black hole mass, bolometric luminosity)

---

## Enrichment Tiers

### Tier 1: VAC Joins (Phase 05)
Direct joins from 9 VACs on TARGETID. No computation required beyond SQL.

### Tier 2: Derived Computations (Phase 07+, deferred)
- Lick indices: HδA, Mgb, Fe5270, Fe5335
- k-NN density: Σ₅ from volume-limited tracers
- Filament distance: DisPerSE @ 3σ persistence
- Spectral embeddings: Spender 16-D autoencoder
- Derived classifications: BPT, EVOL_STAGE, BURST_RATIO

---

## Consumer Projects

The ARD enables these downstream applications:

| Repository | Purpose | State |
|------------|---------|-------|
| `desi-cosmic-void-galaxies` | Void galaxy quenching, environmental effects | This repo (ARD factory) |
| `desi-quasar-outflows` | QSO outflow energetics, BAL physics | Skeletal, awaits ARD |
| `desi-qso-anomaly-detection` | ML-driven spectral anomaly identification | Skeletal, awaits ARD |

---

## Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| ARD Schema v2.0 | `docs/ARD-SCHEMA-v2.md` | 70+ column specifications |
| Data Dictionary v2.0 | `docs/ARD-DATA-DICTIONARY-v2.md` | Implementation reference |
| Roadmap | `ROADMAP.md` | Phase definitions and planning |
| Work Logs | `work-logs/` | Phase-by-phase progress |

---

## Technical Decisions

**PostgreSQL as Materialization Engine**  
Enrichment happens in SQL first. Parquet export is packaging, not computation.

**Separate Galaxy + QSO ARD Tables**  
Science cases are distinct. Avoids 70% null columns when querying galaxies.

**Network Access for Spectral Data**  
2×10G LACP to proj-fs02 assumed adequate. NVMe relocation is contingent optimization.

**PROVABGS for Stellar Mass**  
Non-parametric SFH recovers +0.1-0.2 dex in quiescent systems vs FastSpecFit.

---

## Project Phases

| Phase | Name | Status |
|-------|------|--------|
| 01 | Catalog Acquisition | ✓ Complete |
| 02 | Database Foundation | ✓ Complete |
| 03 | Spectral Pipeline | ✓ Complete |
| 04 | ARD Foundations | ✓ Complete |
| 05 | VAC ETL Sprint | **Next** |
| 06 | ARD Validation | Planned |
| 07+ | Tier 2 Compute, Science | Deferred |
