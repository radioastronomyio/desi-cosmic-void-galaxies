---
title: "DESI Void-Galaxy Live-State Reconciliation"
description: "Read-only reconciliation of pgsql01 catalogs and the fs02 DESI QAD tile store as observed on 2026-07-10."
author: "https://github.com/vintagedon/"
date: "2026-07-10"
version: "1.0"
status: "Complete"
tags:
  - type: worklog
  - domain: [astronomy, data-engineering, documentation]
  - tech: [postgresql, parquet, bash]
---

# DESI Void-Galaxy Live-State Reconciliation

## Scope and method

This is a dated, read-only observation of pgsql01 and the mounted radio-fs02
share. PostgreSQL connections used `default_transaction_read_only=on`; the
only queries were catalog reads and `COUNT(*)` on central relations. The share
was inspected with `find`, `stat`-style size collection, and mount inspection.
No database object, share file, or existing repository file was modified.

The companion machine-readable findings are in
[`live-state-2026-07-10.csv`](live-state-2026-07-10.csv).

## Executive findings

1. pgsql01 is a **multi-database legacy layout**, not one database containing
   the documented `raw_catalogs` universe. The live DESI databases are
   `desi_void_fastspecfit`, `desi_void_desivast`, and `desi_publication_v1`.
   `desi_ard` and `cosmicvoids_ard` are absent.
2. The two source catalogs are live and their exact counts agree with the
   source-catalog claims: 6,445,927 FastSpecFit rows and 10,752 DESIVAST rows.
3. **Assignment verdict: placeholder proxy.** No populated galaxy-to-void
   relation exists. The one plausible relationship table has zero rows, while
   the Phase 02 analysis script explicitly uses randomly sampled RA bands and
   calls them a placeholder rather than true void membership. The Phase 02
   quenching conclusion is therefore unsupported by the live state.
4. None of the Phase 05 target VACs, including Stellar Mass/EmLine, is loaded
   or staged in the inspected locations. No PROVABGS product was found, so its
   DR1-versus-EDR identity is unresolvable.
5. The radio-fs02 tile store has a success outcome for all 12,207 expected
   tiles: 10,793 Parquet outputs and 1,414 no-QSO success markers. Parquet data
   occupy 115,994,008,603 bytes (108.028 GiB; 115.994 decimal GB). This supports
   the Roadmap's 108 figure only when it means GiB; it does not support the
   README/AGENTS 32-GB figure.

## 1. Database topology and table inventory

All non-template databases enumerated on pgsql01 were:

`aimodels_wiki`, `astronomy_rag_corpus`, `bench`, `cosmos2025`,
`desi_publication_v1`, `desi_void_desivast`, `desi_void_fastspecfit`,
`epsteinfiles_ard`, `mlflow_tracking`, `msp4_halopsa_metrics`, `postgres`,
`rbh1_validation`, `steam5k`, and `steamfull`.

Only the three `desi_*` databases are the live DESI layout. A catalog scan also
found an empty legacy-looking `postgres.public.fastspecfit_galaxies` table;
it is not a populated source catalog. `reltuples=-1` below means PostgreSQL has
no usable estimate, not an estimate of negative one. Exact counts were limited
to source, assignment, and `publication_v1` ARD relations.

