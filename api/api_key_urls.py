from django.urls import path
from .views import api_keys_view, generate_api_key, revoke_api_key

urlpatterns = [
    path('keys/', api_keys_view, name='api_keys'),
    path('keys/generate/', generate_api_key, name='generate_api_key'),
    path('keys/revoke/<str:key>/', revoke_api_key, name='revoke_api_key'),
]