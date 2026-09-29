from django.core.management.base import BaseCommand
from hotspots.models import Hotspot
import csv
import os
from django.utils import timezone

class Command(BaseCommand):
    help = 'Exports a stratified sample of hotspots for independent human review to build a mixed-landscape classifier.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1000, help='Maximum number of records to export')
        parser.add_argument('--out', type=str, default='review_export.csv', help='Output CSV file path')

    def handle(self, *args, **options):
        limit = options['limit']
        out_path = options['out']
        
        # We want to export mixed/unresolved hotspots, prioritizing those inside India bounding box
        # and those with actual landcover data if possible.
        qs = Hotspot.objects.filter(
            latitude__gte=6, latitude__lte=38,
            longitude__gte=68, longitude__lte=98
        ).order_by('?')[:limit]  # Random sample

        headers = [
            'id', 'latitude', 'longitude', 'acq_date', 'acq_time', 'satellite', 'instrument', 
            'frp', 'brightness', 'bright_t31', 'daynight', 'scan', 'track',
            'current_predicted_class', 'is_tentative', 'attribution_status', 
            'landcover_source', 'valid_coverage', 'cropland_fraction', 'tree_fraction', 
            'shrub_fraction', 'grass_fraction', 'other_fraction', 'industrial_anomaly_status',
            'reviewer_label', 'reviewer_notes'
        ]

        with open(out_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            count = 0
            for h in qs:
                writer.writerow([
                    h.id, h.latitude, h.longitude, h.acquisition_date, '', h.satellite, h.instrument,
                    h.frp, h.brightness, h.bright_t31, h.daynight, h.scan, h.track,
                    h.predicted_class, h.is_tentative, h.attribution_status,
                    h.landcover_source, h.valid_coverage, h.cropland_fraction, h.tree_fraction,
                    h.shrub_fraction, h.grass_fraction, h.other_fraction, h.industrial_anomaly_status,
                    '', '' # Empty columns for reviewer to fill in
                ])
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully exported {count} records to {out_path} for independent human review.'))
