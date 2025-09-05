from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_barcode = serializers.CharField(source='product.barcode', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_barcode', 'quantity', 'unit_price', 'total_price', 'created_at']
        read_only_fields = ['id', 'total_price', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'supermarket', 'supermarket_name', 'customer_name', 'customer_email', 'customer_phone',
            'status', 'total_amount', 'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']

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
        return instance