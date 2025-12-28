<!--
---
title: "Work Logs"
description: "Milestone-based development history for DESI Cosmic Void Galaxies ARD"
author: "VintageDon"
date: "2025-12-28"
version: "2.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: documentation
---
-->

# Work Logs

Development history organized by milestone. Each phase is self-contained: scripts, outputs, figures, and documentation live together.

---

## 1. Contents

```
work-logs/
├── 01-catalog-acquisition/       # DESIVAST + FastSpecFit → PostgreSQL
├── 02-catalog-validation/        # Integrity, plausibility, systematics
├── 03-spectral-tile-pipeline/    # FITS → Parquet conversion (edge01)
├── 04-ard-foundations/           # Schema design, deep research, planning
└── README.md
```

---

## 2. Milestones

| Phase | Name | Status | Date |
|-------|------|--------|------|
| [01](01-catalog-acquisition/README.md) | Catalog Acquisition | ✅ Complete | Jul 2025 |
| [02](02-catalog-validation/README.md) | Catalog Validation | ✅ Complete | Aug 2025 |
| [03](03-spectral-tile-pipeline/README.md) | Spectral Tile Pipeline | ✅ Complete | Sep 2025 |
| [04](04-ard-foundations/README.md) | ARD Foundations | ✅ Complete | Dec 2025 |

---

## 3. Naming Convention

Scripts and outputs share prefixes for grouping:

```
NN-script-name.py       # Script
NN-output.log           # Its log output
NN-figure.png           # Its figure output
```

Large files (Parquet, SQL dumps) go to `/data` with LFS.

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Project Root](../README.md) | Parent |
| [ARD Schema](../docs/ARD-SCHEMA-v2.md) | Column specifications |
| [Data Dictionary](../docs/ARD-DATA-DICTIONARY-v2.md) | Implementation reference |
| [Roadmap](../ROADMAP.md) | Phase planning |
