<!--
---
title: "Documentation"
description: "Project documentation and standards"
author: "VintageDon"
date: "2025-12-28"
version: "3.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: documentation
---
-->

# Documentation

Project documentation for DESI Cosmic Void Galaxies ARD. Schema specifications, data dictionary, templates, and reference material.

---

## 1. Contents

```
docs/
├── ARD-SCHEMA-v2.md              # ARD column specifications (authoritative)
├── ARD-DATA-DICTIONARY-v2.md     # Implementation reference (authoritative)
├── what-is-an-ard.md             # One-pager: ARD concept explained
├── DATA_DICTIONARY.md            # Legacy schema (superseded by v2.0)
├── data-science-infrastructure.md # Cluster resources reference
├── documentation-standards/      # Templates for project docs
│   └── README.md
└── README.md
```

---

## 2. Key Documents

### ARD Specifications (v2.0)

| Document | Purpose |
|----------|---------|
| [ARD-SCHEMA-v2.md](ARD-SCHEMA-v2.md) | 70+ column schema with Tier 1/2 assignments, 9 VAC inventory |
| [ARD-DATA-DICTIONARY-v2.md](ARD-DATA-DICTIONARY-v2.md) | Implementation specs: types, units, ranges, formulas, join order |

### Reference

| Document | Purpose |
|----------|---------|
| [what-is-an-ard.md](what-is-an-ard.md) | One-pager explaining the Analysis-Ready Dataset concept |
| [data-science-infrastructure.md](data-science-infrastructure.md) | Compute cluster specs and configuration |

### Legacy (Superseded)

| Document | Status |
|----------|--------|
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | v1.0 schema — superseded by ARD-SCHEMA-v2.md |

---

## 3. Subdirectories

| Directory | Description |
|-----------|-------------|
| [documentation-standards/](documentation-standards/README.md) | README, KB, and script header templates |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Project Root](../README.md) | Parent |
| [Roadmap](../ROADMAP.md) | Project phases and planning |
| [Work Logs](../work-logs/README.md) | Development history |
