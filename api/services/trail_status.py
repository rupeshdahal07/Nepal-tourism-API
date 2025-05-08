import requests
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ..models import TrailStatus, TrailSegment, TrailAlert

logger = logging.getLogger(__name__)

# Cache keys and durations
TRAIL_STATUS_CACHE_KEY = "trail_status_{trail_id}"
ALL_TRAILS_CACHE_KEY = "all_trails_status"
TRAIL_STATUS_CACHE_DURATION = 60 * 60 * 6  # 6 hours
TRAILS_WITH_ALERTS_CACHE_KEY = "trails_with_alerts"

class TrailStatusService:
    """Service for retrieving and managing trail status information"""
    
    @staticmethod
    def get_all_trails():
        """
        Get status for all trails
        First tries cache, then database
        """
        # Try getting from cache first
        cached_trails = cache.get(ALL_TRAILS_CACHE_KEY)
        if cached_trails:
            logger.debug("Returning cached trail status list")
            return cached_trails
            
        # Get from database and cache
        trails = TrailStatus.objects.all().prefetch_related(
            'conditions', 
            'conditions__alerts'
        )
        
        # Cache for future requests
        cache.set(ALL_TRAILS_CACHE_KEY, list(trails), TRAIL_STATUS_CACHE_DURATION)
        
        return trails
    
    @staticmethod
    def get_trail_status(trail_id):
        """
        Get detailed status for a specific trail
        First tries cache, then database
        """
        # Try getting from cache first
        cache_key = TRAIL_STATUS_CACHE_KEY.format(trail_id=trail_id)
        cached_trail = cache.get(cache_key)
        if cached_trail:
            logger.debug(f"Returning cached status for trail {trail_id}")
            return cached_trail
            
        # Get from database and cache
        try:
            trail = TrailStatus.objects.prefetch_related(
                'conditions', 
                'conditions__alerts'
            ).get(pk=trail_id)
            
            # Cache for future requests
            cache.set(cache_key, trail, TRAIL_STATUS_CACHE_DURATION)
            
            return trail
        except TrailStatus.DoesNotExist:
            logger.warning(f"Trail with ID {trail_id} not found")
            return None
    
    @staticmethod
    def get_trails_with_alerts():
        """Get all trails that have active alerts"""
        # Try getting from cache first
        cached_trails = cache.get(TRAILS_WITH_ALERTS_CACHE_KEY)
        if cached_trails:
            logger.debug("Returning cached trails with alerts")
            return cached_trails
            
        # Get from database
        trails_with_alerts = TrailStatus.objects.filter(
            conditions__alerts__isnull=False
        ).distinct().prefetch_related(
            'conditions', 
            'conditions__alerts'
        )
        
        # Cache for future requests
        cache.set(TRAILS_WITH_ALERTS_CACHE_KEY, list(trails_with_alerts), TRAIL_STATUS_CACHE_DURATION)
        
        return trails_with_alerts
    
    @staticmethod
    def get_trails_by_region(region):
        """Get all trails in a specific region"""
        return TrailStatus.objects.filter(
            region__iexact=region
        ).prefetch_related(
            'conditions', 
            'conditions__alerts'
        )
    
    @staticmethod
    def get_trails_by_status(status):
        """Get all trails with a specific status (open, caution, closed)"""
        return TrailStatus.objects.filter(
            status=status
        ).prefetch_related(
            'conditions', 
            'conditions__alerts'
        )
    
    @staticmethod
    def update_trail_status(trail_id, new_status, source=None):
        """Update the status of a trail"""
        try:
            trail = TrailStatus.objects.get(pk=trail_id)
            trail.status = new_status
            
            if source:
                trail.source = source
                
            trail.save()
            
            # Invalidate caches
            cache.delete(TRAIL_STATUS_CACHE_KEY.format(trail_id=trail_id))
            cache.delete(ALL_TRAILS_CACHE_KEY)
            cache.delete(TRAILS_WITH_ALERTS_CACHE_KEY)
            
            return trail
        except TrailStatus.DoesNotExist:
            logger.warning(f"Cannot update status: Trail with ID {trail_id} not found")
            return None
    
    @staticmethod
    def add_trail_alert(segment_id, alert_type, severity, description):
        """Add a new alert to a trail segment"""
        try:
            segment = TrailSegment.objects.get(pk=segment_id)
            
            alert = TrailAlert.objects.create(
                segment=segment,
                type=alert_type,
                severity=severity,
                description=description,
                reported_at=timezone.now()
            )
            
            # Update the segment status based on alert severity
            if severity == 'high':
                segment.status = 'closed'
            elif severity == 'medium' and segment.status != 'closed':
                segment.status = 'caution'
                
            segment.save()
            
            # Update the overall trail status
            trail = segment.trail
            if severity == 'high':
                trail.status = 'closed'
            elif severity == 'medium' and trail.status == 'open':
                trail.status = 'caution'
                
            trail.save()
            
            # Invalidate caches
            cache.delete(TRAIL_STATUS_CACHE_KEY.format(trail_id=trail.id))
            cache.delete(ALL_TRAILS_CACHE_KEY)
            cache.delete(TRAILS_WITH_ALERTS_CACHE_KEY)
            
            return alert
        except TrailSegment.DoesNotExist:
            logger.warning(f"Cannot add alert: Segment with ID {segment_id} not found")
            return None
    
    @staticmethod
    def remove_trail_alert(alert_id):
        """Remove a trail alert when it's no longer relevant"""
        try:
            alert = TrailAlert.objects.get(pk=alert_id)
            segment = alert.segment
            trail = segment.trail
            
            # Delete the alert
            alert.delete()
            
            # Recalculate segment status based on remaining alerts
            remaining_alerts = segment.alerts.all()
            if not remaining_alerts.exists():
                segment.status = 'open'
            elif not remaining_alerts.filter(severity='high').exists():
                if remaining_alerts.filter(severity='medium').exists():
                    segment.status = 'caution'
                else:
                    segment.status = 'open'
            
            segment.save()
            
            # Recalculate trail status based on all segments
            segments = trail.conditions.all()
            if segments.filter(status='closed').exists():
                trail.status = 'closed'
            elif segments.filter(status='caution').exists():
                trail.status = 'caution'
            else:
                trail.status = 'open'
                
            trail.save()
            
            # Invalidate caches
            cache.delete(TRAIL_STATUS_CACHE_KEY.format(trail_id=trail.id))
            cache.delete(ALL_TRAILS_CACHE_KEY)
            cache.delete(TRAILS_WITH_ALERTS_CACHE_KEY)
            
            return True
        except TrailAlert.DoesNotExist:
            logger.warning(f"Cannot remove alert: Alert with ID {alert_id} not found")
            return False
    
    @staticmethod
    def get_alert_history(trail_id, days=30):
        """Get alert history for a trail over a specified period"""
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            alerts = TrailAlert.objects.filter(
                segment__trail__id=trail_id,
                reported_at__gte=cutoff_date
            ).order_by('-reported_at')
            
            return alerts
        except Exception as e:
            logger.error(f"Error retrieving alert history: {e}")
            return []
    
    @staticmethod
    def import_trail_updates_from_external_source(source_url=None):
        """Import trail status updates from external sources"""
        try:
            # If no source URL provided, use the one from settings
            if not source_url:
                source_url = getattr(settings, 'TRAIL_STATUS_API_URL', None)
                
            if not source_url:
                logger.error("No trail status source URL provided or configured")
                return False
            
            # Example of fetching from external source
            response = requests.get(source_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"External API error: {response.status_code} - {response.text}")
                return False
                
            data = response.json()
            
            # Process the imported data
            for trail_data in data.get('trails', []):
                try:
                    trail_name = trail_data.get('name')
                    region = trail_data.get('region')
                    status = trail_data.get('status')
                    
                    # Find or create the trail
                    trail, created = TrailStatus.objects.update_or_create(
                        name=trail_name,
                        region=region,
                        defaults={
                            'status': status,
                            'source': f"Imported from {source_url} on {timezone.now().strftime('%Y-%m-%d')}"
                        }
                    )
                    
                    # Update segments
                    for segment_data in trail_data.get('segments', []):
                        segment_name = segment_data.get('name')
                        segment_status = segment_data.get('status')
                        segment_description = segment_data.get('description', '')
                        
                        segment, created = TrailSegment.objects.update_or_create(
                            trail=trail,
                            segment=segment_name,
                            defaults={
                                'status': segment_status,
                                'description': segment_description
                            }
                        )
                        
                        # Handle alerts for this segment
                        for alert_data in segment_data.get('alerts', []):
                            # Create only if it doesn't exist with same description
                            TrailAlert.objects.get_or_create(
                                segment=segment,
                                type=alert_data.get('type', 'other'),
                                severity=alert_data.get('severity', 'medium'),
                                description=alert_data.get('description', '')
                            )
                except Exception as segment_error:
                    logger.error(f"Error processing trail segment: {segment_error}")
                    continue
            
            # Invalidate all caches
            cache.delete(ALL_TRAILS_CACHE_KEY)
            cache.delete(TRAILS_WITH_ALERTS_CACHE_KEY)
            
            return True
            
        except Exception as e:
            logger.exception(f"Error importing trail updates: {e}")
            return False