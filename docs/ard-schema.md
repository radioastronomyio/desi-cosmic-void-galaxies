# DESI DR1 Analysis-Ready Dataset Schema v2.0

Status: Validated  
Last Updated: 2025-12-28  
Validation Sources: Gemini Deep Research, GPT-5.2 Deep Research, GPT Synthesis Document

---

## Overview

This schema defines the column structure for the DESI DR1 Analysis-Ready Dataset (ARD), a materialized dataset designed to support three downstream science cases:

1. Cosmic Void Galaxies & Environmental Quenching (Primary)
2. Quasar Anomaly Detection
3. Quasar Outflow Energetics

The schema follows a tiered materialization strategy:

- Tier 1: Direct joins from existing Value-Added Catalogs (VACs)
- Tier 2: Derived computations requiring cluster/GPU resources

---

## Value-Added Catalog Inventory

### Tier 1 Sources (Direct Join)

| VAC Name | Key | Primary Columns | Science Case |
|----------|-----|-----------------|--------------|
| DESI Core Catalog | TARGETID | RA, DEC, Z, ZWARN, SPECTYPE | All |
| FastSpecFit | TARGETID | Emission lines, VDISP, D4000 | 1, 2, 3 |
| PROVABGS | TARGETID | LOG_MSTAR, LOG_SFR, AGE_MW, Z_MW | 1 |
| DESIVAST | TARGETID | Void assignments, DIST_VOID | 1 |
| Gfinder Group Catalog | TARGETID | GROUP_ID, HALO_MASS, RANK | 1 |
| AGN/QSO Summary | TARGETID | Z_PCA, BAL_PROB, AI, BI | 2, 3 |
| CIV Absorber Catalog | TARGETID | NCIV, EW_CIV, V_ABS | 3 |
| MgII Absorber Catalog | TARGETID | N_MGII, EW_MGII | 3 |
| BHMass VAC | TARGETID | LOG_MBH, L_BOL | 3 |

### Explicitly Excluded VACs (Anti-Portfolio)

| VAC | Reason for Exclusion |
|-----|---------------------|
| Lyman-α Forest Catalogs | Cosmology focus, not object-level; terabyte scale |
| EMFit Catalog | Redundant with FastSpecFit |
| Stellar Catalog | Milky Way focus, not extragalactic |

---

## Schema Tables

### Table 1: Foundation Layer (Identifiers, Coordinates, Quality)

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| TARGETID | int64 | DESI Core | 1 | All | Primary key, unique object identifier |
| RA | float64 | DESI Core | 1 | All | Right Ascension J2000 (degrees) |
| DEC | float64 | DESI Core | 1 | All | Declination J2000 (degrees) |
| Z_HELIO | float32 | DESI Core | 1 | All | Heliocentric spectroscopic redshift |
| Z_SYS | float32 | AGN VAC | 1 | 3 | PCA-based systemic redshift (QSO only) |
| ZWARN | int32 | DESI Core | 1 | All | Redshift warning bitmask (0 = reliable) |
| DELTACHI2 | float32 | DESI Core | 1 | All | Δχ² between best and second-best redshift |
| SPECTYPE | string | DESI Core | 1 | All | Spectral classification (GALAXY, QSO, STAR) |
| SUBTYPE | string | DESI Core | 1 | All | Survey program (BGS, LRG, ELG, QSO) |
| BGS_TARGET | int64 | DESI Core | 1 | 1 | BGS targeting bitmask |
| TSNR2_BGS | float32 | DESI Core | 1 | All | Template S/N squared (quality metric) |

### Table 2: Photometry Layer

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| FLUX_G | float32 | Legacy DR9 | 1 | All | Dereddened g-band flux (nanomaggies) |
| FLUX_R | float32 | Legacy DR9 | 1 | All | Dereddened r-band flux (nanomaggies) |
| FLUX_Z | float32 | Legacy DR9 | 1 | All | Dereddened z-band flux (nanomaggies) |
| FLUX_W1 | float32 | Legacy DR9 | 1 | All | Dereddened W1-band flux (nanomaggies) |
| REST_U_MINUS_R | float32 | Compute | 2 | 1 | K-corrected rest-frame U-R color |

### Table 3: Physics Layer — Galaxy Evolution (Quenching)

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| LOG_MSTAR | float32 | PROVABGS | 1 | 1 | Log₁₀ stellar mass (M☉), Bayesian median |
| LOG_MSTAR_ERR | float32 | PROVABGS | 1 | 1 | Stellar mass uncertainty (dex) |
| LOG_SFR_TOTAL | float32 | PROVABGS | 1 | 1 | Log₁₀ SFR averaged over 1 Gyr (M☉/yr) |
| LOG_SFR_100MYR | float32 | PROVABGS | 1 | 1 | Log₁₀ SFR averaged over 100 Myr (burst indicator) |
| LOG_SFR_FIBER | float32 | FastSpecFit | 1 | 1 | Log₁₀ fiber SFR from Hα/[OII] (M☉/yr) |
| LOG_sSFR | float32 | Compute | 2 | 1 | Log₁₀ specific SFR (yr⁻¹) |
| BURST_RATIO | float32 | Compute | 2 | 1 | 10^(LOG_SFR_FIBER - LOG_SFR_TOTAL) |
| LOG_Z_MW | float32 | PROVABGS | 1 | 1 | Mass-weighted stellar metallicity (log Z/Z☉) |
| AGE_MW | float32 | PROVABGS | 1 | 1 | Mass-weighted stellar age (Gyr) |
| VDISP | float32 | FastSpecFit | 1 | 1 | Stellar velocity dispersion (km/s) |
| VDISP_ERR | float32 | FastSpecFit | 1 | 1 | Velocity dispersion uncertainty (km/s) |

