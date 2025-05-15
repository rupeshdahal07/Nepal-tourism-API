from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class TimestampedModel(models.Model):
    """Base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Destination(TimestampedModel):
    """Model for destinations (treks, cities, heritage sites, etc.)"""
    DESTINATION_TYPES = [
        ('city', 'City'),
        ('trek', 'Trek'),
        ('heritage', 'Heritage Site'),
        ('park', 'National Park'),
        ('cultural', 'cultural'),
        ('wildlife', 'wildlife'),
        ('leisure', 'leisure')
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('hard', 'Hard'),
    ]
    
    id = models.CharField(primary_key=True, max_length=50, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=DESTINATION_TYPES)
    region = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, blank=True, null=True)
    duration = models.PositiveIntegerField(blank=True, null=True, help_text="Duration in days")
    max_elevation = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    min_elevation = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    best_season = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    permits_required = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    highlights = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.type})"


class DestinationPhoto(models.Model):
    """Photos associated with destinations"""
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='destinations/')
    caption = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Photo for {self.destination.name}"


class Lodging(TimestampedModel):
    """Model for accommodation options"""
    LODGING_TYPES = [
        ('hotel', 'Hotel'),
        ('guesthouse', 'Guesthouse'),
        ('teahouse', 'Teahouse'),
        ('lodge', 'Lodge'),
    ]
    
    id = models.CharField(primary_key=True, max_length=50, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=LODGING_TYPES)
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT, related_name='lodgings', null=True, blank=True)
    place = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    min_price = models.PositiveIntegerField(help_text="Minimum price in NPR")
    max_price = models.PositiveIntegerField(help_text="Maximum price in NPR")
    rating = models.DecimalField(max_digits=3, decimal_places=1, 
                                validators=[MinValueValidator(0), MaxValueValidator(5)],
                                blank=True, null=True)
    amenities = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    booking_link = models.URLField(blank=True)
    availability = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.type} in {self.place})"


class Room(models.Model):
    """Room types available in lodging options"""
    lodging = models.ForeignKey(Lodging, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.CharField(max_length=50)
    price = models.PositiveIntegerField(help_text="Price in NPR")
    capacity = models.PositiveIntegerField(default=2)
    amenities = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    
    def __str__(self):
        return f"{self.room_type} at {self.lodging.name}"


class LodgingPhoto(models.Model):
    """Photos associated with lodging options"""
    lodging = models.ForeignKey(Lodging, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='lodgings/')
    caption = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Photo for {self.lodging.name}"


class Guide(TimestampedModel):
    """Model for trekking guides"""
    id = models.CharField(primary_key=True, max_length=50, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    license_id = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    languages = ArrayField(models.CharField(max_length=30))
    regions = ArrayField(models.CharField(max_length=50))
    experience_years = models.PositiveIntegerField()
    specialization = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, 
                                validators=[MinValueValidator(0), MaxValueValidator(5)],
                                blank=True, null=True)
    photo = models.ImageField(upload_to='guides/', blank=True, null=True)
    available = models.BooleanField(default=True)
    daily_rate = models.PositiveIntegerField(help_text="Daily rate in NPR")
    
    def __str__(self):
        return f"{self.name} (License: {self.license_id})"


class GuideReview(models.Model):
    """Reviews for guides"""
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for {self.guide.name} by {self.user_name}"


class Agency(TimestampedModel):
    """Model for trekking agencies"""
    id = models.CharField(primary_key=True, max_length=50, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    license_id = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    regions = ArrayField(models.CharField(max_length=50))
    services = ArrayField(models.CharField(max_length=50))
    rating = models.DecimalField(max_digits=3, decimal_places=1, 
                                validators=[MinValueValidator(0), MaxValueValidator(5)],
                                blank=True, null=True)
    logo = models.ImageField(upload_to='agencies/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} (License: {self.license_id})"


class AgencyReview(models.Model):
    """Reviews for agencies"""
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for {self.agency.name} by {self.user_name}"


class Permit(TimestampedModel):
    """Model for trekking permits"""
    id = models.CharField(primary_key=True, max_length=50, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.TextField()
    regions = ArrayField(models.CharField(max_length=50))
    required_documents = ArrayField(models.CharField(max_length=255))
    application_process = models.TextField()
    online_application = models.URLField(blank=True)
    validity = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name


class PermitFee(models.Model):
    """Fees for permits based on nationality"""
    NATIONALITY_TYPES = [
        ('Foreign', 'Foreign'),
        ('SAARC', 'SAARC Countries'),
        ('Nepali', 'Nepali'),
    ]
    
    permit = models.ForeignKey(Permit, on_delete=models.CASCADE, related_name='fees')
    nationality = models.CharField(max_length=20, choices=NATIONALITY_TYPES)
    amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default='NPR')
    
    class Meta:
        unique_together = ('permit', 'nationality')
    
    def __str__(self):
        return f"{self.permit.name} fee for {self.nationality}: {self.amount} {self.currency}"


class IssuingOffice(models.Model):
    """Offices that issue permits"""
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    hours = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    def __str__(self):
        return self.name


class PermitOffice(models.Model):
    """Many-to-many relationship between permits and issuing offices"""
    permit = models.ForeignKey(Permit, on_delete=models.CASCADE, related_name='issuing_offices')
    office = models.ForeignKey(IssuingOffice, on_delete=models.CASCADE, related_name='permits')
    
    class Meta:
        unique_together = ('permit', 'office')
    
    def __str__(self):
        return f"{self.permit.name} at {self.office.name}"


class Event(TimestampedModel):
    """Model for cultural events and festivals"""
    EVENT_TYPES = [
        ('cultural', 'Cultural'),
        ('religious', 'Religious'),
        ('adventure', 'Adventure'),
        ('food', 'Food'),
        ('music', 'Music'),
    ]
    
    id = models.CharField(primary_key=True, max_length=50, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    city = models.CharField(max_length=50)
    venue = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.TextField()
    significance = models.TextField(blank=True)
    activities = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class EventPhoto(models.Model):
    """Photos associated with events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='events/')
    caption = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Photo for {self.event.name}"


