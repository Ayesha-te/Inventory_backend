from django.urls import path
from . import views

urlpatterns = [
    # Dashboard metrics
    path('dashboard/', views.DashboardMetricsView.as_view(), name='dashboard_metrics'),
    path('dashboard/<uuid:supermarket_id>/', views.SupermarketDashboardView.as_view(), name='supermarket_dashboard'),
    
    # Reports
    path('reports/templates/', views.ReportTemplateListCreateView.as_view(), name='report_template_list_create'),
    path('reports/templates/<int:pk>/', views.ReportTemplateDetailView.as_view(), name='report_template_detail'),
    path('reports/generate/', views.GenerateReportView.as_view(), name='generate_report'),
    path('reports/generated/', views.GeneratedReportListView.as_view(), name='generated_report_list'),
    path('reports/generated/<int:pk>/', views.GeneratedReportDetailView.as_view(), name='generated_report_detail'),
    
    # User activity
    path('activity/', views.UserActivityListView.as_view(), name='user_activity_list'),
    path('activity/log/', views.log_user_activity, name='log_user_activity'),
    
    # Performance metrics
    path('performance/', views.PerformanceMetricsView.as_view(), name='performance_metrics'),
    
    # Analytics insights
    path('insights/trends/', views.TrendsAnalysisView.as_view(), name='trends_analysis'),
    path('insights/predictions/', views.PredictionsView.as_view(), name='predictions'),
]