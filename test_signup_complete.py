#!/usr/bin/env python
"""
Complete test of the signup flow
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import User

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def cleanup_test_data():
    """Clean up any existing test data"""
    from attendance.models import Student
    
    # Remove test users and students
    test_ids = ['TEST001', 'SIGNUP001', 'COMPLETE001']
    
    for test_id in test_ids:
        try:
            User.objects.filter(username=test_id).delete()
            Student.objects.filter(student_id=test_id).delete()
        except:
            pass

def test_complete_signup():
    """Test the complete signup flow"""
    print("🧪 Testing Complete Signup Flow")
    print("=" * 40)
    
    # Clean up first
    cleanup_test_data()
    
    client = Client()
    
    # Test 1: GET signup page
    print("1. Testing GET /signup/")
    response = client.get('/signup/')
    
    if response.status_code != 200:
        print(f"   ❌ Failed to load signup page: {response.status_code}")
        return False
    
    print("   ✅ Signup page loaded successfully")
    
    # Test 2: POST valid signup data
    print("2. Testing POST with valid data")
    
    signup_data = {
        'student_id': 'COMPLETE001',
        'first_name': 'Complete',
        'last_name': 'Test',
        'email': 'complete@test.com',
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
        
        # Verify user was created and logged in
        from attendance.models import Student
        from django.contrib.auth.models import User
        
        try:
            user = User.objects.get(username='COMPLETE001')
            student = Student.objects.get(student_id='COMPLETE001')
            
            print(f"   ✅ User created: {user.username}")
            print(f"   ✅ Student created: {student.full_name}")
            
            return True
            
        except (User.DoesNotExist, Student.DoesNotExist) as e:
            print(f"   ❌ User/Student not created: {e}")
            return False
    
    else:
        print(f"   ❌ Not redirected to face enrollment")
        print(f"   Redirected to: {response.request['PATH_INFO']}")
        
        # Check for error messages
        if hasattr(response, 'context') and response.context:
            messages = list(response.context.get('messages', []))
            if messages:
                print("   Error messages:")
                for message in messages:
                    print(f"     - {message}")
        
        return False

def test_face_enrollment_page():
    """Test if face enrollment page is accessible"""
    print("\n3. Testing face enrollment page access")
    
    client = Client()
    
    # First create and login a user
    from django.contrib.auth.models import User
    from attendance.models import Student
    
    try:
        # Create test user
        user = User.objects.create_user(
            username='FACETEST001',
            email='facetest@test.com',
            password='testpass123'
        )
        
        student = Student.objects.create(
            student_id='FACETEST001',
            first_name='Face',
            last_name='Test',
            email='facetest@test.com'
        )
        
        # Login
        client.login(username='FACETEST001', password='testpass123')
        
        # Test face enrollment page
        response = client.get('/enroll-face/')
        
        if response.status_code == 200:
            print("   ✅ Face enrollment page accessible")
            return True
        else:
            print(f"   ❌ Face enrollment page failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing face enrollment: {e}")
        return False
    finally:
        # Cleanup
        try:
            User.objects.filter(username='FACETEST001').delete()
            Student.objects.filter(student_id='FACETEST001').delete()
        except:
            pass

def main():
    print("🚀 Complete Signup Flow Test")
    print("=" * 50)
    
    # Test complete signup
    signup_success = test_complete_signup()
    
    # Test face enrollment page
    face_page_success = test_face_enrollment_page()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Signup Flow: {'✅ PASS' if signup_success else '❌ FAIL'}")
    print(f"Face Enrollment Page: {'✅ PASS' if face_page_success else '❌ FAIL'}")
    
    if signup_success and face_page_success:
        print("\n🎉 All tests passed!")
        print("\n✅ The signup flow should now work correctly:")
        print("   1. Go to: http://localhost:8000/signup/")
        print("   2. Fill in the form")
        print("   3. Submit → Should redirect to face enrollment")
        print("   4. Complete face registration")
        print("   5. Access student dashboard")
    else:
        print("\n⚠️  Some tests failed.")
        print("Check the Django server logs for detailed error messages.")
    
    # Cleanup
    cleanup_test_data()

if __name__ == "__main__":
    main()
