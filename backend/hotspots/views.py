from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Hotspot
from .serializers import HotspotSerializer

class HotspotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows live hotspots to be viewed.
    Read-only since data is ingested automatically.
    """
    queryset = Hotspot.objects.all().order_by('-fetched_at')
    serializer_class = HotspotSerializer

    @action(detail=True, methods=['get'])
    def predict(self, request, pk=None):
        """
        Endpoint to retrieve the classification and SHAP explanation for a specific hotspot.
        (This data is already pre-computed and stored in the model, so we can just return it).
        """
        hotspot = self.get_object()
        
        return Response({
            'hotspot_id': hotspot.id,
            'predicted_class': hotspot.predicted_class,
            'confidence_score': hotspot.confidence_score,
            'shap_values': hotspot.shap_values
        })
