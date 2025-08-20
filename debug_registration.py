#!/usr/bin/env python
"""
Debug registration serializer
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
django.setup()

from accounts.serializers import UserRegistrationSerializer
from accounts.models import User

def test_serializer():
    print("Testing UserRegistrationSerializer...")
    
    # Clean up any existing test user
    User.objects.filter(email='debuguser@example.com').delete()
    
    data = {
        'email': 'debuguser@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!',
        'first_name': 'Debug',
        'last_name': 'User',
        'supermarket_name': 'Debug Supermarket'
    }
    
    serializer = UserRegistrationSerializer(data=data)
    
    print(f"Is valid: {serializer.is_valid()}")
    
    if not serializer.is_valid():
        print(f"Errors: {serializer.errors}")
        return False
    
    try:
        user = serializer.save()
        print(f"User created: {user.email}")
        print(f"Company name: {user.company_name}")
        print(f"First name: {user.first_name}")
        print(f"Last name: {user.last_name}")
        
        # Clean up
        user.delete()
        print("User cleaned up")
        
        return True
        
    except Exception as e:
        print(f"Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_serializer()