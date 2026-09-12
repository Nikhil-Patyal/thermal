#!/bin/bash
echo "Fetching 7 days of live FIRMS data..."
FIRMS_DAYS=7 python fetch_live_data.py

echo "Enriching data..."
PYTHONPATH=. python hotspots/batch_enrich.py

echo "Classifying data..."
PYTHONPATH=. python hotspots/batch_classify.py

echo "All pipelines finished!"
