# AGNI-DRISHTI: AI-Powered Global Geospatial Thermal Intelligence

This repository contains the prototype for **AGNI-DRISHTI**, built for SIH 26162.

*From global thermal anomaly to actionable intelligence — classify, attribute, explain.*

## Architecture Overview

1. **Database**: PostgreSQL with PostGIS extension for geospatial data.
2. **Backend**: Django REST Framework + GeoDjango for handling API requests and ML pipelines.
3. **Frontend**: React + TypeScript + Leaflet for a professional GIS dashboard.
4. **ML/Scripts**: Python scripts for NASA FIRMS ingestion and machine learning.

## Running the Setup for Presentation

### 1. Database (Docker Recommended)
Ensure you have Docker Desktop installed.
```bash
# From the root folder
docker-compose up -d
```

### 2. Backend (Python/Django)
Ensure you have Python installed.
```bash
cd backend
python -m venv .venv
# Activate the environment (Windows)
.venv\Scripts\activate
# Install requirements (Assuming you add requirements.txt later)
pip install django djangorestframework psycopg2-binary
# Run migrations
python manage.py migrate
# Start server
python manage.py runserver
```

### 3. Frontend (React/Vite)
Ensure you have Node.js installed.
```bash
cd frontend
npm install
npm run dev
```

### 4. Mocking Data (For Demo)
Run the fetching script to demonstrate ingestion:
```bash
cd scripts/ingestion
python fetch_firms.py --source viirs
```

## Dashboard Note
The frontend dashboard currently includes a mock UI state with `IND-00421` (Industrial Fire) to demonstrate the Event Dossier and Risk Assessment visualization.
