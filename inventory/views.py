from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    Category, Supplier, Product, ProductImage, StockMovement,
    ProductAlert, Barcode, ProductReview
)
from .serializers import (
    CategorySerializer, SupplierSerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateUpdateSerializer, StockMovementSerializer,
    ProductAlertSerializer, BarcodeSerializer, ProductReviewSerializer,
    BulkProductUpdateSerializer, ProductStatsSerializer, ProductImageSerializer
)
from .filters import ProductFilter


class CategoryListCreateView(generics.ListCreateAPIView):
    """List and create categories"""
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete categories"""
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class SupplierListCreateView(generics.ListCreateAPIView):
    """List and create suppliers"""
    
    queryset = Supplier.objects.filter(is_active=True)
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete suppliers"""
    
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductListCreateView(generics.ListCreateAPIView):
    """List and create products"""
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'barcode', 'brand', 'description']
    ordering_fields = ['name', 'price', 'quantity', 'expiry_date', 'added_date']
    ordering = ['-added_date']
    
    def get_queryset(self):
        user = self.request.user
        # Filter products by user's supermarkets
        return Product.objects.filter(
            supermarket__owner=user,
            is_active=True
        ).select_related('category', 'supplier', 'supermarket')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductListSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete products"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Product.objects.filter(
            supermarket__owner=user
        ).select_related('category', 'supplier', 'supermarket', 'created_by')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer


