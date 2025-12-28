# PowerShell Script Header Template

> Template Version: 1.0  
> Applies To: All `.ps1` files in desi-cosmic-void-galaxies  
> Last Updated: 2025-12-28

---

## Template

```powershell
<#
.SYNOPSIS
    [One-line description of what the script does]

.DESCRIPTION
    [2-4 sentences explaining the script's purpose, what it operates on,
    and what outputs it produces. Include any important behavioral notes.]

.NOTES
    Repository  : desi-cosmic-void-galaxies
    Author      : VintageDon (https://github.com/vintagedon)
    ORCID       : 0009-0008-7695-4093
    Created     : YYYY-MM-DD
    Phase       : [Phase XX - Phase Name]

.EXAMPLE
    .\script-name.ps1

    [Description of what this invocation does]

.EXAMPLE
    .\script-name.ps1 -Parameter Value

    [Description of what this invocation does]

.LINK
    https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies
#>

# =============================================================================
# Configuration
# =============================================================================

# [Configuration variables with inline comments]

# =============================================================================
# Functions
# =============================================================================

# [Function definitions if needed]

# =============================================================================
# Execution
# =============================================================================

# [Main script logic]
```

---

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `.SYNOPSIS` | Yes | Single line, verb-led description |
| `.DESCRIPTION` | Yes | Expanded explanation of purpose and behavior |
| `.NOTES` | Yes | Static metadata (repository, author, ORCID, dates, phase) |
| `.EXAMPLE` | Yes | At least one usage example with description |
| `.LINK` | Yes | Repository URL |
| `.PARAMETER` | If applicable | Document any script parameters |

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

```powershell
# =============================================================================
# Section Name
# =============================================================================
```

Standard sections (in order):

1. **Configuration** — Variables, paths, settings
2. **Functions** — Helper function definitions (if any)
3. **Execution** — Main script logic

---

## Example: Minimal Script

```powershell
<#
.SYNOPSIS
    Validates Parquet catalog files against expected schema.

.DESCRIPTION
    Scans all Parquet files in the configured catalog directory and validates
    that required columns are present with correct data types. Outputs a
    summary of schema violations.

.NOTES
    Repository  : desi-cosmic-void-galaxies
    Author      : VintageDon (https://github.com/vintagedon)
    ORCID       : 0009-0008-7695-4093
    Created     : 2025-12-28
    Phase       : Phase 02 - Catalog Validation

.EXAMPLE
    .\validate-catalog-schema.ps1

    Validates all Parquet files in the default catalog directory.

.LINK
    https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies
#>

# =============================================================================
# Configuration
# =============================================================================

$catalogPath = "\\proj-fs02\desi-dr1\catalogs"

# =============================================================================
# Execution
# =============================================================================

Get-ChildItem -Path $catalogPath -Filter "*.parquet" | ForEach-Object {
    # Validation logic here
}
```

---

## Notes

- PowerShell comment-based help (`.SYNOPSIS`, `.DESCRIPTION`, etc.) enables `Get-Help script-name.ps1`
- Keep `.SYNOPSIS` under 80 characters
- Use present tense, active voice ("Validates..." not "This script validates...")
- Phase field should match work-log phase names exactly
