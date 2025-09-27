"""
Webhook handlers for multi-channel order management
Processes incoming webhooks from various sales channels
"""

import json
import logging
import hmac
import hashlib
from typing import Dict, Any
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings

from .enhanced_models import Channel
from .services import MultiChannelOrderService, StockService
from .enhanced_models import ChannelSyncLog

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ShopifyWebhookView(View):
    """Handle Shopify webhooks"""
    
    def post(self, request, channel_id):
        try:
            # Get channel
            channel = Channel.objects.get(id=channel_id, type='SHOPIFY')
            
            # Verify webhook signature
            if not self._verify_shopify_webhook(request, channel):
                logger.warning(f"Invalid Shopify webhook signature for channel {channel_id}")
                return HttpResponseBadRequest("Invalid signature")
            
            # Parse webhook data
            webhook_data = json.loads(request.body)
            webhook_topic = request.headers.get('X-Shopify-Topic', '')
            
            # Process webhook based on topic
            if webhook_topic == 'orders/create':
                self._handle_order_create(channel, webhook_data)
            elif webhook_topic == 'orders/updated':
                self._handle_order_update(channel, webhook_data)
            elif webhook_topic == 'orders/cancelled':
                self._handle_order_cancel(channel, webhook_data)
            elif webhook_topic == 'inventory_levels/update':
                self._handle_inventory_update(channel, webhook_data)
            else:
                logger.info(f"Unhandled Shopify webhook topic: {webhook_topic}")
            
            return HttpResponse("OK")
            
        except Channel.DoesNotExist:
            logger.error(f"Channel {channel_id} not found")
            return HttpResponseBadRequest("Channel not found")
        except Exception as e:
            logger.error(f"Error processing Shopify webhook: {str(e)}")
            return HttpResponseBadRequest("Webhook processing failed")
    
    def _verify_shopify_webhook(self, request, channel: Channel) -> bool:
        """Verify Shopify webhook signature"""
        webhook_secret = channel.credentials.get('webhook_secret', '')
        if not webhook_secret:
            return True  # Skip verification if no secret configured
        
        signature = request.headers.get('X-Shopify-Hmac-Sha256', '')
        body = request.body
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _handle_order_create(self, channel: Channel, order_data: Dict):
        """Handle new order creation"""
        try:
            order = MultiChannelOrderService.import_order_from_channel(channel, order_data)
            logger.info(f"Successfully imported Shopify order {order.order_number}")
        except Exception as e:
            logger.error(f"Failed to import Shopify order: {str(e)}")
    
    def _handle_order_update(self, channel: Channel, order_data: Dict):
        """Handle order updates"""
        try:
            external_order_id = str(order_data.get('id', ''))
            order = channel.orders.filter(external_order_id=external_order_id).first()
            
            if order:
                # Update order status based on Shopify status
                shopify_status = order_data.get('fulfillment_status', '')
                if shopify_status == 'fulfilled':
                    order.fulfillment_status = 'FULFILLED'
                elif shopify_status == 'partial':
                    order.fulfillment_status = 'PARTIAL'
                
                order.save()
                logger.info(f"Updated Shopify order {order.order_number}")
            
        except Exception as e:
            logger.error(f"Failed to update Shopify order: {str(e)}")
    
    def _handle_order_cancel(self, channel: Channel, order_data: Dict):
        """Handle order cancellation"""
        try:
            external_order_id = str(order_data.get('id', ''))
            order = channel.orders.filter(external_order_id=external_order_id).first()
            
            if order:
                order.status = 'CANCELLED'
                order.save()
                
                # Release any stock reservations
                for item in order.items.all():
                    if item.reservation:
                        StockService.release_reservation(item.reservation)
                
                logger.info(f"Cancelled Shopify order {order.order_number}")
            
        except Exception as e:
            logger.error(f"Failed to cancel Shopify order: {str(e)}")
    
    def _handle_inventory_update(self, channel: Channel, inventory_data: Dict):
        """Handle inventory level updates from Shopify"""
        # This would sync inventory changes back to internal system
        pass


