import pandas as pd
import numpy as np
from PIL import Image
import easyocr
import cv2
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from django.core.files.storage import default_storage
from django.conf import settings
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import json

from .models import UploadSession, ExtractedProduct, FileProcessingLog, ImageProcessingResult
from inventory.models import Product, Category, Supplier

logger = logging.getLogger(__name__)


class ExcelProcessor:
    """Process Excel files and extract product data"""
    
    def __init__(self, upload_session: UploadSession):
        self.upload_session = upload_session
        self.logger = FileProcessingLogger(upload_session)
    
    def process_file(self) -> bool:
        """Process the Excel file and extract products"""
        try:
            self.logger.log('INFO', 'Starting Excel file processing')
            
            # Read Excel file
            df = pd.read_excel(self.upload_session.file_path)
            
            # Update session with total rows
            self.upload_session.total_rows = len(df)
            self.upload_session.status = 'PROCESSING'
            self.upload_session.save()
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    self.process_row(index + 1, row)
                    self.upload_session.processed_rows += 1
                    
                    # Update progress
                    progress = (self.upload_session.processed_rows / self.upload_session.total_rows) * 100
                    self.upload_session.progress = int(progress)
                    self.upload_session.save()
                    
                except Exception as e:
                    self.logger.log('ERROR', f'Error processing row {index + 1}: {str(e)}', {'row_data': row.to_dict()})
                    self.upload_session.failed_rows += 1
            
            self.upload_session.status = 'COMPLETED'
            self.upload_session.completed_at = datetime.now()
            self.upload_session.save()
            
            self.logger.log('INFO', 'Excel file processing completed successfully')
            return True
            
        except Exception as e:
            self.logger.log('CRITICAL', f'Failed to process Excel file: {str(e)}')
            self.upload_session.status = 'ERROR'
            self.upload_session.error_message = str(e)
            self.upload_session.save()
            return False
    
    def process_row(self, row_number: int, row: pd.Series):
        """Process a single row from Excel file"""
        # Extract product data from row
        product_data = self.extract_product_data(row)
        
        # Validate the data
        validation_errors = self.validate_product_data(product_data)
        
        # Create ExtractedProduct
        extracted_product = ExtractedProduct.objects.create(
            upload_session=self.upload_session,
            row_number=row_number,
            raw_data=row.to_dict(),
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            **product_data
        )
        
        if validation_errors:
            self.logger.log('WARNING', f'Validation errors in row {row_number}', {
                'errors': validation_errors,
                'product_name': product_data.get('name', 'Unknown')
            })
        else:
            self.upload_session.successful_rows += 1
    
    def extract_product_data(self, row: pd.Series) -> Dict[str, Any]:
        """Extract product data from a row"""
        # Common column name mappings
        column_mappings = {
            'name': ['name', 'product_name', 'product', 'item_name', 'title'],
            'barcode': ['barcode', 'ean', 'upc', 'code', 'product_code'],
            'category': ['category', 'category_name', 'type', 'product_type'],
            'supplier': ['supplier', 'vendor', 'manufacturer', 'brand'],
            'brand': ['brand', 'brand_name', 'make'],
            'description': ['description', 'desc', 'details', 'notes'],
            'cost_price': ['cost_price', 'cost', 'purchase_price', 'buy_price'],
            'selling_price': ['selling_price', 'sell_price', 'retail_price', 'price'],
            'price': ['price', 'current_price', 'unit_price'],
            'quantity': ['quantity', 'qty', 'stock', 'inventory', 'units'],
            'min_stock_level': ['min_stock', 'reorder_level', 'minimum_stock'],
            'weight': ['weight', 'size', 'unit_size'],
            'origin': ['origin', 'country', 'made_in'],
            'expiry_date': ['expiry_date', 'expiry', 'exp_date', 'best_before'],
            'location': ['location', 'aisle', 'shelf', 'position'],
            'halal_certified': ['halal', 'halal_certified', 'is_halal'],
        }
        
        product_data = {}
        
        # Extract data using column mappings
        for field, possible_columns in column_mappings.items():
            value = self.find_column_value(row, possible_columns)
            if value is not None:
                product_data[field] = self.clean_value(field, value)
        
        return product_data
    
    def find_column_value(self, row: pd.Series, possible_columns: List[str]) -> Any:
        """Find value from possible column names"""
        for col in possible_columns:
            # Try exact match first
            if col in row.index:
                return row[col]
            
            # Try case-insensitive match
            for actual_col in row.index:
                if col.lower() == actual_col.lower():
                    return row[actual_col]
        
        return None
    
    def clean_value(self, field: str, value: Any) -> Any:
        """Clean and convert values based on field type"""
        if pd.isna(value) or value == '':
            return None
        
        try:
            if field in ['cost_price', 'selling_price', 'price']:
                # Clean price values
                if isinstance(value, str):
                    # Remove currency symbols and spaces
                    cleaned = re.sub(r'[^\d.,]', '', str(value))
                    return Decimal(cleaned) if cleaned else None
                return Decimal(str(value))
            
            elif field in ['quantity', 'min_stock_level']:
                return int(float(value))
            
            elif field == 'expiry_date':
                if isinstance(value, (date, datetime)):
                    return value.date() if isinstance(value, datetime) else value
                # Try to parse string dates
                return pd.to_datetime(value).date()
            
            elif field == 'halal_certified':
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ['true', 'yes', '1', 'halal', 'certified']
            
            else:
                return str(value).strip()
        
        except (ValueError, InvalidOperation, TypeError):
            return None
    
    def validate_product_data(self, product_data: Dict[str, Any]) -> List[str]:
        """Validate extracted product data"""
        errors = []
        
        # Required fields
        if not product_data.get('name'):
            errors.append('Product name is required')
        
        if not product_data.get('barcode'):
            errors.append('Barcode is required')
        
        # Price validation
        if product_data.get('selling_price') and product_data.get('cost_price'):
            if product_data['selling_price'] < product_data['cost_price']:
                errors.append('Selling price cannot be less than cost price')
        
        # Quantity validation
        if product_data.get('quantity') is not None and product_data['quantity'] < 0:
            errors.append('Quantity cannot be negative')
        
        # Date validation
        if product_data.get('expiry_date'):
            if product_data['expiry_date'] < date.today():
                errors.append('Expiry date cannot be in the past')
        
        return errors


