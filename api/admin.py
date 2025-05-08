from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Destination, DestinationPhoto, Lodging, LodgingPhoto, Room,
    Guide, GuideReview, Agency, AgencyReview, Permit, PermitFee,
    IssuingOffice, PermitOffice, Event, EventPhoto, EventLink, 
    TrailStatus, TrailSegment, TrailAlert, WeatherData, WeatherForecast, 
    TourismStat, NationalityStat, PurposeStat, APIKey
)


class DestinationPhotoInline(admin.TabularInline):
    model = DestinationPhoto
    extra = 1
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" />', obj.photo.url)
        return "No Image"


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'region', 'difficulty', 'duration']
    list_filter = ['type', 'region', 'difficulty']
    search_fields = ['name', 'description']
    inlines = [DestinationPhotoInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'type', 'region', 'description')
        }),
        ('Trek Details', {
            'fields': ('difficulty', 'duration', 'max_elevation', 'min_elevation', 
                      'best_season', 'permits_required', 'highlights')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
    )


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


class LodgingPhotoInline(admin.TabularInline):
    model = LodgingPhoto
    extra = 1
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" />', obj.photo.url)
        return "No Image"


@admin.register(Lodging)
class LodgingAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'place', 'min_price', 'max_price', 'rating', 'availability']
    list_filter = ['type', 'place', 'availability']
    search_fields = ['name', 'place']
    inlines = [RoomInline, LodgingPhotoInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'type', 'destination', 'place')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Pricing & Details', {
            'fields': ('min_price', 'max_price', 'rating', 'amenities', 'booking_link', 'availability')
        }),
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_type', 'lodging', 'price', 'capacity']
    list_filter = ['room_type', 'capacity']
    search_fields = ['room_type', 'lodging__name']


class GuideReviewInline(admin.TabularInline):
    model = GuideReview
    extra = 1


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_id', 'experience_years', 'daily_rate', 'rating', 'available']
    list_filter = ['languages', 'regions', 'available']
    search_fields = ['name', 'license_id']
    inlines = [GuideReviewInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'license_id', 'photo')
        }),
        ('Contact', {
            'fields': ('phone', 'email')
        }),
        ('Expertise', {
            'fields': ('languages', 'regions', 'experience_years', 'specialization')
        }),
        ('Status', {
            'fields': ('rating', 'available', 'daily_rate')
        }),
    )
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" />', obj.photo.url)
        return "No Image"


class AgencyReviewInline(admin.TabularInline):
    model = AgencyReview
    extra = 1


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_id', 'email', 'rating']
    list_filter = ['regions', 'services']
    search_fields = ['name', 'license_id', 'address']
    inlines = [AgencyReviewInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'license_id', 'logo')
        }),
        ('Contact', {
            'fields': ('address', 'phone', 'email', 'website')
        }),
        ('Services', {
            'fields': ('regions', 'services', 'rating')
        }),
    )
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="150" />', obj.logo.url)
        return "No Image"


class PermitFeeInline(admin.TabularInline):
    model = PermitFee
    extra = 1


class PermitOfficeInline(admin.TabularInline):
    model = PermitOffice
    extra = 1


@admin.register(Permit)
class PermitAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_regions', 'validity']
    search_fields = ['name', 'description']
    inlines = [PermitFeeInline, PermitOfficeInline]
    
    def get_regions(self, obj):
        return ", ".join(obj.regions)
    get_regions.short_description = 'Regions'


@admin.register(IssuingOffice)
class IssuingOfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'hours', 'phone']
    search_fields = ['name', 'address']


class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 1
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" />', obj.photo.url)
        return "No Image"


class EventLinkInline(admin.TabularInline):
    model = EventLink
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'city', 'start_date', 'end_date']
    list_filter = ['type', 'city', 'start_date']
    search_fields = ['name', 'description', 'city']
    inlines = [EventPhotoInline, EventLinkInline]
    date_hierarchy = 'start_date'


class TrailSegmentInline(admin.TabularInline):
    model = TrailSegment
    extra = 1


class TrailAlertInline(admin.TabularInline):
    model = TrailAlert
    extra = 0


@admin.register(TrailSegment)
class TrailSegmentAdmin(admin.ModelAdmin):
    list_display = ['segment', 'trail', 'status']
    list_filter = ['status', 'trail']
    search_fields = ['segment', 'trail__name']
    inlines = [TrailAlertInline]


@admin.register(TrailStatus)
class TrailStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'status', 'source']
    list_filter = ['status', 'region']
    search_fields = ['name', 'region']
    inlines = [TrailSegmentInline]


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['location', 'timestamp', 'temperature', 'condition', 'wind_speed']
    list_filter = ['location', 'condition']
    search_fields = ['location']
    date_hierarchy = 'timestamp'


@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    list_display = ['location', 'date', 'min_temp', 'max_temp', 'condition', 'precipitation_chance']
    list_filter = ['location', 'condition']
    search_fields = ['location']
    date_hierarchy = 'date'


class NationalityStatInline(admin.TabularInline):
    model = NationalityStat
    extra = 1


class PurposeStatInline(admin.TabularInline):
    model = PurposeStat
    extra = 1


@admin.register(TourismStat)
class TourismStatAdmin(admin.ModelAdmin):
    list_display = ['get_period', 'total_arrivals', 'year_over_year']
    list_filter = ['year']
    search_fields = ['year']
    inlines = [NationalityStatInline, PurposeStatInline]
    
    def get_period(self, obj):
        if obj.month:
            return f"{obj.month}/{obj.year}"
        return f"{obj.year}"
    get_period.short_description = 'Period'


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'organization', 'tier', 'is_active', 'created_at', 'last_used']
    list_filter = ['tier', 'is_active']
    search_fields = ['name', 'email', 'organization']
    readonly_fields = ['key', 'created_at', 'updated_at', 'last_used']
    fieldsets = (
        ('User Information', {
            'fields': ('name', 'email', 'organization')
        }),
        ('API Key Details', {
            'fields': ('key', 'tier', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_used')
        }),
    )