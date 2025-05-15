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
    best_season = CharFilter(field_name='best_season', lookup_expr='icontains')
    permits_required = CharFilter(field_name='permits_required', lookup_expr='icontains')
    highlights = CharFilter(field_name='highlights', lookup_expr='icontains')

    class Meta:
        model = Destination
        fields = ['type', 'region', 'difficulty']


class LodgingFilterSet(FilterSet):
    amenities = CharFilter(field_name='amenities', lookup_expr='icontains')
    
    class Meta:
        model = Lodging
        fields = ['type', 'place', 'availability']


class GuideFilterSet(FilterSet):
    languages = CharFilter(field_name='languages', lookup_expr='icontains')
    regions = CharFilter(field_name='regions', lookup_expr='icontains')
    specialization = CharFilter(field_name='specialization', lookup_expr='icontains')
    
    class Meta:
        model = Guide
        fields = ['available', 'experience_years']


class AgencyFilterSet(FilterSet):
    regions = CharFilter(field_name='regions', lookup_expr='icontains')
    services = CharFilter(field_name='services', lookup_expr='icontains')
    
    class Meta:
        model = Agency
        fields = []


class PermitFilterSet(FilterSet):
    regions = CharFilter(field_name='regions', lookup_expr='icontains')
    
    class Meta:
        model = Permit
        fields = []


class EventFilterSet(FilterSet):
    activities = CharFilter(field_name='activities', lookup_expr='icontains')
    
    class Meta:
        model = Event
        fields = ['type', 'city']


def home_page(request):
    """Home page view"""
    # Check if user was redirected here for login
    show_login = 'next' in request.GET
    
    context = {
        'show_login': show_login,
        'next': request.GET.get('next', '/')
    }
    return render(request, 'home.html', context)

def destinations_page(request):
    return render(request, 'destinations.html')
# Add this function to serve the weather template
def weather_page(request):
    return render(request, 'weather.html')
def trail_page(request):
    return render(request, 'trails.html')
def lodgings_page(request):
    return render(request, 'lodgings.html')


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
    
    @action(detail=True)
    def recommendations(self, request, pk=None):
        """Get recommended destinations similar to this one"""
        from api.services.recommendations import RecommendationService
        
        limit = int(request.query_params.get('limit', 5))
        recommendations = RecommendationService.get_destination_recommendations(pk, limit)
        
        serializer = self.get_serializer(recommendations, many=True)
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
        






from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .models import APIKey

@login_required
def api_keys_view(request):
    """View for displaying and managing API keys"""
    api_keys = APIKey.objects.filter(user=request.user, is_active=True).order_by('-created_at')
    
    context = {
        'api_keys': api_keys,
        # Pass new_api_key to the template if it exists in session
        'new_api_key': request.session.pop('new_api_key', None)
    }
    return render(request, 'api_keys.html', context)

@login_required
def generate_api_key(request):
    """Handle API key generation"""
    if request.method == 'POST':
        name = request.POST.get('name')
        tier = request.POST.get('tier', 'free')
        
        # Generate a new API key
        key_value = APIKey.generate_key()
        
        # Create the API key in the database
        api_key = APIKey.objects.create(
            key=key_value,
            name=name,
            user=request.user,
            email=request.user.email,
            tier=tier
        )
        
        # Store the key value in session to display it once
        request.session['new_api_key'] = key_value
        messages.success(request, f"API key '{name}' created successfully")
        
        return redirect('api_keys')
    
    return redirect('api_keys')

@login_required
def revoke_api_key(request, key):
    """Revoke (deactivate) an API key"""
    try:
        api_key = APIKey.objects.get(key=key, user=request.user)
        
        if request.method == 'POST':
            # Deactivate the key instead of deleting it
            api_key.is_active = False
            api_key.save()
            
            messages.success(request, f"API key '{api_key.name}' has been revoked")
        
        return redirect('api_keys')
        
    except APIKey.DoesNotExist:
        raise Http404("API key not found")