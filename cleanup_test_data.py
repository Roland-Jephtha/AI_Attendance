#!/usr/bin/env python
"""
Clean up test data to fix UNIQUE constraint issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def cleanup_test_data():
    """Remove test data that might be causing conflicts"""
    from django.contrib.auth.models import User
    from attendance.models import Student
    
    print("🧹 Cleaning up test data...")
    
    # Common test IDs that might exist
    test_ids = [
        'TEST001', 'TEST002', 'TEST123',
        'COMPLETE001', 'DEBUG001', 'SIGNUP001',
        'MIN001', 'MINIMAL001', 'FACETEST001',
        'STUDENT001', 'DEMO001', 'EXAMPLE001'
    ]
    
    test_emails = [
        'test@example.com', 'test@test.com',
        'complete@test.com', 'debug@example.com',
        'minimal@test.com', 'facetest@test.com',
        'demo@example.com', 'student@test.com'
    ]
    
    # Remove test users
    deleted_users = 0
    for test_id in test_ids:
        try:
            users = User.objects.filter(username=test_id)
            count = users.count()
            if count > 0:
                users.delete()
                deleted_users += count
                print(f"   ✅ Removed {count} user(s) with username: {test_id}")
        except Exception as e:
            print(f"   ⚠️  Error removing user {test_id}: {e}")
    
    # Remove test students
    deleted_students = 0
    for test_id in test_ids:
        try:
            students = Student.objects.filter(student_id=test_id)
            count = students.count()
            if count > 0:
                students.delete()
                deleted_students += count
                print(f"   ✅ Removed {count} student(s) with ID: {test_id}")
        except Exception as e:
            print(f"   ⚠️  Error removing student {test_id}: {e}")
    
    # Remove users with test emails
    for email in test_emails:
        try:
            users = User.objects.filter(email=email)
            count = users.count()
            if count > 0:
                users.delete()
                deleted_users += count
                print(f"   ✅ Removed {count} user(s) with email: {email}")
        except Exception as e:
            print(f"   ⚠️  Error removing users with email {email}: {e}")
    
    # Remove students with test emails
    for email in test_emails:
        try:
            students = Student.objects.filter(email=email)
            count = students.count()
            if count > 0:
                students.delete()
                deleted_students += count
                print(f"   ✅ Removed {count} student(s) with email: {email}")
        except Exception as e:
            print(f"   ⚠️  Error removing students with email {email}: {e}")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   Users removed: {deleted_users}")
    print(f"   Students removed: {deleted_students}")
    
    return deleted_users + deleted_students > 0

def check_current_data():
    """Check what data currently exists"""
    from django.contrib.auth.models import User
    from attendance.models import Student
    
    print("\n📋 Current Database Status:")
    
    total_users = User.objects.count()
    total_students = Student.objects.count()
    
    print(f"   Total Users: {total_users}")
    print(f"   Total Students: {total_students}")
    
    # Show recent users (last 10)
    recent_users = User.objects.order_by('-id')[:10]
    if recent_users:
        print(f"\n   Recent Users:")
        for user in recent_users:
            print(f"     - {user.username} ({user.email})")
    
    # Show recent students (last 10)
    recent_students = Student.objects.order_by('-id')[:10]
    if recent_students:
        print(f"\n   Recent Students:")
        for student in recent_students:
            print(f"     - {student.student_id} ({student.email})")

def main():
    print("🧹 Test Data Cleanup Tool")
    print("=" * 40)
    
    # Check current data
    check_current_data()
    
    # Ask for confirmation
    print("\n" + "=" * 40)
    response = input("Do you want to clean up test data? (y/n): ").lower().strip()
    
    if response == 'y':
        # Clean up
        cleaned = cleanup_test_data()
        
        if cleaned:
            print("\n✅ Cleanup completed!")
            print("\n📋 Updated Database Status:")
            check_current_data()
        else:
            print("\n✅ No test data found to clean up.")
        
        print("\n🎯 You can now try signup again with any Student ID!")
        
    else:
        print("\n❌ Cleanup cancelled.")
    
    print("\n" + "=" * 40)
    print("💡 Tips:")
    print("1. Use unique Student IDs for each signup attempt")
    print("2. Use unique email addresses")
    print("3. If you get UNIQUE constraint errors, run this cleanup script")

if __name__ == "__main__":
    main()
