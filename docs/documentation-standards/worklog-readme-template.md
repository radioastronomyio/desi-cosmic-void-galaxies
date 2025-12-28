<!--
---
title: "[Phase NN]: [Phase Name]"
description: "What was accomplished in this milestone"
author: "VintageDon"
date: "YYYY-MM-DD"
version: "1.0"
status: "Complete|In Progress|Blocked"
tags:
  - type: worklog
  - domain: [void-science/data-engineering/ml-enrichment]
  - phase: [acquisition/validation/enrichment/materialization]
  - tech: [python/postgresql/fits/parquet]
related_documents:
  - "[Previous Phase](../NN-previous/README.md)"
  - "[Next Phase](../NN-next/README.md)"
---
-->

# Phase NN: [Phase Name]

## Summary

| Attribute | Value |
|-----------|-------|
| Status | ✅ Complete / 🔄 In Progress / ⛔ Blocked |
| Sessions | N |
| Artifacts | N scripts, N configs, N figures |

Objective: [What this phase set out to accomplish. 1-2 sentences.]

Outcome: [What was achieved. 1-2 sentences.]

---

## 1. Contents

```
NN-phase-name/
├── 01-script-name.py       # What it does
├── 01-output.log           # Output from script 01
├── 02-another-script.py    # What it does
├── figures/
│   └── 01-figure-name.png  # What it shows
├── logs/
└── README.md               # This file
```

---

## 2. Scripts

| Script | Purpose | Key Output |
|--------|---------|------------|
| `01-script-name.py` | What it does | What it produces |
| `02-another-script.py` | What it does | What it produces |

---

## 3. Validation

| Check | Status | Evidence |
|-------|--------|----------|
| [What was validated] | ✅ Pass | [How confirmed] |
| [What was validated] | ✅ Pass | [How confirmed] |

---

## 4. Figures

### Figure 01: [Title]

![Description](figures/01-figure-name.png)

[1-2 sentences: What this figure shows and what it confirms.]

---

## 5. Findings

### Key Results

- [Finding 1]
- [Finding 2]

### Issues Encountered

| Issue | Resolution |
|-------|------------|
| [Problem] | [How solved] |

---

## 6. Next Phase

Handoff: [What's ready for the next phase and where it lives.]

Next Steps:

1. [Immediate action]
2. [Immediate action]

---

## 7. Provenance

| | |
|---|---|
| Compute | [Node(s) used] |
| Data Location | [Where inputs/outputs live] |
| Date Range | YYYY-MM-DD to YYYY-MM-DD |

---

<!--
TEMPLATE USAGE NOTES (remove when using):

1. FRONTMATTER: Always include. Links this to phase sequence.

2. SEMANTIC NUMBERING: Preserve gaps if sections omitted.

3. NAMING CONVENTION:
   - Scripts: NN-descriptive-name.py
   - Outputs share prefix: 01-script.py → 01-output.log
   - Figures: NN-description.png

4. SECTIONS:
   - Summary: Always (the quick overview)
   - §1 Contents: Always (directory tree)
   - §2 Scripts: Always (what was built)
   - §3 Validation: Include if validation performed
   - §4 Figures: Include if figures produced
   - §5 Findings: Include if insights worth capturing
   - §6 Next Phase: Include if not final phase
   - §7 Provenance: Always (reproducibility)

5. INLINE FIGURES: Embed key figures with descriptions.
   Don't just list them—explain what they show.

6. KEEP IT LEAN: This documents work done, not work planned.
   Capture what matters for reproducibility and understanding.
-->
