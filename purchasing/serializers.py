from rest_framework import serializers
from .models import SupplierProduct, PurchaseOrder, PurchaseOrderItem
from supermarkets.models import Supermarket
from inventory.models import Product
from inventory.services import ProductService
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid


class SupplierProductSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = SupplierProduct
        fields = [
            'id', 'supplier', 'supplier_name', 'product', 'product_name',
            'supplier_price', 'available_quantity', 'notes', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False, allow_null=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    # Accept free-text product_name for creation
    product_text = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'product', 'product_name', 'product_text', 'quantity', 'unit_price']

    def validate(self, attrs):
        # If neither product nor product_text provided, raise error
        product = attrs.get('product')
        product_text = (attrs.get('product_text') or '').strip()
        if not product and not product_text:
            raise serializers.ValidationError({'product': 'Provide product (ID) or product_text (name).'})
        return attrs


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)
    # Accept free-text supermarket name
    supermarket_text = serializers.CharField(write_only=True, required=False, allow_blank=True)

    items = PurchaseOrderItemSerializer(many=True)
    total_amount = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_name', 'supermarket', 'supermarket_name', 'supermarket_text',
            'status', 'expected_delivery_date', 'payment_terms', 'buyer_name', 'notes',
            'created_by', 'created_at', 'updated_at', 'items', 'total_amount'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'status']

    def _resolve_supermarket(self, data: dict, request=None):
        # Use provided supermarket id if present
        sm = data.get('supermarket')
        if sm:
            return sm
        # Else try supermarket_text (name)
        name = (data.pop('supermarket_text', '') or '').strip()
        if not name:
            return None
        # Try existing by name for this owner first
        qs = Supermarket.objects.filter(name__iexact=name)
        if request and request.user and request.user.is_authenticated:
            qs = qs.filter(owner=request.user)
        existing = qs.first()
        if existing:
            return existing
        # Auto-create minimal supermarket with sane defaults using current user as owner
        if not request or not request.user or not request.user.is_authenticated:
            # Cannot auto-create without an owner
            return None
        minimal = {
            'name': name,
            'description': '',
            'address': 'Unknown',
            'phone': '+10000000000',
            'email': f'auto-{uuid.uuid4().hex[:8]}@example.com',
            'owner': request.user,
            'is_sub_store': False,
            'is_verified': False,
        }
        try:
            sm = Supermarket.objects.create(**minimal)
            return sm
        except Exception:
            return None

    def _resolve_product(self, item: dict, supermarket):
        # Use provided product id if present
        pr = item.get('product')
        if pr:
            return pr
        # Else try product_text (name)
        name = (item.pop('product_text', '') or '').strip()
        if not name:
            return None
        # Try existing by name within same supermarket
        existing = Product.objects.filter(name__iexact=name, supermarket=supermarket).first()
        if existing:
            return existing
        # Auto-create minimal product in this supermarket
        minimal = {
            'name': name,
            'category': None,
            'supplier': None,
            'brand': None,
            'sku': None,
            'cost_price': Decimal('0.00'),
            'selling_price': Decimal('0.00'),
            'price': Decimal('0.00'),
            'quantity': 0,
            'min_stock_level': 0,
            'max_stock_level': None,
            'weight': None,
            'dimensions': None,
            'origin': None,
            'expiry_date': timezone.now().date() + timedelta(days=365),
            'location': None,
            'halal_certified': False,
            'halal_status': 'UNKNOWN',
            'halal_certification_body': None,
            'image_url': None,
            'image': None,
            'supermarket': supermarket,
            'created_by': None,
            'synced_with_pos': False,
            'pos_id': None,
            'last_pos_sync': None,
            'is_active': True,
        }
        product = ProductService.create_product_with_barcode(minimal)
        return product

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        # Resolve supermarket by name if only text provided
        sm_obj = self._resolve_supermarket(validated_data)
        if sm_obj is None and not validated_data.get('supermarket'):
            raise serializers.ValidationError({'supermarket': 'Supermarket not found. Please use an existing supermarket.'})
        if sm_obj:
            validated_data['supermarket'] = sm_obj

        # Auto-generate po_number if not provided: PO-YYYY-<n> (no zero padding)
        po_number = (validated_data.get('po_number') or '').strip()
        if not po_number:
            year = timezone.now().year
            prefix = f"PO-{year}-"
            existing = PurchaseOrder.objects.filter(po_number__startswith=prefix).values_list('po_number', flat=True)
            max_seq = 0
            for s in existing:
                try:
                    seq = int(str(s).split('-')[-1])
                    if seq > max_seq:
                        max_seq = seq
                except Exception:
                    continue
            validated_data['po_number'] = f"PO-{year}-{max_seq + 1}"

        request = self.context.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            validated_data['created_by'] = request.user

        po = PurchaseOrder.objects.create(**validated_data)

        for item in items_data:
            product_obj = self._resolve_product(item, validated_data['supermarket'])
            if product_obj is None and not item.get('product'):
                raise serializers.ValidationError({'items': [{'product': 'Product name is required.'}]})
            if product_obj:
                item['product'] = product_obj
            PurchaseOrderItem.objects.create(purchase_order=po, **item)
        return po

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        sm_obj = self._resolve_supermarket(validated_data)
        if sm_obj:
            validated_data['supermarket'] = sm_obj

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                product_obj = self._resolve_product(item, instance.supermarket)
                if product_obj:
                    item['product'] = product_obj
                PurchaseOrderItem.objects.create(purchase_order=instance, **item)
        return instance