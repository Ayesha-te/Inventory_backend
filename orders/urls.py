from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrderListCreateView.as_view(), name='order_list_create'),
    path('<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]