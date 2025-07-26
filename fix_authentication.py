#!/usr/bin/env python
"""
Fix authentication issues and create working users
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def delete_database():
    """Delete the existing database"""
    print("🗑️  Deleting existing database...")
    
    db_file = 'db.sqlite3'
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"✅ Deleted {db_file}")
            return True
        except Exception as e:
            print(f"❌ Error deleting database: {str(e)}")
            return False
    else:
        print(f"ℹ️  Database file {db_file} not found")
        return True

def run_migrations():
    """Run Django migrations"""
    print("\n📦 Running migrations...")
    
    try:
        from django.core.management import execute_from_command_line
        
        # Run migrate command
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=0'])
        print("✅ Migrations completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error running migrations: {str(e)}")
        return False

def create_test_users():
    """Create test users with the custom user model"""
    print("\n👥 Creating test users...")
    
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Create superuser (admin)
        if not User.objects.filter(email='admin@example.com').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                position='lecturer'
            )
            print(f"✅ Created admin: {admin.email}")
        else:
            print("ℹ️  Admin user already exists")
        
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
        else:
            print("ℹ️  Lecturer user already exists")
        
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
        else:
            print("ℹ️  Student user already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication():
    """Test authentication with created users"""
    print("\n🔐 Testing authentication...")
    
    try:
        from django.contrib.auth import authenticate
        
        test_cases = [
            ('admin@example.com', 'admin123', 'Admin'),
            ('lecturer@example.com', 'lecturer123', 'Lecturer'),
            ('student@example.com', 'student123', 'Student'),
        ]
        
        all_passed = True
        
        for email, password, role in test_cases:
            user = authenticate(username=email, password=password)
            if user:
                print(f"✅ {role} login successful: {user.email} (position: {user.position})")
            else:
                print(f"❌ {role} login failed")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing authentication: {str(e)}")
        return False

def show_login_credentials():
    """Show login credentials for all users"""
    print("\n🔑 Login Credentials")
    print("=" * 30)
    
    print("🔧 Admin Panel (http://localhost:8000/admin/):")
    print("   Email: admin@example.com")
    print("   Password: admin123")
    
    print("\n👨‍🏫 Lecturer Dashboard (http://localhost:8000/lecturer/dashboard/):")
    print("   Email: lecturer@example.com")
    print("   Password: lecturer123")
    
    print("\n🎓 Student Dashboard (http://localhost:8000/dashboard/):")
    print("   Email: student@example.com")
    print("   Password: student123")
    
    print("\n🌐 Login Page: http://localhost:8000/login/")

def verify_models():
    """Verify that models are working correctly"""
    print("\n🔍 Verifying models...")
    
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Student, Lecturer
        
        User = get_user_model()
        
        # Check users
        users = User.objects.all()
        print(f"✅ Found {users.count()} users")
        
        # Check students
        students = Student.objects.all()
        print(f"✅ Found {students.count()} student profiles")
        
        # Check lecturers
        lecturers = Lecturer.objects.all()
        print(f"✅ Found {lecturers.count()} lecturer profiles")
        
        # Show user details
        for user in users:
            print(f"   👤 {user.email} - {user.position} - Active: {user.is_active}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying models: {str(e)}")
        return False

def main():
    print("🎯 Authentication Fix Script")
    print("=" * 50)
    
    # Step 1: Delete database
    db_deleted = delete_database()
    if not db_deleted:
        print("❌ Failed to delete database")
        return
    
    # Step 2: Run migrations
    migrations_ok = run_migrations()
    if not migrations_ok:
        print("❌ Failed to run migrations")
        return
    
    # Step 3: Create users
    users_created = create_test_users()
    if not users_created:
        print("❌ Failed to create users")
        return
    
    # Step 4: Verify models
    models_ok = verify_models()
    
    # Step 5: Test authentication
    auth_ok = test_authentication()
    
    # Step 6: Show credentials
    show_login_credentials()
    
    print("\n" + "=" * 50)
    print("📊 Results:")
    print(f"Database Reset: ✅ SUCCESS")
    print(f"Migrations: ✅ SUCCESS")
    print(f"User Creation: {'✅ SUCCESS' if users_created else '❌ FAILED'}")
    print(f"Model Verification: {'✅ SUCCESS' if models_ok else '❌ FAILED'}")
    print(f"Authentication Test: {'✅ SUCCESS' if auth_ok else '❌ FAILED'}")
    
    if all([users_created, models_ok, auth_ok]):
        print("\n🎉 Authentication system fixed!")
        print("\n💡 Next steps:")
        print("1. Start server: python manage.py runserver")
        print("2. Try logging in with the credentials above")
        print("3. Admin panel should work with email login")
        print("4. Regular login page should work with email login")
    else:
        print("\n⚠️  Some issues remain - check the errors above")

if __name__ == "__main__":
    main()
