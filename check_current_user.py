#!/usr/bin/env python
"""
Check current user and face database status
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def check_face_database_simple():
    """Simple check of face database"""
    from django.conf import settings
    
    face_db_path = os.path.join(settings.MEDIA_ROOT, 'face_db')
    
    print("📁 Face Database Contents:")
    print(f"Path: {face_db_path}")
    
    if not os.path.exists(face_db_path):
        print("❌ Face database doesn't exist")
        return []
    
    student_dirs = []
    for item in os.listdir(face_db_path):
        item_path = os.path.join(face_db_path, item)
        if os.path.isdir(item_path):
            student_dirs.append(item)
            face_files = [f for f in os.listdir(item_path) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"  📂 {item}: {len(face_files)} face images")
    
    return student_dirs

def check_students_in_db():
    """Check students in database"""
    from attendance.models import Student
    
    print("\n👥 Students in Database:")
    students = Student.objects.all()
    
    for student in students:
        print(f"  🎓 {student.student_id}: {student.full_name}")
    
    return [s.student_id for s in students]

def main():
    print("🔍 Current User & Face Database Check")
    print("=" * 40)
    
    # Check face database
    face_students = check_face_database_simple()
    
    # Check database students
    db_students = check_students_in_db()
    
    print(f"\n📊 Summary:")
    print(f"Face images for: {face_students}")
    print(f"Students in DB: {db_students}")
    
    # Check for mismatches
    if face_students and db_students:
        missing_faces = [s for s in db_students if s not in face_students]
        extra_faces = [s for s in face_students if s not in db_students]
        
        if missing_faces:
            print(f"⚠️  Students without face images: {missing_faces}")
        if extra_faces:
            print(f"⚠️  Face images without student records: {extra_faces}")
        
        if not missing_faces and not extra_faces:
            print("✅ Face database and student records match!")
    
    print(f"\n💡 For testing:")
    if face_students:
        print(f"1. Login as student: {face_students[0]}")
        print(f"2. Try face recognition")
        print(f"3. Should recognize as: {face_students[0]}")
    else:
        print("1. No face images found")
        print("2. Students need to enroll faces first")
        print("3. Go to /enroll-face/ to register")

if __name__ == "__main__":
    main()
