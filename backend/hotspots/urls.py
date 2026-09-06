from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HotspotViewSet

router = DefaultRouter()
router.register(r'hotspots', HotspotViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