class ImageProcessor:
    """Process images using OCR to extract product information"""
    
    def __init__(self, upload_session: UploadSession):
        self.upload_session = upload_session
        self.logger = FileProcessingLogger(upload_session)
        self.ocr_reader = easyocr.Reader(['en'])
    
    def process_image(self) -> bool:
        """Process image and extract text/product information"""
        try:
            self.logger.log('INFO', 'Starting image processing')
            
            # Load image
            image_path = self.upload_session.file_path
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError("Could not load image")
            
            # Get image info
            height, width = image.shape[:2]
            image_size = os.path.getsize(image_path)
            
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Extract text using OCR
            start_time = datetime.now()
            ocr_results = self.ocr_reader.readtext(processed_image)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract structured information
            extracted_text = ' '.join([result[1] for result in ocr_results])
            confidence_score = np.mean([result[2] for result in ocr_results])
            
            # Detect products, prices, and barcodes
            detected_products = self.detect_products(ocr_results)
            detected_prices = self.detect_prices(ocr_results)
            detected_barcodes = self.detect_barcodes(ocr_results)
            
            # Save results
            ImageProcessingResult.objects.create(
                upload_session=self.upload_session,
                image_path=image_path,
                image_size=image_size,
                image_dimensions=f"{width}x{height}",
                extracted_text=extracted_text,
                confidence_score=confidence_score,
                detected_products=detected_products,
                detected_prices=detected_prices,
                detected_barcodes=detected_barcodes,
                processing_time=processing_time
            )
            
            # Create extracted products from detected information
            self.create_extracted_products(detected_products, detected_prices, detected_barcodes)
            
            self.upload_session.status = 'COMPLETED'
            self.upload_session.completed_at = datetime.now()
            self.upload_session.save()
            
            self.logger.log('INFO', 'Image processing completed successfully')
            return True
            
        except Exception as e:
            self.logger.log('CRITICAL', f'Failed to process image: {str(e)}')
            self.upload_session.status = 'ERROR'
            self.upload_session.error_message = str(e)
            self.upload_session.save()
            return False
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def detect_products(self, ocr_results: List[Tuple]) -> List[Dict[str, Any]]:
        """Detect product names from OCR results"""
        products = []
        
        for bbox, text, confidence in ocr_results:
            # Skip low confidence results
            if confidence < 0.5:
                continue
            
            # Look for product-like patterns
            if self.is_product_name(text):
                products.append({
                    'name': text.strip(),
                    'confidence': confidence,
                    'bbox': bbox
                })
        
        return products
    
    def detect_prices(self, ocr_results: List[Tuple]) -> List[Dict[str, Any]]:
        """Detect prices from OCR results"""
        prices = []
        price_pattern = r'[\$£€¥₹]?\s*\d+[.,]\d{2}|\d+[.,]\d{2}\s*[\$£€¥₹]?'
        
        for bbox, text, confidence in ocr_results:
            if confidence < 0.5:
                continue
            
            price_matches = re.findall(price_pattern, text)
            for match in price_matches:
                # Clean and convert price
                cleaned_price = re.sub(r'[^\d.,]', '', match)
                try:
                    price_value = float(cleaned_price.replace(',', '.'))
                    prices.append({
                        'price': price_value,
                        'original_text': match,
                        'confidence': confidence,
                        'bbox': bbox
                    })
                except ValueError:
                    continue
        
        return prices
    
    def detect_barcodes(self, ocr_results: List[Tuple]) -> List[Dict[str, Any]]:
        """Detect barcodes from OCR results"""
        barcodes = []
        barcode_patterns = [
            r'\b\d{12,13}\b',  # EAN-13, UPC-A
            r'\b\d{8}\b',      # EAN-8
            r'\b\d{14}\b',     # GTIN-14
        ]
        
        for bbox, text, confidence in ocr_results:
            if confidence < 0.7:  # Higher confidence for barcodes
                continue
            
            for pattern in barcode_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    barcodes.append({
                        'barcode': match,
                        'confidence': confidence,
                        'bbox': bbox
                    })
        
        return barcodes
    
    def is_product_name(self, text: str) -> bool:
        """Determine if text looks like a product name"""
        # Skip very short text
        if len(text.strip()) < 3:
            return False
        
        # Skip pure numbers
        if text.strip().isdigit():
            return False
        
        # Skip common non-product words
        skip_words = ['price', 'total', 'qty', 'quantity', 'barcode', 'sku']
        if text.lower().strip() in skip_words:
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', text):
            return False
        
        return True
    
    def create_extracted_products(self, products: List[Dict], prices: List[Dict], barcodes: List[Dict]):
        """Create ExtractedProduct objects from detected information"""
        # Simple matching: pair products with nearby prices and barcodes
        for i, product in enumerate(products):
            # Find closest price and barcode
            closest_price = self.find_closest_item(product, prices)
            closest_barcode = self.find_closest_item(product, barcodes)
            
            ExtractedProduct.objects.create(
                upload_session=self.upload_session,
                row_number=i + 1,
                name=product['name'],
                barcode=closest_barcode.get('barcode') if closest_barcode else None,
                price=closest_price.get('price') if closest_price else None,
                raw_data={
                    'product': product,
                    'price': closest_price,
                    'barcode': closest_barcode
                },
                is_valid=bool(product['name'] and (closest_price or closest_barcode))
            )
    
    def find_closest_item(self, product: Dict, items: List[Dict]) -> Optional[Dict]:
        """Find the closest item to a product based on bounding box position"""
        if not items:
            return None
        
        product_center = self.get_bbox_center(product['bbox'])
        min_distance = float('inf')
        closest_item = None
        
        for item in items:
            item_center = self.get_bbox_center(item['bbox'])
            distance = np.sqrt(
                (product_center[0] - item_center[0]) ** 2 +
                (product_center[1] - item_center[1]) ** 2
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_item = item
        
        return closest_item
    
    def get_bbox_center(self, bbox: List[List[int]]) -> Tuple[float, float]:
        """Get center point of bounding box"""
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        return (sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords))


