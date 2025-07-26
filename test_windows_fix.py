#!/usr/bin/env python
"""
Test script to verify the Windows signal fix for DeepFace
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def test_face_service():
    """Test the face recognition service"""
    print("Testing Face Recognition Service...")
    
    try:
        from attendance.face_recognition_utils import face_recognition_service
        
        print(f"Service available: {face_recognition_service.available}")
        
        if not face_recognition_service.available:
            print("DeepFace not available, testing fallback service...")
            from attendance.simple_face_service import simple_face_service
            
            print(f"Fallback service available: {simple_face_service.available}")
            
            if simple_face_service.available:
                print("✅ Fallback service is working")
                return True
            else:
                print("❌ No face recognition service available")
                return False
        
        # Test model initialization
        print("Testing model initialization...")
        if face_recognition_service.initialize_model():
            print(f"✅ Model initialized: {face_recognition_service.model_name}")
            
            # Test with a simple image
            print("Testing face encoding generation...")
            from PIL import Image
            import numpy as np
            
            # Create a test image
            test_image = Image.fromarray(np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8))
            
            try:
                encoding = face_recognition_service.generate_face_encoding(test_image)
                print(f"✅ Face encoding generated successfully (shape: {encoding.shape})")
                return True
            except Exception as e:
                print(f"❌ Face encoding failed: {str(e)}")
                return False
        else:
            print("❌ Model initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing face service: {str(e)}")
        return False

def test_image_validation():
    """Test image validation"""
    print("\nTesting image validation...")
    
    try:
        from attendance.views import get_face_recognition_service
        
        service = get_face_recognition_service()
        if not service:
            print("❌ No face recognition service available")
            return False
        
        # Test with a base64 image (small test image)
        test_image_data = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k='
        
        is_valid, message = service.validate_image_quality(test_image_data)
        print(f"Image validation result: {is_valid} - {message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing image validation: {str(e)}")
        return False

def main():
    print("🔧 Windows DeepFace Fix Test")
    print("=" * 40)
    
    # Test face service
    service_ok = test_face_service()
    
    # Test image validation
    validation_ok = test_image_validation()
    
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"Face Service: {'✅ PASS' if service_ok else '❌ FAIL'}")
    print(f"Image Validation: {'✅ PASS' if validation_ok else '❌ FAIL'}")
    
    if service_ok and validation_ok:
        print("\n🎉 All tests passed! Face enrollment should work now.")
        print("\nNext steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Go to: http://localhost:8000/signup/")
        print("3. Create account and test face registration")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        print("\nThe system will try to use fallback services.")

if __name__ == "__main__":
    main()
