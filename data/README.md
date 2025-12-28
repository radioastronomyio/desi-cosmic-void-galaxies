<!--
---
title: "Data"
description: "Large data files (LFS tracked)"
author: "VintageDon"
date: "2025-12-27"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: data-engineering
---
-->

# Data

Large files that don't belong in milestone directories. Tracked with Git LFS.

---

## 1. Overview

This directory holds files too large for inline storage in `work-logs/` milestones:

- Parquet exports (catalog snapshots)
- SQL dumps
- Large validation outputs

Small outputs (logs, figures, CSVs <10MB) stay with their scripts in milestone directories.

---

## 2. Contents

```
data/
├── .gitkeep
└── README.md
```

*Files will be added as ARD materialization progresses.*

---

## 3. Conventions

| File Type | Naming Pattern | Example |
|-----------|----------------|---------|
| Catalog export | `{catalog}_{version}.parquet` | `fastspecfit_v1.parquet` |
| SQL dump | `{database}_{date}.sql.gz` | `desi_void_20251227.sql.gz` |
| Validation | `{phase}_{artifact}.parquet` | `02_validation_sample.parquet` |

---

## 4. Git LFS

Files matching these patterns are LFS-tracked (see `.gitattributes`):

```
*.parquet
*.sql.gz
*.fits
*.h5
```

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [ARD Output](../desi-cosmic-voids-ard/README.md) | Final products go there |
| [Work Logs](../work-logs/README.md) | Small outputs stay with scripts |
