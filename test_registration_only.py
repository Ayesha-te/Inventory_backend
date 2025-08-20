#!/usr/bin/env python
"""
Test script to verify registration with a new email
"""
import requests
import json
import random

BASE_URL = 'http://127.0.0.1:8000'

def test_registration():
    """Test user registration with email"""
    print("Testing Registration with new email...")
    
    # Use a random email to avoid conflicts
    random_id = random.randint(1000, 9999)
    
    registration_data = {
        'email': f'newuser{random_id}@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!',
        'first_name': 'New',
        'last_name': 'User',
        'supermarket_name': 'New Test Supermarket'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/accounts/register/',
            json=registration_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Registration Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Registration Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Registration Response (text): {response.text}")
        
        if response.status_code == 201:
            print("✓ Registration successful!")
            return response.json()
        else:
            print("✗ Registration failed!")
            return None
            
    except Exception as e:
        print(f"Registration error: {e}")
        return None

if __name__ == '__main__':
    print("Registration Test")
    print("=" * 20)
    
    test_registration()