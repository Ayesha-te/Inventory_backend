"""
Multi-Channel Order Management Services
Implements functionality similar to MultiOrders.com
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import Order, OrderItem, Warehouse
from .enhanced_models import (
    Channel, SKUMapping, StockLevel, StockReservation,
    ProductBundle, BundleComponent, AutomationRule,
    EnhancedOrder, EnhancedOrderItem, CourierService,
    ChannelSyncLog
)
from inventory.models import Product, StockMovement
from supermarkets.models import Supermarket

User = get_user_model()
logger = logging.getLogger(__name__)


class MultiChannelOrderService:
    """
    Core service for multi-channel order management
    Handles order import, stock management, and fulfillment
    """
    
    @staticmethod
    def import_order_from_channel(channel: Channel, external_order_data: Dict) -> EnhancedOrder:
        """
        Import an order from an external channel (Shopify, Amazon, etc.)
        Converts external format to internal format and reserves stock
        """
        try:
            with transaction.atomic():
                # Extract order data
                order_data = MultiChannelOrderService._normalize_order_data(
                    channel, external_order_data
                )
                
                # Create enhanced order
                order = EnhancedOrder.objects.create(
                    supermarket=channel.supermarket,
                    channel=channel,
                    order_number=order_data['order_number'],
                    external_order_id=order_data['external_id'],
                    customer_name=order_data['customer_name'],
                    customer_email=order_data['customer_email'],
                    customer_phone=order_data.get('customer_phone', ''),
                    shipping_address=order_data['shipping_address'],
                    billing_address=order_data.get('billing_address', order_data['shipping_address']),
                    total_amount=order_data['total_amount'],
                    currency=order_data.get('currency', 'USD'),
                    placed_at=order_data['placed_at'],
                    status='PENDING'
                )
                
                # Process order items
                for item_data in order_data['items']:
                    MultiChannelOrderService._process_order_item(order, item_data)
                
                # Apply automation rules
                MultiChannelOrderService._apply_automation_rules(order)
                
                # Log successful import
                ChannelSyncLog.objects.create(
                    channel=channel,
                    type='ORDER_IMPORT',
                    status='SUCCESS',
                    message=f'Successfully imported order {order.order_number}',
                    records_processed=1,
                    records_successful=1
                )
                
                return order
                
        except Exception as e:
            logger.error(f"Failed to import order from {channel.name}: {str(e)}")
            ChannelSyncLog.objects.create(
                channel=channel,
                type='ORDER_IMPORT',
                status='ERROR',
                message=f'Failed to import order: {str(e)}',
                records_processed=1,
                records_failed=1
            )
            raise
    
    @staticmethod
    def _normalize_order_data(channel: Channel, external_data: Dict) -> Dict:
        """Normalize external order data to internal format"""
        # This would be customized per channel type
        if channel.type == 'SHOPIFY':
            return MultiChannelOrderService._normalize_shopify_order(external_data)
        elif channel.type == 'AMAZON':
            return MultiChannelOrderService._normalize_amazon_order(external_data)
        elif channel.type == 'EBAY':
            return MultiChannelOrderService._normalize_ebay_order(external_data)
        else:
            return MultiChannelOrderService._normalize_generic_order(external_data)
    
    @staticmethod
    def _normalize_shopify_order(data: Dict) -> Dict:
        """Normalize Shopify order format"""
        return {
            'order_number': data.get('order_number', data.get('name', '')),
            'external_id': str(data.get('id', '')),
            'customer_name': f"{data.get('customer', {}).get('first_name', '')} {data.get('customer', {}).get('last_name', '')}".strip(),
            'customer_email': data.get('customer', {}).get('email', ''),
            'customer_phone': data.get('customer', {}).get('phone', ''),
            'shipping_address': data.get('shipping_address', {}),
            'billing_address': data.get('billing_address', {}),
            'total_amount': Decimal(str(data.get('total_price', '0'))),
            'currency': data.get('currency', 'USD'),
            'placed_at': datetime.fromisoformat(data.get('created_at', timezone.now().isoformat())),
            'items': [
                {
                    'sku': item.get('sku', ''),
                    'name': item.get('name', ''),
                    'quantity': int(item.get('quantity', 1)),
                    'price': Decimal(str(item.get('price', '0'))),
                    'variant_id': item.get('variant_id', ''),
                }
                for item in data.get('line_items', [])
            ]
        }
    
    @staticmethod
    def _normalize_amazon_order(data: Dict) -> Dict:
        """Normalize Amazon order format"""
        # Amazon-specific normalization logic
        return {
            'order_number': data.get('AmazonOrderId', ''),
            'external_id': data.get('AmazonOrderId', ''),
            'customer_name': 'Amazon Customer',  # Amazon doesn't provide customer names
            'customer_email': data.get('BuyerEmail', ''),
            'customer_phone': '',
            'shipping_address': data.get('ShippingAddress', {}),
            'billing_address': data.get('ShippingAddress', {}),
            'total_amount': Decimal(str(data.get('OrderTotal', {}).get('Amount', '0'))),
            'currency': data.get('OrderTotal', {}).get('CurrencyCode', 'USD'),
            'placed_at': datetime.fromisoformat(data.get('PurchaseDate', timezone.now().isoformat())),
            'items': []  # Would be populated from separate API call
        }
    
    @staticmethod
    def _normalize_ebay_order(data: Dict) -> Dict:
        """Normalize eBay order format"""
        # eBay-specific normalization logic
        return {
            'order_number': data.get('orderId', ''),
            'external_id': data.get('orderId', ''),
            'customer_name': data.get('buyer', {}).get('username', ''),
            'customer_email': '',  # eBay doesn't provide email directly
            'customer_phone': '',
            'shipping_address': data.get('fulfillmentStartInstructions', [{}])[0].get('shippingStep', {}).get('shipTo', {}),
            'billing_address': {},
            'total_amount': Decimal(str(data.get('pricingSummary', {}).get('total', {}).get('value', '0'))),
            'currency': data.get('pricingSummary', {}).get('total', {}).get('currency', 'USD'),
            'placed_at': datetime.fromisoformat(data.get('creationDate', timezone.now().isoformat())),
            'items': [
                {
                    'sku': item.get('sku', ''),
                    'name': item.get('title', ''),
                    'quantity': int(item.get('quantity', 1)),
                    'price': Decimal(str(item.get('lineItemCost', {}).get('value', '0'))),
                    'listing_id': item.get('listingMarketplaceId', ''),
                }
                for item in data.get('lineItems', [])
            ]
        }
    
    @staticmethod
    def _normalize_generic_order(data: Dict) -> Dict:
        """Normalize generic order format"""
        return {
            'order_number': data.get('order_number', data.get('id', '')),
            'external_id': str(data.get('id', '')),
            'customer_name': data.get('customer_name', ''),
            'customer_email': data.get('customer_email', ''),
            'customer_phone': data.get('customer_phone', ''),
            'shipping_address': data.get('shipping_address', {}),
            'billing_address': data.get('billing_address', {}),
            'total_amount': Decimal(str(data.get('total_amount', '0'))),
            'currency': data.get('currency', 'USD'),
            'placed_at': datetime.fromisoformat(data.get('placed_at', timezone.now().isoformat())),
            'items': data.get('items', [])
        }
    
    @staticmethod
    def _process_order_item(order: EnhancedOrder, item_data: Dict) -> EnhancedOrderItem:
        """Process individual order item and reserve stock"""
        # Map external SKU to internal product
        product = MultiChannelOrderService._map_sku_to_product(
            order.channel, item_data.get('sku', '')
        )
        
        if not product:
            logger.warning(f"Product not found for SKU: {item_data.get('sku', '')}")
            # Create order item without product mapping
            return EnhancedOrderItem.objects.create(
                order=order,
                sku=item_data.get('sku', ''),
                name=item_data.get('name', ''),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('price', Decimal('0')),
                status='UNMAPPED'
            )
        
        # Check if it's a bundle product
        bundle = ProductBundle.objects.filter(
            supermarket=order.supermarket,
            sku=item_data.get('sku', '')
        ).first()
        
        if bundle:
            return MultiChannelOrderService._process_bundle_item(order, bundle, item_data)
        else:
            return MultiChannelOrderService._process_single_item(order, product, item_data)
    
    @staticmethod
    def _process_single_item(order: EnhancedOrder, product: Product, item_data: Dict) -> EnhancedOrderItem:
        """Process single product item"""
        quantity = item_data.get('quantity', 1)
        
        # Try to reserve stock
        reservation = StockService.reserve_stock(
            product=product,
            quantity=quantity,
            order=order,
            warehouse=order.channel.default_warehouse
        )
        
        # Create order item
        order_item = EnhancedOrderItem.objects.create(
            order=order,
            product=product,
            sku=item_data.get('sku', product.sku or product.barcode),
            name=item_data.get('name', product.name),
            quantity=quantity,
            unit_price=item_data.get('price', product.selling_price),
            reservation=reservation,
            status='RESERVED' if reservation else 'BACKORDER'
        )
        
        return order_item
    
    @staticmethod
    def _process_bundle_item(order: EnhancedOrder, bundle: ProductBundle, item_data: Dict) -> EnhancedOrderItem:
        """Process bundle/kit product item"""
        quantity = item_data.get('quantity', 1)
        
        # Check if all bundle components are available
        components_available = True
        component_reservations = []
        
        for component in bundle.components.all():
            required_qty = component.quantity * quantity
            reservation = StockService.reserve_stock(
                product=component.product,
                quantity=required_qty,
                order=order,
                warehouse=order.channel.default_warehouse
            )
            
            if reservation:
                component_reservations.append(reservation)
            else:
                components_available = False
                break
        
        if not components_available:
            # Release any reservations made
            for reservation in component_reservations:
                StockService.release_reservation(reservation)
            
            # Create backorder item
            return EnhancedOrderItem.objects.create(
                order=order,
                bundle=bundle,
                sku=item_data.get('sku', bundle.sku),
                name=item_data.get('name', bundle.name),
                quantity=quantity,
                unit_price=item_data.get('price', bundle.price),
                status='BACKORDER'
            )
        
        # Create order item with bundle
        return EnhancedOrderItem.objects.create(
            order=order,
            bundle=bundle,
            sku=item_data.get('sku', bundle.sku),
            name=item_data.get('name', bundle.name),
            quantity=quantity,
            unit_price=item_data.get('price', bundle.price),
            status='RESERVED'
        )
    
    @staticmethod
    def _map_sku_to_product(channel: Channel, external_sku: str) -> Optional[Product]:
        """Map external SKU to internal product"""
        # First try direct SKU mapping
        mapping = SKUMapping.objects.filter(
            channel=channel,
            channel_sku=external_sku
        ).first()
        
        if mapping:
            return mapping.product
        
        # Try direct product lookup by SKU or barcode
        product = Product.objects.filter(
            models.Q(sku=external_sku) | models.Q(barcode=external_sku),
            supermarket=channel.supermarket
        ).first()
        
        return product
    
    @staticmethod
    def _apply_automation_rules(order: EnhancedOrder):
        """Apply automation rules to the order"""
        rules = AutomationRule.objects.filter(
            supermarket=order.supermarket,
            is_active=True,
            trigger_event='ORDER_PLACED'
        ).order_by('priority')
        
        for rule in rules:
            try:
                if MultiChannelOrderService._evaluate_rule_conditions(order, rule):
                    MultiChannelOrderService._execute_rule_actions(order, rule)
            except Exception as e:
                logger.error(f"Failed to apply automation rule {rule.name}: {str(e)}")


class StockService:
    """Service for managing stock levels and reservations"""
    
    @staticmethod
    def reserve_stock(product: Product, quantity: int, order: EnhancedOrder, 
                     warehouse: Optional[Warehouse] = None) -> Optional[StockReservation]:
        """Reserve stock for an order"""
        if not warehouse:
            warehouse = Warehouse.objects.filter(
                supermarket=order.supermarket,
                is_default=True
            ).first()
        
        if not warehouse:
            logger.warning(f"No warehouse found for supermarket {order.supermarket}")
            return None
        
        try:
            with transaction.atomic():
                # Get or create stock level
                stock_level, created = StockLevel.objects.get_or_create(
                    product=product,
                    warehouse=warehouse,
                    defaults={'available': 0, 'reserved': 0}
                )
                
                # Check if enough stock is available
                if stock_level.available < quantity:
                    logger.warning(f"Insufficient stock for {product.name}: {stock_level.available} < {quantity}")
                    return None
                
                # Create reservation
                reservation = StockReservation.objects.create(
                    product=product,
                    warehouse=warehouse,
                    order=order,
                    quantity=quantity,
                    expires_at=timezone.now() + timedelta(hours=24)  # 24-hour reservation
                )
                
                # Update stock levels
                stock_level.available -= quantity
                stock_level.reserved += quantity
                stock_level.save()
                
                # Create stock movement record
                StockMovement.objects.create(
                    product=product,
                    movement_type='RESERVATION',
                    quantity=-quantity,
                    previous_quantity=stock_level.available + quantity,
                    new_quantity=stock_level.available,
                    reference=f"Order {order.order_number}",
                    notes=f"Reserved for order {order.order_number}"
                )
                
                return reservation
                
        except Exception as e:
            logger.error(f"Failed to reserve stock: {str(e)}")
            return None
    
    @staticmethod
    def release_reservation(reservation: StockReservation):
        """Release a stock reservation"""
        try:
            with transaction.atomic():
                stock_level = StockLevel.objects.get(
                    product=reservation.product,
                    warehouse=reservation.warehouse
                )
                
                # Update stock levels
                stock_level.available += reservation.quantity
                stock_level.reserved -= reservation.quantity
                stock_level.save()
                
                # Create stock movement record
                StockMovement.objects.create(
                    product=reservation.product,
                    movement_type='RELEASE',
                    quantity=reservation.quantity,
                    previous_quantity=stock_level.available - reservation.quantity,
                    new_quantity=stock_level.available,
                    reference=f"Order {reservation.order.order_number}",
                    notes=f"Released reservation for order {reservation.order.order_number}"
                )
                
                # Delete reservation
                reservation.delete()
                
        except Exception as e:
            logger.error(f"Failed to release reservation: {str(e)}")
    
    @staticmethod
    def fulfill_order_item(order_item: EnhancedOrderItem):
        """Fulfill an order item by converting reservation to actual stock deduction"""
        if not order_item.reservation:
            logger.warning(f"No reservation found for order item {order_item.id}")
            return
        
        try:
            with transaction.atomic():
                reservation = order_item.reservation
                stock_level = StockLevel.objects.get(
                    product=reservation.product,
                    warehouse=reservation.warehouse
                )
                
                # Update stock levels - remove from reserved
                stock_level.reserved -= reservation.quantity
                stock_level.save()
                
                # Create stock movement record
                StockMovement.objects.create(
                    product=reservation.product,
                    movement_type='OUT',
                    quantity=-reservation.quantity,
                    previous_quantity=stock_level.available + stock_level.reserved + reservation.quantity,
                    new_quantity=stock_level.available + stock_level.reserved,
                    reference=f"Order {reservation.order.order_number}",
                    notes=f"Fulfilled order {reservation.order.order_number}"
                )
                
                # Update order item status
                order_item.status = 'FULFILLED'
                order_item.save()
                
                # Delete reservation
                reservation.delete()
                
        except Exception as e:
            logger.error(f"Failed to fulfill order item: {str(e)}")
    
    @staticmethod
    def sync_stock_to_channels(product: Product):
        """Sync stock levels to all connected channels"""
        supermarket = product.supermarket
        channels = Channel.objects.filter(
            supermarket=supermarket,
            is_active=True,
            auto_sync_stock=True
        )
        
        for channel in channels:
            try:
                StockService._sync_product_to_channel(product, channel)
            except Exception as e:
                logger.error(f"Failed to sync stock to {channel.name}: {str(e)}")
                ChannelSyncLog.objects.create(
                    channel=channel,
                    type='STOCK_SYNC',
                    status='ERROR',
                    message=f'Failed to sync stock for {product.name}: {str(e)}',
                    records_processed=1,
                    records_failed=1
                )
    
    @staticmethod
    def _sync_product_to_channel(product: Product, channel: Channel):
        """Sync a single product's stock to a channel"""
        # Get total available stock across all warehouses
        total_available = StockLevel.objects.filter(
            product=product,
            warehouse__supermarket=channel.supermarket
        ).aggregate(
            total=models.Sum('available')
        )['total'] or 0
        
        # Get SKU mapping for this channel
        mapping = SKUMapping.objects.filter(
            product=product,
            channel=channel
        ).first()
        
        if not mapping:
            logger.warning(f"No SKU mapping found for {product.name} on {channel.name}")
            return
        
        # Channel-specific sync logic would go here
        # This would call the appropriate API for each channel type
        if channel.type == 'SHOPIFY':
            StockService._sync_to_shopify(channel, mapping.channel_sku, total_available)
        elif channel.type == 'AMAZON':
            StockService._sync_to_amazon(channel, mapping.channel_sku, total_available)
        elif channel.type == 'EBAY':
            StockService._sync_to_ebay(channel, mapping.channel_sku, total_available)
        
        # Log successful sync
        ChannelSyncLog.objects.create(
            channel=channel,
            type='STOCK_SYNC',
            status='SUCCESS',
            message=f'Successfully synced stock for {product.name}',
            records_processed=1,
            records_successful=1
        )
    
    @staticmethod
    def _sync_to_shopify(channel: Channel, sku: str, quantity: int):
        """Sync stock to Shopify"""
        # Implementation would use Shopify API
        pass
    
    @staticmethod
    def _sync_to_amazon(channel: Channel, sku: str, quantity: int):
        """Sync stock to Amazon"""
        # Implementation would use Amazon MWS/SP-API
        pass
    
    @staticmethod
    def _sync_to_ebay(channel: Channel, sku: str, quantity: int):
        """Sync stock to eBay"""
        # Implementation would use eBay API
        pass


