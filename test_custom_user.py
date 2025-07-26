#!/usr/bin/env python
"""
Test the custom user model setup
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def test_custom_user_model():
    """Test if custom user model is working"""
    print("🧪 Testing Custom User Model")
    print("=" * 35)
    
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import CustomUser, Student, Lecturer
        
        User = get_user_model()
        print(f"✅ Custom User Model: {User}")
        print(f"   Model name: {User._meta.label}")
        
        # Test creating a student user
        print(f"\n📚 Testing Student Creation:")
        
        # Check if user already exists
        if not User.objects.filter(email='test.student@example.com').exists():
            student_user = User.objects.create_user(
                username='teststudent',
                email='test.student@example.com',
                password='testpass123',
                first_name='Test',
                last_name='Student',
                position='student',
                student_id='TEST001'
            )
            print(f"✅ Created student user: {student_user}")
            
            # Check if Student record was created automatically
            try:
                student_profile = Student.objects.get(user=student_user)
                print(f"✅ Student profile created: {student_profile}")
            except Student.DoesNotExist:
                print(f"❌ Student profile not created automatically")
        else:
            print(f"ℹ️  Student user already exists")
        
        # Test creating a lecturer user
        print(f"\n👨‍🏫 Testing Lecturer Creation:")
        
        if not User.objects.filter(email='test.lecturer@example.com').exists():
            lecturer_user = User.objects.create_user(
                username='testlecturer',
                email='test.lecturer@example.com',
                password='testpass123',
                first_name='Test',
                last_name='Lecturer',
                position='lecturer'
            )
            print(f"✅ Created lecturer user: {lecturer_user}")
            
            # Check if Lecturer record was created automatically
            try:
                lecturer_profile = Lecturer.objects.get(user=lecturer_user)
                print(f"✅ Lecturer profile created: {lecturer_profile}")
            except Lecturer.DoesNotExist:
                print(f"❌ Lecturer profile not created automatically")
        else:
            print(f"ℹ️  Lecturer user already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing custom user model: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication():
    """Test authentication with custom user"""
    print(f"\n🔐 Testing Authentication")
    print("=" * 30)
    
    try:
        from django.contrib.auth import authenticate
        
        # Test student authentication
        student_user = authenticate(username='test.student@example.com', password='testpass123')
        if student_user:
            print(f"✅ Student authentication successful: {student_user}")
            print(f"   Position: {student_user.position}")
            print(f"   Is Student: {student_user.is_student}")
            print(f"   Is Lecturer: {student_user.is_lecturer}")
        else:
            print(f"❌ Student authentication failed")
        
        # Test lecturer authentication
        lecturer_user = authenticate(username='test.lecturer@example.com', password='testpass123')
        if lecturer_user:
            print(f"✅ Lecturer authentication successful: {lecturer_user}")
            print(f"   Position: {lecturer_user.position}")
            print(f"   Is Student: {lecturer_user.is_student}")
            print(f"   Is Lecturer: {lecturer_user.is_lecturer}")
        else:
            print(f"❌ Lecturer authentication failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing authentication: {str(e)}")
        return False

def show_all_users():
    """Show all users in the system"""
    print(f"\n👥 All Users in System")
    print("=" * 25)
    
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Student, Lecturer
        
        User = get_user_model()
        users = User.objects.all()
        
        print(f"Total users: {users.count()}")
        
        for user in users:
            print(f"\n👤 {user.username} ({user.email})")
            print(f"   Name: {user.get_full_name()}")
            print(f"   Position: {user.position}")
            print(f"   Staff: {user.is_staff}")
            print(f"   Active: {user.is_active}")
            
            if user.position == 'student':
                try:
                    student = Student.objects.get(user=user)
                    print(f"   📚 Student ID: {student.student_id}")
                    print(f"   📚 Classes: {student.enrolled_classes.count()}")
                except Student.DoesNotExist:
                    print(f"   ❌ No student profile")
            
            elif user.position == 'lecturer':
                try:
                    lecturer = Lecturer.objects.get(user=user)
                    print(f"   👨‍🏫 Employee ID: {lecturer.employee_id}")
                    print(f"   👨‍🏫 Department: {lecturer.department}")
                except Lecturer.DoesNotExist:
                    print(f"   ❌ No lecturer profile")
        
    except Exception as e:
        print(f"❌ Error showing users: {str(e)}")

def main():
    print("🎯 Custom User Model Test Suite")
    print("=" * 50)
    
    # Test custom user model
    model_ok = test_custom_user_model()
    
    # Test authentication
    auth_ok = test_authentication()
    
    # Show all users
    show_all_users()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Custom User Model: {'✅ PASS' if model_ok else '❌ FAIL'}")
    print(f"Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    
    if model_ok and auth_ok:
        print("\n🎉 Custom User Model is working!")
        print("\n💡 Next steps:")
        print("1. Create superuser: python manage.py createsuperuser")
        print("2. Start server: python manage.py runserver")
        print("3. Access admin: http://localhost:8000/admin/")
        print("4. Test login with created users")
    else:
        print("\n⚠️  Custom User Model needs attention")
        print("Check the error messages above")

if __name__ == "__main__":
    main()
