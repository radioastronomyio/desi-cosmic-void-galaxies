# DESI DR1 ARD Data Dictionary v2.0

Status: Validated  
Last Updated: 2025-12-28  
Companion Document: ARD-SCHEMA-v2.md

---

## Document Purpose

This data dictionary provides implementation-level specifications for each column in the DESI DR1 Analysis-Ready Dataset. It serves as the authoritative reference for:

- ETL pipeline development
- Data validation and quality control
- Downstream analysis interpretation
- Cross-referencing with source VACs

---

## Table of Contents

1. [Foundation Layer](#1-foundation-layer)
2. [Photometry Layer](#2-photometry-layer)
3. [Galaxy Physics Layer](#3-galaxy-physics-layer)
4. [Spectral Indices Layer](#4-spectral-indices-layer)
5. [Emission Lines Layer](#5-emission-lines-layer)
6. [Classification Layer](#6-classification-layer)
7. [Environment Layer](#7-environment-layer)
8. [Quasar Physics Layer](#8-quasar-physics-layer)
9. [AI/ML Layer](#9-aiml-layer)
10. [VAC Join Specifications](#10-vac-join-specifications)
11. [Quality Filters](#11-quality-filters)
12. [Data Type Conventions](#12-data-type-conventions)

---

## 1. Foundation Layer

### TARGETID

| Property | Value |
|----------|-------|
| Type | int64 |
| Unit | — |
| Null Allowed | No |
| Source | DESI Core Catalog |
| Tier | 1 |

Description: Unique 64-bit identifier for each DESI target. Serves as the primary key for all ARD tables and the join key for all VAC integrations.

Format: Encodes survey, program, and fiber assignment information. Values are positive integers typically in the range 10^15 to 10^18.

Usage Notes:

- Always use int64, never cast to int32 (overflow risk)
- Guaranteed unique across all DESI observations
- Same target observed multiple times has same TARGETID

---

### RA

| Property | Value |
|----------|-------|
| Type | float64 |
| Unit | degrees |
| Range | [0.0, 360.0) |
| Null Allowed | No |
| Source | DESI Core Catalog |
| Tier | 1 |

Description: Right Ascension in the ICRS/J2000 coordinate system.

Precision: Typical precision ~0.1 arcsec from astrometric solution.

---

### DEC

| Property | Value |
|----------|-------|
| Type | float64 |
| Unit | degrees |
| Range | [-90.0, +90.0] |
| Null Allowed | No |
| Source | DESI Core Catalog |
| Tier | 1 |

Description: Declination in the ICRS/J2000 coordinate system.

Survey Coverage: DESI DR1 covers primarily the Northern Galactic Cap (DEC > -20°) with partial Southern coverage.

---

### Z_HELIO

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [0.0, ~5.0] |
| Null Allowed | No |
| Source | DESI Redshift Pipeline |
| Tier | 1 |

Description: Heliocentric spectroscopic redshift from the DESI redshift fitting pipeline (Redrock).

Algorithm: Template cross-correlation with χ² minimization across galaxy, QSO, and stellar templates.

Quality Indicators: Use in conjunction with ZWARN and DELTACHI2.

Typical Ranges by SPECTYPE:

- GALAXY (BGS): 0.0 < z < 0.6
- GALAXY (LRG): 0.4 < z < 1.1
- QSO: 0.5 < z < 4.5

---

### Z_SYS

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [0.0, ~5.0] |
| Null Allowed | Yes (null for GALAXY) |
| Source | AGN/QSO VAC |
| Tier | 1 |

Description: Systemic redshift for QSOs derived from Principal Component Analysis (PCA) of the spectrum, correcting for broad-line velocity shifts.

Why Needed: The standard pipeline redshift (Z_HELIO) for QSOs is often biased by broad emission lines. Outflow velocity calculations require the true systemic redshift.

Null Handling: Only populated for SPECTYPE='QSO'. Use Z_HELIO for galaxies.

---

### ZWARN

| Property | Value |
|----------|-------|
| Type | int32 |
| Unit | bitmask |
| Good Value | 0 |
| Null Allowed | No |
| Source | DESI Redshift Pipeline |
| Tier | 1 |

Description: Bitmask indicating potential issues with the redshift determination.

Key Bits:

| Bit | Name | Meaning |
|-----|------|---------|
| 0 | ZWARN_NOQSO | Not a QSO (for QSO targets) |
| 1 | ZWARN_SMALL_DELTA_CHI2 | Low confidence |
| 2 | ZWARN_NEGATIVE_MODEL | Unphysical template |
| 4 | ZWARN_BAD_SPECTRA | Poor spectral quality |

Filtering: For science samples, require `ZWARN == 0`.

---

### DELTACHI2

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [0, ∞) |
| Null Allowed | No |
| Source | DESI Redshift Pipeline |
| Tier | 1 |

Description: Difference in χ² between the best-fit redshift solution and the second-best solution. Higher values indicate more confident redshifts.

Recommended Thresholds:

| Sample | Threshold | Notes |
|--------|-----------|-------|
| BGS general | > 40 | Standard for DR1 |
| Emission line work | > 100 | Higher confidence for weak lines |
| LRG | > 25 | Absorption-dominated spectra |

---

### SPECTYPE

| Property | Value |
|----------|-------|
| Type | string |
| Valid Values | GALAXY, QSO, STAR |
| Null Allowed | No |
| Source | DESI Redshift Pipeline |
| Tier | 1 |

Description: Spectral classification from template fitting.

Usage: Primary filter for separating galaxy science from QSO science. Stars are generally excluded from extragalactic ARD.

---

### SUBTYPE

| Property | Value |
|----------|-------|
| Type | string |
| Valid Values | BGS, LRG, ELG, QSO, MWS, etc. |
| Null Allowed | Yes |
| Source | DESI Targeting |
| Tier | 1 |

Description: Survey program subtype indicating the targeting class.

Key Subtypes for ARD:

- BGS: Bright Galaxy Survey (r < 19.5, z < 0.6)
- LRG: Luminous Red Galaxies (0.4 < z < 1.1)
- ELG: Emission Line Galaxies (0.6 < z < 1.6)
- QSO: Quasars (0.5 < z < 4.5)

---

### BGS_TARGET

| Property | Value |
|----------|-------|
| Type | int64 |
| Unit | bitmask |
| Null Allowed | Yes |
| Source | DESI Targeting |
| Tier | 1 |

Description: Targeting bitmask for the Bright Galaxy Survey.

Key Bits:

| Bit | Name | Description |
|-----|------|-------------|
| 0 | BGS_FAINT | 19.5 < r < 20.175 |
| 1 | BGS_BRIGHT | r < 19.5 |
| 2 | BGS_WISE | WISE-selected |

For Quenching Science: Use `BGS_TARGET & 2 != 0` to select BGS Bright (volume-limited gold sample).

---

### TSNR2_BGS

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [0, ∞) |
| Null Allowed | No |
| Source | DESI Core Catalog |
| Tier | 1 |

Description: Template Signal-to-Noise Ratio squared, computed for the BGS galaxy template. Proxy for overall spectral quality.

Recommended Threshold: TSNR2_BGS > 10 for reliable measurements.

---

## 2. Photometry Layer

### FLUX_G, FLUX_R, FLUX_Z, FLUX_W1

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | nanomaggies |
| Range | [0, ∞) |
| Null Allowed | Yes (if not detected) |
| Source | Legacy Surveys DR9 |
| Tier | 1 |

Description: Dereddened photometric fluxes from the DESI Legacy Imaging Surveys.

Bands:

- g: DECam g-band (~4770 Å)
- r: DECam r-band (~6231 Å)
- z: DECam z-band (~9134 Å)
- W1: WISE 3.4 μm

Conversion to Magnitude: `mag = 22.5 - 2.5 * log10(flux)`

Dereddening: Applied using SFD dust map with standard extinction coefficients.

---

### REST_U_MINUS_R

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | magnitude |
| Range | [0.5, 3.0] typical |
| Null Allowed | Yes |
| Source | Computed (K-correction) |
| Tier | 2 |

Description: Rest-frame U-R color computed via K-corrections from observed photometry.

Method: Apply kcorrect or similar to observed g, r, z fluxes using spectroscopic redshift.

Science Use: Classic separator of red sequence vs blue cloud. Green valley typically 1.8 < U-R < 2.2.

---

## 3. Galaxy Physics Layer

### LOG_MSTAR

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(M☉) |
| Range | [7.0, 12.5] |
| Null Allowed | Yes (if PROVABGS fitting failed) |
| Source | PROVABGS VAC |
| Tier | 1 |

Description: Logarithm of total stellar mass in solar masses, derived from Bayesian SED fitting with non-parametric star formation history.

Advantages over FastSpecFit: PROVABGS recovers 0.1-0.2 dex more mass in quiescent systems by properly accounting for older stellar populations.

Posterior: Full posterior samples available in PROVABGS; this column is the median.

Typical Uncertainties: 0.05-0.15 dex depending on S/N and redshift.

---

### LOG_MSTAR_ERR

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dex |
| Range | [0.01, 0.5] |
| Null Allowed | Yes |
| Source | PROVABGS VAC |
| Tier | 1 |

Description: Uncertainty on stellar mass from the 16th-84th percentile range of the posterior.

---

### LOG_SFR_TOTAL

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(M☉/yr) |
| Range | [-3.0, 3.0] |
| Null Allowed | Yes |
| Source | PROVABGS VAC |
| Tier | 1 |

Description: Logarithm of total star formation rate averaged over the past 1 Gyr ("secular" SFR).

Aperture: This is a total galaxy estimate, not fiber-only. PROVABGS uses spectrophotometric fitting with aperture correction.

Comparison: Use this for sSFR calculations to avoid aperture bias.

---

### LOG_SFR_100MYR

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(M☉/yr) |
| Range | [-3.0, 3.0] |
| Null Allowed | Yes |
| Source | PROVABGS VAC |
| Tier | 1 |

Description: Logarithm of SFR averaged over the past 100 Myr. Sensitive to recent bursts.

Science Use: Compare with LOG_SFR_TOTAL to identify burst vs secular star formation.

---

### LOG_SFR_FIBER

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(M☉/yr) |
| Range | [-4.0, 2.0] |
| Null Allowed | Yes |
| Source | FastSpecFit VAC |
| Tier | 1 |

Description: Star formation rate within the DESI fiber aperture (1.5" diameter), derived from Hα or [OII] emission line flux.

⚠️ Warning: Do NOT combine with LOG_MSTAR for sSFR. This severely underestimates total SFR for extended galaxies. Use LOG_SFR_TOTAL instead.

Primary Use: Compute BURST_RATIO to identify inside-out quenching.

---

### LOG_sSFR

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(yr⁻¹) |
| Range | [-14, -8] |
| Null Allowed | Yes |
| Source | Computed |
| Tier | 2 |

Description: Specific star formation rate = SFR / M*.

Formula: `LOG_sSFR = LOG_SFR_TOTAL - LOG_MSTAR`

Classification Thresholds:

| Range | Classification |
|-------|----------------|
| > -10 | Star-Forming |
| -11 to -10 | Green Valley |
| < -11 | Quiescent |

---

### BURST_RATIO

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [0, 10] typical |
| Null Allowed | Yes |
| Source | Computed |
| Tier | 2 |

Description: Ratio of central (fiber) to total SFR, indicating spatial distribution of star formation.

Formula: `BURST_RATIO = 10^(LOG_SFR_FIBER - LOG_SFR_TOTAL)`

Interpretation:

| Value | Meaning |
|-------|---------|
| ≪ 1 | Suppressed core SF (inside-out quenching) |
| ~ 1 | Centrally concentrated SF |
| > 1 | Central starburst (possible measurement issue) |

---

### LOG_Z_MW

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(Z/Z☉) |
| Range | [-2.0, 0.5] |
| Null Allowed | Yes |
| Source | PROVABGS VAC |
| Tier | 1 |

Description: Mass-weighted stellar metallicity relative to solar.

Note: This is stellar metallicity, not gas-phase. Gas-phase metallicity requires emission line diagnostics (e.g., R23, N2).

---

### AGE_MW

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | Gyr |
| Range | [0.1, 13.8] |
| Null Allowed | Yes |
| Source | PROVABGS VAC |
| Tier | 1 |

Description: Mass-weighted mean stellar age.

Upper Bound: Capped at age of universe at observed redshift.

---

### VDISP

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | km/s |
| Range | [50, 500] |
| Null Allowed | Yes |
| Source | FastSpecFit VAC |
| Tier | 1 |

Description: Line-of-sight stellar velocity dispersion measured from absorption line broadening.

Method: pPXF fit to absorption features in the optical.

Instrumental Limit: DESI resolution (R ~ 2000-5000) sets floor at ~70 km/s. Values below this are upper limits.

Aperture: Measured within 1.5" fiber. No aperture correction applied.

---

### VDISP_ERR

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | km/s |
| Range | [1, 100] |
| Null Allowed | Yes |
| Source | FastSpecFit VAC |
| Tier | 1 |

Description: Formal uncertainty on velocity dispersion.

Reliability: Requires TSNR2_BGS > 10 for meaningful measurements.

---

## 4. Spectral Indices Layer

### D4000_N

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [1.0, 2.5] |
| Null Allowed | Yes |
| Source | FastSpecFit VAC (or Compute if not narrow-band) |
| Tier | 1 (pending verification) |

Description: Narrow-band 4000Å break index (Balogh et al. 1999 definition).

Definition: Ratio of mean flux density in 4000-4100 Å to 3850-3950 Å.

Interpretation:

| D4000_N | Population |
|---------|------------|
| < 1.3 | Young, star-forming |
| 1.3-1.6 | Intermediate age |
| > 1.6 | Old, quiescent |

Pending: Verify FastSpecFit D4000 matches narrow-band definition. If not, recompute in Tier 2.

---

### HDELTA_A

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | Å (equivalent width) |
| Range | [-5, 10] |
| Null Allowed | Yes |
| Source | Computed (pPXF/pyphot) |
| Tier | 2 |

Description: Lick HδA absorption index, sensitive to A-star populations (0.1-1 Gyr).

Definition: Index passband 4083.5-4122.25 Å with continuum sidebands.

Computation Requirements:

1. Subtract emission model from FastSpecFit
2. Convolve to Lick/IDS resolution (8.4 Å FWHM)
3. Integrate following Worthey et al. 1994 definitions

Science Use: Primary post-starburst indicator. High HδA (> 5 Å) + low emission = E+A galaxy.

---

### MGB_INDEX

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | Å (equivalent width) |
| Range | [0, 6] |
| Null Allowed | Yes |
| Source | Computed (pPXF/pyphot) |
| Tier | 2 |

Description: Lick Mgb index, sensitive to α-element enhancement and older populations.

Definition: Index passband 5160.125-5192.625 Å.

Science Use: Combined with Fe indices to estimate [Mg/Fe] as proxy for formation timescale.

---

### FE5270, FE5335

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | Å (equivalent width) |
| Range | [0, 4] |
| Null Allowed | Yes |
| Source | Computed (pPXF/pyphot) |
| Tier | 2 |

Description: Lick iron indices at 5270 Å and 5335 Å.

Composite Index: `<Fe> = (FE5270 + FE5335) / 2`

Metallicity Proxy: `[MgFe]' = sqrt(MGB * <Fe>)` breaks age-metallicity degeneracy.

---

## 5. Emission Lines Layer

All emission line columns follow the same pattern:

| Property | Value |
|----------|-------|
| Type | float32 |
| Null Allowed | Yes (if line not detected) |
| Source | FastSpecFit VAC |
| Tier | 1 |

### Equivalent Widths (EW_*)

| Column | Wavelength | Notes |
|--------|------------|-------|
| EW_OII_3727 | 3727 Å | [OII] doublet (unresolved) |
| EW_HBETA | 4861 Å | Hydrogen Balmer |
| EW_OIII_5007 | 5007 Å | [OIII] (stronger of doublet) |
| EW_HALPHA | 6563 Å | Hydrogen Balmer |
| EW_NII_6584 | 6584 Å | [NII] (stronger of doublet) |

Unit: Rest-frame Ångströms. Positive = emission.

### Line Fluxes (FLUX_*)

Same lines as above.

Unit: 10⁻¹⁷ erg/s/cm² (observed frame, not corrected for reddening).

Reddening Correction: Users must apply Balmer decrement correction using Hα/Hβ if needed.

---

## 6. Classification Layer

### BPT_CLASS

| Property | Value |
|----------|-------|
| Type | string |
| Valid Values | SF, AGN, Composite, Unknown |
| Null Allowed | No (but can be "Unknown") |
| Source | Computed |
| Tier | 2 |

Description: Baldwin-Phillips-Terlevich classification based on emission line ratios.

Method: Apply Kauffmann+03 and Kewley+01 demarcation lines to [OIII]/Hβ vs [NII]/Hα diagram.

Classification Logic:

```markdown
if all four lines detected with S/N > 3:
    O3Hb = log10(FLUX_OIII_5007 / FLUX_HBETA)
    N2Ha = log10(FLUX_NII_6584 / FLUX_HALPHA)
    
    if below Kauffmann+03 line:
        BPT_CLASS = "SF"
    elif above Kewley+01 line:
        BPT_CLASS = "AGN"
    else:
        BPT_CLASS = "Composite"
else:
    BPT_CLASS = "Unknown"
```

---

### EVOL_STAGE

| Property | Value |
|----------|-------|
| Type | string |
| Valid Values | Star-Forming, Green Valley, Quiescent |
| Null Allowed | Yes (if sSFR unavailable) |
| Source | Computed |
| Tier | 2 |

Description: Evolutionary classification based on specific star formation rate.

Thresholds:

| LOG_sSFR | Classification |
|----------|----------------|
| > -10 | Star-Forming |
| -11 to -10 | Green Valley |
| < -11 | Quiescent |

---

## 7. Environment Layer

### VOID_ID

| Property | Value |
|----------|-------|
| Type | int32 |
| Range | [1, ~10,000] |
| Null Allowed | Yes (null if ENVIRONMENT = "wall") |
| Source | DESIVAST VAC |
| Tier | 1 |

Description: Identifier of the nearest void from the DESIVAST catalog.

---

### VOID_ALGORITHM

| Property | Value |
|----------|-------|
| Type | string |
| Valid Values | VoidFinder, ZOBOV, VIDE, REVOLVER |
| Null Allowed | Yes |
| Source | DESIVAST VAC |
| Tier | 1 |

Description: Algorithm used to identify the nearest void.

Note: Different algorithms have different void definitions. VoidFinder uses spherical approximations; ZOBOV uses watershed on Voronoi tessellation.

---

### DIST_VOID

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | Mpc (comoving) |
| Range | [0, 100] typical |
| Null Allowed | Yes |
| Source | DESIVAST VAC |
| Tier | 1 |

Description: 3D comoving distance from galaxy to the center of the nearest void.

---

### R_VOID_NORM

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [0, ~3] |
| Null Allowed | Yes |
| Source | DESIVAST VAC |
| Tier | 1 |

Description: Distance to void center normalized by void effective radius.

Interpretation:

| R_VOID_NORM | Location |
|-------------|----------|
| < 0.5 | Deep void interior |
| 0.5-1.0 | Void interior |
| > 1.0 | Outside void (wall) |

---

### ENVIRONMENT

| Property | Value |
|----------|-------|
| Type | string |
| Valid Values | void, wall |
| Null Allowed | No |
| Source | DESIVAST VAC |
| Tier | 1 |

Description: Binary environmental classification.

Definition: `void` if galaxy lies within the effective radius of any catalogued void; `wall` otherwise.

⚠️ Important: "Wall" does NOT mean high-density cluster. It simply means "not inside a catalogued void."

---

### DIST_5NN

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | Mpc (comoving) |
| Range | [0.1, 50] |
| Null Allowed | Yes |
| Source | Computed (cKDTree) |
| Tier | 2 |

Description: 3D comoving distance to the 5th nearest neighbor in the volume-limited tracer sample.

Tracer Sample: M_r < -20.0, z < 0.25 (volume-limited to ensure uniform density).

Computation: scipy.spatial.cKDTree on 3D Cartesian coordinates derived from (RA, DEC, z).

---

### SIGMA_5

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | galaxies/Mpc² |
| Range | [0.01, 100] |
| Null Allowed | Yes |
| Source | Computed |
| Tier | 2 |

Description: Projected surface density estimated from 5th nearest neighbor.

Formula: `SIGMA_5 = 5 / (π × DIST_5NN²)`

Edge Correction: If DIST_5NN circle intersects survey boundary, correct by dividing by the fraction of the circle within the footprint (using randoms catalog).

---

### DIST_FILAMENT

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | Mpc (comoving) |
| Range | [0, 50] |
| Null Allowed | Yes |
| Source | Computed (DisPerSE) |
| Tier | 2 |

Description: 3D perpendicular distance from galaxy to the nearest filament skeleton segment.

Computation:

1. Build density field from volume-limited tracers using DTFE
2. Run DisPerSE with persistence threshold = 3σ
3. Extract filament skeleton (critical points + arcs)
4. For each galaxy, compute minimum distance to any arc segment

DisPerSE Parameters:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Persistence | 3σ | Balance between noise (2σ) and supercluster-only (4σ) |
| Tracer | M_r < -20, z < 0.25 | Volume-limited |
| Tiling | 500 Mpc/h cubes | Memory management |
| Buffer | 50 Mpc overlap | Seamless stitching |

---

### GROUP_ID

| Property | Value |
|----------|-------|
| Type | int32 |
| Range | [1, ~10^6] |
| Null Allowed | Yes (null if isolated) |
| Source | Gfinder VAC |
| Tier | 1 |

Description: Identifier of the host group/cluster from the Gfinder halo-based group catalog.

---

### HALO_MASS

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(M☉) |
| Range | [11, 15] |
| Null Allowed | Yes |
| Source | Gfinder VAC |
| Tier | 1 |

Description: Estimated dark matter halo mass of the host group.

Method: Abundance matching or HOD-based estimation from group richness.

---

### GROUP_RANK

| Property | Value |
|----------|-------|
| Type | int32 |
| Range | [1, N_members] |
| Null Allowed | Yes |
| Source | Gfinder VAC |
| Tier | 1 |

Description: Rank within the group ordered by luminosity or stellar mass.

Interpretation:

| RANK | Classification |
|------|----------------|
| 1 | Central galaxy |
| > 1 | Satellite galaxy |

---

## 8. Quasar Physics Layer

### LOG_MBH

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(M☉) |
| Range | [6, 11] |
| Null Allowed | Yes |
| Source | BHMass VAC |
| Tier | 1 |

Description: Virial black hole mass estimate from single-epoch spectroscopy.

Method: Uses broad line width (typically Hβ, MgII, or CIV) and continuum luminosity with empirically calibrated scaling relations.

Systematic Uncertainty: ~0.3-0.5 dex intrinsic scatter in virial relations.

---

### L_BOL

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | erg/s |
| Range | [10^43, 10^48] |
| Null Allowed | Yes |
| Source | BHMass VAC |
| Tier | 1 |

Description: Bolometric luminosity estimated from continuum luminosity and bolometric corrections.

Eddington Ratio: `λ_Edd = L_BOL / L_Edd` where `L_Edd = 1.26 × 10^38 × 10^LOG_MBH` erg/s.

---

### BAL_PROB

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [0, 1] |
| Null Allowed | Yes |
| Source | AGN/QSO VAC |
| Tier | 1 |

Description: Probability that the QSO exhibits broad absorption line features.

---

### AI_INDEX

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | km/s |
| Range | [0, 30000] |
| Null Allowed | Yes |
| Source | AGN/QSO VAC |
| Tier | 1 |

Description: Absorption Index — integrated equivalent width of absorption troughs between 3000-25000 km/s blueward of CIV emission.

Threshold: AI > 0 indicates BAL candidate.

---

### BI_INDEX

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | km/s |
| Range | [0, 20000] |
| Null Allowed | Yes |
| Source | AGN/QSO VAC |
| Tier | 1 |

Description: Balnicity Index — stricter BAL definition requiring continuous absorption > 10% below continuum for > 2000 km/s.

Threshold: BI > 0 for classical BAL QSO definition.

---

### CIV_NC

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | log₁₀(cm⁻²) |
| Range | [13, 18] |
| Null Allowed | Yes |
| Source | CIV Absorber VAC |
| Tier | 1 |

Description: CIV column density from absorption line fitting.

Usage: Key ingredient for computing total hydrogen column density (with ionization correction) for outflow energetics.

---

### CIV_EW

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | Å (rest-frame) |
| Range | [0, 50] |
| Null Allowed | Yes |
| Source | CIV Absorber VAC |
| Tier | 1 |

Description: CIV λλ1548,1550 doublet equivalent width.

---

### CIV_VABS

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | km/s |
| Range | [-30000, 0] |
| Null Allowed | Yes |
| Source | CIV Absorber VAC |
| Tier | 1 |

Description: Velocity offset of CIV absorption relative to observer frame. Negative = blueshift.

---

### MGII_NC, MGII_EW

Same structure as CIV columns, from MgII Absorber VAC. Traces cooler, lower-ionization gas.

---

### V_OUT_CIV

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | km/s |
| Range | [0, 30000] |
| Null Allowed | Yes |
| Source | Computed |
| Tier | 2 |

Description: Outflow velocity in the QSO rest frame.

Formula:

```markdown
V_OUT_CIV = c × (Z_SYS - Z_ABS) / (1 + Z_SYS)
```

where Z_ABS is derived from CIV_VABS.

Note: Uses Z_SYS (PCA-based systemic redshift), NOT Z_HELIO, to avoid broad-line bias.

---

## 9. AI/ML Layer

### LATENT_VEC

| Property | Value |
|----------|-------|
| Type | float16[16] |
| Unit | dimensionless |
| Range | per-component varies |
| Null Allowed | Yes |
| Source | Computed (Spender) |
| Tier | 2 |

Description: 16-dimensional latent space representation of the spectrum from the Spender autoencoder.

Architecture: Spender is a 1D CNN autoencoder with shift-invariant (redshift-aware) decoder.

Storage: 16 × float16 = 32 bytes per object. Use columnar storage (Parquet) or FAISS index for similarity search.

Science Use: Enables clustering, similarity search, and outlier detection.

---

### RECON_MSE

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [0, ∞) |
| Null Allowed | Yes |
| Source | Computed (Spender) |
| Tier | 2 |

Description: Mean squared error between input spectrum and autoencoder reconstruction.

Interpretation: Higher values indicate the autoencoder struggled to represent the spectrum — potential anomaly.

Normalization: Computed on variance-normalized spectra for comparability.

---

### ANOMALY_SCORE

| Property | Value |
|----------|-------|
| Type | float32 |
| Unit | dimensionless |
| Range | [-1, 1] typical |
| Null Allowed | Yes |
| Source | Computed (Isolation Forest) |
| Tier | 2 |

Description: Isolation Forest anomaly score computed on the 16-D latent space.

Method: Train Isolation Forest on LATENT_VEC for representative sample; score all objects.

Interpretation: More negative = more anomalous.

---

## 10. VAC Join Specifications

### Join Keys

All VACs join on `TARGETID` (int64).

### VAC File Locations

| VAC | Path Pattern | File Format |
|-----|--------------|-------------|
| DESI Core | `spectro/redux/iron/zcatalog/` | FITS |
| FastSpecFit | `vac/dr1/fastspecfit/` | FITS |
| PROVABGS | `vac/dr1/provabgs/` | FITS |
| DESIVAST | `vac/dr1/desivast/` | FITS |
| Gfinder | `vac/dr1/gfinder/` | FITS |
| AGN/QSO | `vac/dr1/agnqso/` | FITS |
| CIV Absorber | `vac/dr1/civ-absorber/` | FITS |
| MgII Absorber | `vac/dr1/mgii-absorber/` | FITS |
| BHMass | `vac/dr1/qmassiron/` | FITS |

### Join Order (Recommended)

1. Start with DESI Core (full catalog)
2. Apply quality filters (ZWARN, DELTACHI2)
3. Left join PROVABGS (galaxy properties)
4. Left join FastSpecFit (lines, kinematics)
5. Left join DESIVAST (void assignments)
6. Left join Gfinder (group assignments)
7. For QSO subset: left join AGN/QSO, CIV, MgII, BHMass VACs

---

## 11. Quality Filters

### Mandatory Filters (Applied During Tier 1)

| Filter | Condition | Rationale |
|--------|-----------|-----------|
| Redshift quality | `ZWARN == 0` | Reliable redshift |
| Redshift confidence | `DELTACHI2 > 40` | Secure identification |
| Object type | `SPECTYPE IN ('GALAXY', 'QSO')` | Exclude stars |

### Recommended Filters (Sample-Dependent)

| Filter | Condition | Use Case |
|--------|-----------|----------|
| BGS Bright | `BGS_TARGET & 2 != 0` | Volume-limited sample |
| High S/N | `TSNR2_BGS > 10` | Reliable indices |
| Strong emission | `DELTACHI2 > 100` | Emission line science |
| Reliable dispersion | `VDISP > 70` | Kinematics studies |
| Void interior | `R_VOID_NORM < 1.0` | Void galaxy sample |
| Clean BAL | `BI_INDEX > 0` | BAL QSO sample |

---

## 12. Data Type Conventions

### Numeric Types

| Type | Use Case | Precision |
|------|----------|-----------|
| int64 | TARGETID, bitmasks | Exact |
| int32 | Flags, IDs, ranks | Exact |
| float64 | Coordinates (RA, DEC) | ~0.1 arcsec |
| float32 | Physical quantities | ~0.01% relative |
| float16 | Embeddings only | ~0.1% relative |

### String Types

- Use fixed-length strings where possible for columnar efficiency
- Standard length: 16 characters for classifications

### Null Handling

| Context | Representation |
|---------|----------------|
| Parquet/Pandas | `NaN` (float), `None` (object) |
| PostgreSQL | `NULL` |
| FITS | As defined by TNULL keyword |

Null Check: Always use `pd.isna()` or `IS NULL` in SQL. Never `== None`.

### Missing Data Semantics

| Null Meaning | Example Columns |
|--------------|-----------------|
| Not applicable | Z_SYS (for galaxies), VOID_ID (for wall galaxies) |
| Measurement failed | VDISP (low S/N), Lick indices |
| VAC not available | Quasar columns for galaxies |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-28 | Complete rewrite: Added quasar VACs, group catalog, detailed derivation methods |
| 1.0 | 2025-10-04 | Initial data dictionary |
