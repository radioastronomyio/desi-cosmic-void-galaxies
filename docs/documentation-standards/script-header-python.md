# Python Script Header Template

> Template Version: 1.0  
> Applies To: All `.py` files in desi-cosmic-void-galaxies  
> Last Updated: 2025-12-28

---

## Template

```python
#!/usr/bin/env python3
"""
Script Name  : script_name.py
Description  : [One-line description of what the script does]
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : YYYY-MM-DD
Phase        : [Phase XX - Phase Name]
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
[2-4 sentences explaining the script's purpose, what it operates on,
and what outputs it produces. Include any important behavioral notes.]

Usage
-----
    python script_name.py [options]

Examples
--------
    python script_name.py
        [Description of what this invocation does]

    python script_name.py --verbose
        [Description of what this invocation does]
"""

# =============================================================================
# Imports
# =============================================================================

from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

# [Configuration constants with inline comments]

# =============================================================================
# Functions
# =============================================================================


def main() -> None:
    """Entry point for script execution."""
    pass


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
```

---

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| Script Name | Yes | Filename for reference (snake_case) |
| Description | Yes | Single line, verb-led description |
| Repository | Yes | Repository name |
| Author | Yes | Name with GitHub profile link |
| ORCID | Yes | Author ORCID identifier |
| Created | Yes | Creation date (YYYY-MM-DD) |
| Phase | Yes | Pipeline phase this script belongs to |
| Link | Yes | Full repository URL |
| Description section | Yes | Expanded multi-line explanation |
| Usage section | Yes | Command syntax |
| Examples section | Yes | At least one usage example |

---

## Phase Reference

| Phase | Name |
|-------|------|
| Phase 01 | Catalog Acquisition |
| Phase 02 | Catalog Validation |
| Phase 03 | Spectral Tile Pipeline |
| Phase 04 | ARD Materialization |

---

## Section Comments

Use banner comments to separate logical sections:

```python
# =============================================================================
# Section Name
# =============================================================================
```

Standard sections (in order):

1. **Imports** — Standard library, third-party, local imports (in that order)
2. **Configuration** — Constants, paths, settings
3. **Functions** — Function and class definitions
4. **Entry Point** — `if __name__ == "__main__":` block

---

## Docstring Style

Use NumPy-style docstrings for functions:

```python
def query_void_galaxies(
    void_id: int,
    radius_factor: float = 1.0
) -> pd.DataFrame:
    """
    Query galaxies within a specified void radius.

    Parameters
    ----------
    void_id : int
        Unique identifier from the unified void catalog.
    radius_factor : float, optional
        Multiplier for void radius. Default is 1.0 (exact void boundary).

    Returns
    -------
    pd.DataFrame
        Galaxies within the specified void, with columns:
        targetid, ra, dec, z, logmstar, sfr, void_centric_radius_norm.

    Raises
    ------
    ValueError
        If void_id does not exist in the catalog.
    ConnectionError
        If PostgreSQL connection fails.

    Examples
    --------
    >>> galaxies = query_void_galaxies(42, radius_factor=0.5)
    >>> len(galaxies)
    127
    """
    pass
```

---

## Example: Minimal Script

```python
#!/usr/bin/env python3
"""
Script Name  : validate_catalog_integrity.py
Description  : Validates galaxy catalog integrity against PostgreSQL source
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-12-28
Phase        : Phase 02 - Catalog Validation
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Compares row counts and checksums between the Parquet catalog export and
the PostgreSQL source tables. Reports any discrepancies in record counts,
null distributions, or value ranges for key columns.

Usage
-----
    python validate_catalog_integrity.py [--output report.json]

Examples
--------
    python validate_catalog_integrity.py
        Validates catalog and prints summary to stdout.

    python validate_catalog_integrity.py --output validation_report.json
        Validates catalog and writes detailed report to JSON.
"""

# =============================================================================
# Imports
# =============================================================================

from pathlib import Path

import pandas as pd
import psycopg2

# =============================================================================
# Configuration
# =============================================================================

PARQUET_PATH = Path("/mnt/proj-fs02/desi-dr1/catalogs/galaxies_core.parquet")
PG_CONNECTION = "postgresql://user@proj-pg01:5432/desi_catalogs"

# =============================================================================
# Functions
# =============================================================================


def validate_row_counts(parquet_df: pd.DataFrame, pg_count: int) -> dict:
    """
    Compare row counts between Parquet and PostgreSQL.

    Parameters
    ----------
    parquet_df : pd.DataFrame
        DataFrame loaded from Parquet file.
    pg_count : int
        Row count from PostgreSQL query.

    Returns
    -------
    dict
        Validation result with keys: 'match', 'parquet_count', 'pg_count'.
    """
    return {
        "match": len(parquet_df) == pg_count,
        "parquet_count": len(parquet_df),
        "pg_count": pg_count,
    }


def main() -> None:
    """Entry point for script execution."""
    print(f"Validating catalog at {PARQUET_PATH}")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
```

---

## Type Hints

Always use type hints for function signatures:

```python
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


def process_spectral_tile(
    tile_path: Path,
    output_dir: Optional[Path] = None,
    target_ids: Optional[list[int]] = None,
) -> dict[str, np.ndarray]:
    """Process a spectral tile and return extracted arrays."""
    pass
```

---

## Notes

- Use `#!/usr/bin/env python3` for portability
- Module docstring goes immediately after shebang
- Keep Description line under 80 characters
- Use present tense, active voice ("Validates..." not "This script validates...")
- Use `pathlib.Path` instead of string paths
- Use type hints for all function parameters and return values
- Follow PEP 8 style guide
