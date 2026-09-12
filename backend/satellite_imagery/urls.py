from django.urls import path
from .views import HotspotImageryView, HotspotGroundImageryView

urlpatterns = [
    path('hotspots/<int:hotspot_id>/imagery/', HotspotImageryView.as_view(), name='hotspot-imagery'),
    path('hotspots/<int:hotspot_id>/ground-imagery/', HotspotGroundImageryView.as_view(), name='hotspot-ground-imagery'),
]
