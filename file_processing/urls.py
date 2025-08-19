from django.urls import path
from . import views

urlpatterns = [
    # File upload
    path('upload/', views.FileUploadView.as_view(), name='file_upload'),
    
    # Upload sessions
    path('sessions/', views.UploadSessionListView.as_view(), name='upload_session_list'),
    path('sessions/<uuid:pk>/', views.UploadSessionDetailView.as_view(), name='upload_session_detail'),
    path('sessions/<uuid:upload_session_id>/cancel/', views.cancel_upload_session, name='cancel_upload_session'),
    path('sessions/<uuid:upload_session_id>/retry/', views.retry_upload_session, name='retry_upload_session'),
    path('sessions/<uuid:upload_session_id>/delete/', views.delete_upload_session, name='delete_upload_session'),
    
    # Extracted products
    path('sessions/<uuid:upload_session_id>/products/', views.ExtractedProductListView.as_view(), name='extracted_product_list'),
    path('extracted-products/<int:pk>/', views.ExtractedProductUpdateView.as_view(), name='extracted_product_update'),
    
    # Product import
    path('import/', views.ProductImportView.as_view(), name='product_import'),
    
    # Batch operations
    path('batch-operations/', views.BatchOperationListView.as_view(), name='batch_operation_list'),
    path('batch-operations/<uuid:pk>/', views.BatchOperationDetailView.as_view(), name='batch_operation_detail'),
    
    # Processing logs
    path('sessions/<uuid:upload_session_id>/logs/', views.FileProcessingLogListView.as_view(), name='processing_log_list'),
    
    # Image processing results
    path('sessions/<uuid:upload_session_id>/image-results/', views.ImageProcessingResultView.as_view(), name='image_processing_result'),
    
    # Processing templates
    path('templates/', views.ProcessingTemplateListCreateView.as_view(), name='processing_template_list_create'),
    path('templates/<int:pk>/', views.ProcessingTemplateDetailView.as_view(), name='processing_template_detail'),
    
    # Statistics
    path('stats/', views.upload_session_stats, name='upload_session_stats'),
]