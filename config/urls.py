from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views import destinations_page, weather_page, home_page, trail_page, lodgings_page, api_keys_view, generate_api_key, revoke_api_key, register_user, user_profile, change_password, password_reset, login_complete, token_verify

schema_view = get_schema_view(
    openapi.Info(
        title="Nepal Tourism API",
        default_version='v1',
        description="API for Nepal tourism information",
    ),
    public=True,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_page, name='home_page'),
    path('destinations', destinations_page, name='destinations_page'),
    path('weather/', weather_page, name='weather_page'),
    path('trails/', trail_page, name='trail_page' ),
    path('lodgings/', lodgings_page, name='lodgings_page'),
    # Token URLs
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # API key URLs
    path('api-keys/', api_keys_view, name='api_keys'),
    path('api-keys/generate/', generate_api_key, name='generate_api_key'),
    path('api-keys/revoke/<str:key>/', revoke_api_key, name='revoke_api_key'),
    
    # Authentication endpoints
    path('api/v1/register/', register_user, name='register'),
    path('api/v1/users/me/', user_profile, name='user_profile'),
    path('api/v1/change-password/', change_password, name='change_password'),
    path('api/v1/password-reset/', password_reset, name='password_reset'),
    path('login-complete/', login_complete, name='login_complete'),
    path('token-verify/', token_verify, name='token_verify'),
    
    
    # Documentation URLs - these should come BEFORE other API patterns
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API version URLs - these come LAST
    path('api/v1/', include('api.urls')),
    path('api/<str:version>/', include('api.urls')),
]
# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)