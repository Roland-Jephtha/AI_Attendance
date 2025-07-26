#!/usr/bin/env python
"""
Debug URL access issues
"""

import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def test_urls():
    """Test if URLs are accessible"""
    print("🔍 Testing URL Access")
    print("=" * 30)
    
    base_url = "http://localhost:8000"
    
    urls_to_test = [
        "/",
        "/login/", 
        "/signup/",
        "/debug-signup/",
        "/simple-test/",
        "/minimal-signup/"
    ]
    
    for url in urls_to_test:
        try:
            print(f"Testing {url}...")
            response = requests.get(f"{base_url}{url}", timeout=5)
            
            if response.status_code == 200:
                print(f"  ✅ {url} - OK (200)")
            elif response.status_code == 404:
                print(f"  ❌ {url} - Not Found (404)")
            elif response.status_code == 500:
                print(f"  ❌ {url} - Server Error (500)")
            else:
                print(f"  ⚠️  {url} - Status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {url} - Connection Error (Server not running?)")
        except requests.exceptions.Timeout:
            print(f"  ❌ {url} - Timeout")
        except Exception as e:
            print(f"  ❌ {url} - Error: {str(e)}")

def check_django_setup():
    """Check Django configuration"""
    print("\n🔧 Checking Django Setup")
    print("=" * 30)
    
    try:
        from django.conf import settings
        print(f"✅ Django settings loaded")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        # Check if URLs are configured
        from django.urls import reverse
        try:
            signup_url = reverse('student_signup')
            print(f"✅ Signup URL configured: {signup_url}")
        except Exception as e:
            print(f"❌ Signup URL error: {e}")
            
        # Check database
        from attendance.models import Student
        student_count = Student.objects.count()
        print(f"✅ Database accessible, {student_count} students")
        
    except Exception as e:
        print(f"❌ Django setup error: {e}")

def main():
    print("🚨 Django URL Debug Tool")
    print("=" * 40)
    
    # Check Django setup
    check_django_setup()
    
    # Test URL access
    test_urls()
    
    print("\n" + "=" * 40)
    print("📋 Next Steps:")
    print("1. If connection errors: Start Django server with 'python manage.py runserver'")
    print("2. If 404 errors: Check URL patterns in urls.py")
    print("3. If 500 errors: Check Django console for error details")
    print("4. If all OK: Try accessing URLs in browser")

if __name__ == "__main__":
    main()
