#!/usr/bin/env python
"""
Demo script to create users with different positions
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def create_demo_users():
    """Create demo users for testing"""
    print("🎯 Creating Demo Users")
    print("=" * 30)
    
    from django.contrib.auth.models import User
    from attendance.models import Student, Class
    from django.db import transaction
    
    users_to_create = [
        {
            'email': 'john.lecturer@university.edu',
            'password': 'lecturer123',
            'first_name': 'Dr. John',
            'last_name': 'Smith',
            'position': 'lecturer'
        },
        {
            'email': 'mary.lecturer@university.edu',
            'password': 'lecturer123',
            'first_name': 'Prof. Mary',
            'last_name': 'Johnson',
            'position': 'lecturer'
        },
        {
            'email': 'alice.student@university.edu',
            'password': 'student123',
            'first_name': 'Alice',
            'last_name': 'Brown',
            'position': 'student',
            'student_id': 'STU001',
            'phone': '123-456-7890'
        },
        {
            'email': 'bob.student@university.edu',
            'password': 'student123',
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'position': 'student',
            'student_id': 'STU002',
            'phone': '123-456-7891'
        },
        {
            'email': 'charlie.student@university.edu',
            'password': 'student123',
            'first_name': 'Charlie',
            'last_name': 'Davis',
            'position': 'student',
            'student_id': 'STU003',
            'phone': '123-456-7892'
        }
    ]
    
    created_users = []
    
    for user_data in users_to_create:
        email = user_data['email']
        
        # Skip if user already exists
        if User.objects.filter(email=email).exists():
            print(f"⚠️  User {email} already exists, skipping...")
            continue
        
        try:
            with transaction.atomic():
                # Create Django user
                if user_data['position'] == 'lecturer':
                    username = email.split('@')[0]
                    is_staff = True
                else:
                    username = user_data['student_id']
                    is_staff = False
                
                # Ensure unique username
                original_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    is_staff=is_staff
                )
                
                print(f"✅ Created user: {user.get_full_name()} ({email})")
                
                # Create student record if needed
                if user_data['position'] == 'student':
                    student = Student.objects.create(
                        student_id=user_data['student_id'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        email=email,
                        phone=user_data.get('phone', ''),
                        is_active=True
                    )
                    print(f"   📚 Created student record: {student.student_id}")
                
                created_users.append({
                    'user': user,
                    'position': user_data['position'],
                    'email': email,
                    'password': user_data['password']
                })
                
        except Exception as e:
            print(f"❌ Error creating user {email}: {str(e)}")
    
    return created_users

def create_demo_classes(lecturers):
    """Create demo classes and enroll students"""
    print(f"\n📚 Creating Demo Classes")
    print("=" * 25)
    
    from attendance.models import Class, Student
    
    classes_to_create = [
        {
            'code': 'CS101',
            'name': 'Introduction to Computer Science',
            'description': 'Basic programming concepts and problem solving',
            'instructor_email': 'john.lecturer@university.edu'
        },
        {
            'code': 'MATH201',
            'name': 'Calculus II',
            'description': 'Advanced calculus topics including integration',
            'instructor_email': 'mary.lecturer@university.edu'
        },
        {
            'code': 'CS201',
            'name': 'Data Structures',
            'description': 'Arrays, linked lists, trees, and algorithms',
            'instructor_email': 'john.lecturer@university.edu'
        }
    ]
    
    created_classes = []
    
    for class_data in classes_to_create:
        # Skip if class already exists
        if Class.objects.filter(code=class_data['code']).exists():
            print(f"⚠️  Class {class_data['code']} already exists, skipping...")
            continue
        
        try:
            # Find instructor
            from django.contrib.auth.models import User
            instructor = User.objects.get(email=class_data['instructor_email'])
            
            # Create class
            class_obj = Class.objects.create(
                code=class_data['code'],
                name=class_data['name'],
                description=class_data['description'],
                instructor=instructor,
                is_active=True
            )
            
            print(f"✅ Created class: {class_obj.code} - {class_obj.name}")
            print(f"   👨‍🏫 Instructor: {instructor.get_full_name()}")
            
            # Enroll all students
            students = Student.objects.filter(is_active=True)
            for student in students:
                class_obj.students.add(student)
            
            print(f"   🎓 Enrolled {students.count()} students")
            
            created_classes.append(class_obj)
            
        except Exception as e:
            print(f"❌ Error creating class {class_data['code']}: {str(e)}")
    
    return created_classes

def show_login_info(created_users):
    """Show login information for created users"""
    print(f"\n🔑 Login Information")
    print("=" * 25)
    
    lecturers = [u for u in created_users if u['position'] == 'lecturer']
    students = [u for u in created_users if u['position'] == 'student']
    
    if lecturers:
        print("👨‍🏫 Lecturers:")
        for user_info in lecturers:
            print(f"   Email: {user_info['email']}")
            print(f"   Password: {user_info['password']}")
            print(f"   Dashboard: /lecturer/dashboard/")
            print()
    
    if students:
        print("🎓 Students:")
        for user_info in students:
            print(f"   Email: {user_info['email']}")
            print(f"   Password: {user_info['password']}")
            print(f"   Dashboard: /dashboard/")
            print()

def main():
    print("🎯 User Management Demo")
    print("=" * 50)
    
    # Create users
    created_users = create_demo_users()
    
    # Create classes if we have lecturers
    lecturers = [u for u in created_users if u['position'] == 'lecturer']
    if lecturers:
        create_demo_classes(lecturers)
    
    # Show login info
    if created_users:
        show_login_info(created_users)
    
    print("=" * 50)
    print("📊 Summary:")
    print(f"Created {len(created_users)} users")
    print(f"Lecturers: {len([u for u in created_users if u['position'] == 'lecturer'])}")
    print(f"Students: {len([u for u in created_users if u['position'] == 'student'])}")
    
    print(f"\n💡 Next steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Go to admin: http://localhost:8000/admin/")
    print("3. Login with superuser account")
    print("4. Manage users in 'Users' section")
    print("5. Test login with created accounts")
    
    print(f"\n🔧 Management Commands:")
    print("Create lecturer:")
    print("python manage.py create_user --email lecturer@example.com --password pass123 --first-name John --last-name Doe --position lecturer")
    print("\nCreate student:")
    print("python manage.py create_user --email student@example.com --password pass123 --first-name Jane --last-name Smith --position student --student-id STU004 --phone 123-456-7890")

if __name__ == "__main__":
    main()
