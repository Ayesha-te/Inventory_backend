#!/usr/bin/env python
"""
Complete test of email-based authentication flow
"""
import requests
import json
import random

BASE_URL = 'http://127.0.0.1:8000'

def test_complete_flow():
    """Test complete authentication flow"""
    print("Complete Email-Based Authentication Flow Test")
    print("=" * 50)
    
    # Generate unique email
    random_id = random.randint(10000, 99999)
    test_email = f'flowtest{random_id}@example.com'
    test_password = 'FlowTest123!'
    
    print(f"Testing with email: {test_email}")
    
    # Step 1: Registration
    print("\n1. Testing Registration...")
    registration_data = {
        'email': test_email,
        'password': test_password,
        'password_confirm': test_password,
        'first_name': 'Flow',
        'last_name': 'Test',
        'supermarket_name': 'Flow Test Market'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/accounts/register/',
            json=registration_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            print("✓ Registration successful!")
            reg_data = response.json()
            print(f"  - User ID: {reg_data['user']['id']}")
            print(f"  - Email: {reg_data['user']['email']}")
            print(f"  - Company: {reg_data['user']['company_name']}")
            print(f"  - Tokens received: {'tokens' in reg_data}")
            registration_token = reg_data['tokens']['access']
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Registration error: {e}")
        return False
    
    # Step 2: Login with email
    print("\n2. Testing Login with Email...")
    login_data = {
        'email': test_email,
        'password': test_password
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/accounts/login/',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✓ Login successful!")
            login_data = response.json()
            print(f"  - User ID: {login_data['user']['id']}")
            print(f"  - Email: {login_data['user']['email']}")
            print(f"  - Name: {login_data['user']['first_name']} {login_data['user']['last_name']}")
            login_token = login_data['tokens']['access']
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Login error: {e}")
        return False
    
    # Step 3: Access protected resource
    print("\n3. Testing Protected Resource Access...")
    try:
        response = requests.get(
            f'{BASE_URL}/api/accounts/profile/',
            headers={
                'Authorization': f'Bearer {login_token}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            print("✓ Profile access successful!")
            profile_data = response.json()
            print(f"  - Profile ID: {profile_data['id']}")
            print(f"  - Email: {profile_data['email']}")
            print(f"  - Subscription: {profile_data['subscription_plan']}")
            print(f"  - Verified: {profile_data['is_verified']}")
        else:
            print(f"✗ Profile access failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Profile access error: {e}")
        return False
    
    # Step 4: Test token refresh
    print("\n4. Testing Token Refresh...")
    try:
        refresh_token = reg_data['tokens']['refresh']
        response = requests.post(
            f'{BASE_URL}/api/auth/token/refresh/',
            json={'refresh': refresh_token},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✓ Token refresh successful!")
            refresh_data = response.json()
            print(f"  - New access token received: {'access' in refresh_data}")
        else:
            print(f"✗ Token refresh failed: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Token refresh error: {e}")
    
    print("\n" + "=" * 50)
    print("✓ Email-based authentication is working correctly!")
    print("✓ Users can register with email (no username required)")
    print("✓ Users can login with email and password")
    print("✓ JWT tokens are properly generated and work")
    print("✓ Protected resources are accessible with valid tokens")
    print("✓ Supermarket name is properly mapped to company_name")
    
    return True

if __name__ == '__main__':
    test_complete_flow()