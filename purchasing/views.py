from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Min
from django.db import DatabaseError, IntegrityError
from .models import SupplierProduct, PurchaseOrder
from .serializers import SupplierProductSerializer, PurchaseOrderSerializer


class SupplierProductViewSet(viewsets.ModelViewSet):
    queryset = SupplierProduct.objects.select_related('supplier', 'product').all()
    serializer_class = SupplierProductSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['supplier', 'product', 'is_active']
    search_fields = ['supplier__name', 'product__name']
    ordering_fields = ['supplier_price', 'available_quantity']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('supplier', 'supermarket', 'created_by').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['supplier', 'supermarket', 'status']
    search_fields = ['supplier__name', 'notes', 'po_number']
    ordering_fields = ['created_at', 'updated_at', 'expected_delivery_date']

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except (DatabaseError, IntegrityError) as e:
            # Return JSON error instead of HTML debug page
            return Response(
                {
                    'detail': 'Database error while creating Purchase Order',
                    'error': str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        po = self.get_object()
        if po.status == 'RECEIVED':
            return Response({'detail': 'Already received'}, status=status.HTTP_400_BAD_REQUEST)
        po.status = 'RECEIVED'
        po.save(update_fields=['status'])
        return Response({'detail': 'Marked as received'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({
            'total': qs.count(),
            'received': qs.filter(status='RECEIVED').count(),
            'draft': qs.filter(status='DRAFT').count(),
            'sent': qs.filter(status='SENT').count(),
        })

    @action(detail=False, methods=['get'])
    def info(self, request):
        """Informational endpoint describing what a PO is and typical fields."""
        return Response({
            'title': 'Purchase Order (PO)',
            'description': 'A formal document that a buyer sends to a supplier/vendor to request goods or services.',
            'fields': [
                'PO Number (unique ID to track it)',
                'Supplier name (who you’re buying from)',
                'Buyer name (your business)',
                'Products/Services list (with quantities and unit prices)',
                'Total amount',
                'Expected delivery date',
                'Payment terms (e.g., 30 days after delivery)'
            ],
            'example': {
                'PO Number': 'PO-2025-01',
                'Supplier': 'Tech Supplier Ltd',
                'Product': 'Dell Laptop',
                'Quantity': 10,
                'Unit Price': '$800',
                'Total': '$8,000',
                'Expected Date': '10-Sep-2025'
            },
            'why_important': [
                'Keeps track of what you ordered.',
                'Helps avoid duplicate or unauthorized purchases.',
                'Acts as a legal contract between buyer & supplier.',
                'Links with inventory (once received, stock is updated).',
                'Links with accounts (payment due against a PO).'
            ]
        })


from rest_framework.views import APIView
class BestSupplierView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        product_id = request.query_params.get('product')
        qty = request.query_params.get('qty')
        try:
            qty = int(qty or '1')
        except ValueError:
            qty = 1
        qs = SupplierProduct.objects.filter(product_id=product_id, is_active=True)
        if not qs.exists():
            return Response({'detail': 'No suppliers for this product'}, status=404)
        best = qs.order_by('supplier_price').first()
        total_cost = best.supplier_price * qty
        data = SupplierProductSerializer(best).data
        data.update({'recommended_quantity': qty, 'estimated_total_cost': str(total_cost)})
        return Response(data)