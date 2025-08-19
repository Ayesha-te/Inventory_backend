"""
Django-Q tasks for file processing
"""
from django_q.tasks import async_task
from django.utils import timezone
from .models import UploadSession, BatchOperation
from .services import ExcelProcessor, ImageProcessor, ProductImporter
import logging

logger = logging.getLogger(__name__)


def process_excel_file(upload_session_id: str):
    """Process Excel file asynchronously"""
    try:
        upload_session = UploadSession.objects.get(id=upload_session_id)
        upload_session.started_at = timezone.now()
        upload_session.save()
        
        processor = ExcelProcessor(upload_session)
        success = processor.process_file()
        
        if success:
            logger.info(f"Successfully processed Excel file for session {upload_session_id}")
        else:
            logger.error(f"Failed to process Excel file for session {upload_session_id}")
            
    except UploadSession.DoesNotExist:
        logger.error(f"Upload session {upload_session_id} not found")
    except Exception as e:
        logger.error(f"Error processing Excel file {upload_session_id}: {str(e)}")


def process_image_file(upload_session_id: str):
    """Process image file asynchronously"""
    try:
        upload_session = UploadSession.objects.get(id=upload_session_id)
        upload_session.started_at = timezone.now()
        upload_session.save()
        
        processor = ImageProcessor(upload_session)
        success = processor.process_image()
        
        if success:
            logger.info(f"Successfully processed image file for session {upload_session_id}")
        else:
            logger.error(f"Failed to process image file for session {upload_session_id}")
            
    except UploadSession.DoesNotExist:
        logger.error(f"Upload session {upload_session_id} not found")
    except Exception as e:
        logger.error(f"Error processing image file {upload_session_id}: {str(e)}")


def import_products_batch(batch_operation_id: str):
    """Import products in batch asynchronously"""
    try:
        batch_operation = BatchOperation.objects.get(id=batch_operation_id)
        batch_operation.status = 'RUNNING'
        batch_operation.started_at = timezone.now()
        batch_operation.save()
        
        importer = ProductImporter(batch_operation.upload_session)
        results = importer.import_products()
        
        # Update batch operation with results
        batch_operation.successful_items = results['imported'] + results['updated']
        batch_operation.failed_items = results['errors']
        batch_operation.processed_items = sum(results.values())
        batch_operation.result_summary = results
        batch_operation.status = 'COMPLETED'
        batch_operation.completed_at = timezone.now()
        batch_operation.save()
        
        logger.info(f"Successfully completed batch import {batch_operation_id}: {results}")
        
    except BatchOperation.DoesNotExist:
        logger.error(f"Batch operation {batch_operation_id} not found")
    except Exception as e:
        logger.error(f"Error in batch import {batch_operation_id}: {str(e)}")
        
        # Update batch operation with error
        try:
            batch_operation = BatchOperation.objects.get(id=batch_operation_id)
            batch_operation.status = 'FAILED'
            batch_operation.error_details = [{'error': str(e)}]
            batch_operation.completed_at = timezone.now()
            batch_operation.save()
        except:
            pass


def cleanup_old_upload_sessions():
    """Clean up old upload sessions and files"""
    from datetime import timedelta
    import os
    
    # Delete sessions older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    old_sessions = UploadSession.objects.filter(created_at__lt=cutoff_date)
    
    deleted_count = 0
    for session in old_sessions:
        try:
            # Delete associated files
            if session.file_path and os.path.exists(session.file_path):
                os.remove(session.file_path)
            
            # Delete session
            session.delete()
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Error deleting session {session.id}: {str(e)}")
    
    logger.info(f"Cleaned up {deleted_count} old upload sessions")


def schedule_file_processing_task(upload_session_id: str, file_type: str):
    """Schedule file processing task"""
    if file_type == 'EXCEL':
        async_task('file_processing.tasks.process_excel_file', upload_session_id)
    elif file_type == 'IMAGE':
        async_task('file_processing.tasks.process_image_file', upload_session_id)
    else:
        logger.error(f"Unknown file type: {file_type}")


def schedule_batch_import_task(batch_operation_id: str):
    """Schedule batch import task"""
    async_task('file_processing.tasks.import_products_batch', batch_operation_id)


def schedule_cleanup_task():
    """Schedule cleanup task (should be run daily)"""
    async_task('file_processing.tasks.cleanup_old_upload_sessions')