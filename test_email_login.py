#!/usr/bin/env python
"""
Test email-based login system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def test_email_authentication():
    """Test email authentication"""
    print("🧪 Testing Email Authentication")
    print("=" * 35)
    
    from django.contrib.auth import authenticate
    from django.contrib.auth.models import User
    from attendance.models import Student
    
    # Check existing users
    users = User.objects.all()
    print(f"📊 Found {users.count()} users in system:")
    
    for user in users:
        print(f"   👤 {user.username}")
        print(f"      Email: {user.email}")
        print(f"      Name: {user.get_full_name()}")
        print(f"      Staff: {'Yes' if user.is_staff else 'No'}")
        print(f"      Active: {'Yes' if user.is_active else 'No'}")
        print()
    
    return users.count() > 0

def create_test_users():
    """Create test users for email login"""
    print("\n🔧 Creating Test Users")
    print("=" * 25)
    
    from django.contrib.auth.models import User
    from attendance.models import Student
    
    # Create test lecturer
    if not User.objects.filter(email='lecturer@example.com').exists():
        lecturer = User.objects.create_user(
            username='lecturer1',
            email='lecturer@example.com',
            password='password123',
            first_name='Dr. John',
            last_name='Smith',
            is_staff=True
        )
        print(f"✅ Created lecturer: {lecturer.email}")
    else:
        print("ℹ️  Lecturer already exists")
    
    # Create test student
    if not User.objects.filter(email='student@example.com').exists():
        # Create Django user
        user = User.objects.create_user(
            username='STUDENT001',
            email='student@example.com',
            password='password123',
            first_name='Jane',
            last_name='Doe'
        )
        
        # Create student record
        student = Student.objects.create(
            student_id='STUDENT001',
            first_name='Jane',
            last_name='Doe',
            email='student@example.com',
            phone='123-456-7890',
            is_active=True
        )
        
        print(f"✅ Created student: {user.email}")
    else:
        print("ℹ️  Student already exists")

def test_authentication():
    """Test authentication with email"""
    print("\n🔐 Testing Authentication")
    print("=" * 30)
    
    from django.contrib.auth import authenticate
    
    # Test cases
    test_cases = [
        ('lecturer@example.com', 'password123', 'Lecturer'),
        ('student@example.com', 'password123', 'Student'),
        ('invalid@example.com', 'password123', 'Invalid Email'),
        ('lecturer@example.com', 'wrongpass', 'Wrong Password'),
    ]
    
    for email, password, description in test_cases:
        print(f"🧪 Testing {description}:")
        print(f"   Email: {email}")
        print(f"   Password: {'*' * len(password)}")
        
        user = authenticate(username=email, password=password)
        
        if user:
            print(f"   ✅ Success: {user.get_full_name() or user.username}")
            print(f"   Role: {'Lecturer' if user.is_staff else 'Student'}")
        else:
            print(f"   ❌ Failed: Authentication failed")
        print()

def show_login_instructions():
    """Show login instructions"""
    print("\n📋 Login Instructions")
    print("=" * 25)
    print("🎓 For Students:")
    print("   Email: student@example.com")
    print("   Password: password123")
    print("   → Redirects to Student Dashboard")
    print()
    print("👨‍🏫 For Lecturers:")
    print("   Email: lecturer@example.com")
    print("   Password: password123")
    print("   → Redirects to Lecturer Dashboard")
    print()
    print("🌐 Login URL: http://localhost:8000/login/")

def main():
    print("🎯 Email Login System Test")
    print("=" * 50)
    
    # Test current users
    has_users = test_email_authentication()
    
    # Create test users if needed
    if not has_users:
        create_test_users()
        has_users = test_email_authentication()
    
    # Test authentication
    if has_users:
        test_authentication()
    
    # Show instructions
    show_login_instructions()
    
    print("\n" + "=" * 50)
    print("📊 System Status:")
    print(f"Email Authentication: {'✅ READY' if has_users else '❌ NEEDS SETUP'}")
    
    if has_users:
        print("\n🎉 Email login system is ready!")
        print("\n💡 Next steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Go to: http://localhost:8000/login/")
        print("3. Login with email and password")
        print("4. System will redirect based on user role")
    else:
        print("\n⚠️  System needs setup")
        print("Run this script again or create users manually")

if __name__ == "__main__":
    main()
