import django_filters
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category, Supplier


class ProductFilter(django_filters.FilterSet):
    """Filter for Product model"""
    
    # Basic filters
    name = django_filters.CharFilter(lookup_expr='icontains')
    barcode = django_filters.CharFilter(lookup_expr='exact')
    brand = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    supplier = django_filters.ModelChoiceFilter(queryset=Supplier.objects.all())
    
    # Price filters
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    cost_price_min = django_filters.NumberFilter(field_name='cost_price', lookup_expr='gte')
    cost_price_max = django_filters.NumberFilter(field_name='cost_price', lookup_expr='lte')
    selling_price_min = django_filters.NumberFilter(field_name='selling_price', lookup_expr='gte')
    selling_price_max = django_filters.NumberFilter(field_name='selling_price', lookup_expr='lte')
    
    # Quantity filters
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    
    # Date filters
    expiry_date_from = django_filters.DateFilter(field_name='expiry_date', lookup_expr='gte')
    expiry_date_to = django_filters.DateFilter(field_name='expiry_date', lookup_expr='lte')
    added_date_from = django_filters.DateTimeFilter(field_name='added_date', lookup_expr='gte')
    added_date_to = django_filters.DateTimeFilter(field_name='added_date', lookup_expr='lte')
    
    # Status filters
    is_active = django_filters.BooleanFilter()
    halal_certified = django_filters.BooleanFilter()
    synced_with_pos = django_filters.BooleanFilter()
    
    # Special filters
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    expired = django_filters.BooleanFilter(method='filter_expired')
    expiring_soon = django_filters.BooleanFilter(method='filter_expiring_soon')
    out_of_stock = django_filters.BooleanFilter(method='filter_out_of_stock')
    
    # Location filter
    location = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Product
        fields = [
            'name', 'barcode', 'brand', 'category', 'supplier',
            'price_min', 'price_max', 'cost_price_min', 'cost_price_max',
            'selling_price_min', 'selling_price_max', 'quantity_min', 'quantity_max',
            'expiry_date_from', 'expiry_date_to', 'added_date_from', 'added_date_to',
            'is_active', 'halal_certified', 'synced_with_pos', 'location',
            'low_stock', 'expired', 'expiring_soon', 'out_of_stock'
        ]
    
    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock"""
        if value:
            return queryset.filter(quantity__lte=models.F('min_stock_level'))
        return queryset
    
    def filter_expired(self, queryset, name, value):
        """Filter expired products"""
        if value:
            return queryset.filter(expiry_date__lt=timezone.now().date())
        return queryset
    
    def filter_expiring_soon(self, queryset, name, value):
        """Filter products expiring soon (within 7 days)"""
        if value:
            soon_date = timezone.now().date() + timedelta(days=7)
            return queryset.filter(
                expiry_date__lte=soon_date,
                expiry_date__gt=timezone.now().date()
            )
        return queryset
    
    def filter_out_of_stock(self, queryset, name, value):
        """Filter out of stock products"""
        if value:
            return queryset.filter(quantity=0)
        return queryset