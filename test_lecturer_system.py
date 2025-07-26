#!/usr/bin/env python
"""
Test the lecturer dashboard system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def test_lecturer_system():
    """Test the lecturer dashboard system"""
    print("🧪 Testing Lecturer Dashboard System")
    print("=" * 40)
    
    from django.contrib.auth.models import User
    from attendance.models import Student, Class, Attendance
    
    # Check for lecturers (staff users)
    lecturers = User.objects.filter(is_staff=True)
    print(f"📚 Found {lecturers.count()} lecturers:")
    
    for lecturer in lecturers:
        print(f"   👨‍🏫 {lecturer.get_full_name() or lecturer.username} ({lecturer.username})")
        
        # Check classes taught by this lecturer
        classes = Class.objects.filter(instructor=lecturer, is_active=True)
        print(f"      Classes: {classes.count()}")
        
        for cls in classes:
            students_count = cls.students.filter(is_active=True).count()
            print(f"         📖 {cls.code} - {cls.name} ({students_count} students)")
    
    # Check students
    students = Student.objects.filter(is_active=True)
    print(f"\n👥 Found {students.count()} active students:")
    
    for student in students:
        print(f"   🎓 {student.full_name} ({student.student_id})")
        enrolled_classes = student.enrolled_classes.filter(is_active=True)
        print(f"      Enrolled in: {enrolled_classes.count()} classes")
    
    return lecturers.count() > 0 and students.count() > 0

def create_test_data():
    """Create test data if needed"""
    print("\n🔧 Creating Test Data")
    print("=" * 30)
    
    from django.contrib.auth.models import User
    from attendance.models import Student, Class
    
    # Create a test lecturer if none exists
    if not User.objects.filter(is_staff=True).exists():
        lecturer = User.objects.create_user(
            username='lecturer1',
            password='password123',
            first_name='Dr. John',
            last_name='Smith',
            email='lecturer@example.com',
            is_staff=True
        )
        print(f"✅ Created lecturer: {lecturer.get_full_name()}")
        
        # Create a test class
        test_class = Class.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            instructor=lecturer,
            description='Basic computer science concepts',
            is_active=True
        )
        print(f"✅ Created class: {test_class.code}")
        
        # Enroll existing students in the class
        students = Student.objects.filter(is_active=True)
        for student in students:
            test_class.students.add(student)
        
        print(f"✅ Enrolled {students.count()} students in {test_class.code}")
        
        return True
    
    return False

def show_urls():
    """Show important URLs"""
    print("\n🔗 Important URLs")
    print("=" * 20)
    print("Lecturer Dashboard: /lecturer/dashboard/")
    print("Student Dashboard: /dashboard/")
    print("Login: /login/")
    print("Admin: /admin/")

def main():
    print("🎯 Lecturer System Test")
    print("=" * 50)
    
    # Test current system
    system_ok = test_lecturer_system()
    
    # Create test data if needed
    if not system_ok:
        print("\n⚠️  System needs test data")
        created = create_test_data()
        if created:
            print("✅ Test data created successfully")
            system_ok = test_lecturer_system()
    
    # Show URLs
    show_urls()
    
    print("\n" + "=" * 50)
    print("📊 System Status:")
    print(f"Lecturer System: {'✅ READY' if system_ok else '❌ NEEDS SETUP'}")
    
    if system_ok:
        print("\n🎉 System is ready!")
        print("\n💡 Next steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Login as lecturer (staff user)")
        print("3. Go to /lecturer/dashboard/")
        print("4. Click 'Start Attendance' for a class")
        print("5. Students use face recognition on that page")
    else:
        print("\n⚠️  System needs setup")
        print("Create lecturers and classes in Django admin")

if __name__ == "__main__":
    main()
