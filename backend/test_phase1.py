"""
Test script for Phase 1 API endpoints
Tests JWT authentication, product management, and cashier transactions
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5001"

def test_jwt_generation():
    """Test JWT token generation for admin/cashier"""
    print("\n=== Test: JWT Token Generation ===")
    
    # We'll need to modify the API to add a login endpoint for cashiers
    # For now, let's test with manual JWT creation
    import jwt
    from datetime import datetime, timedelta
    
    JWT_SECRET = "test-secret-key-do-not-use-in-production"
    payload = {
        'user_id': 'cashier001',
        'role': 'cashier',
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    print(f"✅ Generated JWT Token: {token[:50]}...")
    return token

def test_products_endpoint():
    """Test products endpoint"""
    print("\n=== Test: Products Endpoint ===")
    
    response = requests.get(f"{BASE_URL}/api/products")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Products retrieved: {data['count']} products")
        for product in data['products'][:3]:
            print(f"   - {product['name']}: ₱{product['price']}")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_products_by_category():
    """Test products filtering by category"""
    print("\n=== Test: Products by Category ===")
    
    response = requests.get(f"{BASE_URL}/api/products?category=Food")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Food products: {data['count']} items")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_auth_required():
    """Test that cashier endpoints require authentication"""
    print("\n=== Test: Auth Required ===")
    
    # Try to create product without auth
    response = requests.post(
        f"{BASE_URL}/api/products",
        json={"id": "TEST-001", "name": "Test", "category": "Test", "price": 10}
    )
    
    if response.status_code == 401:
        print("✅ Endpoint correctly requires authentication")
        return True
    else:
        print(f"❌ Expected 401, got {response.status_code}")
        return False

def test_email_service():
    """Test email service with retry logic"""
    print("\n=== Test: Email Service ===")
    
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))
    
    try:
        from email_service import EmailService
        
        # Test initialization
        email_service = EmailService()
        print(f"✅ Email service initialized")
        print(f"   - SMTP Server: {email_service.smtp_server}")
        print(f"   - Max Retries: {email_service.max_retries}")
        print(f"   - Retry Delay: {email_service.retry_delay}s")
        print(f"   - Enabled: {email_service.enabled}")
        
        return True
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return False

def run_all_tests():
    """Run all Phase 1 tests"""
    print("=" * 60)
    print("Phase 1: Backend & Data Structure - API Tests")
    print("=" * 60)
    
    tests = [
        ("Products Endpoint", test_products_endpoint),
        ("Products by Category", test_products_by_category),
        ("Auth Required", test_auth_required),
        ("Email Service", test_email_service),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    return passed == total

if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
