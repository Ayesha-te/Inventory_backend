from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Supermarket, SupermarketStaff, SupermarketSettings,
    SupermarketInvitation, SupermarketAnalytics
)

User = get_user_model()


class SupermarketListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for supermarket lists"""
    
    total_products = serializers.ReadOnlyField()
    total_inventory_value = serializers.ReadOnlyField()
    low_stock_products_count = serializers.ReadOnlyField()
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Supermarket
        fields = [
            'id', 'name', 'address', 'phone', 'email', 'logo',
            'is_verified', 'is_sub_store', 'parent', 'parent_name', 'pos_system_type',
            'pos_system_enabled', 'registration_date', 'is_active',
            'total_products', 'total_inventory_value', 'low_stock_products_count',
            'owner_name'
        ]


class SupermarketDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for supermarket"""
    
    total_products = serializers.ReadOnlyField()
    total_inventory_value = serializers.ReadOnlyField()
    low_stock_products_count = serializers.ReadOnlyField()
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    sub_stores_count = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supermarket
        fields = [
            'id', 'name', 'description', 'address', 'phone', 'email',
            'website', 'business_license', 'tax_id', 'logo',
            'owner', 'owner_name', 'parent', 'parent_name', 'is_sub_store',
            'pos_system_type', 'pos_system_enabled', 'pos_sync_enabled',
            'last_pos_sync', 'timezone', 'currency', 'is_verified',
            'verification_date', 'registration_date', 'is_active',
            'total_products', 'total_inventory_value', 'low_stock_products_count',
            'sub_stores_count', 'staff_count'
        ]
        read_only_fields = [
            'owner', 'registration_date', 'is_verified', 'verification_date',
            'last_pos_sync'
        ]
    
    def get_sub_stores_count(self, obj):
        return obj.sub_stores.filter(is_active=True).count()
    
    def get_staff_count(self, obj):
        return obj.staff.filter(is_active=True).count()


class SupermarketCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating supermarkets"""
    
    class Meta:
        model = Supermarket
        fields = [
            'name', 'description', 'address', 'phone', 'email',
            'website', 'business_license', 'tax_id', 'logo',
            'parent', 'is_sub_store', 'pos_system_type',
            'pos_system_enabled', 'pos_api_key', 'pos_api_secret',
            'pos_store_id', 'pos_sync_enabled', 'timezone', 'currency'
        ]
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_parent(self, value):
        """Validate parent supermarket"""
        if value and value.owner != self.context['request'].user:
            raise serializers.ValidationError("You can only set your own supermarkets as parent.")
        return value


class SupermarketStaffSerializer(serializers.ModelSerializer):
    """Serializer for supermarket staff"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)
    
    class Meta:
        model = SupermarketStaff
        fields = [
            'id', 'supermarket', 'supermarket_name', 'user', 'user_name',
            'user_email', 'role', 'hire_date', 'salary', 'is_active',
            'can_manage_inventory', 'can_view_reports', 'can_manage_pos',
            'can_manage_staff', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SupermarketSettingsSerializer(serializers.ModelSerializer):
    """Serializer for supermarket settings"""
    
    class Meta:
        model = SupermarketSettings
        fields = [
            'low_stock_alert_enabled', 'expiry_alert_enabled', 'expiry_alert_days',
            'daily_report_enabled', 'weekly_report_enabled', 'monthly_report_enabled',
            'auto_reorder_enabled', 'default_min_stock_level', 'barcode_generation_enabled',
            'auto_sync_interval', 'sync_price_changes', 'sync_stock_changes',
            'sync_new_products', 'products_per_page', 'default_currency_symbol',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SupermarketInvitationSerializer(serializers.ModelSerializer):
    """Serializer for supermarket invitations"""
    
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = SupermarketInvitation
        fields = [
            'id', 'supermarket', 'supermarket_name', 'email', 'role',
            'invited_by', 'invited_by_name', 'token', 'status',
            'can_manage_inventory', 'can_view_reports', 'can_manage_pos',
            'can_manage_staff', 'created_at', 'expires_at', 'responded_at',
            'is_expired'
        ]
        read_only_fields = [
            'token', 'invited_by', 'created_at', 'expires_at', 'responded_at'
        ]
    
    def create(self, validated_data):
        validated_data['invited_by'] = self.context['request'].user
        from django.utils import timezone
        from datetime import timedelta
        validated_data['expires_at'] = timezone.now() + timedelta(days=7)
        return super().create(validated_data)


class SupermarketAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for supermarket analytics"""
    
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)
    
    class Meta:
        model = SupermarketAnalytics
        fields = [
            'id', 'supermarket', 'supermarket_name', 'date',
            'total_products', 'total_inventory_value', 'low_stock_products',
            'expired_products', 'expiring_soon_products', 'products_added',
            'products_removed', 'stock_adjustments', 'pos_sync_count',
            'pos_sync_errors', 'last_pos_sync', 'created_at'
        ]
        read_only_fields = ['created_at']


class SupermarketStatsSerializer(serializers.Serializer):
    """Serializer for supermarket statistics"""
    
    total_supermarkets = serializers.IntegerField()
    total_sub_stores = serializers.IntegerField()
    verified_supermarkets = serializers.IntegerField()
    active_supermarkets = serializers.IntegerField()
    total_staff = serializers.IntegerField()
    pos_enabled_count = serializers.IntegerField()
    total_products_across_all = serializers.IntegerField()
    total_inventory_value_across_all = serializers.DecimalField(max_digits=15, decimal_places=2)


class InvitationResponseSerializer(serializers.Serializer):
    """Serializer for responding to invitations"""
    
    RESPONSE_CHOICES = [
        ('ACCEPT', 'Accept'),
        ('DECLINE', 'Decline'),
    ]
    
    response = serializers.ChoiceField(choices=RESPONSE_CHOICES)
    hire_date = serializers.DateField(required=False)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)