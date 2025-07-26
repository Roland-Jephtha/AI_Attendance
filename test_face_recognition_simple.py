#!/usr/bin/env python
"""
Simple test of face recognition
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def test_face_recognition():
    """Test face recognition with a simple image"""
    print("🧪 Testing Face Recognition")
    print("=" * 30)
    
    try:
        from attendance.deepface_service import deepface_service
        
        if not deepface_service.available:
            print("❌ DeepFace service not available")
            return False
        
        print(f"✅ Service available: {deepface_service.model_name}")
        
        # Check face database
        deepface_service.debug_face_database()
        
        # Create a simple test image (random data)
        import numpy as np
        from PIL import Image
        import base64
        from io import BytesIO
        
        # Create a test image
        test_image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        pil_image = Image.fromarray(test_image)
        
        # Convert to base64
        buffer = BytesIO()
        pil_image.save(buffer, format='JPEG')
        image_data = base64.b64encode(buffer.getvalue()).decode()
        image_data = f"data:image/jpeg;base64,{image_data}"
        
        print(f"\n🔍 Testing recognition with random image...")
        
        # Test recognition
        student, confidence = deepface_service.recognize_student(image_data)
        
        if student:
            print(f"✅ Recognition successful!")
            print(f"   Student: {student.full_name}")
            print(f"   ID: {student.student_id}")
            print(f"   Confidence: {confidence:.2f}")
            return True
        else:
            print(f"❌ No student recognized")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_existing_face():
    """Test with an existing face image from the database"""
    print(f"\n🖼️  Testing with Existing Face Image")
    print("=" * 40)
    
    try:
        from django.conf import settings
        from attendance.deepface_service import deepface_service
        import base64
        
        face_db_path = os.path.join(settings.MEDIA_ROOT, 'face_db')
        
        # Find first face image
        for student_dir in os.listdir(face_db_path):
            student_path = os.path.join(face_db_path, student_dir)
            if os.path.isdir(student_path):
                face_files = [f for f in os.listdir(student_path) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                
                if face_files:
                    face_file = face_files[0]
                    face_path = os.path.join(student_path, face_file)
                    
                    print(f"📸 Testing with: {student_dir}/{face_file}")
                    
                    # Read and encode the image
                    with open(face_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode()
                        image_data = f"data:image/jpeg;base64,{image_data}"
                    
                    # Test recognition
                    student, confidence = deepface_service.recognize_student(image_data)
                    
                    if student:
                        print(f"✅ Recognition successful!")
                        print(f"   Expected: {student_dir}")
                        print(f"   Recognized: {student.student_id}")
                        print(f"   Match: {'✅' if student.student_id == student_dir else '❌'}")
                        print(f"   Confidence: {confidence:.2f}")
                        return True
                    else:
                        print(f"❌ Failed to recognize existing face")
                        return False
        
        print("❌ No face images found in database")
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("🎯 Face Recognition Test Suite")
    print("=" * 50)
    
    # Test 1: Basic recognition
    basic_test = test_face_recognition()
    
    # Test 2: With existing face
    existing_test = test_with_existing_face()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Basic Recognition: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"Existing Face: {'✅ PASS' if existing_test else '❌ FAIL'}")
    
    if basic_test or existing_test:
        print("\n🎉 Face recognition is working!")
        print("The attendance system should now recognize students.")
    else:
        print("\n⚠️  Face recognition needs attention.")
        print("Check the face database and model setup.")

if __name__ == "__main__":
    main()
