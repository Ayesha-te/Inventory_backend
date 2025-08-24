#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
django.setup()

from supermarkets.models import Supermarket
from django.contrib.auth import get_user_model

User = get_user_model()

print(f"Users: {User.objects.count()}")
print(f"Supermarkets: {Supermarket.objects.count()}")

print("\nUsers:")
for user in User.objects.all()[:5]:
    print(f"  - {user.email} (ID: {user.id})")

print("\nSupermarkets:")
for store in Supermarket.objects.all()[:10]:
    owner_email = store.owner.email if store.owner else "No owner"
    print(f"  - {store.name} | Owner: {owner_email} | Store Email: {store.email} | Sub-store: {store.is_sub_store}")