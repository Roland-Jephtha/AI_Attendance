#!/usr/bin/env python
"""
Create superuser with custom user model
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def create_superuser():
    """Create a superuser with the custom user model"""
    print("🔧 Creating Superuser with Custom User Model")
    print("=" * 45)
    
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("ℹ️  Superuser already exists")
            superuser = User.objects.filter(is_superuser=True).first()
            print(f"   Username: {superuser.username}")
            print(f"   Email: {superuser.email}")
            return True
        
        # Create superuser
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            position='lecturer'  # Make admin a lecturer for full access
        )
        
        print(f"✅ Created superuser: {superuser.username}")
        print(f"   Email: {superuser.email}")
        print(f"   Password: admin123")
        print(f"   Position: {superuser.position}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating superuser: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_demo_users():
    """Create demo users for testing"""
    print(f"\n👥 Creating Demo Users")
    print("=" * 25)
    
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        demo_users = [
            {
                'username': 'lecturer1',
                'email': 'lecturer@example.com',
                'password': 'lecturer123',
                'first_name': 'Dr. John',
                'last_name': 'Smith',
                'position': 'lecturer'
            },
            {
                'username': 'student1',
                'email': 'student@example.com',
                'password': 'student123',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'position': 'student',
                'student_id': 'STU001'
            }
        ]
        
        created_count = 0
        
        for user_data in demo_users:
            email = user_data['email']
            
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(**user_data)
                print(f"✅ Created {user_data['position']}: {user.email}")
                created_count += 1
            else:
                print(f"ℹ️  User {email} already exists")
        
        print(f"\n📊 Created {created_count} new demo users")
        return True
        
    except Exception as e:
        print(f"❌ Error creating demo users: {str(e)}")
        return False

def show_login_info():
    """Show login information"""
    print(f"\n🔑 Login Information")
    print("=" * 25)
    
    print("🔧 Admin/Superuser:")
    print("   Email: admin@example.com")
    print("   Password: admin123")
    print("   URL: /admin/")
    
    print("\n👨‍🏫 Lecturer:")
    print("   Email: lecturer@example.com")
    print("   Password: lecturer123")
    print("   URL: /lecturer/dashboard/")
    
    print("\n🎓 Student:")
    print("   Email: student@example.com")
    print("   Password: student123")
    print("   URL: /dashboard/")

def main():
    print("🎯 Custom User Model Setup")
    print("=" * 50)
    
    # Create superuser
    superuser_ok = create_superuser()
    
    # Create demo users
    demo_ok = create_demo_users()
    
    # Show login info
    show_login_info()
    
    print("\n" + "=" * 50)
    print("📊 Setup Results:")
    print(f"Superuser: {'✅ READY' if superuser_ok else '❌ FAILED'}")
    print(f"Demo Users: {'✅ READY' if demo_ok else '❌ FAILED'}")
    
    if superuser_ok:
        print("\n🎉 Custom User Model setup complete!")
        print("\n💡 Next steps:")
        print("1. Start server: python manage.py runserver")
        print("2. Access admin: http://localhost:8000/admin/")
        print("3. Login with admin credentials")
        print("4. Test user creation and position assignment")
        print("5. Test login with different user types")
    else:
        print("\n⚠️  Setup incomplete - check errors above")

if __name__ == "__main__":
    main()
