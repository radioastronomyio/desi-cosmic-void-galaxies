<!--
---
title: "What is an Analysis-Ready Dataset?"
description: "One-pager explaining the ARD concept, architecture, and value proposition"
author: "VintageDon"
date: "2025-12-27"
version: "1.0"
status: "Active"
tags:
  - type: reference
  - domain: ard
  - audience: all
related_documents:
  - "[ARD Specification](https://github.com/vintagedon/analysis-ready-datasets)"
  - "[DESI ARD Implementation](../README.md)"
---
-->

# 📋 What is an Analysis-Ready Dataset?

An **Analysis-Ready Dataset (ARD)** is a curated, enriched data product designed to eliminate repetitive preprocessing and enable immediate scientific analysis. Rather than treating data preparation as a prerequisite to research, the ARD treats it as a first-class deliverable — a reusable foundation that serves multiple downstream applications.

---

## 1. Origin

The ARD concept originates from **Earth observation and satellite remote sensing**, where raw satellite imagery requires extensive preprocessing before analysis: atmospheric correction, geometric registration, cloud masking, and radiometric calibration. Space agencies like NASA and ESA recognized that researchers worldwide were duplicating this preprocessing work, so they began publishing Analysis-Ready Data products — preprocessed imagery that scientists could use immediately.

This project adapts the ARD concept to **astronomy**, specifically to spectroscopic survey data. The same principle applies: raw survey data requires substantial preprocessing (catalog cross-matching, quality filtering, derived quantity calculation, spectral extraction) before science can begin. By packaging this preprocessing into a formal ARD, we create a reusable foundation for multiple research applications.

---

## 2. The Problem ARDs Solve

Traditional research data workflows have a hidden cost structure:

| Traditional Approach | ARD Approach |
|---------------------|--------------|
| Each paper reimplements preprocessing | Preprocessing done once, reused many times |
| Data preparation is undocumented side effect | Data preparation is documented deliverable |
| Quality varies between implementations | Consistent quality across all consumers |
| Derived quantities computed ad-hoc | Derived quantities computed systematically |
| Knowledge lost when project ends | Knowledge preserved in dataset structure |

The ARD inverts the relationship: **the dataset is the primary product**, and research papers are consumers of that product. This is particularly valuable when multiple research questions draw from the same underlying data.

---

## 3. Three-Layer Architecture

ARDs employ a layered enrichment model, where each layer builds on the previous:

```
┌─────────────────────────────────────────────────────────┐
│                    AI / Embeddings Layer                │
│         Neural embeddings, similarity metrics,          │
│              learned representations                    │
├─────────────────────────────────────────────────────────┤
│                      Physics Layer                      │
│        Derived physical quantities: kinematics,         │
│           SED fits, spectral indices, ages              │
├─────────────────────────────────────────────────────────┤
│                    Foundation Layer                     │
│       Unified catalogs, cross-matched sources,          │
│         quality flags, environmental context            │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
              ┌────────────┴────────────┐
              │      Source Data        │
              │   Raw catalogs, spectra │
              │   Value-added catalogs  │
              └─────────────────────────┘
```

### Foundation Layer
- Unified schema across source catalogs
- Cross-match linkage between catalogs and spectra
- Quality flags and sample cuts applied
- Environmental classifications (e.g., void vs. wall)
- This layer alone provides significant value

### Physics Layer
- Quantities derivable from spectra: Lick indices, velocity dispersions
- Model-dependent quantities: SED fitting posteriors, stellar population ages
- Requires compute time but uses established tools
- Adds interpretive power beyond raw measurements

### AI/Embeddings Layer
- Neural representations of spectra or catalog properties
- Enables similarity search, anomaly detection, clustering
- Supports downstream ML applications
- Most experimental, highest potential for novel discovery

---

## 4. Factory-Consumer Model

The ARD operates as a **factory** that produces enriched data products consumed by multiple downstream applications:

```
                    ┌─────────────────────┐
                    │     ARD Factory     │
                    │  (This Repository)  │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Consumer 1  │     │ Consumer 2  │     │ Consumer 3  │
    │ Quenching   │     │ QSO Anomaly │     │ Outflows    │
    │   Paper     │     │  Detection  │     │   Paper     │
    └─────────────┘     └─────────────┘     └─────────────┘
```

Each consumer inherits:
- Consistent data quality and provenance
- Documented preprocessing decisions
- Derived quantities they don't need to recompute
- A citation trail back to the ARD

This model is especially powerful when:
- Multiple research questions address the same underlying sample
- Derived quantities are expensive to compute
- Reproducibility and provenance matter
- The dataset itself has value beyond any single paper

---

## 5. Key Characteristics

What distinguishes an ARD from a typical research dataset:

| Characteristic | Description |
|----------------|-------------|
| **Documented provenance** | Every transformation traceable to source data |
| **Layered enrichment** | Progressive value addition, each layer independent |
| **Consumer-agnostic** | Not optimized for one paper, serves many |
| **Distribution-ready** | Packaged in portable formats (Parquet, HDF5) |
| **Version-controlled** | Schema versioning, change documentation |
| **Quality-assured** | Systematic validation at each enrichment stage |

---

## 6. Implementation Notes

### Storage Strategy
- **PostgreSQL** as the materialization engine (flexible queries, joins, spatial operations)
- **Parquet** as the distribution format (portable, compressed, schema-preserving)
- **HDF5** for array data like spectra (efficient for large numerical arrays)

### Materialization Pattern
```
Source Data → PostgreSQL (enrichment) → Parquet (distribution)
```

Enrichment happens in the database where joins and computations are efficient. Distribution happens via Parquet files that consumers can use without database access.

### Work Tiers
Not all enrichment is equal. Categorizing by difficulty helps planning:

| Tier | Characteristics | Examples |
|------|-----------------|----------|
| Easy | SQL-based, no external dependencies | Derived ratios, flags, simple joins |
| Medium | Established tools, compute time | Spectral fitting, kinematics |
| Hard | Significant engineering | SED fitting, embedding generation |

---

## 7. Value Proposition

For **researchers**: Skip months of data wrangling. Start with a validated, enriched dataset and focus on science.

For **the field**: Create a reusable resource that enables research beyond your own papers. Establish a citable data product with long-term value.

For **reproducibility**: Document every decision in the enrichment pipeline. Future researchers can understand exactly how the dataset was built.

For **collaboration**: Downstream projects inherit your data quality without reimplementing your preprocessing. Changes propagate through the factory-consumer chain.

---

## 8. References

- **Earth Observation ARD**: [USGS Landsat ARD](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products), [ESA Sentinel ARD](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/processing-levels)
- **This Implementation**: [DESI Cosmic Void Galaxies](../README.md)
- **Domain-Agnostic Spec**: [analysis-ready-datasets](https://github.com/vintagedon/analysis-ready-datasets) (private)

---

## 9. Document Info

| | |
|---|---|
| Author | VintageDon |
| Created | 2025-12-27 |
| Updated | 2025-12-27 |
| Version | 1.0 |
