#!/usr/bin/env python
"""
Test script to verify email-based authentication API endpoints
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

def test_registration():
    """Test user registration with email"""
    print("Testing Registration...")
    
    registration_data = {
        'email': 'testuser@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'supermarket_name': 'Test Supermarket'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/accounts/register/',
            json=registration_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Registration Status Code: {response.status_code}")
        print(f"Registration Response: {response.json()}")
        
        if response.status_code == 201:
            print("✓ Registration successful!")
            return response.json()
        else:
            print("✗ Registration failed!")
            return None
            
    except Exception as e:
        print(f"Registration error: {e}")
        return None

def test_login():
    """Test user login with email"""
    print("\nTesting Login...")
    
    login_data = {
        'email': 'testuser@example.com',
        'password': 'TestPassword123!'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/accounts/login/',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Login Status Code: {response.status_code}")
        print(f"Login Response: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Login successful!")
            return response.json()
        else:
            print("✗ Login failed!")
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_profile_access(token):
    """Test accessing user profile with token"""
    print("\nTesting Profile Access...")
    
    try:
        response = requests.get(
            f'{BASE_URL}/api/accounts/profile/',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"Profile Status Code: {response.status_code}")
        print(f"Profile Response: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Profile access successful!")
            return True
        else:
            print("✗ Profile access failed!")
            return False
            
    except Exception as e:
        print(f"Profile access error: {e}")
        return False

def cleanup():
    """Clean up test user"""
    print("\nCleaning up test user...")
    
    # This would require admin access or a cleanup endpoint
    # For now, we'll just note that cleanup is needed
    print("Note: Test user 'testuser@example.com' should be manually removed from database if needed")

if __name__ == '__main__':
    print("Email-Based Authentication API Test")
    print("=" * 40)
    
    # Test registration
    registration_result = test_registration()
    
    if registration_result and registration_result.get('tokens'):
        access_token = registration_result['tokens']['access']
        
        # Test profile access with registration token
        test_profile_access(access_token)
    
    # Test login (independent of registration)
    login_result = test_login()
    
    if login_result and login_result.get('tokens'):
        access_token = login_result['tokens']['access']
        
        # Test profile access with login token
        test_profile_access(access_token)
    
    cleanup()
    
    print("\nTest completed!")