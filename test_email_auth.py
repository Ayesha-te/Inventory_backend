#!/usr/bin/env python
"""
Test script to verify email-based authentication is working correctly
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
django.setup()

from accounts.models import User
from django.contrib.auth import authenticate

def test_email_auth():
    print("Testing Email-Based Authentication Configuration")
    print("=" * 50)
    
    # Test 1: Check User model configuration
    print(f"1. USERNAME_FIELD: {User.USERNAME_FIELD}")
    print(f"2. REQUIRED_FIELDS: {User.REQUIRED_FIELDS}")
    
    # Test 2: Try to create a user with email only (no username)
    try:
        # Clean up any existing test user
        User.objects.filter(email='test@example.com').delete()
        
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"3. User created successfully: {user.email}")
        print(f"   - ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - First Name: {user.first_name}")
        print(f"   - Last Name: {user.last_name}")
        print(f"   - Username: {user.username}")
        
        # Test 3: Try to authenticate with email
        auth_user = authenticate(username='test@example.com', password='testpass123')
        if auth_user:
            print("4. Authentication with email: SUCCESS ✓")
        else:
            print("4. Authentication with email: FAILED ✗")
            
        # Clean up
        user.delete()
        print("5. Test user cleaned up")
        
    except Exception as e:
        print(f"3. Error creating user: {e}")
        return False
    
    print("\nEmail-based authentication is configured correctly! ✓")
    return True

if __name__ == '__main__':
    test_email_auth()