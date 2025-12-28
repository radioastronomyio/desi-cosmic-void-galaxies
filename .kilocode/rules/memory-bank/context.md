# DESI Cosmic Void Galaxies ARD — Context

## Current State
**Last Updated:** 2025-12-28

### Recent Accomplishments

- Phase 04 (ARD Foundations) complete across 4 work sessions
- Deep research validation by 3 frontier models (Gemini, GPT-5.2, Claude synthesis)
- Discovered 5 previously unidentified VACs: PROVABGS, Gfinder, AGN/QSO, CIV, MgII, BHMass
- ARD Schema v2.0 produced: 70+ columns across 9 tables
- ARD Data Dictionary v2.0 produced: ~850 lines of implementation specs
- Roadmap rewritten: ARD-first architecture, terminus at Phase 06 validation
- Repository standardization complete: 15 scripts with dual-audience commenting, 14 AI NOTEs
- All worklog READMEs updated

### Current Phase

We are currently at the **Phase 04 → Phase 05 transition**. Foundation work (schema design, planning, documentation) is complete. Ready to begin VAC ETL sprint.

### Active Work

Currently working on:
1. **Phase 04 closeout:** Final documentation updates, memory-bank sync, git commit
2. **Phase 05 preparation:** VAC acquisition planning, DESI data portal URLs

---

## Next Steps

### Immediate (This Session)
1. Update memory-bank files (this task)
2. Git commit for Phase 04 deliverables
3. Verify all files in place

### Near-Term (Phase 05)
- 05.1: VAC Acquisition — download FITS for 6 new VACs
- 05.2: Galaxy VAC ETL — PROVABGS, Gfinder to PostgreSQL
- 05.3: QSO VAC ETL — AGN/QSO, CIV, MgII, BHMass to PostgreSQL
- 05.4: Join Orchestration — materialize `ard.galaxy_ard`, `ard.qso_ard`
- 05.5: Light Validation & Parquet Export

### Future / Backlog
- Phase 06: ARD Validation (completeness audit, statistical distributions, sanity checks)
- Phase 07+: Tier 2 computations (Lick indices, k-NN, DisPerSE, Spender embeddings)
- Phase 08+: Science analysis per downstream paper

---

## Active Decisions

### Pending Decisions
- **D4000_N source:** Verify FastSpecFit meets narrow-band definition during Phase 05 ETL
- **UMAP coordinates:** Deferred to post-Tier 1

### Recent Decisions

- **2025-12-28 - ARD table structure:** Separate `ard.galaxy_ard` and `ard.qso_ard` tables (Option C). Rationale: Science cases distinct, avoids 70% null columns when querying galaxies.
- **2025-12-28 - Stellar mass source:** PROVABGS over FastSpecFit. Rationale: Non-parametric SFH recovers +0.1-0.2 dex in quiescent systems.
- **2025-12-28 - Embedding architecture:** Spender 16-D. Rationale: Fits 16GB GPU, no image I/O needed.
- **2025-12-28 - Filament finding:** DisPerSE @ 3σ persistence. Rationale: Validated for BGS density.

---

## Blockers and Dependencies

### Current Blockers
None.

### External Dependencies
- **DESI Data Portal:** VAC FITS file availability for Phase 05
- **proj-pg01:** PostgreSQL availability for ETL work
- **proj-fs02:** Network storage for Parquet exports

---

## Notes and Observations

### Recent Insights
- Deep research with multiple frontier models validated architectural decisions
- Systematic VAC review revealed significant gaps in original schema (5 new VACs)
- Three-layer enrichment model (Foundation → Physics → AI) architecturally sound
- PostgreSQL as materialization engine, Parquet as distribution format confirmed

### Context for Next Session
- Phase 04 documentation is complete and ready for commit
- Phase 05 begins with VAC acquisition (milestone 05.1)
- Schema and data dictionary are authoritative references for ETL work
- Research archives in `.internal-files/` (gitignored) inform decisions but are not version-controlled
