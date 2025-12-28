# Data Dictionary: DESI Cosmic Void Galaxy Catalog v1.0

## Table of Contents

1. [Core Galaxy Catalog](#1-core-galaxy-catalog-galaxies_coreparquet)
2. [Unified Void Catalog](#2-unified-void-catalog-voids_unifiedparquet)
3. [Environmental Assignments](#3-environmental-assignments-galaxy_void_assignmentsparquet)
4. [Database Schema (PostgreSQL)](#4-database-schema-postgresql-reference)
5. [Derived Quantities & Calculations](#5-derived-quantities--calculations)
6. [Data Types & Conventions](#6-data-types--conventions)

---

## 1. Core Galaxy Catalog (`galaxies_core.parquet`)

Source: DESI DR1 FastSpecFit Value-Added Catalog  
Rows: 6,445,927  
Primary Key: `targetid`

### Column Reference

| Column Name | Data Type | Unit | Null % | Description | Validation Range | Notes |
|-------------|-----------|------|--------|-------------|------------------|-------|
| targetid | int64 | - | 0% | DESI unique target identifier | >0 | Primary key, guaranteed unique |
| ra | float64 | degrees | 0% | Right Ascension (J2000) | [0.01, 359.99] | Equatorial coordinate |
| dec | float64 | degrees | 0% | Declination (J2000) | [-89.5, 89.5] | Equatorial coordinate |
| z | float64 | - | 0% | Spectroscopic redshift | [0.001, 1.02] | DESI pipeline processed |
| z_err | float64 | - | <0.1% | Redshift uncertainty | [1e-5, 0.1] | Median ~0.0001 |
| logmstar | float32 | log₁₀(M☉) | <0.02% | Log stellar mass | [8.0, 12.5] | FastSpecFit SED fit |
| logmstar_err | float32 | dex | <0.02% | Stellar mass uncertainty | [0.01, 0.5] | Typical ~0.1 dex |
| sfr | float32 | M☉/yr | <0.02% | Star formation rate | [0.0, 1000] | FastSpecFit derived |
| sfr_err | float32 | M☉/yr | <0.02% | SFR uncertainty | [0.0, 100] | May be asymmetric |
| age_gyr | float32 | Gyr | <0.1% | Luminosity-weighted age | [0.1, 13.8] | Universe age capped |
| metallicity | float32 | - | <0.1% | Mass-weighted Z/Z☉ | [-2.0, 0.5] | Solar units |
| d4000 | float32 | - | <0.1% | 4000Å break index | [1.0, 2.5] | Quenching diagnostic |
| healpix_id | int32 | - | 0% | HEALPix pixel ID | [0, 32767] | Source file identifier |
| source_file | string | - | 0% | Original FITS filename | - | Data provenance |
| ingestion_timestamp | datetime64 | - | 0% | ETL processing time | - | ISO 8601 format |

### Quality Flags (Recommended Filters)

```python
# High-confidence sample
high_quality = (
    (df['z_err'] < 0.001) &           # Precise redshift
    (df['logmstar_err'] < 0.2) &      # Reliable mass
    (df['sfr'] > 0)                   # Physical SFR
)

# Mass-complete sample (z-dependent)
# Example: M* > 10^9.5 M☉ at z < 0.1
mass_complete = (
    (df['z'] < 0.1) & (df['logmstar'] > 9.5)
)
```

---

## 2. Unified Void Catalog (`voids_unified.parquet`)

Source: DESIVAST DR1 (4 algorithms combined)  
Rows: ~10,752  
Primary Key: `void_id`

### Common Columns (All Algorithms)

| Column Name | Data Type | Unit | Description | Range |
|-------------|-----------|------|-------------|-------|
| void_id | int32 | - | Sequential unique ID | Auto-increment |
| algorithm | string | - | Void-finder method | {'VIDE', 'ZOBOV', 'REVOLVER', 'VoidFinder'} |
| original_void_index | int64 | - | Index in source FITS | Algorithm-dependent |
| ra | float64 | degrees | Void center RA | [0, 360] |
| dec | float64 | degrees | Void center Dec | [-90, 90] |
| redshift | float64 | - | Void center redshift | [0.001, 0.45] |
| x_mpc_h | float64 | Mpc/h | Comoving X | Calculated |
| y_mpc_h | float64 | Mpc/h | Comoving Y | Calculated |
| z_mpc_h | float64 | Mpc/h | Comoving Z | Calculated |
| radius_mpc_h | float64 | Mpc/h | Void radius | [5, 50] typical |
| edge_flag | int32 | - | Survey edge indicator | {0, 1} |
| galactic_cap | string | - | Sky region | {'NGC', 'SGC'} |
| source_file | string | - | Source FITS name | - |
| ingestion_timestamp | datetime64 | - | Processing time | - |

### Algorithm-Specific Columns

VoidFinder Only:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| r_eff | float64 | Mpc/h | Effective radius (maximal sphere) |
| r_eff_uncert | float64 | Mpc/h | Effective radius uncertainty |

ZOBOV Only:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| depth | int64 | - | Watershed depth level |
| tot_area | float64 | - | Total void area |
| edge_area | float64 | - | Edge area fraction |
| void0, void1 | int64 | - | Parent void indices (hierarchy) |

VIDE Specific:

- Uses parameter-space identification (fewer extra columns)

REVOLVER Specific:

- ML-informed detection (enhanced edge detection)

### Void Quality Criteria

```python
# High-quality voids (not near survey edges)
clean_voids = voids[voids['edge_flag'] == 0]

# Size-selected sample
large_voids = voids[voids['radius_mpc_h'] > 15]  # >15 Mpc/h

# Algorithm consensus (optional)
# Find voids detected by multiple algorithms within 2 Mpc
```

---

## 3. Environmental Assignments (`galaxy_void_assignments.parquet`)

Source: Derived via 3D spatial cross-match  
Rows: 6,445,927 (1:1 with galaxies)  
Primary Key: `targetid`

### Column Definitions

| Column Name | Data Type | Unit | Null % | Description | Calculation Method |
|-------------|-----------|------|--------|-------------|-------------------|
| targetid | int64 | - | 0% | Links to galaxies_core | Foreign key |
| environment | string | - | 0% | Environmental class | {'void', 'wall'} |
| nearest_void_id | int32 | - | ~40% | Closest void ID | k-NN search, null if wall |
| nearest_void_algorithm | string | - | ~40% | Algorithm of nearest void | VIDE/ZOBOV/etc., null if wall |
| distance_to_void_center_mpc | float64 | Mpc | ~40% | 3D comoving distance | `sqrt(Δx² + Δy² + Δz²)`, null if wall |
| void_centric_radius_norm | float64 | - | ~40% | Normalized void radius | `distance / void_radius`, null if wall |
| in_void_interior | bool | - | 0% | Interior flag | `r_norm < 1.0` if void, False if wall |

### Environmental Classification Logic

```python
# Pseudocode from ETL pipeline
for galaxy in galaxies:
    nearest_void, distance = find_nearest_void_3d(galaxy.ra, galaxy.dec, galaxy.z)
    
    if distance < nearest_void.radius_mpc_h:
        galaxy.environment = 'void'
        galaxy.void_centric_radius_norm = distance / nearest_void.radius_mpc_h
        galaxy.in_void_interior = True
    else:
        galaxy.environment = 'wall'
        galaxy.void_centric_radius_norm = None
        galaxy.in_void_interior = False
```

Important:

- "Wall" galaxies are NOT in high-density clusters—they are simply NOT in catalogued voids
- This is a binary classification based on void interiors only
- ~60% of galaxies classified as "wall" (outside all voids)

---

## 4. Database Schema (PostgreSQL Reference)

### Schema: `raw_catalogs`

Table: `raw_catalogs.fastspecfit_galaxies`

```sql
CREATE TABLE raw_catalogs.fastspecfit_galaxies (
    targetid         BIGINT PRIMARY KEY,
    ra               DOUBLE PRECISION NOT NULL,
    dec              DOUBLE PRECISION NOT NULL,
    z                DOUBLE PRECISION NOT NULL,
    z_err            DOUBLE PRECISION,
    logmstar         REAL,
    logmstar_err     REAL,
    sfr              REAL,
    sfr_err          REAL,
    age_gyr          REAL,
    metallicity      REAL,
    d4000            REAL,
    healpix_id       INTEGER NOT NULL,
    source_file      VARCHAR(255) NOT NULL,
    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_fastspecfit_z ON raw_catalogs.fastspecfit_galaxies(z);
CREATE INDEX idx_fastspecfit_logmstar ON raw_catalogs.fastspecfit_galaxies(logmstar);
CREATE INDEX idx_fastspecfit_ra_dec ON raw_catalogs.fastspecfit_galaxies USING GIST(ra, dec);
```

Table: `raw_catalogs.desivast_voids`

```sql
CREATE TABLE raw_catalogs.desivast_voids (
    void_id              SERIAL PRIMARY KEY,
    algorithm            VARCHAR(20) NOT NULL,
    original_void_index  BIGINT NOT NULL,
    ra                   DOUBLE PRECISION NOT NULL,
    dec                  DOUBLE PRECISION NOT NULL,
    redshift             DOUBLE PRECISION,
    x_mpc_h              DOUBLE PRECISION,
    y_mpc_h              DOUBLE PRECISION,
    z_mpc_h              DOUBLE PRECISION,
    radius_mpc_h         DOUBLE PRECISION,
    edge_flag            INTEGER,
    -- VoidFinder specific
    r_eff                DOUBLE PRECISION,
    r_eff_uncert         DOUBLE PRECISION,
    -- ZOBOV specific  
    depth                BIGINT,
    tot_area             DOUBLE PRECISION,
    edge_area            DOUBLE PRECISION,
    void0                BIGINT,
    void1                BIGINT,
    -- Common metadata
    galactic_cap         VARCHAR(3) NOT NULL,
    source_file          VARCHAR(255) NOT NULL,
    ingestion_timestamp  TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(algorithm, galactic_cap, original_void_index)
);

CREATE INDEX idx_voids_algorithm ON raw_catalogs.desivast_voids(algorithm);
CREATE INDEX idx_voids_radius ON raw_catalogs.desivast_voids(radius_mpc_h);
```

### Query Performance Notes

Spatial Queries (tested on proj-pg01):

```sql
-- Void proximity search (<1s on 6.4M rows)
SELECT g.targetid, g.ra, g.dec, g.z, g.logmstar, g.sfr
FROM raw_catalogs.fastspecfit_galaxies g
WHERE 
    g.z BETWEEN 0.1 AND 0.2
    AND EXISTS (
        SELECT 1 FROM raw_catalogs.desivast_voids v
        WHERE 
            v.algorithm = 'VIDE'
            AND sqrt(
                power(g.ra - v.ra, 2) + 
                power(g.dec - v.dec, 2)
            ) < 1.0  -- 1 degree angular search
    );
```

Bulk Operations:

- COPY ingestion: ~150k rows/sec
- Spatial index build: ~2 min for 6.4M rows
- Cross-match query: <1s with proper indexes

---

## 5. Derived Quantities & Calculations

### 3D Comoving Distances

Formula (using Astropy):

```python
from astropy.cosmology import FlatLambdaCDM

cosmo = FlatLambdaCDM(H0=70, Om0=0.3)  # DESI DR1 standard

# Comoving distance to object at redshift z
d_comov = cosmo.comoving_distance(z).value  # Mpc

# 3D Cartesian coordinates
x = d_comov * cos(dec_rad) * cos(ra_rad)
y = d_comov * cos(dec_rad) * sin(ra_rad)
z = d_comov * sin(dec_rad)

# 3D separation between objects
distance_3d = sqrt((x1-x2)2 + (y1-y2)2 + (z1-z2)2)
```

### Quenching Diagnostics

Specific Star Formation Rate (sSFR):

```python
sSFR = SFR / M_star  # yr⁻¹

# Standard quenching threshold
quenched = sSFR < 10^(-11) yr⁻¹
```

Alternative: sSFR-Mass Relation:

```python
# Below main sequence = quenched
log_sSFR_MS = -0.5 * (logmstar - 10) - 9.5  # Simplified MS at z~0.1
quenched = log10(sSFR) < log_sSFR_MS - 1.0  # 1 dex below MS
```

D4000 Index:

```python
# D4000 > 1.6 typically indicates old, quenched population
quenched_D4000 = d4000 > 1.6
```

### Local Density (k-NN Method)

Recommended Calculation:

```python
from scipy.spatial import KDTree

# Build tree on 3D comoving coordinates
tree = KDTree(galaxies[['x_mpc_h', 'y_mpc_h', 'z_mpc_h']])

# 5th nearest neighbor distance
distances, indices = tree.query(galaxies[['x_mpc_h', 'y_mpc_h', 'z_mpc_h']], k=6)
d5 = distances[:, 5]  # 6th neighbor (index 0 is self)

# Local density estimate
local_density = 5 / (4/3 * pi * d53)  # galaxies per Mpc³
```

---

## 6. Data Types & Conventions

### Naming Conventions

- Snake_case: All column names (e.g., `void_centric_radius_norm`)
- Lowercase: Algorithm names, environment labels
- Uppercase: Coordinate systems (RA, DEC) in docs only

### Units & Systems

| Quantity | Unit | Convention |
|----------|------|------------|
| Distances | Mpc or Mpc/h | Always specify h-dependence |
| Masses | M☉ (solar masses) | Log₁₀ scale preferred |
| SFR | M☉/yr | Linear scale |
| Coordinates | degrees | J2000 epoch |
| Redshift | dimensionless | Spectroscopic (not photometric) |
| Time | Gyr or yr | Context-dependent |

### Missing Data Encoding

| Context | Representation | Meaning |
|---------|---------------|---------|
| Parquet/Pandas | `NaN` (float), `None` (object) | Missing measurement |
| PostgreSQL | `NULL` | Missing value |
| Flags | `-999` or `-99` | Sentinel value (legacy) |
| Boolean | `False` | Negative assertion (not missing) |

Important: Use `pd.isna()` for safe null checking across types.

### File Format Specifications

Parquet:

- Engine: `pyarrow`
- Compression: `snappy` (default, fast decode)
- Row group size: 1M rows (for 6.4M dataset)
- Index: Always include primary key in data

CSV (if provided):

- Delimiter: `,`
- Quoting: Minimal (only when necessary)
- Encoding: UTF-8
- Missing: Empty string or explicit `NaN`

FITS (optional export):

- HDU structure: HDU[0] = empty primary, HDU[1] = binary table
- Column types: Standard FITS (TFORMn keywords)
- Coordinate system: Encoded in WCS headers

---

## Quick Reference Card

### Most Important Columns

For Galaxy Evolution Studies:

1. `logmstar`, `sfr` → Star formation main sequence
2. `z` → Redshift bin selection
3. `environment` → Void vs. wall split
4. `void_centric_radius_norm` → Void depth probe

For ML Applications:

1. `targetid` → Unique identifier for joins
2. All numeric columns → Feature vectors
3. `healpix_id` → Spatial partitioning
4. `environment` → Supervised learning target

For Quality Control:

1. `z_err`, `logmstar_err`, `sfr_err` → Uncertainties
2. `edge_flag` (voids) → Survey boundary effects
3. `source_file` → Data provenance
4. `ingestion_timestamp` → Version tracking

### Common Data Mistakes to Avoid

❌ Don't: Use `radius_mpc_h` directly without checking h-convention  
✅ Do: Confirm h=0.7 (DESI DR1) or convert: `radius_mpc = radius_mpc_h / 0.7`

❌ Don't: Assume all voids have `r_eff` (VoidFinder only)  
✅ Do: Check `algorithm` before using algorithm-specific columns

❌ Don't: Filter nulls with `== None` in Parquet  
✅ Do: Use `pd.isna()` or `.notna()` for robust null handling

❌ Don't: Ignore `edge_flag=1` voids (truncated shapes)  
✅ Do: Filter to `edge_flag=0` for complete void populations

---

## Schema Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-04 | Initial schema release |
