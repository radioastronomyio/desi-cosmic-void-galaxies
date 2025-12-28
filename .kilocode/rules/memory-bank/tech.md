# DESI Cosmic Void Galaxies ARD — Technology Stack

## Technology Stack

### Primary Technologies

- **PostgreSQL:** 14+ — Materialization engine, VAC joins, derived columns
- **Python:** 3.11+ — ETL scripts, validation, Parquet export
- **Parquet:** Apache Parquet — Distribution format, columnar queries

### Supporting Technologies

- **Astropy:** 5.0+ — FITS I/O, coordinate transforms, unit handling
- **Pandas:** 2.0+ — DataFrame operations, data validation
- **PyArrow:** 14.0+ — Parquet read/write, schema enforcement
- **psycopg2:** 2.9+ — PostgreSQL connectivity
- **SQLAlchemy:** 2.0+ — ORM for complex queries (optional)

### Future Technologies (Tier 2)

- **pPXF:** Stellar kinematics, Lick indices
- **DisPerSE:** Cosmic web reconstruction
- **PyTorch:** Spender autoencoder inference
- **FAISS:** Vector similarity search for embeddings

---

## Dependencies

### Required Dependencies

```
astropy>=5.0        # FITS handling, coordinates
pandas>=2.0         # DataFrames
pyarrow>=14.0       # Parquet I/O
psycopg2>=2.9       # PostgreSQL driver
numpy>=1.24         # Numerical operations
scipy>=1.10         # Spatial queries (cKDTree)
```

### Optional Dependencies

```
sqlalchemy>=2.0     # ORM (when complex queries needed)
matplotlib>=3.7     # Validation plots
seaborn>=0.12       # Statistical visualization
tqdm>=4.65          # Progress bars for ETL
```

---

## Development Environment

### Prerequisites

- Python 3.11+ with pip/conda
- PostgreSQL client tools (psql)
- Network access to proj-pg01 (192.168.x.x)
- Network access to proj-fs02 (spectral tiles)

### Setup Instructions

```bash
# Clone repository
git clone https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies.git
cd desi-cosmic-void-galaxies

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt  # (when created)

# Configure database connection
cp .env.example .env
# Edit .env with proj-pg01 credentials

# Verify setup
python -c "import astropy; import pandas; import pyarrow; print('OK')"
```

### Environment Variables

```bash
PGHOST=proj-pg01              # PostgreSQL host
PGPORT=5432                   # PostgreSQL port
PGDATABASE=desi_ard           # Database name
PGUSER=ard_user               # Database user
PGPASSWORD=***                # Database password
SPECTRAL_TILES=/mnt/proj-fs02/spectral-tiles  # Tile archive path
```

---

## Infrastructure

### Compute Resources

| Resource | Specs | Role |
|----------|-------|------|
| proj-pg01 | 8 vCPU, 32GB RAM, SSD | PostgreSQL, materialization |
| proj-fs02 | 2×10G LACP, 10TB | Network storage, Parquet exports |
| radio-gpu01 | A4000 16GB | Tier 2 embeddings (future) |

### Network Topology

```
Workstation → proj-pg01 (PostgreSQL)
           → proj-fs02 (spectral tiles, Parquet)
           → radio-gpu01 (GPU compute, future)
```

### External Services

- **DESI Data Portal:** VAC FITS file downloads (HTTPS)
- **GitHub:** Repository hosting, version control

---

## Technical Constraints

### Performance Requirements

- ETL must complete within reasonable time (~hours, not days)
- Parquet queries should return in seconds for typical analysis
- Network access to spectral tiles must support streaming reads

### Storage Constraints

- PostgreSQL: ~32GB available for catalog tables
- proj-fs02: ~500GB available for Parquet exports
- Spectral tiles: 108GB (already converted)

### Compatibility Requirements

- PostgreSQL 14+ for JSON and array features
- Python 3.11+ for modern typing and performance
- Parquet schema must be compatible with PyArrow and DuckDB

---

## Development Workflow

### Version Control

- **Repository:** `https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies`
- **Branching:** Main branch for stable, feature branches for development
- **Commit Conventions:** See `.kilocode/rules/commit-conventions.md`

### Code Standards

- **Headers:** All scripts use standardized headers with ORCID
- **Comments:** Dual-audience pattern (human-first + AI NOTEs)
- **Style:** Black formatting, type hints on function signatures

### Testing

- Validation scripts in `work-logs/02-catalog-validation/`
- Statistical distribution checks against published DESI results
- Cross-VAC consistency validation

---

## Automation and Tooling

### Available Scripts

| Location | Script | Purpose |
|----------|--------|---------|
| `work-logs/01-*/` | `03-etl-*.py` | VAC ingestion to PostgreSQL |
| `work-logs/02-*/` | `01-validate-*.py` | Data validation |
| `work-logs/03-*/` | `02-extract-*.py` | FITS→Parquet conversion |

### Development Tools

- **DBeaver/pgAdmin:** PostgreSQL GUI for query development
- **VS Code:** Primary editor with Python extension
- **Git:** Version control

---

## Troubleshooting

### Common Issues

#### PostgreSQL Connection Refused
**Problem:** Cannot connect to proj-pg01  
**Solution:** Verify VPN/network access, check `.env` credentials, confirm PostgreSQL is running

#### FITS File Corruption
**Problem:** Astropy fails to read VAC FITS file  
**Solution:** Re-download from DESI portal, verify checksum

#### Parquet Schema Mismatch
**Problem:** PyArrow rejects schema during write  
**Solution:** Check column types against ARD-SCHEMA-v2.md, cast as needed

### Debug Commands

```bash
# Test PostgreSQL connection
psql -h proj-pg01 -U ard_user -d desi_ard -c "SELECT 1"

# Verify spectral tile access
ls /mnt/proj-fs02/spectral-tiles/ | head

# Check Parquet schema
python -c "import pyarrow.parquet as pq; print(pq.read_schema('file.parquet'))"
```

---

## Technical Documentation

- **DESI Data Model:** https://desi.lbl.gov/trac/wiki/DataModel
- **Astropy FITS:** https://docs.astropy.org/en/stable/io/fits/
- **PyArrow Parquet:** https://arrow.apache.org/docs/python/parquet.html
- **PostgreSQL:** https://www.postgresql.org/docs/14/
