from rest_framework import serializers
from .models import POSSystem, POSIntegration, POSSyncLog


class POSSystemSerializer(serializers.ModelSerializer):
    """Serializer for POS systems"""
    
    class Meta:
        model = POSSystem
        fields = [
            'id', 'name', 'pos_type', 'api_endpoint', 'api_version',
            'documentation_url', 'is_active'
        ]


class POSIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for integrations (POS, Channels, Couriers)"""
    
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)
    pos_system_name = serializers.CharField(source='pos_system.name', read_only=True)
    
    class Meta:
        model = POSIntegration
        fields = [
            'id', 'supermarket', 'supermarket_name', 'pos_system', 'pos_system_name', 'kind',
            'api_key', 'api_secret', 'store_id',
            'oauth_client_id', 'oauth_client_secret', 'refresh_token', 'region', 'sandbox',
            'auto_sync_enabled', 'sync_interval', 'sync_orders', 'sync_products', 'sync_inventory', 'sync_prices',
            'status', 'last_sync', 'last_error', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'api_secret': {'write_only': True},
            'oauth_client_secret': {'write_only': True},
            'refresh_token': {'write_only': True},
        }
    
    def validate_supermarket(self, value):
        """Validate supermarket ownership"""
        if value.owner != self.context['request'].user:
            raise serializers.ValidationError("You don't have permission to create integration for this supermarket")
        return value


class POSSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for POS sync logs"""
    
    supermarket_name = serializers.CharField(source='pos_integration.supermarket.name', read_only=True)
    pos_system_name = serializers.CharField(source='pos_integration.pos_system.name', read_only=True)
    
    class Meta:
        model = POSSyncLog
        fields = [
            'id', 'pos_integration', 'supermarket_name', 'pos_system_name',
            'sync_type', 'status', 'total_items', 'successful_items', 'failed_items',
            'error_message', 'sync_details', 'started_at', 'completed_at',
            'duration', 'created_at'
        ]