### Table 4: Spectral Indices Layer

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| D4000_N | float32 | FastSpecFit | 1 | 1 | Narrow 4000Å break (Balogh definition) |
| HDELTA_A | float32 | Compute | 2 | 1 | Lick HδA index (Å), post-starburst indicator |
| MGB_INDEX | float32 | Compute | 2 | 1 | Lick Mgb index (Å), α-enhancement |
| FE5270 | float32 | Compute | 2 | 1 | Lick Fe5270 index (Å) |
| FE5335 | float32 | Compute | 2 | 1 | Lick Fe5335 index (Å) |

Note: Lick indices require convolution to 8.4Å FWHM resolution and emission masking. D4000_N from FastSpecFit meets narrow-band definition — verify during ETL (pending).

### Table 5: Emission Lines Layer

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| EW_OII_3727 | float32 | FastSpecFit | 1 | 1 | [OII] λ3727 equivalent width (Å) |
| EW_HBETA | float32 | FastSpecFit | 1 | 1 | Hβ equivalent width (Å) |
| EW_OIII_5007 | float32 | FastSpecFit | 1 | 1 | [OIII] λ5007 equivalent width (Å) |
| EW_HALPHA | float32 | FastSpecFit | 1 | 1, 3 | Hα equivalent width (Å) |
| EW_NII_6584 | float32 | FastSpecFit | 1 | 1 | [NII] λ6584 equivalent width (Å) |
| FLUX_OII_3727 | float32 | FastSpecFit | 1 | 1 | [OII] flux (10⁻¹⁷ erg/s/cm²) |
| FLUX_HBETA | float32 | FastSpecFit | 1 | 1 | Hβ flux (10⁻¹⁷ erg/s/cm²) |
| FLUX_OIII_5007 | float32 | FastSpecFit | 1 | 1 | [OIII] flux (10⁻¹⁷ erg/s/cm²) |
| FLUX_HALPHA | float32 | FastSpecFit | 1 | 1 | Hα flux (10⁻¹⁷ erg/s/cm²) |
| FLUX_NII_6584 | float32 | FastSpecFit | 1 | 1 | [NII] flux (10⁻¹⁷ erg/s/cm²) |

### Table 6: Classification Layer

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| BPT_CLASS | string | Compute | 2 | 1, 3 | SF / AGN / Composite / Unknown |
| EVOL_STAGE | string | Compute | 2 | 1 | Star-Forming / Green Valley / Quiescent |

### Table 7: Environment Layer

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| VOID_ID | int32 | DESIVAST | 1 | 1 | ID of nearest void (null if wall) |
| VOID_ALGORITHM | string | DESIVAST | 1 | 1 | Algorithm (VoidFinder, ZOBOV, VIDE, REVOLVER) |
| DIST_VOID | float32 | DESIVAST | 1 | 1 | Distance to void center (Mpc) |
| R_VOID_NORM | float32 | DESIVAST | 1 | 1 | Distance / void radius (normalized) |
| ENVIRONMENT | string | DESIVAST | 1 | 1 | void / wall classification |
| DIST_5NN | float32 | Compute | 2 | 1 | Distance to 5th nearest neighbor (Mpc) |
| SIGMA_5 | float32 | Compute | 2 | 1 | Surface density Σ₅ (galaxies/Mpc²) |
| DIST_FILAMENT | float32 | Compute | 2 | 1 | Distance to nearest filament spine (Mpc) |
| GROUP_ID | int32 | Gfinder | 1 | 1 | Group/cluster ID (null if isolated) |
| HALO_MASS | float32 | Gfinder | 1 | 1 | Estimated halo mass (log M☉) |
| GROUP_RANK | int32 | Gfinder | 1 | 1 | Central (1) vs satellite (>1) |

