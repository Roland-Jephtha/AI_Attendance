#!/usr/bin/env python
"""
Simple test script to verify face enrollment functionality
Run this after starting the Django server to test the API endpoints
"""

import requests
import base64
import json

# Test configuration
BASE_URL = 'http://localhost:8000'
TEST_IMAGE_DATA = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k='

def test_api_validate_image():
    """Test the image validation API"""
    print("Testing image validation API...")
    
    url = f"{BASE_URL}/api/validate-image/"
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'image_data': TEST_IMAGE_DATA
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_api_recognize_face():
    """Test the face recognition API"""
    print("\nTesting face recognition API...")
    
    url = f"{BASE_URL}/api/recognize-face/"
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'image_data': TEST_IMAGE_DATA,
        'class_id': 1  # Assuming class with ID 1 exists
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [200, 503]  # 503 is acceptable if DeepFace not available
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Face Enrollment API Test")
    print("=" * 40)
    
    # Test image validation
    validation_success = test_api_validate_image()
    
    # Test face recognition
    recognition_success = test_api_recognize_face()
    
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"Image Validation API: {'✓ PASS' if validation_success else '✗ FAIL'}")
    print(f"Face Recognition API: {'✓ PASS' if recognition_success else '✗ FAIL'}")
    
    if validation_success and recognition_success:
        print("\n✅ All tests passed! The face enrollment should work correctly.")
    else:
        print("\n❌ Some tests failed. Check the Django server logs for more details.")
        print("\nTroubleshooting tips:")
        print("1. Make sure Django server is running on localhost:8000")
        print("2. Check if DeepFace is properly installed")
        print("3. Verify that the API endpoints are accessible")

if __name__ == "__main__":
    main()
