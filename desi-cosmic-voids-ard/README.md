<!--
---
title: "DESI Cosmic Voids ARD"
description: "Analysis-Ready Dataset output directory"
author: "VintageDon"
date: "2025-12-27"
version: "0.1"
status: "In Progress"
tags:
  - type: directory-readme
  - domain: data-engineering
  - phase: materialization
---
-->

# DESI Cosmic Voids ARD

Output directory for the Analysis-Ready Dataset. This is where materialized ARD products will be published.

---

## 1. Overview

The DESI Cosmic Void Galaxies ARD is a three-layer enriched dataset:

| Layer | Content | Status |
|-------|---------|--------|
| **Foundation** | Unified catalog + spectral linkage | 🔄 In Progress |
| **Physics** | Derived quantities (Lick indices, kinematics, SED fits) | ⬜ Planned |
| **AI/Embeddings** | Neural embeddings, similarity metrics | ⬜ Planned |

---

## 2. Contents

```
desi-cosmic-voids-ard/
└── README.md               # This file
```

*ARD products will be added as Phase 04 progresses.*

---

## 3. Planned Structure

```
desi-cosmic-voids-ard/
├── foundation/
│   ├── catalog.parquet         # Unified galaxy catalog
│   ├── voids.parquet           # Void catalog
│   └── spectral_index.parquet  # Catalog ↔ spectral tile linkage
├── physics/
│   ├── lick_indices.parquet    # Dn4000, HδA, etc.
│   ├── kinematics.parquet      # pPXF velocity dispersion
│   └── sed_fits.parquet        # Bagpipes posteriors
├── embeddings/
│   └── spectral_embeddings.parquet
└── README.md
```

---

## 4. Source Data

| Source | Location | Rows |
|--------|----------|------|
| Galaxy catalog | PostgreSQL (proj-pg01) | 6.4M |
| Void catalog | PostgreSQL (proj-pg01) | 10.7K |
| Spectral tiles | Parquet (proj-fs02) | ~32GB |

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [Work Logs](../work-logs/README.md) | Development history |
| [Phase 04](../work-logs/04-ard-materialization/README.md) | Current work |
| [Data Dictionary](../docs/DATA_DICTIONARY.md) | Schema reference |