class FileProcessingLogger:
    """Logger for file processing operations"""
    
    def __init__(self, upload_session: UploadSession):
        self.upload_session = upload_session
    
    def log(self, level: str, message: str, details: Dict[str, Any] = None, row_number: int = None):
        """Log a message"""
        FileProcessingLog.objects.create(
            upload_session=self.upload_session,
            level=level,
            message=message,
            details=details or {},
            row_number=row_number
        )
        
        # Also log to Django logger
        django_logger = logging.getLogger(__name__)
        log_method = getattr(django_logger, level.lower(), django_logger.info)
        log_method(f"Upload {self.upload_session.id}: {message}")


class ProductImporter:
    """Import extracted products to inventory"""
    
    def __init__(self, upload_session: UploadSession):
        self.upload_session = upload_session
        self.logger = FileProcessingLogger(upload_session)
    
    def import_products(self, product_ids: List[int] = None) -> Dict[str, int]:
        """Import extracted products to inventory"""
        extracted_products = ExtractedProduct.objects.filter(
            upload_session=self.upload_session,
            is_valid=True,
            is_processed=False
        )
        
        if product_ids:
            extracted_products = extracted_products.filter(id__in=product_ids)
        
        results = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for extracted_product in extracted_products:
            try:
                result = self.import_single_product(extracted_product)
                results[result] += 1
                extracted_product.is_processed = True
                extracted_product.save()
                
            except Exception as e:
                self.logger.log('ERROR', f'Failed to import product {extracted_product.name}: {str(e)}')
                results['errors'] += 1
        
        return results
    
    def import_single_product(self, extracted_product: ExtractedProduct) -> str:
        """Import a single extracted product"""
        # Check if product already exists
        existing_product = None
        if extracted_product.barcode:
            try:
                existing_product = Product.objects.get(
                    barcode=extracted_product.barcode,
                    supermarket=self.upload_session.supermarket
                )
            except Product.DoesNotExist:
                pass
        
        if existing_product:
            # Update existing product
            self.update_existing_product(existing_product, extracted_product)
            return 'updated'
        else:
            # Create new product
            self.create_new_product(extracted_product)
            return 'imported'
    
    def create_new_product(self, extracted_product: ExtractedProduct):
        """Create a new product from extracted data"""
        # Get or create category and supplier
        category = self.get_or_create_category(extracted_product.category)
        supplier = self.get_or_create_supplier(extracted_product.supplier)
        
        Product.objects.create(
            name=extracted_product.name,
            barcode=extracted_product.barcode or f"AUTO_{extracted_product.id}",
            category=category,
            supplier=supplier,
            brand=extracted_product.brand,
            description=extracted_product.description,
            cost_price=extracted_product.cost_price or 0,
            selling_price=extracted_product.selling_price or extracted_product.price or 0,
            price=extracted_product.price or extracted_product.selling_price or 0,
            quantity=extracted_product.quantity or 0,
            min_stock_level=extracted_product.min_stock_level or 5,
            weight=extracted_product.weight,
            origin=extracted_product.origin,
            expiry_date=extracted_product.expiry_date or date.today(),
            location=extracted_product.location,
            halal_certified=extracted_product.halal_certified or False,
            halal_certification_body=extracted_product.halal_certification_body,
            supermarket=self.upload_session.supermarket,
            created_by=self.upload_session.user
        )
    
    def update_existing_product(self, product: Product, extracted_product: ExtractedProduct):
        """Update existing product with extracted data"""
        # Update only non-null values
        if extracted_product.name:
            product.name = extracted_product.name
        if extracted_product.description:
            product.description = extracted_product.description
        if extracted_product.brand:
            product.brand = extracted_product.brand
        if extracted_product.cost_price:
            product.cost_price = extracted_product.cost_price
        if extracted_product.selling_price:
            product.selling_price = extracted_product.selling_price
        if extracted_product.price:
            product.price = extracted_product.price
        if extracted_product.quantity is not None:
            product.quantity = extracted_product.quantity
        if extracted_product.weight:
            product.weight = extracted_product.weight
        if extracted_product.origin:
            product.origin = extracted_product.origin
        if extracted_product.location:
            product.location = extracted_product.location
        
        product.save()
    
    def get_or_create_category(self, category_name: str) -> Optional[Category]:
        """Get or create category"""
        if not category_name:
            return None
        
        category, created = Category.objects.get_or_create(
            name=category_name.strip(),
            defaults={'description': f'Auto-created from file import'}
        )
        return category
    
    def get_or_create_supplier(self, supplier_name: str) -> Optional[Supplier]:
        """Get or create supplier"""
        if not supplier_name:
            return None
        
        supplier, created = Supplier.objects.get_or_create(
            name=supplier_name.strip(),
            defaults={'contact_person': 'Unknown'}
        )
        return supplier