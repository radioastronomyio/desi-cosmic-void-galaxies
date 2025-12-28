<!--
---
title: "Tagging Strategy"
description: "Controlled vocabulary for document classification and RAG retrieval in desi-cosmic-void-galaxies"
author: "VintageDon - https://github.com/vintagedon"
ai_contributor: "Claude Opus 4.5 (Anthropic)"
date: "2025-12-28"
version: "1.0"
phase: [phase-01, phase-02, phase-03, phase-04, ard]
tags:
  - domain: documentation
  - type: specification
related_documents:
  - "[Interior README Template](interior-readme-template.md)"
  - "[General KB Template](general-kb-template.md)"
---
-->

# Tagging Strategy

## 1. Purpose

This document defines the controlled tag vocabulary for all documentation in desi-cosmic-void-galaxies, enabling consistent classification for human navigation and RAG system retrieval.

---

## 2. Scope

Covers all tag categories, valid values, and usage guidance. Does not cover front-matter field structure—see individual templates for field requirements.

---

## 3. Tag Categories

### Phase Tags

Pipeline execution phases. Documents may belong to multiple phases.

| Tag | Description |
|-----|-------------|
| `phase-01` | Catalog acquisition (DESI DR1, FastSpecFit, DESIVAST) |
| `phase-02` | Catalog validation and quality assessment |
| `phase-03` | Spectral tile pipeline (Parquet conversion, tile indexing) |
| `phase-04` | ARD materialization (enrichment layers, packaging) |
| `ard` | Analysis-Ready Dataset specification and distribution |

**Usage**: Tag with all phases a document supports. A methodology doc explaining void assignment used in phases 02-04 would carry `phase-02`, `phase-03`, `phase-04`.

---

### Domain Tags

Primary functional area. Usually one per document.

| Tag | Description |
|-----|-------------|
| `catalog` | Galaxy/void catalog operations, schema, queries |
| `spectral` | Spectral data processing, tile management |
| `environment` | Void/wall classification, environmental assignments |
| `enrichment` | Derived quantities, physics layers, embeddings |
| `validation` | Data quality, integrity checks, QA |
| `documentation` | Methodology, specifications, standards |
| `infrastructure` | Database, storage, compute configuration |

**Usage**: Choose the primary domain. A document about validating catalog ingestion is `validation`, not `catalog`.

---

### Type Tags

Document purpose and structure.

| Tag | Description |
|-----|-------------|
| `methodology` | How we do something |
| `reference` | Lookup information (data dictionary, schema) |
| `guide` | Step-by-step procedures |
| `decision-record` | Why we chose X over Y |
| `specification` | Formal requirements |
| `source-code` | Code files and scripts |
| `configuration` | Config files, parameters |
| `data-manifest` | Data inventory and provenance |

**Usage**: One type per document. If a document explains both *how* and *why*, choose the dominant purpose.

---

### Tech Tags

Data sources and external dependencies.

| Tag | Description |
|-----|-------------|
| `desi-dr1` | DESI Data Release 1 base data |
| `fastspecfit` | FastSpecFit Value-Added Catalog (galaxy properties) |
| `desivast` | DESIVAST void catalogs (VIDE, ZOBOV, REVOLVER, VoidFinder) |
| `postgresql` | PostgreSQL materialization engine |
| `parquet` | Parquet file format operations |
| `hdf5` | HDF5 spectral array storage |

**Usage**: Tag when the document is specific to that data source or technology. A general enrichment methodology doc doesn't need `fastspecfit`; a doc about FastSpecFit column mappings does.

---

### Enrichment Layer Tags

For ARD-specific documentation.

| Tag | Description |
|-----|-------------|
| `layer-foundation` | Base catalog + void assignments |
| `layer-physics` | Derived physical quantities (Lick indices, sSFR, density) |
| `layer-ai` | Embeddings, ML features, tokenization |

**Usage**: Tag ARD materialization documents with the layer(s) they address.

---

## 4. References

| Reference | Link |
|-----------|------|
| Main README | [../../README.md](../../README.md) |
| Interior README Template | [interior-readme-template.md](interior-readme-template.md) |
| General KB Template | [general-kb-template.md](general-kb-template.md) |
| Data Dictionary | [../DATA_DICTIONARY.md](../DATA_DICTIONARY.md) |

---
