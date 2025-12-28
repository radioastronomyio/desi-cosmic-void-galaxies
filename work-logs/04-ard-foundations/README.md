<!--
---
title: "Phase 04: ARD Foundations"
description: "Repository standardization, deep research schema validation, VAC discovery, and sprint planning"
author: "VintageDon"
date: "2025-12-28"
version: "2.0"
status: "Complete"
tags:
  - type: worklog
  - domain: [documentation, schema-design, planning]
  - phase: foundations
  - tech: [python, markdown, postgresql]
related_documents:
  - "[Previous Phase](../03-spectral-tile-pipeline/README.md)"
  - "[ARD Schema v2.0](../../docs/ARD-SCHEMA-v2.md)"
  - "[Data Dictionary v2.0](../../docs/ARD-DATA-DICTIONARY-v2.md)"
  - "[Roadmap](../../ROADMAP.md)"
---
-->

# Phase 04: ARD Foundations

## Summary

| Attribute | Value |
|-----------|-------|
| Status | ✅ Complete |
| Sessions | 4 (Dec 27-28, 2025) |
| Artifacts | Schema v2.0, Data Dictionary v2.0, Roadmap, 15 scripts updated |

Objective: Establish the foundation for ARD development — standardize repository, validate schema design through multi-model deep research, and plan the ETL sprint.

Outcome: Discovered 5 previously unidentified VACs through systematic research, expanded schema from ~30 to 70+ columns, produced comprehensive data dictionary, and defined clear Phase 05-06 milestones. Repository documentation and code standards complete.

---

## 1. Contents

```markdown
04-ard-foundations/
└── README.md                         # This file (work log)
```

Work artifacts distributed to appropriate locations:

| Artifact | Location |
|----------|----------|
| ARD Schema v2.0 | `docs/ARD-SCHEMA-v2.md` |
| Data Dictionary v2.0 | `docs/ARD-DATA-DICTIONARY-v2.md` |
| Roadmap | `ROADMAP.md` (root) |
| Documentation standards | `docs/documentation-standards/` |
| Research archives | `.internal-files/` (gitignored) |

---

## 2. Work Sessions

### Session 1: Repository Restructure (Dec 27)

Migrated from ad-hoc structure to milestone-based organization.

Actions:

- Consolidated work into 4 milestone directories (01-03 existing, 04 new)
- Rewrote all READMEs with ARD-first framing
- Created lean documentation templates (YAML frontmatter, semantic numbering)
- Added ARD concept one-pager (`docs/what-is-an-ard.md`)
- Created GDR prompts for schema research (literature-driven + data-driven)

Deliverables:

- 11 READMEs written/updated
- 3 documentation templates
- 2 GDR prompt specifications

---

### Session 2: Code Commenting Standards (Dec 28, AM)

Applied dual-audience commenting pattern across all scripts.

Actions:

- Added standardized headers to all 15 Python scripts
- Applied human-first + AI NOTE commenting pattern
- Documented domain knowledge (thresholds, data conventions)
- Flagged hidden constraints that could cause silent bugs

Deliverables:

- 15 scripts standardized
- 14 AI NOTEs added (positional dependencies, placeholder flags)

Key AI NOTEs by Phase:

| Phase | Example Constraint |
|-------|-------------------|
| 01 | VoidFinder uses "MAXIMALS" HDU, not "VOIDS" |
| 02 | log_ssfr floor (1e-15) is numerical, not physical |
| 03 | B→R→Z concatenation order is mandatory for monotonic wavelength |

---

### Session 3: Deep Research & Schema Validation (Dec 28, PM)

Executed systematic schema validation using three frontier models.

Research Approach:

Two isolated GDR prompts executed in parallel:

1. Literature-driven: Survey DESI publications 2020-2025 for derived quantities
2. Data-driven: First-principles analysis of available VACs and science cases

Results synthesized by GPT, then validated by Gemini Deep Research against the synthesis.

Major Discovery: 5 New VACs Identified

The validation research revealed critical gaps in the original schema. Five VACs were missing entirely:

| VAC | Purpose | Impact |
|-----|---------|--------|
| PROVABGS | Bayesian stellar mass, SFR (non-parametric SFH) | +0.1-0.2 dex mass recovery in quiescent systems |
| Gfinder Group Catalog | Group/cluster membership, halo mass | Central vs satellite classification |
| AGN/QSO Summary | Z_PCA systemic redshift, BAL flags | Corrects broad-line bias in outflow velocities |
| CIV Absorber Catalog | Column densities, absorption velocities | Required for outflow energetics |
| MgII Absorber Catalog | Low-ionization outflow tracers | Complementary to CIV |
| BHMass VAC | Virial black hole mass, bolometric luminosity | Eddington normalization |

