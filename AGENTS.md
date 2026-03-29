# AGENTS.md

Entry point for AI coding agents working on this repository.

## Project Identity

**Domain:** Astronomy / Data Engineering / Environmental Quenching
**Repository:** https://github.com/radioastronomyio/desi-cosmic-void-galaxies
**Purpose:** The first Analysis-Ready Dataset (ARD) for astronomy, built from DESI Data Release 1. Combines galaxy catalogs, void classifications, QSO properties, and spectral data into a unified three-layer enriched dataset. The environmental quenching study (comparing galaxy properties in cosmic voids versus walls) serves as the first consumer application and validation of the ARD architecture.

**Downstream consumers:**

| Project | Repository | Focus |
|---------|-----------|-------|
| QSO Anomaly Detection | [desi-qso-anomaly-detection](https://github.com/radioastronomyio/desi-qso-anomaly-detection) | ML outlier detection in QSO spectra |
| Quasar Outflows | [desi-quasar-outflows](https://github.com/radioastronomyio/desi-quasar-outflows) | AGN feedback and outflow energetics |

## Current State

**Phase:** Phase 04 (ARD Foundations) complete. Phase 05 (VAC ETL Sprint) next.
**Date:** March 2026

### Completed Phases

| Phase | Outcome |
|-------|---------|
| 01 Catalog Acquisition | 6.4M galaxies + 10.7K voids ingested to PostgreSQL |
| 02 Catalog Validation | 3-stage QA, 98.4% retention rate |
| 03 Spectral Pipeline | 10.8K HEALPix tiles, 2.3TB FITS to 32GB Parquet (98.6% compression) |
| 04 ARD Foundations | Schema v2.0, 9 VACs inventoried, data dictionary complete |

### What's Next

- Phase 05: Ingest remaining 7 VACs
- Phase 06: ARD validation
- Phase 07+: Tier 2 derived computations (Lick indices, pPXF kinematics, embeddings)

See `ROADMAP.md` for the full phase plan.

## Data Scale

| Component | Rows | Storage |
|-----------|------|---------|
| Galaxy catalog (post-QA) | 6,342,556 | PostgreSQL |
| Void catalog | 10,752 | PostgreSQL |
| Spectral tiles | 10,800+ | ~32 GB Parquet |
| Source FITS | n/a | ~2.3 TB (S3 archive) |

## Key Constraints

- DESI DR1 data is public but large; downloads require careful orchestration
- 9 VACs span galaxy and QSO domains with different schemas
- Spectral data lives in Parquet (converted from FITS), catalog data lives in PostgreSQL
- ARD output directory is `desi-cosmic-voids-ard/`
- The ARD methodology spec lives in a separate repo: [analysis-ready-dataset](https://github.com/radioastronomyio/analysis-ready-dataset)

## Execution Environment

**Primary execution:** ML01 (`/opt/repos/desi-cosmic-void-galaxies/`)
**Agent runtime:** OpenCode (global config at `~/.config/opencode/opencode.json`)
**Session management:** aoe (Agent of Empires)
**Strategic work:** Claude.ai Projects
**Agentic coding:** Claude Code, OpenCode

## Infrastructure

| Resource | Host | Purpose |
|----------|------|---------|
| PostgreSQL 16 | radio-pgsql01 (10.25.20.8) | Catalog storage, materialization engine |
| Spectral tiles | radio-fs02 (10.25.20.15) | Parquet storage |
| GPU compute | ML01 (A4000, 16GB) | ML training, embedding generation |

Connection patterns follow `/opt/global-env/research.env`. Never hardcode credentials.

## Repository Structure

```
desi-cosmic-void-galaxies/
├── assets/                         # Images, diagrams, banners
├── config/                         # Configuration files
├── data/                           # Large files (LFS tracked)
├── desi-cosmic-voids-ard/          # ARD output directory
├── docs/
│   ├── documentation-standards/    # Templates, tagging strategy
│   ├── ARD-SCHEMA-v2.md            # Table structure reference
│   └── ARD-DATA-DICTIONARY-v2.md   # Column definitions
├── internal-files/                 # Working documents
├── output/                         # Processing outputs
├── shared/                         # Cross-cutting assets (SQL schemas, etc.)
├── spec/                           # Specifications
├── staging/                        # Staged work (gitignored)
├── work-logs/                      # Milestone-based development history
│   ├── 01-catalog-acquisition/
│   ├── 02-catalog-validation/
│   ├── 03-spectral-tile-pipeline/
│   └── 04-ard-foundations/
├── AGENTS.md                       # This file
├── CLAUDE.md                       # Pointer to AGENTS.md
├── ROADMAP.md                      # Full phase plan
├── LICENSE                         # MIT
└── README.md
```

## Conventions

- **Documentation:** Use templates from `docs/documentation-standards/`
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `data:`)
- **Frontmatter:** YAML frontmatter with tags from `docs/documentation-standards/tagging-strategy.md`
- **Interior READMEs:** Every directory has one

## Related Repositories

| Repository | Relationship |
|-----------|-------------|
| `analysis-ready-dataset` | Domain-agnostic ARD methodology spec |
| `astronomy-rag-corpus` | Literature corpus supporting DESI research |
| `desi-qso-anomaly-detection` | Downstream consumer, QSO anomaly detection |
| `desi-quasar-outflows` | Downstream consumer, outflow energetics |
| `proxmox-astronomy-lab` | Infrastructure documentation |
