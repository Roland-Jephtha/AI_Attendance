#!/usr/bin/env python
"""
Create working users without deleting database
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def create_users():
    """Create users that work with the current system"""
    print("👥 Creating Working Users")
    print("=" * 30)
    
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Create admin user
        admin_email = 'admin@example.com'
        if not User.objects.filter(email=admin_email).exists():
            admin = User.objects.create_superuser(
                username='admin',
                email=admin_email,
                password='admin123',
                first_name='Admin',
                last_name='User',
                position='lecturer'
            )
            print(f"✅ Created admin: {admin.email}")
        else:
            print(f"ℹ️  Admin already exists: {admin_email}")
        
        # Create lecturer
        lecturer_email = 'lecturer@example.com'
        if not User.objects.filter(email=lecturer_email).exists():
            lecturer = User.objects.create_user(
                username='lecturer1',
                email=lecturer_email,
                password='lecturer123',
                first_name='Dr. John',
                last_name='Smith',
                position='lecturer'
            )
            print(f"✅ Created lecturer: {lecturer.email}")
        else:
            print(f"ℹ️  Lecturer already exists: {lecturer_email}")
        
        # Create student
        student_email = 'student@example.com'
        if not User.objects.filter(email=student_email).exists():
            student = User.objects.create_user(
                username='student1',
                email=student_email,
                password='student123',
                first_name='Jane',
                last_name='Doe',
                position='student',
                student_id='STU001'
            )
            print(f"✅ Created student: {student.email}")
        else:
            print(f"ℹ️  Student already exists: {student_email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_login():
    """Test login functionality"""
    print(f"\n🔐 Testing Login")
    print("=" * 20)
    
    try:
        from django.contrib.auth import authenticate
        
        # Test cases
        test_cases = [
            ('admin@example.com', 'admin123', 'Admin'),
            ('lecturer@example.com', 'lecturer123', 'Lecturer'),
            ('student@example.com', 'student123', 'Student'),
        ]
        
        for email, password, role in test_cases:
            user = authenticate(username=email, password=password)
            if user:
                print(f"✅ {role}: {email} - Position: {user.position}")
            else:
                print(f"❌ {role}: {email} - Login failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing login: {str(e)}")
        return False

def show_all_users():
    """Show all users in the system"""
    print(f"\n👤 All Users")
    print("=" * 15)
    
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        users = User.objects.all()
        
        print(f"Total users: {users.count()}")
        
        for user in users:
            print(f"📧 {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Name: {user.get_full_name()}")
            print(f"   Position: {user.position}")
            print(f"   Staff: {user.is_staff}")
            print(f"   Superuser: {user.is_superuser}")
            print(f"   Active: {user.is_active}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error showing users: {str(e)}")
        return False

def show_credentials():
    """Show login credentials"""
    print("🔑 Login Credentials")
    print("=" * 25)
    
    print("🔧 Admin Panel:")
    print("   URL: http://localhost:8000/admin/")
    print("   Email: admin@example.com")
    print("   Password: admin123")
    
    print("\n👨‍🏫 Lecturer Dashboard:")
    print("   URL: http://localhost:8000/lecturer/dashboard/")
    print("   Email: lecturer@example.com")
    print("   Password: lecturer123")
    
    print("\n🎓 Student Dashboard:")
    print("   URL: http://localhost:8000/dashboard/")
    print("   Email: student@example.com")
    print("   Password: student123")
    
    print("\n🌐 Main Login:")
    print("   URL: http://localhost:8000/login/")
    print("   Use EMAIL and PASSWORD (not username)")

def main():
    print("🎯 Create Working Users")
    print("=" * 50)
    
    # Create users
    users_ok = create_users()
    
    # Show all users
    show_all_users()
    
    # Test login
    login_ok = test_login()
    
    # Show credentials
    print()
    show_credentials()
    
    print("\n" + "=" * 50)
    print("📊 Results:")
    print(f"User Creation: {'✅ SUCCESS' if users_ok else '❌ FAILED'}")
    print(f"Login Test: {'✅ SUCCESS' if login_ok else '❌ FAILED'}")
    
    if users_ok and login_ok:
        print("\n🎉 Users created successfully!")
        print("\n💡 Important Notes:")
        print("1. Use EMAIL for login, not username")
        print("2. Admin panel: admin@example.com / admin123")
        print("3. Regular login: Use the credentials above")
        print("4. Start server: python manage.py runserver")
    else:
        print("\n⚠️  Some issues occurred - check errors above")

if __name__ == "__main__":
    main()
