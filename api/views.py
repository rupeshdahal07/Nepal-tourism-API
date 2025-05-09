from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.shortcuts import get_object_or_404
from django_filters import CharFilter
from django.shortcuts import render

from .models import (
    Destination, Lodging, Guide, Agency, Permit,
    Event, TrailStatus, WeatherData, WeatherForecast, TourismStat
)
from .serializers.serializers import (
    DestinationSerializer, LodgingSerializer, GuideSerializer, 
    AgencySerializer, PermitSerializer, EventSerializer, 
    TrailStatusSerializer, WeatherDataSerializer, WeatherForecastSerializer,
    TourismStatSerializer
)
from .services.weather import WeatherService
from api.services.trail_status import TrailStatusService
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class CachedReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Base ViewSet with caching for list and retrieve actions"""
    
    @method_decorator(cache_page(60*1))  # Cache for 15 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    @method_decorator(cache_page(60*15))  # Cache for 15 minutes
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


# Custom filter sets for handling ArrayFields
class DestinationFilterSet(FilterSet):
    best_season = CharFilter(field_name='best_season', lookup_expr='contains')
    permits_required = CharFilter(field_name='permits_required', lookup_expr='contains')
    highlights = CharFilter(field_name='highlights', lookup_expr='contains')

    class Meta:
        model = Destination
        fields = ['type', 'region', 'difficulty']


class LodgingFilterSet(FilterSet):
    amenities = CharFilter(field_name='amenities', lookup_expr='contains')
    
    class Meta:
        model = Lodging
        fields = ['type', 'place', 'availability']


class GuideFilterSet(FilterSet):
    languages = CharFilter(field_name='languages', lookup_expr='contains')
    regions = CharFilter(field_name='regions', lookup_expr='contains')
    specialization = CharFilter(field_name='specialization', lookup_expr='contains')
    
    class Meta:
        model = Guide
        fields = ['available', 'experience_years']


class AgencyFilterSet(FilterSet):
    regions = CharFilter(field_name='regions', lookup_expr='contains')
    services = CharFilter(field_name='services', lookup_expr='contains')
    
    class Meta:
        model = Agency
        fields = []


class PermitFilterSet(FilterSet):
    regions = CharFilter(field_name='regions', lookup_expr='contains')
    
    class Meta:
        model = Permit
        fields = []


class EventFilterSet(FilterSet):
    activities = CharFilter(field_name='activities', lookup_expr='contains')
    
    class Meta:
        model = Event
        fields = ['type', 'city']


def home_page(request):
    """Render the home page"""
    return render(request, 'home.html')

def destinations_page(request):
    return render(request, 'destinations.html')
# Add this function to serve the weather template
def weather_page(request):
    return render(request, 'weather.html')
def trail_page(request):
    return render(request, 'trails.html')

class DestinationViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing destination information.
    """
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    filterset_class = DestinationFilterSet  # Use our custom filterset
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'highlights']
    ordering_fields = ['name', 'created_at', 'updated_at']
    
    @action(detail=False)
    def treks(self, request):
        """Get all trekking destinations"""
        treks = self.queryset.filter(type='trek')
        serializer = self.get_serializer(treks, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def heritage(self, request):
        """Get all heritage sites"""
        heritage = self.queryset.filter(type='heritage')
        serializer = self.get_serializer(heritage, many=True)
        return Response(serializer.data)


class LodgingViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing lodging information.
    """
    queryset = Lodging.objects.all()
    serializer_class = LodgingSerializer
    filterset_class = LodgingFilterSet  # Use our custom filterset
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'place', 'amenities']
    ordering_fields = ['name', 'min_price', 'rating', 'created_at']
    
    @action(detail=False)
    def by_destination(self, request):
        """Get lodgings by destination ID"""
        destination_id = request.query_params.get('id')
        if not destination_id:
            return Response({"error": "Destination ID is required"}, status=400)
            
        lodgings = self.queryset.filter(destination_id=destination_id)
        serializer = self.get_serializer(lodgings, many=True)
        return Response(serializer.data)


class GuideViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing guide information.
    """
    queryset = Guide.objects.all()
    serializer_class = GuideSerializer
    filterset_class = GuideFilterSet  # Use our custom filterset
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'specialization']
    ordering_fields = ['name', 'experience_years', 'daily_rate', 'rating']
    
    @action(detail=False)
    def top_rated(self, request):
        """Get top rated guides (rating >= 4.5)"""
        top_guides = self.queryset.filter(rating__gte=4.5, available=True)
        serializer = self.get_serializer(top_guides, many=True)
        return Response(serializer.data)


class AgencyViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing trekking agency information.
    """
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    filterset_class = AgencyFilterSet  # Use our custom filterset
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'services']
    ordering_fields = ['name', 'rating']


class PermitViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing permit information.
    """
    queryset = Permit.objects.all()
    serializer_class = PermitSerializer
    filterset_class = PermitFilterSet  # Use our custom filterset
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']


class EventViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing event information.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filterset_class = EventFilterSet  # Use our custom filterset
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'activities']
    ordering_fields = ['start_date', 'name']
    
    @action(detail=False)
    def upcoming(self, request):
        """Get upcoming events"""
        from django.utils import timezone
        today = timezone.now().date()
        upcoming = self.queryset.filter(end_date__gte=today).order_by('start_date')
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


class TrailStatusViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing trail status information.
    """
    queryset = TrailStatus.objects.all()
    serializer_class = TrailStatusSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['region', 'status']
    search_fields = ['name']
    
    @action(detail=False)
    def alerts(self, request):
        """Get trails with alerts"""
        trails_with_alerts = TrailStatusService.get_trails_with_alerts()
        serializer = self.get_serializer(trails_with_alerts, many=True)
        return Response(serializer.data)


class WeatherDataViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing current weather data.
    """
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['location']
    ordering_fields = ['timestamp']
    
    @action(detail=False)
    def latest(self, request):
        """Get latest weather data for a location"""
        location = request.query_params.get('location')
        weather_data = WeatherService.get_current_weather(location)
        if weather_data:
            serializer = self.get_serializer(weather_data)
            return Response(serializer.data)
        return Response({"error": f"No weather data found for {location}"}, status=404)
    
    @action(detail=False)
    def mountain(self, request):
        """Get weather adjusted for mountain elevations"""
        location = request.query_params.get('location')
        elevation = request.query_params.get('elevation')
        
        if not location or not elevation:
            return Response({
                "error": "Both 'location' and 'elevation' parameters are required"
            }, status=400)
        
        try:
            elevation = int(elevation)
            mountain_weather = WeatherService.get_mountain_weather(location, elevation)
            
            if not mountain_weather:
                return Response({
                    "error": f"Could not retrieve weather for {location}"
                }, status=404)
                
            serializer = self.get_serializer(mountain_weather)
            return Response(serializer.data)
        except ValueError:
            return Response({
                "error": "Elevation must be a valid integer"
            }, status=400)


class WeatherForecastViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing weather forecasts.
    """
    queryset = WeatherForecast.objects.all()
    serializer_class = WeatherForecastSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['location', 'date']
    ordering_fields = ['date']
    
    @action(detail=False)
    def for_location(self, request):
        """Get weather forecast for a specified location"""
        location = request.query_params.get('location')
        if not location:
            return Response({"error": "Location parameter is required"}, status=400)
        
        from django.utils import timezone
        today = timezone.now().date()
        
        # Get 7-day forecast
        forecasts = WeatherForecast.objects.filter(
            location=location,
            date__gte=today
        ).order_by('date')[:7]
        
        serializer = self.get_serializer(forecasts, many=True)
        return Response(serializer.data)


class TourismStatViewSet(CachedReadOnlyModelViewSet):
    """
    API endpoints for viewing tourism statistics.
    """
    queryset = TourismStat.objects.all()
    serializer_class = TourismStatSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['year', 'month']
    ordering_fields = ['year', 'month']
    
    @action(detail=False)
    def annual(self, request):
        """Get annual statistics (no monthly breakdown)"""
        annual_stats = self.queryset.filter(month__isnull=True).order_by('-year')
        serializer = self.get_serializer(annual_stats, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def monthly(self, request):
        """Get monthly statistics for a specific year"""
        year = request.query_params.get('year')
        if not year:
            return Response({"error": "Year parameter is required"}, status=400)
        
        try:
            year_int = int(year)
            monthly_stats = self.queryset.filter(
                year=year_int, 
                month__isnull=False
            ).order_by('month')
            serializer = self.get_serializer(monthly_stats, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response({"error": "Year must be a valid integer"}, status=400)