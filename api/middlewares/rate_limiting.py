from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from api.models import APIKey  # Assuming APIKey model is in api.models

# Enhanced APIKey middleware for rate limiting
class APIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'free': {'requests': 100, 'period': 3600},  # 100 requests per hour
            'pro': {'requests': 1000, 'period': 3600},  # 1000 requests per hour
            'enterprise': None  # Unlimited
        }
        
    def __call__(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        if api_key and not request.path.startswith('/admin/'):
            try:
                key_object = APIKey.objects.get(key=api_key, is_active=True)
                # Update last used timestamp
                key_object.last_used = timezone.now()
                key_object.save(update_fields=['last_used'])
                
                # Check rate limit
                if key_object.tier != 'enterprise':
                    cache_key = f"api_usage_{api_key}"
                    usage = cache.get(cache_key, 0)
                    limit = self.rate_limits[key_object.tier]
                    
                    if usage >= limit['requests']:
                        return JsonResponse({
                            'error': 'Rate limit exceeded',
                            'detail': f"Your {key_object.tier} plan allows {limit['requests']} requests per hour."
                        }, status=429)
                    
                    # Increment usage counter
                    cache.set(cache_key, usage + 1, limit['period'])
                
                # Add API key info to request
                request.api_key = key_object
                
            except APIKey.DoesNotExist:
                return JsonResponse({'error': 'Invalid API key'}, status=401)
                
        return self.get_response(request)