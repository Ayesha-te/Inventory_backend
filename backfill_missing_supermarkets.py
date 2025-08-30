#!/usr/bin/env python
"""
Backfill script: create a primary Supermarket for any user who doesn't have one yet.

Naming rule:
- Prefer user's company_name (set from registration supermarket_name if provided)
- Otherwise: "<first_name or email local part>'s Supermarket"

Address/Phone defaults:
- Address: user.address or "Not provided"
- Phone: user.phone sanitized to +<digits>, else "+10000000000"

Also creates default SupermarketSettings when possible.

Run:
  python backfill_missing_supermarkets.py
"""
import os
import re
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from supermarkets.models import Supermarket, SupermarketSettings  # noqa: E402

User = get_user_model()

PHONE_RE = re.compile(r"\d+")

def sanitize_phone(phone: str | None) -> str:
    if not phone:
        return "+10000000000"
    digits = "".join(PHONE_RE.findall(str(phone)))
    if not digits:
        return "+10000000000"
    return "+" + digits

def supermarket_name_for(user: User) -> str:
    name = (getattr(user, 'company_name', None) or '').strip()
    if name:
        return name
    first = (getattr(user, 'first_name', None) or '').strip()
    if first:
        return f"{first}'s Supermarket"
    # email local part
    email = getattr(user, 'email', '') or ''
    local = email.split('@')[0] if '@' in email else email
    local = local.strip() or 'My'
    return f"{local}'s Supermarket"

def supermarket_address_for(user: User) -> str:
    addr = (getattr(user, 'address', None) or '').strip()
    return addr or 'Not provided'

def main() -> int:
    users_missing = User.objects.filter(owned_supermarkets__isnull=True).distinct()
    total_missing = users_missing.count()
    print(f"Users without supermarkets: {total_missing}")

    created = 0
    skipped = 0
    for user in users_missing:
        try:
            name = supermarket_name_for(user)
            address = supermarket_address_for(user)
            phone = sanitize_phone(getattr(user, 'phone', None))

            sm = Supermarket.objects.create(
                owner=user,
                name=name,
                address=address,
                phone=phone,
                email=user.email,
                description='Backfilled supermarket created after registration issue',
            )
            try:
                SupermarketSettings.objects.create(supermarket=sm)
            except Exception as se:
                print(f"  ⚠️  Failed to create settings for {sm.id}: {se}")

            created += 1
            print(f"✅ Created supermarket for {user.email}: {name}")
        except Exception as e:
            skipped += 1
            print(f"❌ Failed to create supermarket for {getattr(user, 'email', 'unknown')}: {e}")

    print("\nSummary:")
    print(f"  Users missing supermarkets: {total_missing}")
    print(f"  Created: {created}")
    print(f"  Skipped (errors): {skipped}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())