class ProductStockUpdateView(APIView):
    """Update product stock with movement tracking"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, product_id):
        try:
            product = Product.objects.get(
                id=product_id,
                supermarket__owner=request.user
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        movement_type = request.data.get('movement_type')
        quantity_change = request.data.get('quantity', 0)
        unit_cost = request.data.get('unit_cost')
        reference = request.data.get('reference', '')
        notes = request.data.get('notes', '')
        
        if not movement_type or quantity_change == 0:
            return Response(
                {'error': 'Movement type and quantity are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        previous_quantity = product.quantity
        
        # Calculate new quantity based on movement type
        if movement_type in ['IN', 'RETURNED']:
            new_quantity = previous_quantity + abs(quantity_change)
        elif movement_type in ['OUT', 'EXPIRED', 'DAMAGED']:
            new_quantity = max(0, previous_quantity - abs(quantity_change))
        elif movement_type == 'ADJUSTMENT':
            new_quantity = quantity_change  # Direct quantity set
        else:
            return Response(
                {'error': 'Invalid movement type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update product quantity
        product.quantity = new_quantity
        product.save()
        
        # Create stock movement record
        total_cost = None
        if unit_cost:
            total_cost = Decimal(str(unit_cost)) * abs(quantity_change)
        
        StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity_change if movement_type != 'ADJUSTMENT' else new_quantity - previous_quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            reference=reference,
            notes=notes,
            created_by=request.user
        )
        
        # Check for alerts
        self.check_and_create_alerts(product)
        
        return Response({
            'message': 'Stock updated successfully',
            'previous_quantity': previous_quantity,
            'new_quantity': new_quantity,
            'product': ProductListSerializer(product).data
        })
    
    def check_and_create_alerts(self, product):
        """Check and create alerts for the product"""
        alerts_to_create = []
        
        # Low stock alert
        if product.is_low_stock and product.quantity > 0:
            alerts_to_create.append(ProductAlert(
                product=product,
                alert_type='LOW_STOCK',
                priority='MEDIUM',
                message=f'{product.name} is running low on stock. Current quantity: {product.quantity}'
            ))
        
        # Out of stock alert
        if product.quantity == 0:
            alerts_to_create.append(ProductAlert(
                product=product,
                alert_type='OUT_OF_STOCK',
                priority='HIGH',
                message=f'{product.name} is out of stock.'
            ))
        
        # Expiry alerts
        if product.is_expiring_soon:
            alerts_to_create.append(ProductAlert(
                product=product,
                alert_type='EXPIRING_SOON',
                priority='MEDIUM',
                message=f'{product.name} expires in {product.days_until_expiry} days.'
            ))
        elif product.is_expired:
            alerts_to_create.append(ProductAlert(
                product=product,
                alert_type='EXPIRED',
                priority='CRITICAL',
                message=f'{product.name} has expired.'
            ))
        
        # Bulk create alerts (avoiding duplicates)
        for alert in alerts_to_create:
            if not ProductAlert.objects.filter(
                product=product,
                alert_type=alert.alert_type,
                is_resolved=False
            ).exists():
                alert.save()


class BulkProductUpdateView(APIView):
    """Bulk update products"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BulkProductUpdateSerializer(data=request.data)
        if serializer.is_valid():
            product_ids = serializer.validated_data['product_ids']
            updates = serializer.validated_data['updates']
            
            # Filter products by user's supermarkets
            products = Product.objects.filter(
                id__in=product_ids,
                supermarket__owner=request.user
            )
            
            if not products.exists():
                return Response(
                    {'error': 'No products found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update products
            updated_count = products.update(**updates)
            
            return Response({
                'message': f'{updated_count} products updated successfully',
                'updated_count': updated_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductStatsView(APIView):
    """Get product statistics"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        products = Product.objects.filter(
            supermarket__owner=user,
            is_active=True
        )
        
        # Calculate statistics
        total_products = products.count()
        total_value = products.aggregate(
            total=Sum('quantity') * Sum('price')
        )['total'] or 0
        
        low_stock_count = products.filter(
            quantity__lte=models.F('min_stock_level')
        ).count()
        
        expired_count = products.filter(
            expiry_date__lt=timezone.now().date()
        ).count()
        
        expiring_soon_count = products.filter(
            expiry_date__lte=timezone.now().date() + timedelta(days=7),
            expiry_date__gt=timezone.now().date()
        ).count()
        
        out_of_stock_count = products.filter(quantity=0).count()
        
        categories_count = Category.objects.filter(
            product__in=products
        ).distinct().count()
        
        suppliers_count = Supplier.objects.filter(
            product__in=products
        ).distinct().count()
        
        # Calculate average profit margin
        profit_margins = []
        for product in products.filter(cost_price__gt=0):
            if product.selling_price > product.cost_price:
                margin = ((product.selling_price - product.cost_price) / product.cost_price) * 100
                profit_margins.append(margin)
        
        average_profit_margin = sum(profit_margins) / len(profit_margins) if profit_margins else 0
        
        stats = {
            'total_products': total_products,
            'total_value': total_value,
            'low_stock_count': low_stock_count,
            'expired_count': expired_count,
            'expiring_soon_count': expiring_soon_count,
            'out_of_stock_count': out_of_stock_count,
            'categories_count': categories_count,
            'suppliers_count': suppliers_count,
            'average_profit_margin': round(average_profit_margin, 2)
        }
        
        serializer = ProductStatsSerializer(stats)
        return Response(serializer.data)


class StockMovementListView(generics.ListAPIView):
    """List stock movements"""
    
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['movement_type', 'product']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        return StockMovement.objects.filter(
            product__supermarket__owner=user
        ).select_related('product', 'created_by')


class ProductAlertListView(generics.ListAPIView):
    """List product alerts"""
    
    serializer_class = ProductAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['alert_type', 'priority', 'is_read', 'is_resolved']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        return ProductAlert.objects.filter(
            product__supermarket__owner=user
        ).select_related('product', 'resolved_by')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_alert_as_read(request, alert_id):
    """Mark alert as read"""
    try:
        alert = ProductAlert.objects.get(
            id=alert_id,
            product__supermarket__owner=request.user
        )
        alert.is_read = True
        alert.save()
        
        return Response({'message': 'Alert marked as read'})
    except ProductAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resolve_alert(request, alert_id):
    """Resolve alert"""
    try:
        alert = ProductAlert.objects.get(
            id=alert_id,
            product__supermarket__owner=request.user
        )
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.save()
        
        return Response({'message': 'Alert resolved'})
    except ProductAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class ProductReviewListCreateView(generics.ListCreateAPIView):
    """List and create product reviews"""
    
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        return ProductReview.objects.filter(
            product__supermarket__owner=user
        ).select_related('product', 'user')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_products_by_barcode(request, barcode):
    """Search products by barcode"""
    try:
        product = Product.objects.get(
            barcode=barcode,
            supermarket__owner=request.user,
            is_active=True
        )
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )