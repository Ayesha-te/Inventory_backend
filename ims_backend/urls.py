"""
URL configuration for ims_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.apps import apps
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # App URLs
    path('api/accounts/', include('accounts.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/supermarkets/', include('supermarkets.urls')),
    # 'pos_integration' URLs are added conditionally below
    # path('api/files/', include('file_processing.urls')),    # Temporarily disabled
    # path('api/analytics/', include('analytics.urls')),      # Temporarily disabled
    path('api/notifications/', include('notifications.urls')),
    path('api/orders/', include('orders.urls')),
]

# Purchasing URLs
urlpatterns.append(path('api/purchasing/', include('purchasing.urls')))

# Conditionally include POS integration URLs only if the app is installed
if apps.is_installed('pos_integration'):
    urlpatterns.append(path('api/pos/', include('pos_integration.urls')))

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)