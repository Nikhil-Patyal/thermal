from django.core.management.base import BaseCommand
from hotspots.models import Hotspot, ModelVersion
from ml.evidence_engine import EvidenceEngine
from django.db.models import Q
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Reprocesses unresolved thermal anomalies using the new land-cover classification baseline, with resumability.'

    def add_arguments(self, parser):
        parser.add_argument('--resume', action='store_true', help='Resume from the last processed ID in .reprocess_state')
        parser.add_argument('--reset', action='store_true', help='Reset the resume state and start from the beginning')

    def handle(self, *args, **options):
        state_file = '.reprocess_state'
        
        if options['reset']:
            if os.path.exists(state_file):
                os.remove(state_file)
                self.stdout.write(self.style.WARNING("Resetting reprocess state."))
        
        last_id = 0
        if options['resume'] and os.path.exists(state_file):
            with open(state_file, 'r') as f:
                last_id = int(f.read().strip())
                self.stdout.write(self.style.NOTICE(f"Resuming from ID > {last_id}"))

        # Version the classifier
        mv, _ = ModelVersion.objects.get_or_create(
            version_string='v2.0-baseline',
            defaults={'description': 'Evidence-based heuristic cascade baseline'}
        )

        unresolved_qs = Hotspot.objects.filter(
            latitude__gte=6, latitude__lte=38,
            longitude__gte=68, longitude__lte=98,
            latitude__isnull=False, longitude__isnull=False,
            id__gt=last_id
        ).filter(
            Q(predicted_class__in=['Pending classification', 'Unknown thermal anomaly', 'Other classification', 'Other / uncertain thermal anomaly', 'Unknown daytime thermal anomaly', 'Unknown nighttime thermal anomaly', '']) | 
            Q(predicted_class__isnull=True) |
            Q(attribution_status='pending_enrichment') |
            Q(attribution_status__isnull=True)
        ).order_by('id')
        
        count = unresolved_qs.count()
        self.stdout.write(self.style.NOTICE(f'Found {count} unresolved or pending hotspots to reprocess.'))
        
        if count == 0:
            return
            
        chunk_size = 1000
        engine = EvidenceEngine()
        
        # We will process in chunks up to a limit or entirely, but order by id enables simple pagination
        # Note: limiting to 10000 total per run to avoid infinite loops or memory bloat if running manually
        total_limit = 10000
        processed_count = 0
        
        while processed_count < total_limit:
            hotspots = list(unresolved_qs[:chunk_size])
            if not hotspots:
                break
                
            df = pd.DataFrame(list(Hotspot.objects.filter(id__in=[h.id for h in hotspots]).values(
                'id', 'latitude', 'longitude', 'scan', 'track', 'frp', 'daynight'
            )))
            
            if df.empty:
                break
                
            res_df = engine.generate_weak_labels(df)
            
            updates = []
            max_id_in_chunk = 0
            for hotspot in hotspots:
                if hotspot.id > max_id_in_chunk:
                    max_id_in_chunk = hotspot.id
                    
                if hotspot.id not in res_df.index:
                    continue
                res = res_df.loc[hotspot.id]
                hotspot.predicted_class = res['label']
                hotspot.source_type = None  # Clear legacy field so frontend uses predicted_class
                hotspot.confidence_score = res.get('label_confidence_str')
                hotspot.attribution_status = res.get('attribution_status')
                hotspot.is_tentative = res.get('is_tentative', False)
                hotspot.evidence_strength = res.get('label_confidence_str')
                hotspot.model_version = mv
                
                fractions = res.get('fractions')
                if fractions:
                    hotspot.cropland_fraction = fractions.get('cropland_fraction')
                    hotspot.tree_fraction = fractions.get('tree_fraction')
                    hotspot.shrub_fraction = fractions.get('shrub_fraction')
                    hotspot.grass_fraction = fractions.get('grass_fraction')
                    hotspot.other_fraction = fractions.get('other_fraction')
                    hotspot.valid_coverage = fractions.get('valid_coverage')
                    hotspot.footprint_method = fractions.get('footprint_method')
                    hotspot.landcover_source = fractions.get('landcover_source')
                    hotspot.landcover_version = fractions.get('landcover_version')
                
                updates.append(hotspot)
                
            Hotspot.objects.bulk_update(
                updates,
                ['predicted_class', 'source_type', 'confidence_score', 'attribution_status', 'is_tentative', 'evidence_strength',
                 'model_version', 'cropland_fraction', 'tree_fraction', 'shrub_fraction', 'grass_fraction', 'other_fraction',
                 'valid_coverage', 'footprint_method', 'landcover_source', 'landcover_version'],
                batch_size=500
            )
            
            processed_count += len(hotspots)
            self.stdout.write(self.style.SUCCESS(f'Processed chunk up to ID {max_id_in_chunk}. Total processed: {processed_count}'))
            
            # Save resume state
            with open(state_file, 'w') as f:
                f.write(str(max_id_in_chunk))
                
            # Advance query
            unresolved_qs = unresolved_qs.filter(id__gt=max_id_in_chunk)
            
        self.stdout.write(self.style.SUCCESS(f'Finished reprocessing {processed_count} records. Run with --resume to continue if interrupted.'))
