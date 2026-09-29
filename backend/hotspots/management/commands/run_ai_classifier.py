import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from django.db.models import Q
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from hotspots.models import Hotspot

class Command(BaseCommand):
    help = 'Runs an Unsupervised Gaussian Mixture Model (GMM) to classify unknown anomalies based on FIRMS features.'

    def handle(self, *args, **options):
        self.stdout.write("Fetching unclassified hotspots from the database...")
        
        # We target records that don't have a strong industrial/mining classification
        qs = Hotspot.objects.filter(
            Q(predicted_class__isnull=True) | 
            Q(predicted_class='Other / uncertain thermal anomaly') |
            Q(predicted_class='Unknown / Uncertain') |
            Q(attribution_status='pending_enrichment')
        ).exclude(
            industrial_anomaly_status=True
        )

        total_count = qs.count()
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("No unclassified hotspots found. Exiting."))
            return

        self.stdout.write(f"Found {total_count} unclassified hotspots. Extracting features...")
        
        # Load data into memory (doing it in chunks if necessary, but GMM can handle ~360k in memory on a decent machine)
        # We will extract only what we need to save memory
        data = list(qs.values('id', 'frp', 'brightness', 'bright_t31', 'daynight'))
        df = pd.DataFrame(data)

        # Handle missing values
        df['frp'] = pd.to_numeric(df['frp'], errors='coerce').fillna(0)
        df['brightness'] = pd.to_numeric(df['brightness'], errors='coerce').fillna(0)
        df['bright_t31'] = pd.to_numeric(df['bright_t31'], errors='coerce').fillna(0)
        
        # Feature Engineering
        df['is_day'] = (df['daynight'] == 'D').astype(float)

        features = ['frp', 'brightness', 'bright_t31', 'is_day']
        X = df[features].values

        self.stdout.write("Scaling features...")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        self.stdout.write("Fitting Gaussian Mixture Model (k=2)...")
        gmm = GaussianMixture(n_components=2, covariance_type='full', random_state=42, max_iter=100)
        gmm.fit(X_scaled)
        
        # Predict clusters and probabilities
        labels = gmm.predict(X_scaled)
        probs = gmm.predict_proba(X_scaled)

        # Determine which cluster is Forest vs Agriculture
        # We expect Forest Fires to have higher average FRP than Agricultural fires.
        means = scaler.inverse_transform(gmm.means_)
        frp_cluster_0 = means[0][0]
        frp_cluster_1 = means[1][0]

        if frp_cluster_0 > frp_cluster_1:
            forest_cluster = 0
            agri_cluster = 1
        else:
            forest_cluster = 1
            agri_cluster = 0

        self.stdout.write(f"Cluster {forest_cluster} identified as Forest (Avg FRP: {means[forest_cluster][0]:.2f})")
        self.stdout.write(f"Cluster {agri_cluster} identified as Agriculture (Avg FRP: {means[agri_cluster][0]:.2f})")

        # Map predictions back to the dataframe
        df['cluster'] = labels
        df['max_prob'] = probs.max(axis=1)

        # Update the database in batches
        self.stdout.write("Updating database records in bulk...")
        
        batch_size = 5000
        updates = []
        
        # Create a mapping dictionary for fast lookup
        # to avoid instantiating massive querysets at once
        id_to_pred = {}
        for idx, row in df.iterrows():
            is_forest = (row['cluster'] == forest_cluster)
            label_str = 'Likely wildland vegetation burning' if is_forest else 'Likely agricultural burning'
            prob = row['max_prob']
            
            # Formulate a confidence score string
            conf_percent = round(prob * 100, 1)
            conf_str = f"{conf_percent}% (AI GMM)"
            
            id_to_pred[row['id']] = {
                'predicted_class': label_str,
                'confidence_score': conf_str,
                'is_tentative': prob < 0.65,
                'attribution_status': 'ai_unsupervised_classified'
            }

        # Fetch and update instances in chunks to prevent memory bloat
        # Since qs is unevaluated, we can chunk it using an iterator
        chunk = []
        for hotspot in qs.iterator(chunk_size=batch_size):
            pred = id_to_pred.get(hotspot.id)
            if pred:
                hotspot.predicted_class = pred['predicted_class']
                hotspot.confidence_score = pred['confidence_score']
                hotspot.is_tentative = pred['is_tentative']
                hotspot.attribution_status = pred['attribution_status']
                chunk.append(hotspot)
            
            if len(chunk) >= batch_size:
                Hotspot.objects.bulk_update(chunk, ['predicted_class', 'confidence_score', 'is_tentative', 'attribution_status'])
                self.stdout.write(f"Updated {len(chunk)} records...")
                chunk = []

        if chunk:
            Hotspot.objects.bulk_update(chunk, ['predicted_class', 'confidence_score', 'is_tentative', 'attribution_status'])
            self.stdout.write(f"Updated final {len(chunk)} records...")

        self.stdout.write(self.style.SUCCESS(f"Successfully classified and updated {total_count} hotspots using AI!"))
