from rest_framework import serializers
from .models import Order, OrderItem, Warehouse, RMA, RMAItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_barcode = serializers.CharField(source='product.barcode', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_barcode', 'quantity', 'unit_price', 'total_price', 'created_at']
        read_only_fields = ['id', 'total_price', 'created_at']


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'address_line1', 'address_line2', 'city', 'postcode', 'country', 'latitude', 'longitude', 'is_active']
        read_only_fields = ['id']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['from_status', 'to_status', 'note', 'changed_at']
        read_only_fields = ['changed_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)
    assigned_warehouse_detail = WarehouseSerializer(source='assigned_warehouse', read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'supermarket', 'supermarket_name',
            'channel', 'external_order_id',
            'customer_name', 'customer_email', 'customer_phone',
            'ship_name', 'ship_phone', 'ship_address_line1', 'ship_address_line2', 'ship_city', 'ship_postcode', 'ship_country',
            'assigned_warehouse', 'assigned_warehouse_detail',
            'status', 'payment_method', 'payment_status',
            'courier', 'courier_awb', 'tracking_id', 'shipping_label_url', 'shipping_status',
            'total_amount', 'notes', 'raw_payload', 'items', 'status_history', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at', 'assigned_warehouse_detail', 'status_history']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        total = 0
        for item in items_data:
            oi = OrderItem.objects.create(order=order, **item)
            total += oi.total_price
        order.total_amount = total
        order.save(update_fields=['total_amount'])
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        # Track status transition
        new_status = validated_data.get('status', instance.status)
        from_status = instance.status

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        if items_data is not None:
            instance.items.all().delete()
            total = 0
            for item in items_data:
                oi = OrderItem.objects.create(order=instance, **item)
                total += oi.total_price
            instance.total_amount = total

        instance.save()

        if new_status != from_status:
            OrderStatusHistory.objects.create(order=instance, from_status=from_status, to_status=new_status)

        return instance


class RMASerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = RMA
        fields = ['id', 'order', 'reason', 'status', 'refund_amount', 'restock', 'created_at', 'items']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        rma = RMA.objects.create(**validated_data)
        # Create RMA items from order items mapping
        for item in items_data:
            RMAItem.objects.create(rma=rma, order_item_id=item['order_item'], quantity=item.get('quantity', 1), condition=item.get('condition'))
        return rma