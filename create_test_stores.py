#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
django.setup()

from supermarkets.models import Supermarket
from django.contrib.auth import get_user_model

User = get_user_model()

# Get the first user
user = User.objects.first()
if not user:
    print("No users found. Please create a user first.")
    exit()

print(f"Creating stores for user: {user.email}")

# Create main store
main_store = Supermarket.objects.create(
    name="Main Store",
    description="Primary supermarket location",
    address="123 Main Street, City, State 12345",
    phone="+1234567890",
    email=user.email,  # Same email as user
    owner=user,
    is_sub_store=False
)
print(f"Created main store: {main_store.name}")

# Create sub-store 1
sub_store1 = Supermarket.objects.create(
    name="Downtown Branch",
    description="Downtown location sub-store",
    address="456 Downtown Ave, City, State 12345",
    phone="+1234567891",
    email=user.email,  # Same email as user
    owner=user,
    parent=main_store,
    is_sub_store=True
)
print(f"Created sub-store: {sub_store1.name}")

# Create sub-store 2
sub_store2 = Supermarket.objects.create(
    name="Mall Location",
    description="Shopping mall sub-store",
    address="789 Mall Blvd, City, State 12345",
    phone="+1234567892",
    email=user.email,  # Same email as user
    owner=user,
    parent=main_store,
    is_sub_store=True
)
print(f"Created sub-store: {sub_store2.name}")

print(f"\nTotal stores created: {Supermarket.objects.count()}")
print("All stores belong to the same user/email, demonstrating multi-store support.")