@method_decorator(csrf_exempt, name='dispatch')
class AmazonWebhookView(View):
    """Handle Amazon SQS notifications"""
    
    def post(self, request, channel_id):
        try:
            # Get channel
            channel = Channel.objects.get(id=channel_id, type='AMAZON')
            
            # Parse SQS message
            message_data = json.loads(request.body)
            
            # Process different notification types
            notification_type = message_data.get('NotificationType', '')
            
            if notification_type == 'AnyOfferChanged':
                self._handle_offer_change(channel, message_data)
            elif notification_type == 'OrderStatusChange':
                self._handle_order_status_change(channel, message_data)
            elif notification_type == 'FeedProcessingFinished':
                self._handle_feed_processing(channel, message_data)
            else:
                logger.info(f"Unhandled Amazon notification type: {notification_type}")
            
            return HttpResponse("OK")
            
        except Channel.DoesNotExist:
            logger.error(f"Channel {channel_id} not found")
            return HttpResponseBadRequest("Channel not found")
        except Exception as e:
            logger.error(f"Error processing Amazon webhook: {str(e)}")
            return HttpResponseBadRequest("Webhook processing failed")
    
    def _handle_offer_change(self, channel: Channel, message_data: Dict):
        """Handle Amazon offer changes"""
        # Implementation for handling price/inventory changes
        pass
    
    def _handle_order_status_change(self, channel: Channel, message_data: Dict):
        """Handle Amazon order status changes"""
        # Implementation for handling order status updates
        pass
    
    def _handle_feed_processing(self, channel: Channel, message_data: Dict):
        """Handle Amazon feed processing results"""
        # Implementation for handling feed processing results
        pass


@method_decorator(csrf_exempt, name='dispatch')
class EbayWebhookView(View):
    """Handle eBay notifications"""
    
    def post(self, request, channel_id):
        try:
            # Get channel
            channel = Channel.objects.get(id=channel_id, type='EBAY')
            
            # Verify eBay signature
            if not self._verify_ebay_webhook(request, channel):
                logger.warning(f"Invalid eBay webhook signature for channel {channel_id}")
                return HttpResponseBadRequest("Invalid signature")
            
            # Parse webhook data
            webhook_data = json.loads(request.body)
            
            # Process different notification types
            for notification in webhook_data.get('notifications', []):
                notification_type = notification.get('notificationEventType', '')
                
                if notification_type == 'ITEM_SOLD':
                    self._handle_item_sold(channel, notification)
                elif notification_type == 'ORDER_PAYMENT_RECEIVED':
                    self._handle_payment_received(channel, notification)
                elif notification_type == 'ORDER_SHIPPED':
                    self._handle_order_shipped(channel, notification)
                else:
                    logger.info(f"Unhandled eBay notification type: {notification_type}")
            
            return HttpResponse("OK")
            
        except Channel.DoesNotExist:
            logger.error(f"Channel {channel_id} not found")
            return HttpResponseBadRequest("Channel not found")
        except Exception as e:
            logger.error(f"Error processing eBay webhook: {str(e)}")
            return HttpResponseBadRequest("Webhook processing failed")
    
    def _verify_ebay_webhook(self, request, channel: Channel) -> bool:
        """Verify eBay webhook signature"""
        # eBay webhook verification logic
        return True  # Simplified for now
    
    def _handle_item_sold(self, channel: Channel, notification: Dict):
        """Handle eBay item sold notification"""
        # Implementation for handling sold items
        pass
    
    def _handle_payment_received(self, channel: Channel, notification: Dict):
        """Handle eBay payment received notification"""
        # Implementation for handling payment notifications
        pass
    
    def _handle_order_shipped(self, channel: Channel, notification: Dict):
        """Handle eBay order shipped notification"""
        # Implementation for handling shipping notifications
        pass