class AutomationService:
    """Service for handling automation rules and workflows"""
    
    @staticmethod
    def _evaluate_rule_conditions(order: EnhancedOrder, rule: AutomationRule) -> bool:
        """Evaluate if rule conditions are met"""
        conditions = rule.conditions
        
        # Example condition evaluations
        if 'min_order_value' in conditions:
            if order.total_amount < Decimal(str(conditions['min_order_value'])):
                return False
        
        if 'channel_types' in conditions:
            if order.channel.type not in conditions['channel_types']:
                return False
        
        if 'customer_email_contains' in conditions:
            if conditions['customer_email_contains'] not in order.customer_email:
                return False
        
        return True
    
    @staticmethod
    def _execute_rule_actions(order: EnhancedOrder, rule: AutomationRule):
        """Execute rule actions"""
        actions = rule.actions
        
        # Example actions
        if 'assign_warehouse' in actions:
            warehouse_id = actions['assign_warehouse']
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
                order.assigned_warehouse = warehouse
                order.save()
            except Warehouse.DoesNotExist:
                logger.error(f"Warehouse {warehouse_id} not found for rule {rule.name}")
        
        if 'set_priority' in actions:
            order.priority = actions['set_priority']
            order.save()
        
        if 'add_tags' in actions:
            current_tags = order.tags or []
            new_tags = actions['add_tags']
            order.tags = list(set(current_tags + new_tags))
            order.save()
        
        if 'send_notification' in actions:
            # Implementation for sending notifications
            pass


class ChannelConnectorService:
    """Service for managing channel connections and webhooks"""
    
    @staticmethod
    def setup_channel_webhooks(channel: Channel):
        """Setup webhooks for a channel"""
        if channel.type == 'SHOPIFY':
            ChannelConnectorService._setup_shopify_webhooks(channel)
        elif channel.type == 'AMAZON':
            ChannelConnectorService._setup_amazon_notifications(channel)
        elif channel.type == 'EBAY':
            ChannelConnectorService._setup_ebay_notifications(channel)
    
    @staticmethod
    def _setup_shopify_webhooks(channel: Channel):
        """Setup Shopify webhooks"""
        # Implementation would create webhooks via Shopify API
        webhooks = [
            'orders/create',
            'orders/updated',
            'orders/cancelled',
            'inventory_levels/update'
        ]
        # Create webhooks pointing to channel.webhook_url
        pass
    
    @staticmethod
    def _setup_amazon_notifications(channel: Channel):
        """Setup Amazon notifications"""
        # Implementation would setup Amazon SQS notifications
        pass
    
    @staticmethod
    def _setup_ebay_notifications(channel: Channel):
        """Setup eBay notifications"""
        # Implementation would setup eBay notifications
        pass