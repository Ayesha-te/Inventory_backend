from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import POSSystem, POSIntegration, POSSyncLog
from .serializers import POSSystemSerializer, POSIntegrationSerializer, POSSyncLogSerializer
from .services import POSService


class POSSystemListView(generics.ListAPIView):
    """List available POS systems"""
    
    queryset = POSSystem.objects.filter(is_active=True)
    serializer_class = POSSystemSerializer
    permission_classes = [permissions.IsAuthenticated]


class POSIntegrationListView(generics.ListAPIView):
    """List POS integrations for user's supermarkets"""
    
    serializer_class = POSIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return POSIntegration.objects.filter(
            supermarket__owner=self.request.user
        ).select_related('supermarket', 'pos_system')


class POSIntegrationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete POS integrations"""
    
    serializer_class = POSIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return POSIntegration.objects.filter(
            supermarket__owner=self.request.user
        )


class POSIntegrationCreateView(generics.CreateAPIView):
    """Create POS integration"""
    
    serializer_class = POSIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]


class POSSyncLogListView(generics.ListAPIView):
    """List sync logs for POS integration"""
    
    serializer_class = POSSyncLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sync_type', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        integration_id = self.kwargs.get('integration_id')
        return POSSyncLog.objects.filter(
            pos_integration_id=integration_id,
            pos_integration__supermarket__owner=self.request.user
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_sync(request, integration_id):
    """Trigger POS sync"""
    try:
        integration = POSIntegration.objects.get(
            id=integration_id,
            supermarket__owner=request.user
        )
        
        sync_type = request.data.get('sync_type', 'FULL')
        
        # Use POS service to trigger sync
        pos_service = POSService(integration)
        result = pos_service.trigger_sync(sync_type)
        
        return Response({
            'message': 'Sync triggered successfully',
            'sync_id': result.get('sync_id')
        })
        
    except POSIntegration.DoesNotExist:
        return Response({
            'error': 'POS integration not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_connection(request, integration_id):
    """Test POS connection"""
    try:
        integration = POSIntegration.objects.get(
            id=integration_id,
            supermarket__owner=request.user
        )
        
        pos_service = POSService(integration)
        result = pos_service.test_connection()
        
        return Response(result)
        
    except POSIntegration.DoesNotExist:
        return Response({
            'error': 'POS integration not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)