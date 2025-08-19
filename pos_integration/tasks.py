"""
Django-Q tasks for POS integration
"""
from django_q.tasks import async_task
from django.utils import timezone
from .models import POSIntegration, POSSyncLog
from .services import SquarePOSSync
import logging

logger = logging.getLogger(__name__)


def perform_pos_sync(integration_id: int, sync_type: str, sync_log_id: int):
    """Perform POS synchronization"""
    try:
        integration = POSIntegration.objects.get(id=integration_id)
        sync_log = POSSyncLog.objects.get(id=sync_log_id)
        
        # Update sync log
        sync_log.started_at = timezone.now()
        sync_log.save()
        
        # Perform sync based on POS type
        if integration.pos_system.pos_type == 'SQUARE':
            sync_service = SquarePOSSync(integration)
            result = sync_service.sync_products()
        else:
            result = {'success': False, 'error': 'POS type not supported yet'}
        
        # Update sync log with results
        sync_log.completed_at = timezone.now()
        sync_log.duration = sync_log.completed_at - sync_log.started_at
        
        if result.get('success'):
            sync_log.status = 'SUCCESS'
            sync_log.successful_items = result.get('synced_count', 0)
            sync_log.total_items = result.get('synced_count', 0)
        else:
            sync_log.status = 'FAILED'
            sync_log.error_message = result.get('error', 'Unknown error')
        
        sync_log.save()
        
        # Update integration
        integration.last_sync = timezone.now()
        integration.status = 'ACTIVE' if result.get('success') else 'ERROR'
        integration.last_error = result.get('error') if not result.get('success') else None
        integration.save()
        
        logger.info(f"POS sync completed for integration {integration_id}: {result}")
        
    except Exception as e:
        logger.error(f"Error in POS sync {integration_id}: {str(e)}")
        
        # Update sync log with error
        try:
            sync_log = POSSyncLog.objects.get(id=sync_log_id)
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
        except:
            pass


def schedule_auto_syncs():
    """Schedule automatic POS syncs"""
    active_integrations = POSIntegration.objects.filter(
        status='ACTIVE',
        auto_sync_enabled=True
    )
    
    for integration in active_integrations:
        # Check if it's time for sync
        if integration.last_sync:
            time_since_sync = timezone.now() - integration.last_sync
            if time_since_sync.total_seconds() >= (integration.sync_interval * 60):
                # Schedule sync
                async_task('pos_integration.tasks.perform_pos_sync', 
                          integration.id, 'INCREMENTAL', None)
        else:
            # First sync
            async_task('pos_integration.tasks.perform_pos_sync', 
                      integration.id, 'FULL', None)