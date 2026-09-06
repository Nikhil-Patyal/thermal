# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python Backend
FROM python:3.11-slim

# Install system dependencies for PostGIS, GDAL, etc.
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
# For this sprint, we'll install required packages directly if requirements.txt is missing
RUN pip install django djangorestframework django-cors-headers celery redis psycopg2-binary \
    django-redis lightgbm optuna pandas scikit-learn numpy

# Copy backend code
COPY backend/ ./

# Copy built frontend assets to Django's staticfiles (or a specific directory to serve)
COPY --from=frontend-builder /app/frontend/dist /app/frontend_dist

# Collect static files (mocked or actual if configured)
# RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Start command (Gunicorn or Django dev server for sprint)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
