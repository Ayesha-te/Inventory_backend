#!/usr/bin/env python
import requests
import json

# Test the products API endpoints
BASE_URL = "http://127.0.0.1:8000"

# Login first
login_data = {
    "email": "demo@example.com",
    "password": "demo123"
}

response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data)
if response.status_code == 200:
    login_result = response.json()
    if 'tokens' in login_result:
        token = login_result['tokens']['access']
    elif 'access' in login_result:
        token = login_result['access']
    else:
        print("No token found")
        exit()
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get supermarkets
    response = requests.get(f"{BASE_URL}/api/supermarkets/", headers=headers)
    supermarkets = response.json()
    
    print(f"Testing products for {len(supermarkets)} stores:")
    
    # Test products endpoint for each store
    for store in supermarkets:
        store_id = store['id']
        store_name = store['name']
        
        # Get products for this store
        response = requests.get(f"{BASE_URL}/api/inventory/products/?supermarket={store_id}", headers=headers)
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, dict) and 'results' in products:
                products = products['results']
            
            print(f"\n{store_name} ({store_id}):")
            print(f"  Products: {len(products)}")
            for product in products:
                print(f"    - {product['name']} (Qty: {product['quantity']})")
        else:
            print(f"\nError getting products for {store_name}: {response.status_code}")
            print(response.text)
else:
    print("Login failed")
    print(response.text)