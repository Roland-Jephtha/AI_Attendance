#!/usr/bin/env python
"""
Set up classes and test enrollment system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def create_test_classes():
    """Create test classes for enrollment"""
    print("📚 Creating Test Classes")
    print("=" * 30)
    
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Class, Student
        
        User = get_user_model()
        
        # Get or create lecturer
        lecturer_email = 'lecturer@example.com'
        try:
            lecturer = User.objects.get(email=lecturer_email)
        except User.DoesNotExist:
            lecturer = User.objects.create_user(
                username='lecturer1',
                email=lecturer_email,
                password='lecturer123',
                first_name='Dr. John',
                last_name='Smith',
                position='lecturer'
            )
            print(f"✅ Created lecturer: {lecturer.email}")
        
        # Test classes to create
        test_classes = [
            {
                'code': 'CS101',
                'name': 'Introduction to Computer Science',
                'description': 'Basic programming concepts and problem-solving techniques',
                'schedule': 'Mon/Wed/Fri 9:00-10:00 AM'
            },
            {
                'code': 'MATH201',
                'name': 'Calculus II',
                'description': 'Advanced calculus including integration and series',
                'schedule': 'Tue/Thu 11:00-12:30 PM'
            },
            {
                'code': 'ENG102',
                'name': 'English Composition',
                'description': 'Academic writing and communication skills',
                'schedule': 'Mon/Wed 2:00-3:30 PM'
            },
            {
                'code': 'PHYS101',
                'name': 'General Physics I',
                'description': 'Mechanics, waves, and thermodynamics',
                'schedule': 'Tue/Thu/Fri 10:00-11:00 AM'
            },
            {
                'code': 'HIST201',
                'name': 'World History',
                'description': 'Survey of world civilizations and cultures',
                'schedule': 'Mon/Wed 1:00-2:30 PM'
            }
        ]
        
        created_count = 0
        
        for class_data in test_classes:
            # Check if class already exists
            if not Class.objects.filter(code=class_data['code']).exists():
                class_obj = Class.objects.create(
                    code=class_data['code'],
                    name=class_data['name'],
                    description=class_data['description'],
                    schedule=class_data['schedule'],
                    instructor=lecturer,
                    is_active=True
                )
                print(f"✅ Created class: {class_obj.code} - {class_obj.name}")
                created_count += 1
            else:
                print(f"ℹ️  Class {class_data['code']} already exists")
        
        print(f"\n📊 Created {created_count} new classes")
        return True
        
    except Exception as e:
        print(f"❌ Error creating classes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_test_students():
    """Create test students"""
    print(f"\n👥 Creating Test Students")
    print("=" * 30)
    
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Student
        
        User = get_user_model()
        
        test_students = [
            {
                'username': 'alice',
                'email': 'alice@example.com',
                'password': 'student123',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'student_id': 'STU001'
            },
            {
                'username': 'bob',
                'email': 'bob@example.com',
                'password': 'student123',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'student_id': 'STU002'
            },
            {
                'username': 'charlie',
                'email': 'charlie@example.com',
                'password': 'student123',
                'first_name': 'Charlie',
                'last_name': 'Brown',
                'student_id': 'STU003'
            }
        ]
        
        created_count = 0
        
        for student_data in test_students:
            email = student_data['email']
            
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=student_data['username'],
                    email=email,
                    password=student_data['password'],
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name'],
                    position='student',
                    student_id=student_data['student_id']
                )
                print(f"✅ Created student: {user.email} ({student_data['student_id']})")
                created_count += 1
            else:
                print(f"ℹ️  Student {email} already exists")
        
        print(f"\n📊 Created {created_count} new students")
        return True
        
    except Exception as e:
        print(f"❌ Error creating students: {str(e)}")
        return False

def test_enrollment():
    """Test the enrollment system"""
    print(f"\n🎯 Testing Enrollment System")
    print("=" * 35)
    
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Class, Student
        
        User = get_user_model()
        
        # Get a test student
        student_user = User.objects.filter(position='student').first()
        if not student_user:
            print("❌ No student users found")
            return False
        
        student = Student.objects.get(user=student_user)
        
        # Get available classes
        available_classes = Class.objects.filter(is_active=True)
        enrolled_classes = student.enrolled_classes.all()
        
        print(f"👤 Student: {student.full_name} ({student.student_id})")
        print(f"📚 Available classes: {available_classes.count()}")
        print(f"✅ Currently enrolled: {enrolled_classes.count()}")
        
        # Show available classes
        print(f"\n📋 Available Classes:")
        for class_obj in available_classes:
            is_enrolled = class_obj in enrolled_classes
            status = "✅ ENROLLED" if is_enrolled else "⏳ AVAILABLE"
            print(f"   {class_obj.code} - {class_obj.name} [{status}]")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enrollment: {str(e)}")
        return False

def show_system_status():
    """Show current system status"""
    print(f"\n📊 System Status")
    print("=" * 20)
    
    try:
        from django.contrib.auth import get_user_model
        from attendance.models import Class, Student, Attendance
        
        User = get_user_model()
        
        # Count users
        total_users = User.objects.count()
        lecturers = User.objects.filter(position='lecturer').count()
        students = User.objects.filter(position='student').count()
        
        # Count classes and enrollments
        total_classes = Class.objects.filter(is_active=True).count()
        total_enrollments = sum(cls.students.count() for cls in Class.objects.filter(is_active=True))
        total_attendance = Attendance.objects.count()
        
        print(f"👥 Users: {total_users} (Lecturers: {lecturers}, Students: {students})")
        print(f"📚 Active Classes: {total_classes}")
        print(f"📝 Total Enrollments: {total_enrollments}")
        print(f"✅ Attendance Records: {total_attendance}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting system status: {str(e)}")
        return False

def show_login_info():
    """Show login information"""
    print(f"\n🔑 Login Information")
    print("=" * 25)
    
    print("👨‍🏫 Lecturer:")
    print("   Email: lecturer@example.com")
    print("   Password: lecturer123")
    print("   Dashboard: /lecturer/dashboard/")
    
    print("\n🎓 Students:")
    print("   Alice: alice@example.com / student123")
    print("   Bob: bob@example.com / student123")
    print("   Charlie: charlie@example.com / student123")
    print("   Dashboard: /dashboard/")
    
    print("\n🌐 URLs:")
    print("   Login: http://localhost:8000/login/")
    print("   Admin: http://localhost:8000/admin/")

def main():
    print("🎯 Class Enrollment System Setup")
    print("=" * 50)
    
    # Create classes
    classes_ok = create_test_classes()
    
    # Create students
    students_ok = create_test_students()
    
    # Test enrollment
    enrollment_ok = test_enrollment()
    
    # Show system status
    status_ok = show_system_status()
    
    # Show login info
    show_login_info()
    
    print("\n" + "=" * 50)
    print("📊 Setup Results:")
    print(f"Classes: {'✅ SUCCESS' if classes_ok else '❌ FAILED'}")
    print(f"Students: {'✅ SUCCESS' if students_ok else '❌ FAILED'}")
    print(f"Enrollment Test: {'✅ SUCCESS' if enrollment_ok else '❌ FAILED'}")
    print(f"System Status: {'✅ SUCCESS' if status_ok else '❌ FAILED'}")
    
    if all([classes_ok, students_ok, enrollment_ok, status_ok]):
        print("\n🎉 Setup completed successfully!")
        print("\n💡 Next steps:")
        print("1. Start server: python manage.py runserver")
        print("2. Login as student and test enrollment")
        print("3. Login as lecturer and start attendance sessions")
        print("4. Test face recognition attendance")
    else:
        print("\n⚠️  Some issues occurred - check errors above")

if __name__ == "__main__":
    main()
