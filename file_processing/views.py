from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone
import os
import uuid

from .models import (
    UploadSession, ExtractedProduct, FileProcessingLog,
    ImageProcessingResult, ProcessingTemplate, BatchOperation
)
from .serializers import (
    UploadSessionSerializer, ExtractedProductSerializer, FileProcessingLogSerializer,
    ImageProcessingResultSerializer, ProcessingTemplateSerializer, BatchOperationSerializer,
    FileUploadSerializer, ProductImportSerializer, ExtractedProductUpdateSerializer
)
from .tasks import schedule_file_processing_task, schedule_batch_import_task


class FileUploadView(APIView):
    """Handle file uploads"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            file = serializer.validated_data['file']
            upload_type = serializer.validated_data['upload_type']
            supermarket = serializer.validated_data['supermarket']
            
            # Generate unique filename
            file_extension = file.name.split('.')[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Save file
            upload_dir = f"uploads/{upload_type.lower()}/{timezone.now().strftime('%Y/%m/%d')}"
            file_path = os.path.join(upload_dir, unique_filename)
            saved_path = default_storage.save(file_path, file)
            full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
            
            # Create upload session
            upload_session = UploadSession.objects.create(
                user=request.user,
                supermarket=supermarket,
                upload_type=upload_type,
                file_name=file.name,
                file_size=file.size,
                file_path=full_path,
                status='UPLOADING'
            )
            
            # Schedule processing task
            schedule_file_processing_task(str(upload_session.id), upload_type)
            
            return Response({
                'message': 'File uploaded successfully',
                'upload_session': UploadSessionSerializer(upload_session).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UploadSessionListView(generics.ListAPIView):
    """List upload sessions"""
    
    serializer_class = UploadSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['upload_type', 'status', 'supermarket']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return UploadSession.objects.filter(user=self.request.user)


class UploadSessionDetailView(generics.RetrieveAPIView):
    """Get upload session details"""
    
    serializer_class = UploadSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UploadSession.objects.filter(user=self.request.user)


class ExtractedProductListView(generics.ListAPIView):
    """List extracted products from upload session"""
    
    serializer_class = ExtractedProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_valid', 'is_processed']
    ordering = ['row_number']
    
    def get_queryset(self):
        upload_session_id = self.kwargs.get('upload_session_id')
        return ExtractedProduct.objects.filter(
            upload_session_id=upload_session_id,
            upload_session__user=self.request.user
        )


class ExtractedProductUpdateView(generics.UpdateAPIView):
    """Update extracted product before import"""
    
    serializer_class = ExtractedProductUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ExtractedProduct.objects.filter(
            upload_session__user=self.request.user,
            is_processed=False
        )


class ProductImportView(APIView):
    """Import extracted products to inventory"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ProductImportSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            upload_session = serializer.validated_data['upload_session']
            product_ids = serializer.validated_data.get('product_ids')
            
            # Count products to import
            extracted_products = ExtractedProduct.objects.filter(
                upload_session=upload_session,
                is_valid=True,
                is_processed=False
            )
            
            if product_ids:
                extracted_products = extracted_products.filter(id__in=product_ids)
            
            total_items = extracted_products.count()
            
            if total_items == 0:
                return Response({
                    'error': 'No valid products to import'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create batch operation
            batch_operation = BatchOperation.objects.create(
                upload_session=upload_session,
                user=request.user,
                operation_type='IMPORT',
                total_items=total_items
            )
            
            # Schedule import task
            schedule_batch_import_task(str(batch_operation.id))
            
            return Response({
                'message': f'Import started for {total_items} products',
                'batch_operation': BatchOperationSerializer(batch_operation).data
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BatchOperationListView(generics.ListAPIView):
    """List batch operations"""
    
    serializer_class = BatchOperationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['operation_type', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return BatchOperation.objects.filter(user=self.request.user)


class BatchOperationDetailView(generics.RetrieveAPIView):
    """Get batch operation details"""
    
    serializer_class = BatchOperationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BatchOperation.objects.filter(user=self.request.user)


class FileProcessingLogListView(generics.ListAPIView):
    """List processing logs for upload session"""
    
    serializer_class = FileProcessingLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['level']
    ordering = ['created_at']
    
    def get_queryset(self):
        upload_session_id = self.kwargs.get('upload_session_id')
        return FileProcessingLog.objects.filter(
            upload_session_id=upload_session_id,
            upload_session__user=self.request.user
        )


class ImageProcessingResultView(generics.RetrieveAPIView):
    """Get image processing results"""
    
    serializer_class = ImageProcessingResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        upload_session_id = self.kwargs.get('upload_session_id')
        return ImageProcessingResult.objects.filter(
            upload_session_id=upload_session_id,
            upload_session__user=self.request.user
        )


class ProcessingTemplateListCreateView(generics.ListCreateAPIView):
    """List and create processing templates"""
    
    serializer_class = ProcessingTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['template_type', 'is_active']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ProcessingTemplate.objects.filter(user=self.request.user)


class ProcessingTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete processing templates"""
    
    serializer_class = ProcessingTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProcessingTemplate.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_upload_session(request, upload_session_id):
    """Cancel an upload session"""
    try:
        upload_session = UploadSession.objects.get(
            id=upload_session_id,
            user=request.user
        )
        
        if upload_session.status in ['UPLOADING', 'PROCESSING']:
            upload_session.status = 'CANCELLED'
            upload_session.save()
            
            return Response({'message': 'Upload session cancelled'})
        else:
            return Response({
                'error': 'Cannot cancel upload session in current status'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except UploadSession.DoesNotExist:
        return Response({
            'error': 'Upload session not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def retry_upload_session(request, upload_session_id):
    """Retry a failed upload session"""
    try:
        upload_session = UploadSession.objects.get(
            id=upload_session_id,
            user=request.user
        )
        
        if upload_session.status == 'ERROR':
            upload_session.status = 'UPLOADING'
            upload_session.progress = 0
            upload_session.error_message = None
            upload_session.error_details = {}
            upload_session.save()
            
            # Schedule processing task
            schedule_file_processing_task(str(upload_session.id), upload_session.upload_type)
            
            return Response({'message': 'Upload session retry started'})
        else:
            return Response({
                'error': 'Cannot retry upload session in current status'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except UploadSession.DoesNotExist:
        return Response({
            'error': 'Upload session not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_upload_session(request, upload_session_id):
    """Delete an upload session and associated files"""
    try:
        upload_session = UploadSession.objects.get(
            id=upload_session_id,
            user=request.user
        )
        
        # Delete associated file
        if upload_session.file_path and os.path.exists(upload_session.file_path):
            try:
                os.remove(upload_session.file_path)
            except OSError:
                pass  # File might already be deleted
        
        # Delete session
        upload_session.delete()
        
        return Response({'message': 'Upload session deleted'})
        
    except UploadSession.DoesNotExist:
        return Response({
            'error': 'Upload session not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def upload_session_stats(request):
    """Get upload session statistics"""
    user = request.user
    
    total_sessions = UploadSession.objects.filter(user=user).count()
    completed_sessions = UploadSession.objects.filter(user=user, status='COMPLETED').count()
    failed_sessions = UploadSession.objects.filter(user=user, status='ERROR').count()
    processing_sessions = UploadSession.objects.filter(
        user=user, 
        status__in=['UPLOADING', 'PROCESSING']
    ).count()
    
    total_products_extracted = ExtractedProduct.objects.filter(
        upload_session__user=user
    ).count()
    
    total_products_imported = ExtractedProduct.objects.filter(
        upload_session__user=user,
        is_processed=True
    ).count()
    
    stats = {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'failed_sessions': failed_sessions,
        'processing_sessions': processing_sessions,
        'total_products_extracted': total_products_extracted,
        'total_products_imported': total_products_imported,
        'success_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
        'import_rate': (total_products_imported / total_products_extracted * 100) if total_products_extracted > 0 else 0
    }
    
    return Response(stats)