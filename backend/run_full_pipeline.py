"""
run_full_pipeline.py – orchestrates the whole ingestion → enrichment → classification pipeline.
Shows timing & progress for each stage.
"""
import os
import time

# Ensure Django env
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from hotspots.tasks import fetch_live_firms_data
from hotspots.batch_enrich import batch_enrich_all
from hotspots.batch_classify import batch_classify_all

def main():
    start = time.time()
    print("🚀 Starting full pipeline at", time.strftime('%Y-%m-%d %H:%M:%S'))
    
    # Phase 1 – fetch and bulk insert FIRMS data
    print("\n=== Phase 1: Fetch & Bulk Insert FIRMS ===")
    fetch_start = time.time()
    fetch_live_firms_data()  # this will print its own progress
    print(f"Phase 1 completed in {time.time() - fetch_start:.1f}s")
    
    # Phase 2 – batch enrichment
    print("\n=== Phase 2: Batch Enrichment ===")
    enrich_start = time.time()
    batch_enrich_all()  # prints its own progress
    print(f"Phase 2 completed in {time.time() - enrich_start:.1f}s")
    
    # Phase 3 – batch classification
    print("\n=== Phase 3: Batch Classification ===")
    classify_start = time.time()
    batch_classify_all()  # prints its own progress
    print(f"Phase 3 completed in {time.time() - classify_start:.1f}s")
    
    total = time.time() - start
    print("\n🎉 Full pipeline finished in", f"{total:.1f}s")

if __name__ == '__main__':
    main()
