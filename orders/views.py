from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from .models import Order, Warehouse, RMA
from .serializers import OrderSerializer, WarehouseSerializer, RMASerializer


class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all().select_related('supermarket', 'assigned_warehouse').prefetch_related('items')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'supermarket', 'channel', 'courier', 'payment_status']
    search_fields = ['customer_name', 'customer_email', 'customer_phone', 'external_order_id']
    ordering_fields = ['created_at', 'updated_at', 'total_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        # Scope to the authenticated user's supermarkets
        return qs.filter(supermarket__owner=self.request.user)

    def perform_create(self, serializer):
        order = serializer.save(created_by=self.request.user)
        # Auto-assign nearest warehouse if not set and shipping address present
        if not order.assigned_warehouse:
            order.assigned_warehouse = assign_nearest_warehouse(order)
            order.save(update_fields=['assigned_warehouse'])


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all().select_related('supermarket', 'assigned_warehouse').prefetch_related('items')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(supermarket__owner=self.request.user)


class WarehouseListCreateView(generics.ListCreateAPIView):
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['supermarket']

    def get_queryset(self):
        return Warehouse.objects.filter(supermarket__owner=self.request.user)


class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Warehouse.objects.filter(supermarket__owner=self.request.user)


class RMAListCreateView(generics.ListCreateAPIView):
    serializer_class = RMASerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RMA.objects.filter(order__supermarket__owner=self.request.user)


class RMADetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RMASerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RMA.objects.filter(order__supermarket__owner=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_warehouse(request, pk):
    """Manually assign a warehouse to an order."""
    try:
        order = Order.objects.get(pk=pk, supermarket__owner=request.user)
    except Order.DoesNotExist:
        return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    warehouse_id = request.data.get('warehouse')
    try:
        wh = Warehouse.objects.get(pk=warehouse_id, supermarket__owner=request.user)
    except Warehouse.DoesNotExist:
        return Response({'detail': 'Invalid warehouse'}, status=status.HTTP_400_BAD_REQUEST)

    order.assigned_warehouse = wh
    order.save(update_fields=['assigned_warehouse'])
    return Response(OrderSerializer(order).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_label(request, pk):
    """Create shipment: generate AWB/label based on courier. Mocked provider integration for now."""
    try:
        order = Order.objects.get(pk=pk, supermarket__owner=request.user)
    except Order.DoesNotExist:
        return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    courier = request.data.get('courier')
    if courier not in ['DPD', 'YODEL', 'CITYSPRINT', 'COLLECTPLUS', 'TUFFNELLS']:
        return Response({'detail': 'Unsupported courier'}, status=status.HTTP_400_BAD_REQUEST)

    # Mocked AWB/tracking generation; integrate real APIs later
    order.courier = courier
    order.courier_awb = f"{courier}-AWB-{str(order.id)[:8]}"
    order.tracking_id = f"{courier}-TRK-{str(order.id)[:8]}"
    order.shipping_label_url = f"https://labels.example.com/{order.tracking_id}.pdf"
    order.shipping_status = 'LABEL_CREATED'
    order.status = 'PROCESSING'
    order.save(update_fields=['courier', 'courier_awb', 'tracking_id', 'shipping_label_url', 'shipping_status', 'status'])

    return Response(OrderSerializer(order).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_orders(request):
    """
    Import orders from external channels.
    Body: { channel, supermarket, orders: [ { external_order_id, customer_name/email/phone,
            ship_* fields, payment_method, items: [{ product, quantity, unit_price }] } ] }
    """
    channel = request.data.get('channel')
    supermarket = request.data.get('supermarket')
    orders = request.data.get('orders', [])
    if channel not in ['SHOPIFY', 'AMAZON', 'DARAZ', 'POS', 'MANUAL', 'WEBSITE']:
        return Response({'detail': 'Invalid channel'}, status=status.HTTP_400_BAD_REQUEST)
    if not supermarket:
        return Response({'detail': 'supermarket required'}, status=status.HTTP_400_BAD_REQUEST)

    created, updated = 0, 0
    results = []
    for data in orders:
        ext_id = data.get('external_order_id')
        defaults = {
            'supermarket_id': supermarket,
            'channel': channel,
            'customer_name': data.get('customer_name'),
            'customer_email': data.get('customer_email'),
            'customer_phone': data.get('customer_phone'),
            'ship_name': data.get('ship_name'),
            'ship_phone': data.get('ship_phone'),
            'ship_address_line1': data.get('ship_address_line1'),
            'ship_address_line2': data.get('ship_address_line2'),
            'ship_city': data.get('ship_city'),
            'ship_postcode': data.get('ship_postcode'),
            'ship_country': data.get('ship_country'),
            'payment_method': data.get('payment_method') or 'COD',
            'status': data.get('status') or 'PENDING',
            'notes': data.get('notes'),
            'raw_payload': data.get('raw_payload'),
        }
        if ext_id:
            obj, created_flag = Order.objects.update_or_create(
                external_order_id=ext_id, supermarket_id=supermarket, defaults=defaults
            )
            action = 'created' if created_flag else 'updated'
        else:
            obj = Order.objects.create(**defaults)
            action = 'created'
        # items
        items = data.get('items') or []
        if items:
            obj.items.all().delete()
            total = 0
            for it in items:
                oi = obj.items.create(product_id=it['product'], quantity=it['quantity'], unit_price=it['unit_price'])
                total += oi.total_price
            obj.total_amount = total
            obj.save(update_fields=['total_amount'])
        created += (1 if action == 'created' else 0)
        updated += (1 if action == 'updated' else 0)
        results.add if False else None  # placeholder to avoid linter
    return Response({'created': created, 'updated': updated})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def tracking_update(request, pk):
    """Update shipping status from courier webhook or manual trigger."""
    try:
        order = Order.objects.get(pk=pk, supermarket__owner=request.user)
    except Order.DoesNotExist:
        return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    status_map = {'IN_TRANSIT': 'IN_TRANSIT', 'DELIVERED': 'DELIVERED', 'FAILED': 'FAILED'}
    shipping_status = request.data.get('shipping_status')
    if shipping_status not in status_map:
        return Response({'detail': 'Invalid shipping_status'}, status=status.HTTP_400_BAD_REQUEST)

    order.shipping_status = shipping_status
    if shipping_status == 'DELIVERED':
        order.status = 'DELIVERED'
        order.payment_status = order.payment_status or 'PAID'
    elif shipping_status == 'FAILED':
        order.status = 'CANCELLED'
    order.save(update_fields=['shipping_status', 'status', 'payment_status'])

    return Response(OrderSerializer(order).data)


def assign_nearest_warehouse(order: Order):
    """Naive nearest warehouse selection by same city/postcode if available; otherwise first active."""
    if not order.ship_city and not order.ship_postcode:
        return None
    qs = Warehouse.objects.filter(supermarket=order.supermarket, is_active=True)
    if order.ship_postcode:
        wh = qs.filter(postcode__iexact=order.ship_postcode).first()
        if wh:
            return wh
    if order.ship_city:
        wh = qs.filter(city__iexact=order.ship_city).first()
        if wh:
            return wh
    return qs.first()