| Database | Schema | Relation | Kind | `reltuples` estimate | Exact count where required |
|---|---|---|---|---:|---:|
| desi_void_fastspecfit | raw_catalogs | fastspecfit_galaxies | table | 6,445,880 | 6,445,927 |
| desi_void_fastspecfit | public | fastspecfit_galaxies | table | unknown | — |
| desi_void_desivast | raw_catalogs | desivast_voids | table | 10,752 | 10,752 |
| desi_void_desivast | public | desivast_revolver_voids | table | unknown | — |
| desi_void_desivast | public | desivast_vide_voids | table | unknown | — |
| desi_void_desivast | public | desivast_voidfinder_maximals | table | unknown | — |
| desi_void_desivast | public | desivast_zobov_voids | table | unknown | — |
| desi_publication_v1 | publication_v1 | galaxies | table | unknown | 0 |
| desi_publication_v1 | publication_v1 | voids | table | unknown | 0 |
| desi_publication_v1 | publication_v1 | galaxy_void_relationships | table | unknown | 0 |
| desi_publication_v1 | publication_v1 | galaxy_embeddings | table | unknown | 0 |
| desi_publication_v1 | publication_v1 | galaxy_ml | table | unknown | 0 |
| desi_publication_v1 | publication_v1 | discovery_candidates | view | unknown | — |
| desi_publication_v1 | publication_v1 | environmental_analysis | view | unknown | — |
| desi_publication_v1 | public | source_galaxies | foreign table | unknown | — |
| desi_publication_v1 | public | source_voids | foreign table | unknown | — |
| desi_publication_v1 | public | spatial_ref_sys | table | 8,500 | — |
| desi_publication_v1 | public | geography_columns | view | unknown | — |
| desi_publication_v1 | public | geometry_columns | view | unknown | — |
| desi_publication_v1 | public | pg_stat_statements | view | unknown | — |
| desi_publication_v1 | public | pg_stat_statements_info | view | unknown | — |
| desi_void_desivast | public | pg_stat_statements | view | unknown | — |
| desi_void_desivast | public | pg_stat_statements_info | view | unknown | — |
| desi_void_fastspecfit | public | pg_stat_statements | view | unknown | — |
| desi_void_fastspecfit | public | pg_stat_statements_info | view | unknown | — |

The source relations the documentation asserts are present, but in separate
databases: `desi_void_fastspecfit.raw_catalogs.fastspecfit_galaxies` and
`desi_void_desivast.raw_catalogs.desivast_voids`. Every ROADMAP Phase 05 target
table is absent. There is no materialized post-QA relation: the documented
6,342,556 retained galaxies cannot be independently measured from a live table.

## 2. Void/wall assignment provenance

**Verdict: placeholder proxy.**

The only plausible materialized relation is
`desi_publication_v1.publication_v1.galaxy_void_relationships`. Its columns
(`pal_id`, `void_id`, `distance_mpc`, `is_interior`, `distance_in_radii`, and
`distance_rank`) could support a traceable geometric assignment, but the exact
row count is **0**. `publication_v1.galaxies` and `publication_v1.voids` are
also empty. No other assignment relation was found across the cluster's
non-template databases.

The only located assignment-producing analysis is
`work-logs/02-catalog-validation/03-systematic-uncertainty.py`. Its
`extract_void_samples()` documentation (lines 226-230) explicitly identifies
RA partitioning as a "PLACEHOLDER for actual void membership." The code then
uses RA bands `120–180`, `180–240`, and so on (lines 245-251), a random 10%
sample, and a 2,000-row limit; it does not join a galaxy to a DESIVAST void or
test a comoving distance against a void radius. The field comparator is likewise
an RA 0–60 sample. Because there are no populated assignments, no geometric
sample can be made; the code itself supplies decisive proxy evidence.

Accordingly, the Phase 02 README claim that algorithm comparison established
consistent environmental quenching signals must be downgraded: it is an
RA-partition demonstration, not a real void-versus-wall result.

## 3. Phase 05 VAC status

The inventory searched every non-template database's relation catalog and
targeted filenames under `/mnt/fs02/ml-datasets` plus this repository's
`staging/`, `data/`, and `output/` locations. No target VAC table or staged
product was found.

| VAC | Documentation target/claim | Live state |
|---|---|---|
| PROVABGS | `raw_catalogs.provabgs`; README links EDR | Absent; no DR1 or EDR product located |
| Gfinder | `raw_catalogs.gfinder_groups` | Absent |
| AGN/QSO Summary | `raw_catalogs.agnqso_summary` | Absent |
| CIV absorber | `raw_catalogs.civ_absorbers` | Absent |
| MgII absorber | `raw_catalogs.mgii_absorbers` | Absent |
| BHMass / QMassIron | `raw_catalogs.bhmass`; README calls it QMassIron | Absent |
| Stellar Mass/EmLine | README inventory | Absent |

This agrees with the Roadmap's *Pending* state for the six named Phase 05
targets, but not with documentation that treats all nine VACs as loaded. The
stellar-mass-emline catalog is an additional documented VAC, not a loaded one.

## 4. radio-fs02 spectral tile audit

The canonical root is reachable at:

`/mnt/fs02/ml-datasets/repository-datasets/desi-qad`

`/etc/fstab` identifies `/mnt/fs02/ml-datasets` as the CIFS mount for
`//10.25.20.15/ml-datasets`. The live root contains 12,207 `tile_*`
directories. Each has one success outcome: 10,793 contain a Parquet file and
1,414 contain `_SUCCESS_NO_QSO`. Thus all 12,207 expected tile outcomes are
accounted for; no identity-level expected-tile manifest is retained here, but
the count-based missing set is zero.

| Measure | Measured value |
|---|---:|
| Expected tile outcomes | 12,207 |
| Tile directories / completed outcomes | 12,207 |
| Parquet-bearing tiles | 10,793 |
| Legitimate no-QSO outcomes | 1,414 |
| Unaccounted outcomes by count | 0 |
| Recorded failed tiles | 0 |
| Parquet bytes | 115,994,008,603 |
| Parquet size | 108.028 GiB / 115.994 GB |

The production record
`03-spectral-tile-pipeline/03-production_20250901_043529.log.txt` ends in
"Run finished" and contains no `ERROR`, `FAILED`, `FAILURE`, `EXCEPTION`, or
`Traceback` marker. Together with the one-per-tile success markers, that is the
basis for the zero recorded failures. The root itself has no separate failure or
resume log.

The 108-GiB measurement supports the Roadmap's 108 figure if its unit is binary
GiB. It conflicts with the repeated 32-GB claim. The original 2.3-TB FITS input
is not present in the audited root, so neither that amount nor a 98.6%
compression percentage can be independently confirmed in this run.

## 5. Documentation-claim delta

| Current claim | Live measurement | Result |
|---|---|---|
| README/Phase 02: 6,445,927 FastSpecFit rows | 6,445,927 exact | Agree |
| AGENTS/ROADMAP: 6.4M galaxies | 6,445,927 exact | Agree as rounded |
| AGENTS/Phase 02: post-QA 6,342,556; 98.4% | No materialized post-QA table; source is 6,445,927 | Cannot validate from live tables |
| README/AGENTS/ROADMAP: 10,752 / ~10.7K voids | 10,752 exact | Agree |
| ROADMAP: 6.4M materialized galaxy-void assignments | 0 relationship rows; no other assignment table | Disagree |
| Phase 02: consistent quenching across four algorithms | RA-band placeholder; no live assignments | Unsupported |
| README/AGENTS: 10.8K or 10,800+ tiles | 12,207 completed outcomes | Disagree/outdated |
| ROADMAP: 12,207 tiles | 12,207 completed outcomes | Agree |
| README/AGENTS: ~32 GB Parquet | 115.994 GB / 108.028 GiB | Disagree |
| ROADMAP: 108 GB Parquet | 108.028 GiB (115.994 decimal GB) | Agree only if GB was intended as GiB |
| README/AGENTS: 2.3 TB FITS, 98.6% compression | FITS no longer at audited root | Unresolvable here |
| ROADMAP: single `raw_catalogs` schema design | Two source `raw_catalogs` schemas in separate DESI databases; empty publication database | Disagree |
| README/AGENTS: pgsql01 10.25.20.8 and fs02 10.25.20.15 | env-selected pgsql01 and fstab-selected fs02 match | Agree |
| Phase 05 targets pending | All seven documented targets absent/un-staged | Agree, with Stellar Mass/EmLine also absent |

## Required documentation refresh edits

- Replace the single-database `raw_catalogs` narrative with the measured
  three-database legacy topology; state that the publication schema is empty.
- Remove the assertion that 6.4M galaxy-void assignments are materialized and
  downgrade the Phase 02 quenching statement to a placeholder RA-band
  demonstration.
- Mark every Phase 05 VAC, including Stellar Mass/EmLine, as absent rather than
  ingested; do not identify PROVABGS as DR1 or EDR until a product is located.
- Use 12,207 completed tile outcomes, distinguishing 10,793 Parquet-bearing
  tiles from 1,414 valid no-QSO outcomes.
- Replace 32 GB with 115.994 GB (108.028 GiB), and qualify the 2.3-TB/
  98.6%-compression claim as unverified by the current share audit.
