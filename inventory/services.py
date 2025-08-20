"""
Inventory services for barcode generation, PDF tickets, and other utilities
"""
import io
import os
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

import barcode
import qrcode
from barcode import Code128, EAN13, UPCA
from barcode.writer import ImageWriter, SVGWriter
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.platypus.flowables import PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics.barcode.common import Barcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import Product, Barcode as BarcodeModel


class BarcodeService:
    """Service for generating and managing barcodes"""
    
    BARCODE_TYPES = {
        'CODE128': Code128,
        'EAN13': EAN13,
        'UPCA': UPCA,
    }
    
    @staticmethod
    def generate_barcode_number(product_id: str = None) -> str:
        """Generate a unique barcode number"""
        import uuid
        import random
        
        if product_id:
            # Use product ID to generate consistent barcode
            base = str(hash(product_id))[-10:]
        else:
            # Generate random barcode
            base = str(random.randint(1000000000, 9999999999))
        
        # Ensure it's 12 digits for EAN13 (13th digit is check digit)
        barcode_num = base.zfill(12)
        return barcode_num
    
    @staticmethod
    def generate_barcode_image(code: str, barcode_type: str = 'CODE128', format: str = 'PNG') -> bytes:
        """Generate barcode image"""
        try:
            barcode_class = BarcodeService.BARCODE_TYPES.get(barcode_type, Code128)
            
            # Create barcode with image writer
            writer = ImageWriter()
            barcode_instance = barcode_class(code, writer=writer)
            
            # Generate image
            buffer = io.BytesIO()
            barcode_instance.write(buffer, options={
                'module_width': 0.2,
                'module_height': 15.0,
                'quiet_zone': 6.5,
                'font_size': 10,
                'text_distance': 5.0,
                'background': 'white',
                'foreground': 'black',
            })
            
            return buffer.getvalue()
        except Exception as e:
            raise ValueError(f"Error generating barcode: {str(e)}")
    
    @staticmethod
    def generate_qr_code(data: str, size: int = 10) -> bytes:
        """Generate QR code image"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
        except Exception as e:
            raise ValueError(f"Error generating QR code: {str(e)}")
    
    @staticmethod
    def create_product_barcode(product: Product, barcode_type: str = 'CODE128') -> BarcodeModel:
        """Create and save barcode for a product"""
        if not product.barcode:
            product.barcode = BarcodeService.generate_barcode_number(str(product.id))
            product.save()
        
        # Create or update barcode record
        barcode_obj, created = BarcodeModel.objects.get_or_create(
            product=product,
            code=product.barcode,
            defaults={
                'barcode_type': barcode_type,
                'is_primary': True
            }
        )
        
        return barcode_obj


class TicketService:
    """Service for generating product tickets and labels"""
    
    @staticmethod
    def generate_product_ticket(product: Product, include_qr: bool = True) -> bytes:
        """Generate a single product ticket/label as PDF"""
        buffer = io.BytesIO()
        
        # Create PDF with custom page size (ticket size)
        ticket_width = 4 * inch  # 4 inches wide
        ticket_height = 2.5 * inch  # 2.5 inches tall
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(ticket_width, ticket_height),
            rightMargin=0.2*inch,
            leftMargin=0.2*inch,
            topMargin=0.2*inch,
            bottomMargin=0.2*inch
        )
        
        # Build content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            alignment=1,  # Center
            textColor=colors.black
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            alignment=1,  # Center
        )
        
        # Product name
        story.append(Paragraph(product.name[:30], title_style))
        
        # Price
        price_text = f"<b>${product.price:.2f}</b>"
        story.append(Paragraph(price_text, title_style))
        
        # Generate barcode
        try:
            barcode_img = BarcodeService.generate_barcode_image(product.barcode)
            barcode_buffer = io.BytesIO(barcode_img)
            
            # Add barcode image
            barcode_image = RLImage(barcode_buffer, width=2.5*inch, height=0.8*inch)
            story.append(barcode_image)
            
        except Exception as e:
            # Fallback to text if barcode generation fails
            story.append(Paragraph(f"Barcode: {product.barcode}", normal_style))
        
        # Product details
        details = []
        if product.brand:
            details.append(f"Brand: {product.brand}")
        if product.category:
            details.append(f"Category: {product.category.name if hasattr(product.category, 'name') else product.category}")
        if product.weight:
            details.append(f"Weight: {product.weight}")
        
        for detail in details:
            story.append(Paragraph(detail, normal_style))
        
        # Expiry date
        if product.expiry_date:
            expiry_text = f"Exp: {product.expiry_date.strftime('%m/%d/%Y')}"
            story.append(Paragraph(expiry_text, normal_style))
        
        # QR Code with product info (optional)
        if include_qr:
            try:
                qr_data = {
                    'name': product.name,
                    'barcode': product.barcode,
                    'price': str(product.price),
                    'id': str(product.id)
                }
                qr_text = f"Product: {product.name}\nBarcode: {product.barcode}\nPrice: ${product.price}"
                qr_img = BarcodeService.generate_qr_code(qr_text)
                qr_buffer = io.BytesIO(qr_img)
                
                qr_image = RLImage(qr_buffer, width=0.8*inch, height=0.8*inch)
                story.append(qr_image)
            except Exception:
                pass  # Skip QR if generation fails
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_bulk_tickets(products: List[Product], tickets_per_page: int = 8) -> bytes:
        """Generate multiple product tickets in a single PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=20,
            alignment=1
        )
        
        story.append(Paragraph("Product Tickets", title_style))
        story.append(Spacer(1, 20))
        
        # Create table for tickets
        tickets_data = []
        current_row = []
        
        for i, product in enumerate(products):
            # Generate individual ticket content
            ticket_content = TicketService._create_ticket_cell_content(product)
            current_row.append(ticket_content)
            
            # If we have 2 tickets in a row or it's the last product
            if len(current_row) == 2 or i == len(products) - 1:
                # Pad row if needed
                while len(current_row) < 2:
                    current_row.append("")
                
                tickets_data.append(current_row)
                current_row = []
        
        if tickets_data:
            # Create table
            table = Table(tickets_data, colWidths=[3.5*inch, 3.5*inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey]),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def _create_ticket_cell_content(product: Product) -> str:
        """Create HTML content for a single ticket cell"""
        content = f"""
        <b>{product.name[:25]}</b><br/>
        <font size="12"><b>${product.price:.2f}</b></font><br/>
        Barcode: {product.barcode}<br/>
        """
        
        if product.brand:
            content += f"Brand: {product.brand}<br/>"
        
        if product.expiry_date:
            content += f"Exp: {product.expiry_date.strftime('%m/%d/%Y')}<br/>"
        
        return content
    
    @staticmethod
    def generate_barcode_sheet(products: List[Product], barcodes_per_page: int = 20) -> bytes:
        """Generate a sheet with just barcodes for multiple products"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Product Barcodes", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Create table for barcodes
        barcode_data = []
        current_row = []
        
        for i, product in enumerate(products):
            try:
                # Generate barcode image
                barcode_img = BarcodeService.generate_barcode_image(product.barcode)
                barcode_buffer = io.BytesIO(barcode_img)
                
                # Create barcode cell content
                barcode_content = [
                    RLImage(barcode_buffer, width=2*inch, height=0.6*inch),
                    Paragraph(f"{product.name[:20]}", styles['Normal']),
                    Paragraph(f"${product.price:.2f}", styles['Normal'])
                ]
                
                current_row.append(barcode_content)
                
                # If we have 3 barcodes in a row or it's the last product
                if len(current_row) == 3 or i == len(products) - 1:
                    # Pad row if needed
                    while len(current_row) < 3:
                        current_row.append("")
                    
                    barcode_data.append(current_row)
                    current_row = []
                    
            except Exception as e:
                # Skip products with barcode generation errors
                continue
        
        if barcode_data:
            table = Table(barcode_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


class ProductService:
    """Service for product-related operations"""
    
    @staticmethod
    def create_product_with_barcode(product_data: Dict[str, Any], user=None) -> Product:
        """Create a product and automatically generate barcode"""
        # Generate barcode if not provided
        if not product_data.get('barcode'):
            product_data['barcode'] = BarcodeService.generate_barcode_number()
        
        # Create product
        product = Product.objects.create(**product_data)
        
        # Create barcode record
        BarcodeService.create_product_barcode(product)
        
        return product
    
    @staticmethod
    def bulk_create_products_with_barcodes(products_data: List[Dict[str, Any]], user=None) -> List[Product]:
        """Create multiple products with barcodes"""
        created_products = []
        
        for product_data in products_data:
            try:
                product = ProductService.create_product_with_barcode(product_data, user)
                created_products.append(product)
            except Exception as e:
                # Log error but continue with other products
                print(f"Error creating product {product_data.get('name', 'Unknown')}: {str(e)}")
                continue
        
        return created_products