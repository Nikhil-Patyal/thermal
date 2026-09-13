# AGNI-DRISHTI: Thermal Sentinel

AGNI-DRISHTI is an advanced thermal anomaly detection and classification system. It uses a strict, deterministic spatial engine (PostGIS) to evaluate satellite thermal hotspots against high-fidelity 2D industrial/mining footprints from OpenStreetMap, filtering specifically for the Indian subcontinent.

## 🚀 Quickstart Guide

This guide will walk you through setting up the project from scratch, populating your database with the massive geographic datasets, and running the application locally.

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 14+** with **PostGIS** extension installed.

### 2. Database Setup
You must have a running Postgres database with the PostGIS extension enabled.

```bash
# In your psql console or database manager:
CREATE DATABASE thermal_sentinel;
\c thermal_sentinel
CREATE EXTENSION postgis;
```

Update the `.env` file in the `backend/` directory with your database credentials:
```env
DB_NAME=thermal_sentinel
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

### 3. Backend Setup & Migrations
Install the required python dependencies and run the Django migrations to create the database schemas.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install rasterio osmium  # Required for spatial parsing

# Run migrations to build the tables
python manage.py migrate
```

### 4. Downloading and Ingesting Geographic Data
The raw datasets (PBF files, shapefiles) are ignored in Git because they are massive (1.2+ GB). You must run the ingestion scripts to download and parse them into your local database.

**Step 4a: Load India Boundary**
This enforces the strict spatial predicate for the Indian subcontinent.
```bash
# Still inside the backend/ directory
python3 load_india_boundary.py
```

**Step 4b: Extract Industrial & Mining Footprints (RAM Intensive)**
This script downloads the latest `india-latest.osm.pbf` file and parses out true 2D polygons for factories, mines, and smelters.
```bash
# This may take several minutes and uses ~2GB of RAM.
python3 import_india_osm.py
```

**Step 4c: Reclassify Thermal Hotspots**
If you already have thermal hotspots in your database (e.g. from an API pull or CSV import), run the strict classification engine to assign them evidence-based labels.
```bash
python3 reclassify_v2.py
```

### 5. Running the Application

**Start the Django Backend Server:**
```bash
# Inside the backend/ directory
python manage.py runserver 0.0.0.0:8000
```

**Start the React Frontend:**
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` in your browser. The map will load centered on India, displaying hotspots with rigorous evidence-based classifications (Low, Moderate, Strong) rather than uncalibrated percentage scores.

## Architecture Notes
- **Evidence Engine (`backend/ml/evidence_engine.py`)**: Responsible for all spatial overlap logic (`ST_Intersects`, `ST_DWithin`).
- **Data Parsing (`backend/import_india_osm.py`)**: Converts raw OpenStreetMap nodes/ways into PostGIS `GeometryField` polygons.
- **Frontend (`frontend/src/components/Map.tsx`)**: Renders the UI popups and decouples visual certainty from unverified machine learning scores.
