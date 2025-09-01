from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Min, F
from .models import SupplierProduct, PurchaseOrder
from .serializers import SupplierProductSerializer, PurchaseOrderSerializer


class SupplierProductViewSet(viewsets.ModelViewSet):
    queryset = SupplierProduct.objects.select_related('supplier', 'product').all()
    serializer_class = SupplierProductSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['supplier', 'product', 'is_active']
    search_fields = ['supplier__name', 'product__name']
    ordering_fields = ['supplier_price', 'available_quantity']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('supplier', 'supermarket', 'created_by').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['supplier', 'supermarket', 'status']
    search_fields = ['supplier__name', 'notes']
    ordering_fields = ['created_at', 'updated_at']

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        po = self.get_object()
        if po.status == 'RECEIVED':
            return Response({'detail': 'Already received'}, status=status.HTTP_400_BAD_REQUEST)
        # Mark received — stock update could be added here
        po.status = 'RECEIVED'
        po.save(update_fields=['status'])
        return Response({'detail': 'Marked as received'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total = self.get_queryset().count()
        received = self.get_queryset().filter(status='RECEIVED').count()
        draft = self.get_queryset().filter(status='DRAFT').count()
        sent = self.get_queryset().filter(status='SENT').count()
        return Response({ 'total': total, 'received': received, 'draft': draft, 'sent': sent })

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        # Stub: return JSON; replace with real PDF generation when needed
        po = self.get_object()
        return Response({'detail': f'PDF generation placeholder for PO {po.id}'})

    @action(detail=True, methods=['post'])
    def email(self, request, pk=None):
        # Stub: send email; integrate with notifications/email later
        po = self.get_object()
        return Response({'detail': f'Email sent placeholder for PO {po.id}'})


from rest_framework.views import APIView
class BestSupplierView(APIView):
    permission_classes = [IsAuthenticated]

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