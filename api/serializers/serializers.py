from rest_framework import serializers
from ..models import (
    Destination, DestinationPhoto, Lodging, LodgingPhoto, Room,
    Guide, GuideReview, Agency, AgencyReview, Permit, PermitFee,
    IssuingOffice, Event, EventPhoto, EventLink, TrailStatus,
    TrailSegment, TrailAlert, WeatherData, WeatherForecast, 
    TourismStat, NationalityStat, PurposeStat
)


class DestinationPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationPhoto
        fields = ['photo', 'caption', 'is_primary']


class DestinationSerializer(serializers.ModelSerializer):
    photos = DestinationPhotoSerializer(many=True, read_only=True)
    coordinates = serializers.SerializerMethodField()
    elevation = serializers.SerializerMethodField()
    
    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'type', 'region', 'description', 'difficulty', 
            'duration', 'coordinates', 'elevation', 'best_season', 
            'permits_required', 'highlights', 'photos', 'created_at', 'updated_at'
        ]
    
    def get_coordinates(self, obj):
        if obj.latitude and obj.longitude:
            return {
                'lat': obj.latitude,
                'lng': obj.longitude
            }
        return None
    
    def get_elevation(self, obj):
        if obj.max_elevation or obj.min_elevation:
            return {
                'max': obj.max_elevation,
                'min': obj.min_elevation
            }
        return None


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['room_type', 'price', 'capacity', 'amenities']


class LodgingPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LodgingPhoto
        fields = ['photo', 'caption']


class LodgingSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    photos = LodgingPhotoSerializer(many=True, read_only=True)
    location = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    
    class Meta:
        model = Lodging
        fields = [
            'id', 'name', 'type', 'location', 'contact', 'price_range',
            'rooms', 'rating', 'amenities', 'booking_link', 'availability',
            'photos', 'created_at', 'updated_at'
        ]
    
    def get_location(self, obj):
        location_data = {
            'place': obj.place,
            'coordinates': {
                'lat': obj.latitude,
                'lng': obj.longitude
            }
        }
        
        if obj.destination:
            location_data['destination_id'] = obj.destination.id
            
        return location_data
    
    def get_contact(self, obj):
        contact_data = {}
        if obj.phone:
            contact_data['phone'] = obj.phone
        if obj.email:
            contact_data['email'] = obj.email
        if obj.website:
            contact_data['website'] = obj.website
        return contact_data
    
    def get_price_range(self, obj):
        return {
            'min': obj.min_price,
            'max': obj.max_price,
            'currency': 'NPR'
        }


class GuideReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuideReview
        fields = ['user_name', 'rating', 'comment', 'date']


class GuideSerializer(serializers.ModelSerializer):
    reviews = GuideReviewSerializer(many=True, read_only=True)
    contact = serializers.SerializerMethodField()
    daily_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Guide
        fields = [
            'id', 'name', 'license_id', 'contact', 'languages', 'regions',
            'experience_years', 'specialization', 'rating', 'reviews',
            'photo', 'available', 'daily_rate', 'created_at', 'updated_at'
        ]
    
    def get_contact(self, obj):
        contact_data = {}
        if obj.phone:
            contact_data['phone'] = obj.phone
        if obj.email:
            contact_data['email'] = obj.email
        return contact_data
    
    def get_daily_rate(self, obj):
        return {
            'amount': obj.daily_rate,
            'currency': 'NPR'
        }


class AgencyReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyReview
        fields = ['user_name', 'rating', 'comment', 'date']


class AgencySerializer(serializers.ModelSerializer):
    reviews = AgencyReviewSerializer(many=True, read_only=True)
    contact = serializers.SerializerMethodField()
    
    class Meta:
        model = Agency
        fields = [
            'id', 'name', 'license_id', 'address', 'contact', 'regions',
            'services', 'rating', 'reviews', 'logo', 'created_at', 'updated_at'
        ]
    
    def get_contact(self, obj):
        contact_data = {
            'phone': obj.phone,
            'email': obj.email,
        }
        if obj.website:
            contact_data['website'] = obj.website
        return contact_data


