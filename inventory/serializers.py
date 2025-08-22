from rest_framework import serializers
from .models import (
    Category, Supplier, Product, ProductImage, StockMovement, 
    ProductAlert, Barcode, ProductReview
)
from .services import BarcodeService


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    
    full_name = serializers.ReadOnlyField()
    subcategories_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'parent', 'image', 'is_active',
            'full_name', 'subcategories_count', 'products_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_subcategories_count(self, obj):
        return obj.subcategories.filter(is_active=True).count()
    
    def get_products_count(self, obj):
        return obj.product_set.filter(is_active=True).count()


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for Supplier model"""
    
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_person', 'email', 'phone', 'address',
            'website', 'tax_id', 'payment_terms', 'is_active',
            'products_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.product_set.filter(is_active=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model"""
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class BarcodeSerializer(serializers.ModelSerializer):
    """Serializer for Barcode model"""
    
    class Meta:
        model = Barcode
        fields = ['id', 'code', 'barcode_type', 'is_primary', 'created_at']
        read_only_fields = ['created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    is_low_stock = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    is_expiring_soon = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    total_value = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'barcode', 'category_name', 'supplier_name',
            'quantity', 'min_stock_level', 'price', 'selling_price',
            'expiry_date', 'location', 'is_low_stock', 'is_expired',
            'is_expiring_soon', 'days_until_expiry', 'total_value',
            'image', 'is_active', 'added_date'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Product model"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # Computed fields
    is_low_stock = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    is_expiring_soon = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()
    total_value = serializers.ReadOnlyField()
    
    # Related data
    images = ProductImageSerializer(many=True, read_only=True)
    barcodes = BarcodeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'supplier', 'supplier_name', 'brand', 'barcode', 'sku',
            'cost_price', 'selling_price', 'price', 'quantity',
            'min_stock_level', 'max_stock_level', 'weight', 'dimensions',
            'origin', 'expiry_date', 'location', 'halal_certified',
            'halal_status', 'halal_certification_body', 'image_url', 'image',
            'supermarket', 'supermarket_name', 'created_by', 'created_by_name',
            'synced_with_pos', 'pos_id', 'last_pos_sync', 'is_active',
            'added_date', 'updated_date', 'is_low_stock', 'is_expired',
            'is_expiring_soon', 'days_until_expiry', 'profit_margin',
            'total_value', 'images', 'barcodes'
        ]
        read_only_fields = ['added_date', 'updated_date', 'created_by']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'supplier', 'brand',
            'barcode', 'sku', 'cost_price', 'selling_price', 'price',
            'quantity', 'min_stock_level', 'max_stock_level', 'weight',
            'dimensions', 'origin', 'expiry_date', 'location',
            'halal_certified', 'halal_status', 'halal_certification_body',
            'image_url', 'image', 'supermarket'
        ]
        extra_kwargs = {
            'barcode': {'required': False},  # Allow omitting barcode; it will be auto-generated
        }
    
    def validate_barcode(self, value):
        """Validate barcode uniqueness"""
        # If value is omitted or blank, let create() generate it
        if not value:
            return value
        if self.instance:
            # Update case - exclude current instance
            if Product.objects.exclude(id=self.instance.id).filter(barcode=value).exists():
                raise serializers.ValidationError("Product with this barcode already exists.")
        else:
            # Create case
            if Product.objects.filter(barcode=value).exists():
                raise serializers.ValidationError("Product with this barcode already exists.")
        return value
    
    def validate(self, attrs):
        """Validate product data"""
        if attrs.get('selling_price', 0) < attrs.get('cost_price', 0):
            raise serializers.ValidationError("Selling price cannot be less than cost price.")
        
        if attrs.get('max_stock_level') and attrs.get('min_stock_level', 0) > attrs['max_stock_level']:
            raise serializers.ValidationError("Minimum stock level cannot be greater than maximum stock level.")
        
        return attrs
    
    def create(self, validated_data):
        """Create product with automatic barcode generation"""
        # Generate barcode if not provided
        if not validated_data.get('barcode'):
            validated_data['barcode'] = BarcodeService.generate_barcode_number()
        
        # Set created_by if available in context
        if 'request' in self.context:
            validated_data['created_by'] = self.context['request'].user
        
        # Create product
        product = super().create(validated_data)
        
        # Create barcode record
        BarcodeService.create_product_barcode(product)
        
        return product


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for StockMovement model"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'movement_type', 'quantity',
            'previous_quantity', 'new_quantity', 'unit_cost', 'total_cost',
            'reference', 'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['created_at', 'created_by']


class ProductAlertSerializer(serializers.ModelSerializer):
    """Serializer for ProductAlert model"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = ProductAlert
        fields = [
            'id', 'product', 'product_name', 'alert_type', 'priority',
            'message', 'is_read', 'is_resolved', 'created_at',
            'resolved_at', 'resolved_by', 'resolved_by_name'
        ]
        read_only_fields = ['created_at']


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for ProductReview model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'product_name', 'user', 'user_name',
            'rating', 'title', 'comment', 'is_verified_purchase',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BulkProductUpdateSerializer(serializers.Serializer):
    """Serializer for bulk product updates"""
    
    product_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    updates = serializers.DictField()
    
    def validate_updates(self, value):
        """Validate update fields"""
        allowed_fields = [
            'category', 'supplier', 'price', 'selling_price', 'cost_price',
            'min_stock_level', 'max_stock_level', 'location', 'is_active'
        ]
        
        for field in value.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(f"Field '{field}' is not allowed for bulk update.")
        
        return value


class ProductStatsSerializer(serializers.Serializer):
    """Serializer for product statistics"""
    
    total_products = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    low_stock_count = serializers.IntegerField()
    expired_count = serializers.IntegerField()
    expiring_soon_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    categories_count = serializers.IntegerField()
    suppliers_count = serializers.IntegerField()
    average_profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2)