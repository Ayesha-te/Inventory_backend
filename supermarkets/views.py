from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum
from .models import (
    Supermarket, SupermarketStaff, SupermarketSettings,
    SupermarketInvitation, SupermarketAnalytics
)
from .serializers import (
    SupermarketListSerializer, SupermarketDetailSerializer,
    SupermarketCreateUpdateSerializer, SupermarketStaffSerializer,
    SupermarketSettingsSerializer, SupermarketInvitationSerializer,
    SupermarketAnalyticsSerializer, SupermarketStatsSerializer,
    InvitationResponseSerializer
)


class SupermarketListCreateView(generics.ListCreateAPIView):
    """List and create supermarkets"""
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'is_sub_store', 'pos_system_type']
    ordering = ['-registration_date']
    
    def get_queryset(self):
        return Supermarket.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SupermarketCreateUpdateSerializer
        return SupermarketListSerializer


class SupermarketDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete supermarkets"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Supermarket.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SupermarketCreateUpdateSerializer
        return SupermarketDetailSerializer


class SupermarketStaffListView(generics.ListCreateAPIView):
    """List and create supermarket staff"""
    
    serializer_class = SupermarketStaffSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active']
    ordering = ['-created_at']
    
    def get_queryset(self):
        supermarket_id = self.kwargs.get('supermarket_id')
        return SupermarketStaff.objects.filter(
            supermarket_id=supermarket_id,
            supermarket__owner=self.request.user
        )


class SupermarketSettingsView(generics.RetrieveUpdateAPIView):
    """Retrieve and update supermarket settings"""
    
    serializer_class = SupermarketSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        supermarket_id = self.kwargs.get('supermarket_id')
        supermarket = Supermarket.objects.get(
            id=supermarket_id,
            owner=self.request.user
        )
        settings, created = SupermarketSettings.objects.get_or_create(
            supermarket=supermarket
        )
        return settings


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def supermarket_stats(request):
    """Get supermarket statistics"""
    user = request.user
    supermarkets = Supermarket.objects.filter(owner=user)
    
    stats = {
        'total_supermarkets': supermarkets.count(),
        'total_sub_stores': supermarkets.filter(is_sub_store=True).count(),
        'verified_supermarkets': supermarkets.filter(is_verified=True).count(),
        'active_supermarkets': supermarkets.filter(is_active=True).count(),
        'total_staff': SupermarketStaff.objects.filter(
            supermarket__owner=user,
            is_active=True
        ).count(),
        'pos_enabled_count': supermarkets.filter(pos_system_enabled=True).count(),
        'total_products_across_all': sum(s.total_products for s in supermarkets),
        'total_inventory_value_across_all': sum(s.total_inventory_value for s in supermarkets)
    }
    
    serializer = SupermarketStatsSerializer(stats)
    return Response(serializer.data)