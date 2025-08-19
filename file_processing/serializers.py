from rest_framework import serializers
from .models import (
    UploadSession, ExtractedProduct, FileProcessingLog,
    ImageProcessingResult, ProcessingTemplate, BatchOperation
)


class UploadSessionSerializer(serializers.ModelSerializer):
    """Serializer for UploadSession model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    supermarket_name = serializers.CharField(source='supermarket.name', read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = UploadSession
        fields = [
            'id', 'user', 'user_name', 'supermarket', 'supermarket_name',
            'upload_type', 'file_name', 'file_size', 'status', 'progress',
            'total_rows', 'processed_rows', 'successful_rows', 'failed_rows',
            'error_message', 'created_at', 'started_at', 'completed_at', 'duration'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'started_at', 'completed_at',
            'status', 'progress', 'total_rows', 'processed_rows',
            'successful_rows', 'failed_rows', 'error_message'
        ]


class ExtractedProductSerializer(serializers.ModelSerializer):
    """Serializer for ExtractedProduct model"""
    
    class Meta:
        model = ExtractedProduct
        fields = [
            'id', 'upload_session', 'name', 'barcode', 'category', 'supplier',
            'brand', 'description', 'cost_price', 'selling_price', 'price',
            'quantity', 'min_stock_level', 'weight', 'origin', 'expiry_date',
            'location', 'halal_certified', 'halal_certification_body',
            'is_processed', 'is_valid', 'validation_errors', 'row_number',
            'raw_data', 'created_at'
        ]
        read_only_fields = ['id', 'upload_session', 'created_at', 'raw_data']


class FileProcessingLogSerializer(serializers.ModelSerializer):
    """Serializer for FileProcessingLog model"""
    
    class Meta:
        model = FileProcessingLog
        fields = [
            'id', 'upload_session', 'level', 'message', 'details',
            'row_number', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ImageProcessingResultSerializer(serializers.ModelSerializer):
    """Serializer for ImageProcessingResult model"""
    
    class Meta:
        model = ImageProcessingResult
        fields = [
            'id', 'upload_session', 'image_path', 'image_size', 'image_dimensions',
            'extracted_text', 'confidence_score', 'detected_products',
            'detected_prices', 'detected_barcodes', 'ocr_engine',
            'processing_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProcessingTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ProcessingTemplate model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ProcessingTemplate
        fields = [
            'id', 'name', 'template_type', 'user', 'user_name',
            'column_mappings', 'validation_rules', 'transformation_rules',
            'has_header_row', 'start_row', 'is_default', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BatchOperationSerializer(serializers.ModelSerializer):
    """Serializer for BatchOperation model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    upload_session_file_name = serializers.CharField(source='upload_session.file_name', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = BatchOperation
        fields = [
            'id', 'upload_session', 'upload_session_file_name', 'user', 'user_name',
            'operation_type', 'status', 'total_items', 'processed_items',
            'successful_items', 'failed_items', 'result_summary', 'error_details',
            'progress_percentage', 'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'started_at', 'completed_at',
            'status', 'processed_items', 'successful_items', 'failed_items',
            'result_summary', 'error_details'
        ]


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads"""
    
    UPLOAD_TYPE_CHOICES = [
        ('EXCEL', 'Excel File'),
        ('IMAGE', 'Image File'),
        ('CSV', 'CSV File'),
    ]
    
    file = serializers.FileField()
    upload_type = serializers.ChoiceField(choices=UPLOAD_TYPE_CHOICES)
    supermarket = serializers.UUIDField()
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Check file extension based on upload type
        upload_type = self.initial_data.get('upload_type')
        allowed_extensions = {
            'EXCEL': ['.xlsx', '.xls'],
            'IMAGE': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
            'CSV': ['.csv'],
        }
        
        if upload_type in allowed_extensions:
            file_extension = value.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions[upload_type]:
                raise serializers.ValidationError(
                    f"Invalid file type for {upload_type}. "
                    f"Allowed: {', '.join(allowed_extensions[upload_type])}"
                )
        
        return value
    
    def validate_supermarket(self, value):
        """Validate supermarket ownership"""
        from supermarkets.models import Supermarket
        
        try:
            supermarket = Supermarket.objects.get(id=value)
            if supermarket.owner != self.context['request'].user:
                raise serializers.ValidationError("You don't have permission to upload to this supermarket")
            return supermarket
        except Supermarket.DoesNotExist:
            raise serializers.ValidationError("Supermarket not found")


class ProductImportSerializer(serializers.Serializer):
    """Serializer for importing products"""
    
    upload_session = serializers.UUIDField()
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of extracted product IDs to import. If not provided, all valid products will be imported."
    )
    
    def validate_upload_session(self, value):
        """Validate upload session"""
        try:
            upload_session = UploadSession.objects.get(id=value)
            if upload_session.user != self.context['request'].user:
                raise serializers.ValidationError("You don't have permission to access this upload session")
            if upload_session.status != 'COMPLETED':
                raise serializers.ValidationError("Upload session is not completed yet")
            return upload_session
        except UploadSession.DoesNotExist:
            raise serializers.ValidationError("Upload session not found")


class ExtractedProductUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating extracted products before import"""
    
    class Meta:
        model = ExtractedProduct
        fields = [
            'name', 'barcode', 'category', 'supplier', 'brand', 'description',
            'cost_price', 'selling_price', 'price', 'quantity', 'min_stock_level',
            'weight', 'origin', 'expiry_date', 'location', 'halal_certified',
            'halal_certification_body'
        ]
    
    def validate_barcode(self, value):
        """Validate barcode uniqueness within the supermarket"""
        if value:
            from inventory.models import Product
            upload_session = self.instance.upload_session
            
            # Check if barcode exists in the supermarket
            if Product.objects.filter(
                barcode=value,
                supermarket=upload_session.supermarket
            ).exists():
                raise serializers.ValidationError("Product with this barcode already exists in the supermarket")
        
        return value