class EventLink(models.Model):
    """External links related to events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='links')
    title = models.CharField(max_length=100)
    url = models.URLField()
    
    def __str__(self):
        return f"{self.title} for {self.event.name}"


class TrailStatus(TimestampedModel):
    """Model for trail conditions and status"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('caution', 'Caution'),
        ('closed', 'Closed'),
    ]
    
    id = models.CharField(primary_key=True, max_length=50, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    region = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    source = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.name}: {self.status}"


class TrailSegment(models.Model):
    """Individual segments of a trail with specific conditions"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('caution', 'Caution'),
        ('closed', 'Closed'),
    ]
    
    trail = models.ForeignKey(TrailStatus, on_delete=models.CASCADE, related_name='conditions')
    segment = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = models.TextField()
    
    def __str__(self):
        return f"{self.segment} ({self.trail.name}): {self.status}"


class TrailAlert(models.Model):
    """Alerts associated with trail segments"""
    ALERT_TYPES = [
        ('landslide', 'Landslide'),
        ('snow', 'Snow'),
        ('flood', 'Flood'),
        ('bridge', 'Bridge Issue'),
        ('weather', 'Weather'),
        ('other', 'Other'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    segment = models.ForeignKey(TrailSegment, on_delete=models.CASCADE, related_name='alerts')
    type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    description = models.TextField()
    reported_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type} alert on {self.segment.segment} ({self.severity})"


class WeatherData(models.Model):
    """Weather data for locations"""
    location = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    elevation = models.IntegerField(help_text="Elevation in meters")
    timestamp = models.DateTimeField()
    temperature = models.IntegerField(help_text="Temperature in celsius")
    feels_like = models.IntegerField(help_text="Feels like temperature in celsius")
    condition = models.CharField(max_length=50)
    wind_speed = models.IntegerField(help_text="Wind speed in km/h")
    wind_direction = models.CharField(max_length=20)
    precipitation = models.DecimalField(max_digits=5, decimal_places=1, help_text="Precipitation in mm")
    humidity = models.IntegerField(help_text="Humidity percentage")
    pressure = models.IntegerField(help_text="Pressure in hPa")
    visibility = models.IntegerField(help_text="Visibility in meters")
    uv_index = models.IntegerField()
    
    def __str__(self):
        return f"Weather for {self.location} at {self.timestamp}"


class WeatherForecast(models.Model):
    """Weather forecast for locations"""
    location = models.CharField(max_length=100)
    date = models.DateField()
    min_temp = models.IntegerField(help_text="Minimum temperature in celsius")
    max_temp = models.IntegerField(help_text="Maximum temperature in celsius")
    condition = models.CharField(max_length=50)
    precipitation_chance = models.IntegerField(help_text="Precipitation chance in percentage")
    sunrise = models.TimeField()
    sunset = models.TimeField()
    
    class Meta:
        unique_together = ('location', 'date')
    
    def __str__(self):
        return f"Forecast for {self.location} on {self.date}"


class TourismStat(models.Model):
    """Tourism statistics"""
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)
    total_arrivals = models.IntegerField()
    year_over_year = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                        help_text="Year-over-year growth percentage")
    fastest_growing_market = models.CharField(max_length=50, blank=True)
    fastest_growing_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ('year', 'month')
    
    def __str__(self):
        if self.month:
            return f"Tourism stats for {self.month}/{self.year}: {self.total_arrivals} arrivals"
        return f"Tourism stats for {self.year}: {self.total_arrivals} arrivals"


class NationalityStat(models.Model):
    """Tourism statistics by nationality"""
    tourism_stat = models.ForeignKey(TourismStat, on_delete=models.CASCADE, related_name='nationality_breakdown')
    nationality = models.CharField(max_length=50)
    count = models.IntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        unique_together = ('tourism_stat', 'nationality')
    
    def __str__(self):
        return f"{self.nationality}: {self.count} ({self.percentage}%)"


class PurposeStat(models.Model):
    """Tourism statistics by purpose of visit"""
    tourism_stat = models.ForeignKey(TourismStat, on_delete=models.CASCADE, related_name='purpose_breakdown')
    purpose = models.CharField(max_length=50)
    count = models.IntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        unique_together = ('tourism_stat', 'purpose')
    
    def __str__(self):
        return f"{self.purpose}: {self.count} ({self.percentage}%)"


from django.contrib.auth import get_user_model
import secrets

User = get_user_model()

class APIKey(TimestampedModel):
    """API keys for accessing restricted endpoints"""
    TIER_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    key = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=100, )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys', null=True)
    email = models.EmailField()
    organization = models.CharField(max_length=100, blank=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now_add=True ,null=True, blank=True)
    
    def __str__(self):
        return f"API Key for {self.name} ({self.tier})"
    
    @classmethod
    def generate_key(cls):
        """Generate a secure random API key"""
        return secrets.token_hex(32)  # 64 character hex string