#!/usr/bin/env python
"""
Initialize DeepFace models and ensure persistent storage
Run this once to set up the face recognition system properly
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def ensure_weights_directory():
    """Ensure DeepFace weights directory exists and is persistent"""
    print("🔧 Setting up DeepFace weights directory...")
    
    weights_dir = Path.home() / '.deepface' / 'weights'
    weights_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Weights directory created: {weights_dir}")
    
    # Check existing weights
    weight_files = {
        'vgg_face_weights.h5': 'VGG-Face model weights',
        'facenet_weights.h5': 'Facenet model weights',
        'openface_weights.h5': 'OpenFace model weights',
    }
    
    for filename, description in weight_files.items():
        weight_file = weights_dir / filename
        if weight_file.exists():
            size_mb = weight_file.stat().st_size / (1024 * 1024)
            print(f"✅ {description}: {weight_file} ({size_mb:.1f} MB)")
        else:
            print(f"⚠️  {description}: Not found, will download on first use")
    
    return weights_dir

def test_deepface_import():
    """Test DeepFace import and basic functionality"""
    print("\n🧪 Testing DeepFace import...")
    
    try:
        from deepface import DeepFace
        from deepface.basemodels import VGGFace
        print("✅ DeepFace imported successfully")
        
        # Test model preloading
        print("🔄 Testing model preloading...")
        try:
            model = VGGFace.loadModel()
            print("✅ VGG-Face model preloaded successfully")
            return True
        except Exception as e:
            print(f"⚠️  Model preloading failed: {str(e)}")
            print("   This is normal on first run - model will download when needed")
            return False
            
    except ImportError as e:
        print(f"❌ DeepFace import failed: {str(e)}")
        print("   Please install DeepFace: pip install deepface")
        return False

def initialize_face_database():
    """Initialize face database directory structure"""
    print("\n📁 Setting up face database...")
    
    from django.conf import settings
    
    face_db_path = os.path.join(settings.MEDIA_ROOT, 'face_db')
    os.makedirs(face_db_path, exist_ok=True)
    
    print(f"✅ Face database directory: {face_db_path}")
    
    # Create temp directory for recognition
    temp_path = os.path.join(settings.MEDIA_ROOT, 'temp')
    os.makedirs(temp_path, exist_ok=True)
    
    print(f"✅ Temp directory: {temp_path}")
    
    return face_db_path

def test_deepface_service():
    """Test the DeepFace service"""
    print("\n🧪 Testing DeepFace service...")
    
    try:
        from attendance.deepface_service import deepface_service
        
        print(f"Service available: {deepface_service.available}")
        print(f"Model preloaded: {deepface_service.model_preloaded}")
        print(f"Face DB path: {deepface_service.face_db_path}")
        
        if deepface_service.available:
            print("✅ DeepFace service is ready")
            return True
        else:
            print("❌ DeepFace service not available")
            return False
            
    except Exception as e:
        print(f"❌ Error testing service: {str(e)}")
        return False

def main():
    print("🚀 DeepFace Initialization Script")
    print("=" * 50)
    
    # Step 1: Ensure weights directory
    weights_dir = ensure_weights_directory()
    
    # Step 2: Test DeepFace import
    import_success = test_deepface_import()
    
    # Step 3: Initialize face database
    face_db_path = initialize_face_database()
    
    # Step 4: Test service
    service_success = test_deepface_service()
    
    print("\n" + "=" * 50)
    print("📊 Initialization Summary:")
    print(f"Weights Directory: ✅ {weights_dir}")
    print(f"DeepFace Import: {'✅' if import_success else '❌'}")
    print(f"Face Database: ✅ {face_db_path}")
    print(f"Service Ready: {'✅' if service_success else '❌'}")
    
    if import_success and service_success:
        print("\n🎉 DeepFace is ready to use!")
        print("\n📋 Next steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Test signup and face enrollment")
        print("3. Models will be downloaded automatically on first use")
        
    else:
        print("\n⚠️  Some components need attention:")
        if not import_success:
            print("- Install DeepFace: pip install deepface opencv-python tensorflow")
        if not service_success:
            print("- Check Django configuration and imports")
    
    print("\n💡 Tips:")
    print("- Keep the ~/.deepface/weights/ directory for persistent storage")
    print("- Models are downloaded once and reused")
    print("- Preloaded models improve performance")

if __name__ == "__main__":
    main()
