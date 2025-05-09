from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DestinationViewSet, LodgingViewSet, GuideViewSet, AgencyViewSet,
    PermitViewSet, EventViewSet, TrailStatusViewSet, WeatherDataViewSet,
    WeatherForecastViewSet, TourismStatViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'destinations', DestinationViewSet)
router.register(r'lodgings', LodgingViewSet)
router.register(r'guides', GuideViewSet)
router.register(r'agencies', AgencyViewSet)
router.register(r'permits', PermitViewSet)
router.register(r'events', EventViewSet)
router.register(r'trails', TrailStatusViewSet)
router.register(r'weather', WeatherDataViewSet)
router.register(r'forecasts', WeatherForecastViewSet)
router.register(r'statistics', TourismStatViewSet)  
router.register(r'weather-forecast', WeatherForecastViewSet, basename='weather-forecast')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]