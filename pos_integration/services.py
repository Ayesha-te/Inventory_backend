import requests
from django.utils import timezone
from datetime import timedelta
from .models import POSIntegration, POSSyncLog
from inventory.models import Product
import logging

logger = logging.getLogger(__name__)


class POSService:
    """Service for POS system integration"""
    
    def __init__(self, pos_integration: POSIntegration):
        self.integration = pos_integration
        self.pos_system = pos_integration.pos_system
    
    def test_connection(self) -> dict:
        """Test connection to POS system"""
        try:
            if self.pos_system.pos_type == 'SQUARE':
                return self._test_square_connection()
            elif self.pos_system.pos_type == 'SHOPIFY':
                return self._test_shopify_connection()
            else:
                return self._test_custom_connection()
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def trigger_sync(self, sync_type: str = 'FULL') -> dict:
        """Trigger synchronization with POS system"""
        from django_q.tasks import async_task
        
        # Create sync log
        sync_log = POSSyncLog.objects.create(
            pos_integration=self.integration,
            sync_type=sync_type,
            status='SUCCESS',
            started_at=timezone.now()
        )
        
        # Schedule async sync task
        task_id = async_task(
            'pos_integration.tasks.perform_pos_sync',
            self.integration.id,
            sync_type,
            sync_log.id
        )
        
        return {
            'sync_id': sync_log.id,
            'task_id': task_id
        }
    
    def _test_square_connection(self) -> dict:
        """Test Square POS connection"""
        headers = {
            'Authorization': f'Bearer {self.integration.api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'https://connect.squareup.com/v2/locations',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Connection successful',
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}'
            }
    
    def _test_shopify_connection(self) -> dict:
        """Test Shopify connection"""
        shop_url = f"https://{self.integration.store_id}.myshopify.com"
        headers = {
            'X-Shopify-Access-Token': self.integration.api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'{shop_url}/admin/api/2023-10/shop.json',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Connection successful',
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}'
            }
    
    def _test_custom_connection(self) -> dict:
        """Test custom API connection"""
        headers = {
            'Authorization': f'Bearer {self.integration.api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'{self.pos_system.api_endpoint}/health',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Connection successful'
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}'
            }


class SquarePOSSync:
    """Square POS synchronization service"""
    
    def __init__(self, integration: POSIntegration):
        self.integration = integration
        self.headers = {
            'Authorization': f'Bearer {integration.api_key}',
            'Content-Type': 'application/json'
        }
        self.base_url = 'https://connect.squareup.com/v2'
    
    def sync_products(self) -> dict:
        """Sync products with Square"""
        try:
            # Get products from Square
            response = requests.get(
                f'{self.base_url}/catalog/list',
                headers=self.headers,
                params={'types': 'ITEM'}
            )
            
            if response.status_code != 200:
                raise Exception(f'Failed to fetch products: {response.text}')
            
            square_products = response.json().get('objects', [])
            
            # Sync with local inventory
            synced_count = 0
            for square_product in square_products:
                self._sync_single_product(square_product)
                synced_count += 1
            
            return {
                'success': True,
                'synced_count': synced_count
            }
            
        except Exception as e:
            logger.error(f'Square product sync failed: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _sync_single_product(self, square_product: dict):
        """Sync a single product from Square"""
        item_data = square_product.get('item_data', {})
        name = item_data.get('name', '')
        
        # Try to find existing product
        product = None
        if square_product.get('id'):
            try:
                product = Product.objects.get(
                    pos_id=square_product['id'],
                    supermarket=self.integration.supermarket
                )
            except Product.DoesNotExist:
                pass
        
        # Create or update product
        if product:
            # Update existing
            product.name = name
            product.synced_with_pos = True
            product.last_pos_sync = timezone.now()
            product.save()
        else:
            # Create new (if we have enough data)
            if name:
                Product.objects.create(
                    name=name,
                    barcode=f"SQUARE_{square_product.get('id', '')}",
                    pos_id=square_product.get('id'),
                    supermarket=self.integration.supermarket,
                    synced_with_pos=True,
                    last_pos_sync=timezone.now(),
                    price=0,  # Will be updated with inventory sync
                    quantity=0,
                    expiry_date=timezone.now().date() + timedelta(days=365)
                )