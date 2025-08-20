#!/usr/bin/env python
"""
Test script for the barcode and ticket generation system
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
django.setup()

from inventory.services import BarcodeService, TicketService, ProductService
from inventory.models import Product, Category, Supplier
from supermarkets.models import Supermarket
from accounts.models import User

def create_test_data():
    """Create test data for barcode system"""
    print("Creating test data...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create test supermarket
    supermarket, created = Supermarket.objects.get_or_create(
        name='Test Supermarket',
        defaults={
            'owner': user,
            'address': '123 Test Street',
            'phone': '+1-555-0123',
            'email': 'test@supermarket.com'
        }
    )
    
    # Create test category
    category, created = Category.objects.get_or_create(
        name='Test Category',
        defaults={'description': 'Test category for barcode system'}
    )
    
    # Create test supplier
    supplier, created = Supplier.objects.get_or_create(
        name='Test Supplier',
        defaults={
            'contact_person': 'John Doe',
            'email': 'supplier@test.com',
            'phone': '+1-555-0456'
        }
    )
    
    # Create test product
    from datetime import date, timedelta
    
    product, created = Product.objects.get_or_create(
        name='Test Product for Barcode',
        defaults={
            'category': category,
            'supplier': supplier,
            'supermarket': supermarket,
            'created_by': user,
            'description': 'Test product for barcode generation',
            'brand': 'Test Brand',
            'price': 9.99,
            'selling_price': 12.99,
            'cost_price': 7.99,
            'quantity': 100,
            'min_stock_level': 10,
            'weight': '500g',
            'origin': 'USA',
            'expiry_date': date.today() + timedelta(days=365),  # 1 year from now
            'halal_certified': True,
            'halal_certification_body': 'Test Halal Authority'
        }
    )
    
    return user, supermarket, product

def test_barcode_generation():
    """Test barcode generation functionality"""
    print("\n=== Testing Barcode Generation ===")
    
    user, supermarket, product = create_test_data()
    
    # Test barcode number generation
    print("1. Testing barcode number generation...")
    barcode_number = BarcodeService.generate_barcode_number(str(product.id))
    print(f"   Generated barcode: {barcode_number}")
    
    # Test barcode creation
    print("2. Testing barcode record creation...")
    barcode_obj = BarcodeService.create_product_barcode(product)
    print(f"   Created barcode record: {barcode_obj.code} (Type: {barcode_obj.barcode_type})")
    
    # Test barcode image generation
    print("3. Testing barcode image generation...")
    try:
        barcode_image = BarcodeService.generate_barcode_image(product.barcode, 'CODE128', 'PNG')
        print(f"   Generated barcode image: {len(barcode_image)} bytes")
    except Exception as e:
        print(f"   Error generating barcode image: {e}")
    
    return product

def test_ticket_generation():
    """Test ticket generation functionality"""
    print("\n=== Testing Ticket Generation ===")
    
    user, supermarket, product = create_test_data()
    
    # Test single ticket generation
    print("1. Testing single ticket generation...")
    try:
        ticket_pdf = TicketService.generate_product_ticket(product, include_qr=True)
        print(f"   Generated ticket PDF: {len(ticket_pdf)} bytes")
    except Exception as e:
        print(f"   Error generating ticket: {e}")
    
    # Test bulk ticket generation
    print("2. Testing bulk ticket generation...")
    try:
        products = [product]  # In real scenario, this would be multiple products
        bulk_pdf = TicketService.generate_bulk_tickets(products, tickets_per_page=8)
        print(f"   Generated bulk tickets PDF: {len(bulk_pdf)} bytes")
    except Exception as e:
        print(f"   Error generating bulk tickets: {e}")
    
    # Test barcode sheet generation
    print("3. Testing barcode sheet generation...")
    try:
        barcode_sheet = TicketService.generate_barcode_sheet(products, barcodes_per_page=20)
        print(f"   Generated barcode sheet PDF: {len(barcode_sheet)} bytes")
    except Exception as e:
        print(f"   Error generating barcode sheet: {e}")

def test_product_service():
    """Test product service functionality"""
    print("\n=== Testing Product Service ===")
    
    user, supermarket, product = create_test_data()
    
    # Test product creation with automatic barcode
    print("1. Testing product creation with automatic barcode...")
    try:
        new_product_data = {
            'name': 'Auto Barcode Product',
            'category': product.category,
            'supplier': product.supplier,
            'supermarket': supermarket,
            'created_by': user,
            'price': 15.99,
            'quantity': 50
        }
        
        new_product = ProductService.create_product_with_barcode(new_product_data)
        print(f"   Created product with barcode: {new_product.name} - {new_product.barcode}")
    except Exception as e:
        print(f"   Error creating product with barcode: {e}")

def main():
    """Main test function"""
    print("Starting Barcode and Ticket System Tests")
    print("=" * 50)
    
    try:
        # Test barcode generation
        product = test_barcode_generation()
        
        # Test ticket generation
        test_ticket_generation()
        
        # Test product service
        test_product_service()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()