class IssuingOfficeSerializer(serializers.ModelSerializer):
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = IssuingOffice
        fields = ['name', 'address', 'coordinates', 'hours', 'phone', 'website']
    
    def get_coordinates(self, obj):
        return {
            'lat': obj.latitude,
            'lng': obj.longitude
        }


class PermitFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermitFee
        fields = ['nationality', 'amount', 'currency']


class PermitSerializer(serializers.ModelSerializer):
    fees = PermitFeeSerializer(many=True, read_only=True)
    issuing_offices = serializers.SerializerMethodField()
    
    class Meta:
        model = Permit
        fields = [
            'id', 'name', 'description', 'regions', 'fees', 'required_documents',
            'issuing_offices', 'application_process', 'online_application', 'validity',
            'created_at', 'updated_at'
        ]
    
    def get_issuing_offices(self, obj):
        permit_offices = obj.issuing_offices.all()
        serializer = IssuingOfficeSerializer(
            [po.office for po in permit_offices], many=True
        )
        return serializer.data


class EventLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLink
        fields = ['title', 'url']


class EventPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventPhoto
        fields = ['photo', 'caption']


class EventSerializer(serializers.ModelSerializer):
    photos = EventPhotoSerializer(many=True, read_only=True)
    links = EventLinkSerializer(many=True, read_only=True)
    location = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'type', 'start_date', 'end_date', 'location', 
            'description', 'significance', 'activities', 'photos', 'links',
            'created_at', 'updated_at'
        ]
    
    def get_location(self, obj):
        return {
            'city': obj.city,
            'venue': obj.venue,
            'coordinates': {
                'lat': obj.latitude,
                'lng': obj.longitude
            }
        }


class TrailAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrailAlert
        fields = ['type', 'severity', 'description']


class TrailSegmentSerializer(serializers.ModelSerializer):
    alerts = TrailAlertSerializer(many=True, read_only=True)
    
    class Meta:
        model = TrailSegment
        fields = ['segment', 'status', 'description', 'alerts']


class TrailStatusSerializer(serializers.ModelSerializer):
    conditions = TrailSegmentSerializer(many=True, read_only=True)
    last_updated = serializers.SerializerMethodField()  # Define as SerializerMethodField
    
    class Meta:
        model = TrailStatus
        fields = [
            'id', 'name', 'region', 'status', 'conditions', 'source',
            'last_updated'
        ]
    
    # This method should be outside of Meta class
    def get_last_updated(self, obj):
        return obj.updated_at


class WeatherForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherForecast
        fields = [
            'date', 'min_temp', 'max_temp', 'condition', 
            'precipitation_chance', 'sunrise', 'sunset'
        ]





class PurposeStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurposeStat
        fields = ['purpose', 'count', 'percentage']


class NationalityStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalityStat
        fields = ['nationality', 'count', 'percentage']


class TourismStatSerializer(serializers.ModelSerializer):
    nationality_breakdown = NationalityStatSerializer(many=True, read_only=True)
    purpose_breakdown = PurposeStatSerializer(many=True, read_only=True)
    period = serializers.SerializerMethodField()
    
    class Meta:
        model = TourismStat
        fields = [
            'year', 'month', 'total_arrivals', 'year_over_year',
            'fastest_growing_market', 'fastest_growing_percentage',
            'nationality_breakdown', 'purpose_breakdown', 'period'
        ]
    
    def get_period(self, obj):
        if obj.month:
            return f"{obj.month}/{obj.year}"
        return str(obj.year)
    


class WeatherDataSerializer(serializers.ModelSerializer):
    location_coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = WeatherData
        fields = [
            'location', 'location_coordinates', 'elevation', 'timestamp',
            'temperature', 'feels_like', 'condition', 'wind_speed', 
            'wind_direction', 'precipitation', 'humidity', 'pressure', 
            'visibility', 'uv_index'
        ]
    
    def get_location_coordinates(self, obj):
        return {
            'lat': obj.latitude,
            'lng': obj.longitude
        }