### Table 8: Quasar Physics Layer (Outflow Energetics)

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| LOG_MBH | float32 | BHMass VAC | 1 | 3 | Virial black hole mass (log M☉) |
| L_BOL | float32 | BHMass VAC | 1 | 3 | Bolometric luminosity (erg/s) |
| BAL_PROB | float32 | AGN VAC | 1 | 2, 3 | BAL probability |
| AI_INDEX | float32 | AGN VAC | 1 | 3 | Absorption Index |
| BI_INDEX | float32 | AGN VAC | 1 | 3 | Balnicity Index (strict BAL flag) |
| CIV_NC | float32 | CIV VAC | 1 | 3 | CIV column density (log N) |
| CIV_EW | float32 | CIV VAC | 1 | 3 | CIV equivalent width (Å) |
| CIV_VABS | float32 | CIV VAC | 1 | 3 | CIV absorption velocity (km/s) |
| MGII_NC | float32 | MgII VAC | 1 | 3 | MgII column density (log N) |
| MGII_EW | float32 | MgII VAC | 1 | 3 | MgII equivalent width (Å) |
| V_OUT_CIV | float32 | Compute | 2 | 3 | Outflow velocity: c(Z_sys - Z_abs)/(1+Z_sys) |

### Table 9: AI/ML Layer (Anomaly Detection)

| Column | Type | Source | Tier | Science Case | Description |
|--------|------|--------|------|--------------|-------------|
| LATENT_VEC | float16[16] | Compute | 2 | 2 | Spender 16-D spectral embedding |
| RECON_MSE | float32 | Compute | 2 | 2 | Reconstruction error (anomaly metric) |
| ANOMALY_SCORE | float32 | Compute | 2 | 2 | Isolation Forest score on latent space |

---

## Quality Filters (Applied at Tier 1)

| Filter | Condition | Rationale |
|--------|-----------|-----------|
| Redshift quality | ZWARN == 0 | Reliable redshift |
| Redshift confidence | DELTACHI2 > 40 | BGS standard (>100 for line work) |
| S/N threshold | TSNR2_BGS > 10 | Quality spectra |
| Velocity dispersion | VDISP > 70 km/s | Instrumental resolution floor |
| Object type | SPECTYPE in ('GALAXY', 'QSO') | Exclude stars |

---

## Tier 2 Computation Specifications

### Lick Indices (HDELTA_A, MGB_INDEX, FE5270, FE5335)

| Parameter | Value |
|-----------|-------|
| Tool | pPXF or pyphot |
| Resolution | Convolve to 8.4Å FWHM (Lick/IDS) |
| Preprocessing | Subtract FastSpecFit emission model |
| Parallelization | 192 cores across 4 nodes |
| Estimate | ~10 ms/spectrum → <1 hour for 6.4M |

### k-NN Density (DIST_5NN, SIGMA_5)

| Parameter | Value |
|-----------|-------|
| Tool | scipy.spatial.cKDTree |
| k value | 5 (standard for environment studies) |
| Tracer sample | Volume-limited: M_r < -20.0, z < 0.25 |
| Edge correction | Randoms catalog intersection |
| Formula | Σ₅ = 5 / (π × d₅²) |

### Filament Distance (DIST_FILAMENT)

| Parameter | Value |
|-----------|-------|
| Tool | DisPerSE |
| Persistence threshold | 3σ |
| Tracer sample | Volume-limited: M_r < -20.0, z < 0.25 |
| Tiling | 500 Mpc/h cubes, 50 Mpc buffer |
| Parallelization | 4 nodes, stitch skeletons |

### Spectral Embeddings (LATENT_VEC, RECON_MSE)

| Parameter | Value |
|-----------|-------|
| Architecture | Spender autoencoder |
| Latent dimensions | 16 |
| Precision | float16 (inference) |
| Batch size | 2048 |
| Hardware | A4000 16GB |
| Estimate | ~10k spectra/sec → <1 hour for 18M |

### Derived Classifications

| Column | Formula |
|--------|---------|
| LOG_sSFR | LOG_SFR_TOTAL - LOG_MSTAR |
| BURST_RATIO | 10^(LOG_SFR_FIBER - LOG_SFR_TOTAL) |
| BPT_CLASS | Kauffmann+03 / Kewley+01 demarcation on [OIII]/Hβ vs [NII]/Hα |
| EVOL_STAGE | log sSFR > -10 → SF; < -11 → Quiescent; else Green Valley |
| V_OUT_CIV | c × (Z_SYS - Z_ABS) / (1 + Z_SYS) |

---

## Storage Specifications

| Format | Use Case |
|--------|----------|
| PostgreSQL | Materialization engine, metadata, small lookups |
| Parquet | Distribution format, columnar queries |
| HDF5 | Spectral arrays (if retained) |
| FAISS | Latent vector similarity search |

### Estimated Sizes

| Component | Rows | Columns | Estimate |
|-----------|------|---------|----------|
| Galaxy ARD | 6.4M | ~60 | ~15 GB |
| QSO ARD | 1.6M | ~40 | ~3 GB |
| Combined | 18.7M | ~70 | ~40 GB |

---

## Pending Items

1. D4000_N Source: Verify FastSpecFit D4000 meets narrow-band definition vs recompute
2. UMAP Coordinates: Deferred to post-Tier 1 completion
3. Fe index inclusion: Confirmed (FE5270, FE5335 for [MgFe]' proxy)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-28 | Major expansion: Quasar VACs (CIV, MgII, BHMass, AGN), Group catalog, refined Tier 2 specs |
| 1.0 | 2025-10-04 | Initial schema (galaxy-focused) |
