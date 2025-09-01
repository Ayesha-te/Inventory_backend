from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupplierProductViewSet, PurchaseOrderViewSet, BestSupplierView

router = DefaultRouter()
router.register(r'supplier-products', SupplierProductViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('best-supplier/', BestSupplierView.as_view(), name='best-supplier'),
]