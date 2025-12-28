# Data Infrastructure Reference

This project uses shared research infrastructure on the radioastronomy.io cluster. This document provides connection details and usage patterns.

## VM Inventory

### Kubernetes Cluster

4-node cluster for containerized workloads. kubectl points to k8s01 by default.

| VMID | Hostname | IP | vCPU | RAM | Storage | Notes |
|------|----------|-----|------|-----|---------|-------|
| 3001 | radio-k8s01 | 10.25.20.4 | 12 | 48G | 1TB PM983 | Primary node |
| 3002 | radio-k8s02 | — | 12 | 48G | 1TB PM983 | Worker |
| 3003 | radio-k8s03 | — | 12 | 48G | 1TB PM983 | Worker |
| 2005 | radio-gpu01 | 10.25.20.10 | 12 | 48G | 100G | Worker + A4000 GPU |

Workload Constraints:
- 48GB RAM per node — Maximum memory for any single pod/job
- A4000 GPU: 16GB vRAM — Model size limit for GPU workloads
- GPU available both as standalone VM and via K8s scheduling

### Database Servers

| VMID | Hostname | OS | IP | vCPU | RAM | Storage | Purpose |
|------|----------|----|----|------|-----|---------|---------|
| 2002 | radio-pgsql01 | Ubuntu 24.04 | 10.25.20.8 | 8 | 32G | 250G | Primary research PostgreSQL (pgvector, postgis) |
| 2012 | radio-pgsql02 | Ubuntu 24.04 | 10.25.20.16 | 4 | 16G | 100G | Application PostgreSQL (Gitea, local apps) |
| 2018 | radio-neo4j01 | Ubuntu 24.04 | 10.25.20.21 | 6 | 24G | 250G | Graph database |
| 2016 | radio-mongo01 | Ubuntu 24.04 | 10.25.20.18 | 2 | 4G | 100G | Document database (available, unused) |
| 2003 | radio-dfdb01 | Ubuntu 24.04 | 10.25.20.23 | 4 | 8G | — | DragonFlyDB |

### Storage & Support

| VMID | Hostname | OS | IP | vCPU | RAM | Storage | Purpose |
|------|----------|----|----|------|-----|---------|---------|
| 2011 | radio-fs02 | Server 2025 | 10.25.20.15 | 4 | 6G | 125G | Windows SMB (ML data shares, DESIVAST parquets) |
| 2007 | radio-fs01 | Ubuntu 24.04 | 10.25.20.11 | 2 | 6G | 1TB | NFS server (available, unused) |
| 2006 | radio-agents01 | Ubuntu 24.04 | 10.25.20.20 | 8 | 32G | 200G | AI agents, MetaMCP, monitoring stack |

## Global Environment

All research VMs source credentials from `/opt/global-env/research.env`. Projects should load this file rather than hardcoding connection details.

```bash
# Load in shell
set -a && source /opt/global-env/research.env && set +a

# Load in Python
from dotenv import load_dotenv
load_dotenv('/opt/global-env/research.env')
```

### Environment Variable Reference

| Variable | Value | Description |
|----------|-------|-------------|
| PostgreSQL - pgsql01 |||
| `PGSQL01_HOST` | 10.25.20.8 | Research data server |
| `PGSQL01_PORT` | 5432 | |
| `PGSQL01_ADMIN_USER` | clusteradmin_pg01 | Admin credentials (password in env) |
| `PGSQL01_DESIVAST_DB` | desi_void_desivast | DESI-VAST void catalog |
| `PGSQL01_FASTSPEC_DB` | desi_void_fastspecfit | FastSpecFit spectroscopic data |
| `PGSQL01_COSMICVOIDS_ARD_DB` | cosmicvoids_ard | Cosmic voids ARD |
| `PGSQL01_RBH1_DB` | rbh1_validation | RBH-1 validation data |
| PostgreSQL - pgsql02 |||
| `PGSQL02_HOST` | 10.25.20.16 | Application databases |
| `PGSQL02_PORT` | 5432 | |
| `PGSQL02_ADMIN_USER` | clusteradmin_pg02 | Admin credentials (password in env) |
| Neo4j |||
| `NEO4J_HOST` | 10.25.20.21 | Graph database |
| `NEO4J_PORT` | 7687 | |
| `NEO4J_USER` | neo4j | |
| `NEO4J_DATABASE` | desi_void_graphs | |
| MongoDB |||
| `MONGO_HOST` | 10.25.20.18 | Document database (unused) |
| `MONGO_PORT` | 27017 | |
| `MONGO_ADMIN_USER` | mongoadmin | |
| GPU Processing |||
| `GPU_HOST` | 10.25.20.10 | gpu01 (A4000, 16GB vRAM) |
| `GPU_USER` | ubuntu | |
| `GPU_PYTHON_ENV` | /home/ubuntu/venv/desi | |
| `OLLAMA_ENDPOINT` | http://10.25.20.10:11434 | |
| Processing Defaults |||
| `BATCH_SIZE` | 10000 | Records per batch |
| `MAX_WORKERS` | 4 | Parallel workers |
| `ML_PROCESSING_MODE` | remote_gpu | Options: local, remote_gpu, hybrid |
| Development |||
| `HEALPIX_SUBSET_SIZE` | 5 | Tiles for prototype testing |
| `LOG_LEVEL` | INFO | |
| `ENABLE_PROFILING` | false | |

## Database Connections

### PostgreSQL (pgsql01 - Research Data)

Use admin credentials for all connections. Individual database users deprecated.

```python
import os
import psycopg2

conn = psycopg2.connect(
    host=os.getenv('PGSQL01_HOST'),
    port=os.getenv('PGSQL01_PORT'),
    user=os.getenv('PGSQL01_ADMIN_USER'),
    password=os.getenv('PGSQL01_ADMIN_PASSWORD'),
    database=os.getenv('PGSQL01_DESIVAST_DB')  # or other DB variable
)
```

Available databases on pgsql01:
- `PGSQL01_DESIVAST_DB` — DESI-VAST void catalog
- `PGSQL01_FASTSPEC_DB` — FastSpecFit spectroscopic data
- `PGSQL01_COSMICVOIDS_ARD_DB` — Cosmic voids analysis-ready dataset
- `PGSQL01_RBH1_DB` — RBH-1 validation data

### Neo4j

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    f"bolt://{os.getenv('NEO4J_HOST')}:{os.getenv('NEO4J_PORT')}",
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)
```

### GPU Processing

A4000 with 16GB vRAM — constraint for model sizing. SSH access for remote execution or use Ollama endpoint directly:

```python
import requests

response = requests.post(
    f"{os.getenv('OLLAMA_ENDPOINT')}/api/generate",
    json={"model": "llama3", "prompt": "..."}
)
```

## Processing Patterns

Default batch processing configuration from env:
- `BATCH_SIZE=10000` — Records per batch
- `MAX_WORKERS=4` — Parallel workers
- `ML_PROCESSING_MODE=remote_gpu` — Offload ML to gpu01

## Performance Baselines

### Storage (Samsung PM983 NVMe)

Shared across database VMs on node06.

| Metric | Specification | Current Utilization |
|--------|---------------|---------------------|
| Sequential Read | 3,000 MB/s | ~1.0 GiB/s |
| Sequential Write | 1,400 MB/s | — |
| Random Read IOPS | 480,000 | ~65K IOPS |
| Random Write IOPS | 42,000 | — |
| Headroom | — | 7-8x current load |

Multiple VMs can share storage without performance degradation at current utilization levels.

### PostgreSQL Throughput (pgsql01)

| Workload | Throughput | Latency | Notes |
|----------|------------|---------|-------|
| Read-only (hot cache) | 205,000 TPS | 0.078ms | CPU-bound, not I/O limited |
| Durable writes | 20,000-22,000 TPS | ~0.8-1.5ms | Optimal at 16-32 connections |
| Bulk ingestion | 2-4x improvement | — | Use `synchronous_commit = off` |

Performance limited by WAL commit/flush, not storage bandwidth.

### Monitoring Thresholds

| Metric | Warning Threshold | Action |
|--------|-------------------|--------|
| Average query time | >10ms | Review indexes |
| Cache hit ratio | <95% | Increase shared_buffers |
| Active connections | >40 | Implement connection pooling |
| WAL write rate | >500MB/min | Tune checkpoints |
| Fsync latency P95 | >1ms | Investigate storage |

## Monitoring

Logs and metrics from all data science VMs route to radio-agents01's monitoring stack (Prometheus/Loki/Grafana) with 7-day retention.
