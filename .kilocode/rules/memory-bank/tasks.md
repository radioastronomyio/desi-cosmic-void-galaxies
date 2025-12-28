# DESI Cosmic Void Galaxies ARD — Tasks and Workflows

## Common Workflows

### VAC Ingestion (Phase 05)

**When to use:** Adding a new Value Added Catalog to PostgreSQL  
**Frequency:** Once per VAC, 6 VACs in Phase 05

**Steps:**
1. Download FITS file from DESI Data Portal
2. Inspect schema with `astropy.io.fits.info()`
3. Create target table in `raw_catalogs` schema matching FITS columns
4. Write ETL script following `work-logs/01-*/03-etl-*.py` pattern
5. Execute ETL with logging to `NN-output.log`
6. Validate row counts and null rates
7. Update work-log README with results

**Expected Outcome:** Table populated, row count matches source, no unexpected nulls  
**Common Issues:** TARGETID type mismatch (must be int64), column name case sensitivity

---

### ARD Materialization (Phase 05.4)

**When to use:** Creating unified ARD table from raw_catalogs  
**Frequency:** Once per ARD product (galaxy, qso)

**Steps:**
1. Create `ard.galaxy_ard` or `ard.qso_ard` table with schema from ARD-SCHEMA-v2.md
2. Write SQL join query following join order in ARD-DATA-DICTIONARY-v2.md
3. Apply quality filters (ZWARN==0, DELTACHI2>40, etc.)
4. Compute derived columns (LOG_sSFR, BURST_RATIO, BPT_CLASS, EVOL_STAGE)
5. Execute as `CREATE TABLE ... AS SELECT` or `INSERT INTO`
6. Validate row counts and completeness

**Expected Outcome:** ARD table populated with all Tier 1 columns  
**Common Issues:** JOIN failures due to missing TARGETIDs, null propagation in derived columns

---

### Parquet Export (Phase 05.5)

**When to use:** Exporting ARD table to distribution format  
**Frequency:** After each ARD materialization

**Steps:**
1. Query ARD table with desired columns
2. Load into Pandas DataFrame
3. Enforce schema types per ARD-DATA-DICTIONARY-v2.md
4. Write to Parquet with `pyarrow.parquet.write_table()`
5. Verify schema with `pq.read_schema()`
6. Copy to proj-fs02 distribution location

**Expected Outcome:** Parquet file with correct schema, readable by PyArrow and DuckDB  
**Common Issues:** Float64→Float32 precision loss, string encoding issues

---

### Validation Check (Phase 06)

**When to use:** Verifying ARD quality before downstream use  
**Frequency:** After each ARD materialization

**Steps:**
1. Run completeness audit: JOIN success rates, null patterns
2. Generate statistical distributions: mass function, z distribution, SFR-M* relation
3. Compare to published DESI results
4. Check environment sanity: void fraction ~40%, group rates
5. Document findings in validation report

**Expected Outcome:** Distributions match expectations, no systematic issues  
**Common Issues:** Malmquist bias in mass-z correlation, unexpected null rates

---

## Memory Bank Maintenance

### Updating context.md

**When:** After every significant work session  
**What to update:**
1. Move completed items from "Next Steps" to "Recent Accomplishments"
2. Update "Current Phase" if phase changed
3. Update "Next Steps" with new actionable items
4. Document any new decisions in "Active Decisions"
5. Add/resolve blockers as appropriate
6. Update "Last Updated" date

**Quality check:** Does context.md accurately reflect current state?

---

### Updating architecture.md

**When:** When architectural patterns emerge or change  
**What to update:**
1. Add new components/areas as they're created
2. Document architectural decisions with rationale
3. Update design patterns if approach evolves
4. Record new integration points
5. Update constraints if environment changes

**Quality check:** Can someone understand the structure from this file alone?

---

## Session Management

### Session Start Procedure

**Objective:** Load context and confirm understanding

1. **Load memory bank files**
   - Read brief.md (foundational context)
   - Read context.md (current state and next steps)
   - Scan architecture.md and tech.md as needed

2. **Confirm context**
   - Display: `[Memory Bank: Active | Project: desi-cosmic-void-galaxies]`
   - Briefly summarize: Current phase, immediate next steps

3. **Verify currency**
   - Check "Last Updated" in context.md
   - If >7 days old, flag for human review

---

### Session End Procedure

**Objective:** Update memory bank with session outcomes

1. **Update context.md**
   - Add accomplishments to "Recent Accomplishments"
   - Update "Next Steps" based on current state
   - Document decisions made during session
   - Add/resolve blockers
   - Update "Last Updated" date

2. **Update other files if needed**
   - architecture.md if design changed
   - tech.md if stack/setup changed
   - product.md if goals/vision evolved

3. **Commit changes**
   ```bash
   git add .kilocode/rules/memory-bank/
   git commit -m "Update memory bank: [what changed]"
   ```

---

## Script Development Patterns

### New ETL Script

**Template:** Follow `work-logs/01-catalog-acquisition/03-etl-*.py`

**Required elements:**
1. Standard header with ORCID
2. Docstring with Description/Usage/Examples
3. Section banners: Imports, Configuration, Functions, Entry Point
4. Type hints on function signatures
5. `main() -> int` return pattern with `sys.exit(main())`
6. Human-first comments for domain knowledge
7. AI NOTEs for hidden constraints

---

### New Validation Script

**Template:** Follow `work-logs/02-catalog-validation/01-validate-*.py`

**Required elements:**
1. Clear stage structure (integrity, plausibility, systematics)
2. Threshold documentation with rationale
3. Output logging to `NN-output.log`
4. Figure generation to `NN-figure.png`

---

## Quality Checklists

### ETL Script Checklist
- [ ] Standard header with ORCID
- [ ] Docstring with usage examples
- [ ] Type hints on functions
- [ ] Error handling for file/database operations
- [ ] Logging to output file
- [ ] AI NOTEs for hidden constraints
- [ ] Tested with small sample before full run

### Validation Checklist
- [ ] Row counts match expectations
- [ ] Null rates within acceptable bounds
- [ ] Statistical distributions plausible
- [ ] No unexpected outliers
- [ ] Cross-VAC consistency verified
- [ ] Results documented in work-log README

### Commit Checklist
- [ ] All modified files staged
- [ ] Commit message follows conventions
- [ ] Work-log README updated
- [ ] Memory-bank context.md updated
- [ ] No sensitive data (credentials, paths) in commit
