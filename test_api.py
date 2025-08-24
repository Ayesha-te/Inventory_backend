#!/usr/bin/env python
import requests
import json

# Test the API endpoints
BASE_URL = "http://127.0.0.1:8000"

# Test login
login_data = {
    "email": "demo@example.com",
    "password": "demo123"  # Assuming this is the password
}

print("Testing login...")
try:
    response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data)
    print(f"Login status: {response.status_code}")
    if response.status_code == 200:
        login_result = response.json()
        print("Login successful!")
        
        # Get the token
        if 'tokens' in login_result:
            token = login_result['tokens']['access']
        elif 'access' in login_result:
            token = login_result['access']
        else:
            print("No token found in response")
            print(json.dumps(login_result, indent=2))
            exit()
        
        # Test supermarkets endpoint
        headers = {"Authorization": f"Bearer {token}"}
        print(f"\nTesting supermarkets endpoint with token...")
        
        response = requests.get(f"{BASE_URL}/api/supermarkets/", headers=headers)
        print(f"Supermarkets status: {response.status_code}")
        
        if response.status_code == 200:
            supermarkets = response.json()
            print(f"Found {len(supermarkets)} supermarkets:")
            for store in supermarkets:
                print(f"  - {store['name']} (Sub-store: {store.get('is_sub_store', False)})")
        else:
            print("Error response:")
            print(response.text)
    else:
        print("Login failed:")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")