Architectural Decisions Validated:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Embeddings | Spender 16-D | Fits 16GB GPU, no image I/O needed |
| Stellar mass | PROVABGS (not FastSpecFit) | Non-parametric SFH, better quiescent recovery |
| Void source | DESIVAST (no recompute) | Authoritative, 4 algorithms available |
| Filaments | DisPerSE @ 3σ persistence | Validated for BGS density |
| ARD structure | Separate Galaxy + QSO tables | Clean science separation, avoids 70% null columns |

---

### Session 4: Schema & Roadmap Production (Dec 28, PM)

Materialized research into actionable deliverables.

Actions:

- Produced ARD Schema v2.0 (70+ columns, 9 tables)
- Produced Data Dictionary v2.0 (implementation specifications)
- Rewrote project roadmap (terminates at Phase 06)
- Defined Phase 05 milestones (VAC ETL sprint)
- Defined Phase 06 milestones (ARD validation)

---

## 3. Deliverables

### ARD Schema v2.0

| Property | Value |
|----------|-------|
| Columns | 70+ |
| Tables | 9 (Foundation, Photometry, Galaxy Physics, Spectral Indices, Emission Lines, Classification, Environment, QSO Physics, AI/ML) |
| Tier 1 sources | 9 VACs |
| Tier 2 computations | 6 (Lick indices, k-NN, DisPerSE, Spender, derived classifications) |

### Data Dictionary v2.0

| Property | Value |
|----------|-------|
| Length | ~850 lines |
| Coverage | Every column: type, unit, range, null handling, source, formula |
| Sections | 12 (one per layer + VAC joins, quality filters, conventions) |

### Roadmap

| Property | Value |
|----------|-------|
| Phases defined | 04-06 (current through validation) |
| Phases deferred | 07+ (Tier 2 compute, science analysis) |
| Terminus | Phase 06 (ARD Validation) |

---

## 4. VAC Inventory (Post-Research)

### Currently Ingested

| VAC | Rows | Status |
|-----|------|--------|
| FastSpecFit | 6.4M | ✓ Complete |
| DESIVAST | ~10.7K voids | ✓ Complete |

### Phase 05 Targets

| VAC | Est. Rows | Status |
|-----|-----------|--------|
| PROVABGS | ~6M | Pending |
| Gfinder | ~2M | Pending |
| AGN/QSO Summary | ~1.6M | Pending |
| CIV Absorber | ~100K | Pending |
| MgII Absorber | ~200K | Pending |
| BHMass | ~1M | Pending |

### Excluded (Anti-Portfolio)

| VAC | Reason |
|-----|--------|
| Lyman-α Forest | Cosmology focus, terabyte scale |
| EMFit | Redundant with FastSpecFit |
| Stellar Catalog | Milky Way, not extragalactic |

---

## 5. Phase 05-06 Plan

### Phase 05: VAC ETL Sprint

| Milestone | Description |
|-----------|-------------|
| 05.1 | VAC Acquisition (download, Parquet conversion if needed) |
| 05.2 | Galaxy VAC ETL (PROVABGS, Gfinder) |
| 05.3 | QSO VAC ETL (AGN/QSO, CIV, MgII, BHMass) |
| 05.4 | Join Orchestration (`ard.galaxy_ard`, `ard.qso_ard`) |
| 05.5 | Light Validation & Parquet Export |

### Phase 06: ARD Validation

| Milestone | Description |
|-----------|-------------|
| 06.1 | Completeness Audit (join success, coverage) |
| 06.2 | Statistical Distributions (mass function, SFR-M*, D4000) |
| 06.3 | Environment Sanity Checks (void fraction, group rates) |
| 06.4 | QSO Diagnostics (BAL fraction, BH mass distribution) |
| 06.5 | Cross-VAC Consistency (PROVABGS vs FastSpecFit) |
| 06.6 | Validation Report |

Validation Gate: No downstream work begins until Phase 06 complete.

---

## 6. Research Archive

Deep research outputs stored in `.internal-files/` (gitignored):

| Category | Contents |
|----------|----------|
| GDR outputs | Literature-driven and data-driven schema research |
| Validation | Schema validation by 3 frontier models |
| Synthesis | GPT synthesis document, Gemini validation |
| Archives | Prior project documents (superseded) |

These inform decisions but are not version-controlled. The schema and data dictionary are the authoritative outputs.

---

## 7. Pending Items

Carried forward to Phase 05:

| Item | Resolution |
|------|------------|
| D4000_N source | Verify FastSpecFit meets narrow-band definition vs recompute |
| UMAP coordinates | Deferred to post-Tier 1 |
| Fe indices | Confirmed for inclusion (FE5270, FE5335) |

---

## 8. Provenance

| | |
|---|---|
| Compute | Local development |
| Date Range | 2025-12-27 to 2025-12-28 |
| Research Tools | Gemini Deep Research, GPT-5.2 Deep Research, Claude synthesis |
| Reference | GDR prompts in `scratch/gdr-01-*.md`, `scratch/gdr-02-*.md` |
