#!/usr/bin/env python
"""
Test OpenFace model setup and functionality
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def check_weights_file():
    """Check if OpenFace weights file exists"""
    print("🔍 Checking OpenFace weights file...")
    
    weights_dir = Path.home() / '.deepface' / 'weights'
    openface_weights = weights_dir / 'openface_weights.h5'
    
    if openface_weights.exists():
        size_mb = openface_weights.stat().st_size / (1024 * 1024)
        print(f"✅ OpenFace weights found: {openface_weights}")
        print(f"   File size: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ OpenFace weights not found at: {openface_weights}")
        print("   Run: python fix_deepface_models.py to download")
        return False

def test_openface_import():
    """Test OpenFace model import and loading"""
    print("\n🧪 Testing OpenFace model import...")
    
    try:
        from deepface import DeepFace
        from deepface.basemodels import OpenFace
        print("✅ DeepFace and OpenFace imported successfully")
        
        # Try to load the model
        print("🔄 Loading OpenFace model...")
        model = OpenFace.loadModel()
        print("✅ OpenFace model loaded successfully!")
        print(f"   Model type: {type(model)}")
        
        return True, model
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ Model loading error: {str(e)}")
        return False, None

def test_deepface_service():
    """Test the DeepFace service with OpenFace"""
    print("\n🧪 Testing DeepFace service...")
    
    try:
        from attendance.deepface_service import deepface_service
        
        print(f"Service available: {deepface_service.available}")
        print(f"Model name: {deepface_service.model_name}")
        print(f"Model preloaded: {deepface_service.model_preloaded}")
        print(f"Face DB path: {deepface_service.face_db_path}")
        
        if deepface_service.available and deepface_service.model_name == 'OpenFace':
            print("✅ DeepFace service configured for OpenFace")
            return True
        else:
            print("❌ DeepFace service not properly configured")
            return False
            
    except Exception as e:
        print(f"❌ Service test error: {str(e)}")
        return False

def test_basic_recognition():
    """Test basic face recognition functionality"""
    print("\n🧪 Testing basic recognition functionality...")
    
    try:
        from deepface import DeepFace
        import numpy as np
        
        # Create a test image
        test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        print("🔄 Testing DeepFace.represent with OpenFace...")
        
        # Test representation (encoding)
        embedding = DeepFace.represent(
            img_path=test_image,
            model_name='OpenFace',
            detector_backend='opencv',
            enforce_detection=False
        )
        
        if embedding:
            print(f"✅ Face representation successful!")
            print(f"   Embedding length: {len(embedding[0]['embedding'])}")
            return True
        else:
            print("❌ Face representation failed")
            return False
            
    except Exception as e:
        print(f"❌ Recognition test error: {str(e)}")
        return False

def main():
    print("🎯 OpenFace Model Test")
    print("=" * 40)
    
    # Test 1: Check weights file
    weights_ok = check_weights_file()
    
    # Test 2: Test model import and loading
    import_ok, model = test_openface_import()
    
    # Test 3: Test service configuration
    service_ok = test_deepface_service()
    
    # Test 4: Test basic recognition
    recognition_ok = test_basic_recognition()
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"Weights File: {'✅' if weights_ok else '❌'}")
    print(f"Model Import: {'✅' if import_ok else '❌'}")
    print(f"Service Config: {'✅' if service_ok else '❌'}")
    print(f"Basic Recognition: {'✅' if recognition_ok else '❌'}")
    
    if all([weights_ok, import_ok, service_ok, recognition_ok]):
        print("\n🎉 OpenFace is ready to use!")
        print("\n📋 Benefits of OpenFace:")
        print("✅ Lightweight: Only 17MB (vs 553MB for VGG-Face)")
        print("✅ Fast: Good performance for real-time recognition")
        print("✅ Persistent: Downloaded once, used forever")
        print("✅ Reliable: Good accuracy for most use cases")
        
        print("\n🚀 Next steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Test signup and face enrollment")
        print("3. Face recognition will use OpenFace model")
        
    else:
        print("\n⚠️  Some tests failed:")
        if not weights_ok:
            print("- Download OpenFace weights: python fix_deepface_models.py")
        if not import_ok:
            print("- Check DeepFace installation: pip install deepface")
        if not service_ok:
            print("- Check service configuration")
        if not recognition_ok:
            print("- Check DeepFace functionality")
    
    print("\n💡 OpenFace Model Info:")
    print("- Size: 17MB (very lightweight)")
    print("- Speed: Fast recognition")
    print("- Accuracy: Good for most applications")
    print("- Storage: ~/.deepface/weights/openface_weights.h5")

if __name__ == "__main__":
    main()