@method_decorator(csrf_exempt, name='dispatch')
class WooCommerceWebhookView(View):
    """Handle WooCommerce webhooks"""
    
    def post(self, request, channel_id):
        try:
            # Get channel
            channel = Channel.objects.get(id=channel_id, type='WOOCOMMERCE')
            
            # Verify webhook signature
            if not self._verify_woocommerce_webhook(request, channel):
                logger.warning(f"Invalid WooCommerce webhook signature for channel {channel_id}")
                return HttpResponseBadRequest("Invalid signature")
            
            # Parse webhook data
            webhook_data = json.loads(request.body)
            webhook_event = request.headers.get('X-WC-Webhook-Event', '')
            
            # Process webhook based on event
            if webhook_event == 'order.created':
                self._handle_order_create(channel, webhook_data)
            elif webhook_event == 'order.updated':
                self._handle_order_update(channel, webhook_data)
            elif webhook_event == 'order.deleted':
                self._handle_order_delete(channel, webhook_data)
            else:
                logger.info(f"Unhandled WooCommerce webhook event: {webhook_event}")
            
            return HttpResponse("OK")
            
        except Channel.DoesNotExist:
            logger.error(f"Channel {channel_id} not found")
            return HttpResponseBadRequest("Channel not found")
        except Exception as e:
            logger.error(f"Error processing WooCommerce webhook: {str(e)}")
            return HttpResponseBadRequest("Webhook processing failed")
    
    def _verify_woocommerce_webhook(self, request, channel: Channel) -> bool:
        """Verify WooCommerce webhook signature"""
        webhook_secret = channel.credentials.get('webhook_secret', '')
        if not webhook_secret:
            return True
        
        signature = request.headers.get('X-WC-Webhook-Signature', '')
        body = request.body
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest().hex()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _handle_order_create(self, channel: Channel, order_data: Dict):
        """Handle new WooCommerce order"""
        try:
            order = MultiChannelOrderService.import_order_from_channel(channel, order_data)
            logger.info(f"Successfully imported WooCommerce order {order.order_number}")
        except Exception as e:
            logger.error(f"Failed to import WooCommerce order: {str(e)}")
    
    def _handle_order_update(self, channel: Channel, order_data: Dict):
        """Handle WooCommerce order update"""
        try:
            external_order_id = str(order_data.get('id', ''))
            order = channel.orders.filter(external_order_id=external_order_id).first()
            
            if order:
                # Update order status
                wc_status = order_data.get('status', '')
                if wc_status == 'completed':
                    order.fulfillment_status = 'FULFILLED'
                elif wc_status == 'processing':
                    order.status = 'PROCESSING'
                elif wc_status == 'cancelled':
                    order.status = 'CANCELLED'
                
                order.save()
                logger.info(f"Updated WooCommerce order {order.order_number}")
            
        except Exception as e:
            logger.error(f"Failed to update WooCommerce order: {str(e)}")
    
    def _handle_order_delete(self, channel: Channel, order_data: Dict):
        """Handle WooCommerce order deletion"""
        try:
            external_order_id = str(order_data.get('id', ''))
            order = channel.orders.filter(external_order_id=external_order_id).first()
            
            if order:
                order.status = 'CANCELLED'
                order.save()
                
                # Release stock reservations
                for item in order.items.all():
                    if item.reservation:
                        StockService.release_reservation(item.reservation)
                
                logger.info(f"Deleted WooCommerce order {order.order_number}")
            
        except Exception as e:
            logger.error(f"Failed to delete WooCommerce order: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class EtsyWebhookView(View):
    """Handle Etsy webhooks"""
    
    def post(self, request, channel_id):
        try:
            # Get channel
            channel = Channel.objects.get(id=channel_id, type='ETSY')
            
            # Parse webhook data
            webhook_data = json.loads(request.body)
            event_type = webhook_data.get('event_type', '')
            
            # Process different event types
            if event_type == 'receipt_paid':
                self._handle_receipt_paid(channel, webhook_data)
            elif event_type == 'receipt_shipped':
                self._handle_receipt_shipped(channel, webhook_data)
            else:
                logger.info(f"Unhandled Etsy webhook event: {event_type}")
            
            return HttpResponse("OK")
            
        except Channel.DoesNotExist:
            logger.error(f"Channel {channel_id} not found")
            return HttpResponseBadRequest("Channel not found")
        except Exception as e:
            logger.error(f"Error processing Etsy webhook: {str(e)}")
            return HttpResponseBadRequest("Webhook processing failed")
    
    def _handle_receipt_paid(self, channel: Channel, webhook_data: Dict):
        """Handle Etsy receipt paid notification"""
        # Implementation for handling paid receipts
        pass
    
    def _handle_receipt_shipped(self, channel: Channel, webhook_data: Dict):
        """Handle Etsy receipt shipped notification"""
        # Implementation for handling shipped receipts
        pass


# URL patterns for webhooks
webhook_urls = [
    ('shopify/<uuid:channel_id>/', ShopifyWebhookView.as_view(), 'shopify_webhook'),
    ('amazon/<uuid:channel_id>/', AmazonWebhookView.as_view(), 'amazon_webhook'),
    ('ebay/<uuid:channel_id>/', EbayWebhookView.as_view(), 'ebay_webhook'),
    ('woocommerce/<uuid:channel_id>/', WooCommerceWebhookView.as_view(), 'woocommerce_webhook'),
    ('etsy/<uuid:channel_id>/', EtsyWebhookView.as_view(), 'etsy_webhook'),
]