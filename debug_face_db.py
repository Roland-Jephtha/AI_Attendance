#!/usr/bin/env python
"""
Simple debug script to check face database
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def check_face_database():
    """Check what's in the face database"""
    from django.conf import settings
    
    face_db_path = os.path.join(settings.MEDIA_ROOT, 'face_db')
    
    print("🔍 Face Database Debug")
    print("=" * 30)
    print(f"Face DB Path: {face_db_path}")
    
    if not os.path.exists(face_db_path):
        print("❌ Face database directory doesn't exist!")
        return False
    
    # List contents
    items = os.listdir(face_db_path)
    print(f"Items in face_db: {len(items)}")
    
    student_dirs = []
    cache_files = []
    
    for item in items:
        item_path = os.path.join(face_db_path, item)
        if os.path.isdir(item_path):
            student_dirs.append(item)
        elif item.endswith('.pkl'):
            cache_files.append(item)
    
    print(f"Student directories: {len(student_dirs)}")
    print(f"Cache files: {len(cache_files)}")
    
    # Show student directories
    for student_dir in student_dirs:
        student_path = os.path.join(face_db_path, student_dir)
        face_files = [f for f in os.listdir(student_path) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        print(f"  📂 {student_dir}: {len(face_files)} images")
        for face_file in face_files:
            face_path = os.path.join(student_path, face_file)
            size_kb = os.path.getsize(face_path) / 1024
            print(f"    📄 {face_file} ({size_kb:.1f} KB)")
    
    # Show cache files
    for cache_file in cache_files:
        cache_path = os.path.join(face_db_path, cache_file)
        size_kb = os.path.getsize(cache_path) / 1024
        print(f"  📦 {cache_file} ({size_kb:.1f} KB)")
    
    return len(student_dirs) > 0

def check_students():
    """Check students in database"""
    from attendance.models import Student, FaceEncoding
    
    print("\n👥 Students in Database")
    print("=" * 30)
    
    students = Student.objects.all()
    print(f"Total students: {students.count()}")
    
    for student in students:
        face_encodings = FaceEncoding.objects.filter(student=student)
        print(f"🎓 {student.full_name} ({student.student_id})")
        print(f"   Face encodings: {face_encodings.count()}")
        
        for encoding in face_encodings:
            if encoding.image:
                print(f"   📸 Image: {encoding.image.name}")
            else:
                print(f"   📸 No image file")

def test_deepface_service():
    """Test the DeepFace service"""
    print("\n🤖 DeepFace Service Test")
    print("=" * 30)
    
    try:
        from attendance.deepface_service import deepface_service
        
        print(f"Available: {deepface_service.available}")
        print(f"Model: {deepface_service.model_name}")
        print(f"Preloaded: {deepface_service.model_preloaded}")
        
        if deepface_service.available:
            # Test debug function
            deepface_service.debug_face_database()
            return True
        else:
            print("❌ DeepFace service not available")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("🔍 Face Recognition Debug")
    print("=" * 50)
    
    # Check face database
    db_ok = check_face_database()
    
    # Check students
    check_students()
    
    # Test service
    service_ok = test_deepface_service()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"Face Database: {'✅ OK' if db_ok else '❌ EMPTY'}")
    print(f"DeepFace Service: {'✅ OK' if service_ok else '❌ FAIL'}")
    
    if not db_ok:
        print("\n💡 Issue: No face images in database")
        print("Solution: Students need to enroll their faces first")
        print("1. Go to /enroll-face/ to register face")
        print("2. Make sure face enrollment completes successfully")
    
    if not service_ok:
        print("\n💡 Issue: DeepFace service not working")
        print("Solution: Check DeepFace installation and model")

if __name__ == "__main__":
    main()
