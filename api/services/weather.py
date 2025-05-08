import requests
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ..models import WeatherData, WeatherForecast

logger = logging.getLogger(__name__)

# Cache keys and durations
CURRENT_WEATHER_CACHE_KEY = "weather_data_{location}"
FORECAST_CACHE_KEY = "weather_forecast_{location}"
CURRENT_WEATHER_CACHE_DURATION = 60 * 30  # 30 minutes
FORECAST_CACHE_DURATION = 60 * 60 * 3  # 3 hours


class WeatherService:
    """Service for retrieving and managing weather data"""

    @staticmethod
    def get_current_weather(location):
        """
        Get current weather for a location.
        First tries cache, then database, then external API.
        """
        # Try getting from cache first
        cache_key = CURRENT_WEATHER_CACHE_KEY.format(location=location)
        cached_weather = cache.get(cache_key)
        if cached_weather:
            logger.debug(f"Returning cached weather for {location}")
            return cached_weather

        # Try getting latest from database
        try:
            # Get weather data from the last 3 hours
            three_hours_ago = timezone.now() - timedelta(hours=3)
            latest_weather = WeatherData.objects.filter(
                location__iexact=location,
                timestamp__gte=three_hours_ago
            ).latest('timestamp')
            
            # Cache and return the result
            cache.set(cache_key, latest_weather, CURRENT_WEATHER_CACHE_DURATION)
            return latest_weather
            
        except WeatherData.DoesNotExist:
            # Data not found or too old, fetch from API
            return WeatherService._fetch_and_store_current_weather(location)
    
    @staticmethod
    def get_forecast(location, days=7):
        """
        Get weather forecast for a location.
        First tries cache, then database, then external API.
        """
        # Try getting from cache first
        cache_key = FORECAST_CACHE_KEY.format(location=location)
        cached_forecast = cache.get(cache_key)
        if cached_forecast:
            logger.debug(f"Returning cached forecast for {location}")
            return cached_forecast

        # Try getting from database
        today = timezone.now().date()
        end_date = today + timedelta(days=days)
        
        forecasts = WeatherForecast.objects.filter(
            location__iexact=location,
            date__gte=today,
            date__lt=end_date
        ).order_by('date')
        
        # If we have all days needed, return from DB
        if forecasts.count() == days:
            cache.set(cache_key, list(forecasts), FORECAST_CACHE_DURATION)
            return forecasts
        
        # Otherwise fetch from API
        return WeatherService._fetch_and_store_forecast(location, days)
    
    @staticmethod
    def _fetch_and_store_current_weather(location):
        """Fetch current weather from external API and store in database"""
        try:
            # In a real app, you'd use settings.WEATHER_API_KEY
            api_key = getattr(settings, 'WEATHER_API_KEY', 'demo_key')
            
            # Example API call (replace with actual weather API)
            response = requests.get(
                f"https://api.weatherapi.com/v1/current.json",
                params={
                    'key': api_key,
                    'q': location,
                    'aqi': 'no'
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Weather API error: {response.status_code} - {response.text}")
                return None
                
            # Parse response (adjust according to your actual API)
            data = response.json()
            current = data['current']
            location_data = data['location']
            
            # Create new WeatherData object
            weather = WeatherData(
                location=location,
                latitude=location_data['lat'],
                longitude=location_data['lon'],
                elevation=location_data.get('elevation', 0),
                timestamp=timezone.now(),
                temperature=current['temp_c'],
                feels_like=current['feelslike_c'],
                condition=current['condition']['text'],
                wind_speed=current['wind_kph'],
                wind_direction=current['wind_dir'],
                precipitation=current['precip_mm'],
                humidity=current['humidity'],
                pressure=current['pressure_mb'],
                visibility=current['vis_km'] * 1000,  # convert to meters
                uv_index=current['uv']
            )
            
            # Save to database
            weather.save()
            
            # Cache the result
            cache_key = CURRENT_WEATHER_CACHE_KEY.format(location=location)
            cache.set(cache_key, weather, CURRENT_WEATHER_CACHE_DURATION)
            
            return weather
            
        except Exception as e:
            logger.exception(f"Error fetching weather data for {location}: {e}")
            return None
    
    @staticmethod
    def _fetch_and_store_forecast(location, days=7):
        """Fetch weather forecast from external API and store in database"""
        try:
            # In a real app, you'd use settings.WEATHER_API_KEY
            api_key = getattr(settings, 'WEATHER_API_KEY', 'demo_key')
            
            # Example API call
            response = requests.get(
                f"https://api.weatherapi.com/v1/forecast.json",
                params={
                    'key': api_key,
                    'q': location,
                    'days': days,
                    'aqi': 'no',
                    'alerts': 'no'
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Weather API error: {response.status_code} - {response.text}")
                return []
                
            # Parse response (adjust according to your actual API)
            data = response.json()
            forecast_days = data['forecast']['forecastday']
            location_data = data['location']
            
            # Delete existing forecasts for this period
            today = timezone.now().date()
            end_date = today + timedelta(days=days)
            WeatherForecast.objects.filter(
                location__iexact=location,
                date__gte=today,
                date__lt=end_date
            ).delete()
            
            # Create new forecast objects
            forecasts = []
            for day_data in forecast_days:
                day = day_data['day']
                astro = day_data['astro']
                
                forecast = WeatherForecast(
                    location=location,
                    date=day_data['date'],
                    min_temp=day['mintemp_c'],
                    max_temp=day['maxtemp_c'],
                    condition=day['condition']['text'],
                    precipitation_chance=day['daily_chance_of_rain'],
                    sunrise=datetime.strptime(astro['sunrise'], '%I:%M %p').time(),
                    sunset=datetime.strptime(astro['sunset'], '%I:%M %p').time()
                )
                forecast.save()
                forecasts.append(forecast)
            
            # Cache the result
            cache_key = FORECAST_CACHE_KEY.format(location=location)
            cache.set(cache_key, forecasts, FORECAST_CACHE_DURATION)
            
            return forecasts
            
        except Exception as e:
            logger.exception(f"Error fetching forecast data for {location}: {e}")
            return []
    
    @staticmethod
    def update_all_locations():
        """Update weather data for all locations we track"""
        # Get unique locations from existing data
        locations = set(WeatherData.objects.values_list('location', flat=True).distinct())
        locations.update(WeatherForecast.objects.values_list('location', flat=True).distinct())
        
        for location in locations:
            WeatherService._fetch_and_store_current_weather(location)
            WeatherService._fetch_and_store_forecast(location)
    
    @staticmethod
    def get_historical_weather(location, start_date, end_date=None):
        """Get historical weather data for a location within a date range"""
        if end_date is None:
            end_date = timezone.now()
            
        return WeatherData.objects.filter(
            location__iexact=location,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
    
    @staticmethod
    def get_mountain_weather(location, elevation):
        """
        Get weather data adjusted for high mountain elevations
        Uses a temperature lapse rate of approximately 0.65°C per 100m
        """
        # Get base weather data
        base_weather = WeatherService.get_current_weather(location)
        if not base_weather:
            return None
        
        # Calculate elevation difference
        elev_diff = elevation - base_weather.elevation
        
        # Apply lapse rate to temperature (0.65°C cooler per 100m of elevation)
        temp_adjustment = (elev_diff / 100) * 0.65
        adjusted_temp = base_weather.temperature - temp_adjustment
        adjusted_feels_like = base_weather.feels_like - temp_adjustment
        
        # Create an adjusted "virtual" weather object (but don't save to DB)
        adjusted_weather = WeatherData(
            location=f"{location} at {elevation}m",
            latitude=base_weather.latitude,
            longitude=base_weather.longitude,
            elevation=elevation,
            timestamp=base_weather.timestamp,
            temperature=int(round(adjusted_temp)),
            feels_like=int(round(adjusted_feels_like)),
            condition=base_weather.condition,
            wind_speed=base_weather.wind_speed,
            wind_direction=base_weather.wind_direction,
            precipitation=base_weather.precipitation,
            humidity=base_weather.humidity,
            pressure=int(base_weather.pressure - (elev_diff / 8)),  # Approximate pressure decrease
            visibility=base_weather.visibility,
            uv_index=min(11, base_weather.uv_index + (1 if elev_diff > 1000 else 0)),  # UV increases at altitude
        )
        
        return adjusted_weather