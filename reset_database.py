#!/usr/bin/env python
"""
Reset database and create fresh users with custom user model
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def reset_database():
    """Reset the database"""
    print("🔄 Resetting Database")
    print("=" * 25)
    
    try:
        # Delete database file if it exists
        db_path = 'db.sqlite3'
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✅ Deleted database file: {db_path}")
        else:
            print(f"ℹ️  Database file not found: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {str(e)}")
        return False

def run_migrations():
    """Run Django migrations"""
    print(f"\n📦 Running Migrations")
    print("=" * 25)
    
    try:
        from django.core.management import execute_from_command_line
        
        # Run migrations
        print("Running: python manage.py migrate")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Migrations completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error running migrations: {str(e)}")
        return False

def create_users():
    """Create users with custom user model"""
    print(f"\n👥 Creating Users")
    print("=" * 20)
    
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Student, Lecturer
        
        User = get_user_model()
        
        # Create superuser
        if not User.objects.filter(is_superuser=True).exists():
            superuser = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                position='lecturer'
            )
            print(f"✅ Created superuser: {superuser.email}")
        
        # Create lecturer
        if not User.objects.filter(email='lecturer@example.com').exists():
            lecturer = User.objects.create_user(
                username='lecturer1',
                email='lecturer@example.com',
                password='lecturer123',
                first_name='Dr. John',
                last_name='Smith',
                position='lecturer'
            )
            print(f"✅ Created lecturer: {lecturer.email}")
        
        # Create student
        if not User.objects.filter(email='student@example.com').exists():
            student = User.objects.create_user(
                username='student1',
                email='student@example.com',
                password='student123',
                first_name='Jane',
                last_name='Doe',
                position='student',
                student_id='STU001'
            )
            print(f"✅ Created student: {student.email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication():
    """Test authentication with created users"""
    print(f"\n🔐 Testing Authentication")
    print("=" * 30)
    
    try:
        from django.contrib.auth import authenticate
        
        test_cases = [
            ('admin@example.com', 'admin123', 'Admin'),
            ('lecturer@example.com', 'lecturer123', 'Lecturer'),
            ('student@example.com', 'student123', 'Student'),
        ]
        
        for email, password, role in test_cases:
            user = authenticate(username=email, password=password)
            if user:
                print(f"✅ {role} authentication successful: {user.email}")
            else:
                print(f"❌ {role} authentication failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing authentication: {str(e)}")
        return False

def show_login_info():
    """Show login information"""
    print(f"\n🔑 Login Information")
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
    
    print("\n🌐 Login Page:")
    print("   URL: http://localhost:8000/login/")

def main():
    print("🎯 Database Reset & Custom User Setup")
    print("=" * 50)
    
    # Reset database
    reset_ok = reset_database()
    if not reset_ok:
        print("❌ Database reset failed")
        return
    
    # Run migrations
    migrate_ok = run_migrations()
    if not migrate_ok:
        print("❌ Migrations failed")
        return
    
    # Create users
    users_ok = create_users()
    if not users_ok:
        print("❌ User creation failed")
        return
    
    # Test authentication
    auth_ok = test_authentication()
    
    # Show login info
    show_login_info()
    
    print("\n" + "=" * 50)
    print("📊 Setup Results:")
    print(f"Database Reset: {'✅ SUCCESS' if reset_ok else '❌ FAILED'}")
    print(f"Migrations: {'✅ SUCCESS' if migrate_ok else '❌ FAILED'}")
    print(f"User Creation: {'✅ SUCCESS' if users_ok else '❌ FAILED'}")
    print(f"Authentication: {'✅ SUCCESS' if auth_ok else '❌ FAILED'}")
    
    if all([reset_ok, migrate_ok, users_ok, auth_ok]):
        print("\n🎉 Setup completed successfully!")
        print("\n💡 Next steps:")
        print("1. Start server: python manage.py runserver")
        print("2. Access admin: http://localhost:8000/admin/")
        print("3. Login with admin credentials")
        print("4. Test different user types")
    else:
        print("\n⚠️  Setup incomplete - check errors above")

if __name__ == "__main__":
    main()
