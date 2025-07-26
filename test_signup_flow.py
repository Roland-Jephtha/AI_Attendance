#!/usr/bin/env python
"""
Test script to verify the signup flow works correctly
"""

import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def test_signup_flow():
    """Test the complete signup flow"""
    print("Testing student signup flow...")
    
    client = Client()
    
    # Test GET request to signup page
    print("1. Testing GET request to signup page...")
    response = client.get('/signup/')
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print("   ❌ Signup page not accessible")
        return False
    
    print("   ✅ Signup page accessible")
    
    # Test POST request with valid data
    print("2. Testing POST request with valid data...")
    
    signup_data = {
        'student_id': 'TEST001',
        'first_name': 'Test',
        'last_name': 'Student',
        'email': 'test@example.com',
        'phone': '1234567890',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }
    
    response = client.post('/signup/', signup_data, follow=True)
    print(f"   Status: {response.status_code}")
    print(f"   Final URL: {response.request['PATH_INFO']}")
    
    # Check if redirected to face enrollment
    if '/enroll-face/' in response.request['PATH_INFO']:
        print("   ✅ Successfully redirected to face enrollment")
        return True
    elif '/login/' in response.request['PATH_INFO']:
        print("   ⚠️  Redirected to login (authentication might have failed)")
        return False
    else:
        print(f"   ❌ Unexpected redirect to: {response.request['PATH_INFO']}")
        
        # Check for error messages
        if hasattr(response, 'context') and response.context:
            messages = list(response.context.get('messages', []))
            if messages:
                print("   Error messages:")
                for message in messages:
                    print(f"     - {message}")
        
        return False

def test_urls():
    """Test if all required URLs are working"""
    print("\nTesting URL patterns...")
    
    client = Client()
    
    urls_to_test = [
        ('/', 'Login page'),
        ('/signup/', 'Signup page'),
        ('/login/', 'Login page'),
    ]
    
    all_good = True
    
    for url, description in urls_to_test:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"   ✅ {description}: {url}")
            else:
                print(f"   ❌ {description}: {url} (Status: {response.status_code})")
                all_good = False
        except Exception as e:
            print(f"   ❌ {description}: {url} (Error: {str(e)})")
            all_good = False
    
    return all_good

def check_models():
    """Check if models are working correctly"""
    print("\nTesting models...")
    
    try:
        from attendance.models import Student, Class
        from django.contrib.auth.models import User
        
        # Check if we can create a test student
        print("   Testing Student model...")
        
        # Clean up any existing test data
        User.objects.filter(username='TESTMODEL').delete()
        Student.objects.filter(student_id='TESTMODEL').delete()
        
        # Create test user
        user = User.objects.create_user(
            username='TESTMODEL',
            email='testmodel@example.com',
            password='testpass123'
        )
        
        # Create test student
        student = Student.objects.create(
            student_id='TESTMODEL',
            first_name='Test',
            last_name='Model',
            email='testmodel@example.com'
        )
        
        print(f"   ✅ Student created: {student.full_name}")
        
        # Clean up
        user.delete()
        student.delete()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model test failed: {str(e)}")
        return False

def main():
    print("🧪 Student Signup Flow Test")
    print("=" * 40)
    
    # Test URLs
    urls_ok = test_urls()
    
    # Test models
    models_ok = check_models()
    
    # Test signup flow
    signup_ok = test_signup_flow()
    
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"URLs: {'✅ PASS' if urls_ok else '❌ FAIL'}")
    print(f"Models: {'✅ PASS' if models_ok else '❌ FAIL'}")
    print(f"Signup Flow: {'✅ PASS' if signup_ok else '❌ FAIL'}")
    
    if all([urls_ok, models_ok, signup_ok]):
        print("\n🎉 All tests passed! Signup should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the Django server logs for more details.")
        print("\nTroubleshooting steps:")
        print("1. Make sure Django server is running")
        print("2. Check for any migration issues: python manage.py migrate")
        print("3. Check Django logs for error messages")
        print("4. Try accessing the signup page manually in browser")

if __name__ == "__main__":
    main()
