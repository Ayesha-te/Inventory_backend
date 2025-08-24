#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
django.setup()

from supermarkets.models import Supermarket
from inventory.models import Product, Category, Supplier
from django.contrib.auth import get_user_model
from datetime import date, timedelta
import random

User = get_user_model()

# Get stores
stores = Supermarket.objects.all()
if not stores:
    print("No stores found. Please create stores first.")
    exit()

# Create categories
category1, _ = Category.objects.get_or_create(name="Electronics")
category2, _ = Category.objects.get_or_create(name="Groceries")

# Create suppliers
supplier1, _ = Supplier.objects.get_or_create(name="Tech Supplier Co")
supplier2, _ = Supplier.objects.get_or_create(name="Food Distributor Inc")

print(f"Creating products for {stores.count()} stores...")

# Create products for each store
for i, store in enumerate(stores):
    # Create 2 products per store with unique barcodes
    Product.objects.create(
        name=f"Product A{i+1} - {store.name}",
        barcode=f"123456789{i:03d}1",  # Unique barcode
        category=category1,
        supplier=supplier1,
        supermarket=store,
        quantity=50,
        price=99.99,
        selling_price=99.99,
        cost_price=70.00,
        expiry_date=date.today() + timedelta(days=365),
        description=f"Electronics product for {store.name}"
    )
    
    Product.objects.create(
        name=f"Product B{i+1} - {store.name}",
        barcode=f"123456789{i:03d}2",  # Unique barcode
        category=category2,
        supplier=supplier2,
        supermarket=store,
        quantity=25,
        price=19.99,
        selling_price=19.99,
        cost_price=12.00,
        expiry_date=date.today() + timedelta(days=180),
        description=f"Grocery product for {store.name}"
    )

total_products = Product.objects.count()
print(f"Created {total_products} products across all stores")

# Show products per store
for store in stores:
    product_count = store.products.count()
    print(f"  - {store.name}: {product_count} products")