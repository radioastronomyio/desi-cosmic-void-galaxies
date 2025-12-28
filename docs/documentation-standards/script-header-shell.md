# Shell Script Header Template

> Template Version: 1.0  
> Applies To: All `.sh` files in desi-cosmic-void-galaxies  
> Last Updated: 2025-12-28

---

## Template

```bash
#!/usr/bin/env bash
# =============================================================================
# Script Name  : script-name.sh
# Description  : [One-line description of what the script does]
# Repository   : desi-cosmic-void-galaxies
# Author       : VintageDon (https://github.com/vintagedon)
# ORCID        : 0009-0008-7695-4093
# Created      : YYYY-MM-DD
# Phase        : [Phase XX - Phase Name]
# Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies
# =============================================================================
#
# DESCRIPTION
#   [2-4 sentences explaining the script's purpose, what it operates on,
#   and what outputs it produces. Include any important behavioral notes.]
#
# USAGE
#   ./script-name.sh [options]
#
# EXAMPLES
#   ./script-name.sh
#       [Description of what this invocation does]
#
#   ./script-name.sh --verbose
#       [Description of what this invocation does]
#
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# Configuration
# =============================================================================

# [Configuration variables with inline comments]

# =============================================================================
# Functions
# =============================================================================

# [Function definitions if needed]

# =============================================================================
# Main
# =============================================================================

main() {
    # [Main script logic]
}

main "$@"
```

---

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| Script Name | Yes | Filename for reference |
| Description | Yes | Single line, verb-led description |
| Repository | Yes | Repository name |
| Author | Yes | Name with GitHub profile link |
| ORCID | Yes | Author ORCID identifier |
| Created | Yes | Creation date (YYYY-MM-DD) |
| Phase | Yes | Pipeline phase this script belongs to |
| Link | Yes | Full repository URL |
| DESCRIPTION block | Yes | Expanded multi-line explanation |
| USAGE block | Yes | Command syntax |
| EXAMPLES block | Yes | At least one usage example |

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

```bash
# =============================================================================
# Section Name
# =============================================================================
```

Standard sections (in order):

1. **Configuration** — Variables, paths, settings
2. **Functions** — Helper function definitions (if any)
3. **Main** — Entry point function

---

## Best Practices

```bash
# Always use strict mode
set -euo pipefail

# Use main() function pattern for cleaner structure
main() {
    # Script logic here
}

main "$@"

# Quote variables to prevent word splitting
echo "${variable}"

# Use lowercase for local variables, UPPERCASE for exports/constants
local data_path="/mnt/proj-fs02/desi-dr1"
export DATA_ROOT="/mnt/proj-fs02/desi-dr1"
```

---

## Example: Minimal Script

```bash
#!/usr/bin/env bash
# =============================================================================
# Script Name  : check-catalog-sizes.sh
# Description  : Reports disk usage for catalog and spectral tile directories
# Repository   : desi-cosmic-void-galaxies
# Author       : VintageDon (https://github.com/vintagedon)
# ORCID        : 0009-0008-7695-4093
# Created      : 2025-12-28
# Phase        : Phase 02 - Catalog Validation
# Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies
# =============================================================================
#
# DESCRIPTION
#   Calculates and displays disk usage statistics for the catalog Parquet
#   files and spectral tile directories on cluster storage. Useful for
#   verifying acquisition completeness and monitoring storage consumption.
#
# USAGE
#   ./check-catalog-sizes.sh
#
# EXAMPLES
#   ./check-catalog-sizes.sh
#       Prints human-readable sizes for catalog and spectral directories.
#
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

CATALOG_PATH="/mnt/proj-fs02/desi-dr1/catalogs"
SPECTRAL_PATH="/mnt/proj-fs02/desi-dr1/spectral-tiles"

# =============================================================================
# Main
# =============================================================================

main() {
    echo "Catalog Data:"
    du -sh "${CATALOG_PATH}"

    echo "Spectral Tiles:"
    du -sh "${SPECTRAL_PATH}"

    echo "Tile count:"
    find "${SPECTRAL_PATH}" -maxdepth 1 -type d | wc -l
}

main "$@"
```

---

## Notes

- Always use `#!/usr/bin/env bash` for portability
- `set -euo pipefail` catches common errors early
- Use `main()` function pattern even for simple scripts — it's easier to extend
- Keep Description line under 80 characters
- Use present tense, active voice ("Reports..." not "This script reports...")
