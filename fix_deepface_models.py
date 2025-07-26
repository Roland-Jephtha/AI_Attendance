#!/usr/bin/env python
"""
Script to fix DeepFace model download issues
This script will download the required models manually if automatic download fails
"""

import os
import sys
import requests
from pathlib import Path
import time

def download_file(url, filepath, timeout=60):
    """Download a file with progress indication"""
    try:
        print(f"Downloading {filepath.name}...")
        
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n✅ Successfully downloaded {filepath.name}")
        return True
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout downloading {filepath.name}")
        return False
    except Exception as e:
        print(f"\n❌ Error downloading {filepath.name}: {str(e)}")
        return False

def setup_deepface_models():
    """Set up DeepFace models manually"""
    print("Setting up DeepFace models...")
    
    # Get the home directory for DeepFace models
    home_dir = Path.home()
    deepface_dir = home_dir / '.deepface' / 'weights'
    deepface_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"DeepFace models directory: {deepface_dir}")
    
    # Model files with their download URLs
    models = {
        'vgg_face_weights.h5': {
            'url': 'https://github.com/serengil/deepface_models/releases/download/v1.0/vgg_face_weights.h5',
            'size': '553MB'
        },
        'facenet_weights.h5': {
            'url': 'https://github.com/serengil/deepface_models/releases/download/v1.0/facenet_weights.h5',
            'size': '92MB'
        },
        'openface_weights.h5': {
            'url': 'https://github.com/serengil/deepface_models/releases/download/v1.0/openface_weights.h5',
            'size': '17MB'
        },
        'deepface_weights.h5': {
            'url': 'https://github.com/serengil/deepface_models/releases/download/v1.0/deepface_weights.h5',
            'size': '553MB'
        }
    }
    
    downloaded_any = False
    
    for filename, info in models.items():
        file_path = deepface_dir / filename
        
        if file_path.exists():
            print(f"✅ {filename} already exists ({info['size']})")
            continue
        
        print(f"\n📥 Downloading {filename} ({info['size']})...")
        
        if download_file(info['url'], file_path):
            downloaded_any = True
        else:
            print(f"⚠️  Failed to download {filename}")
    
    return downloaded_any

def test_deepface():
    """Test if DeepFace is working"""
    try:
        print("\n🧪 Testing DeepFace...")
        
        from deepface import DeepFace
        import numpy as np
        
        # Create a small test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Try different models in order of preference
        models_to_test = ['OpenFace', 'Facenet', 'VGG-Face']
        
        for model in models_to_test:
            try:
                print(f"Testing {model} model...")
                
                embedding = DeepFace.represent(
                    img_path=test_image,
                    model_name=model,
                    detector_backend='opencv',
                    enforce_detection=False
                )
                
                if embedding:
                    print(f"✅ {model} model is working!")
                    return True
                    
            except Exception as e:
                print(f"❌ {model} failed: {str(e)}")
                continue
        
        print("❌ No DeepFace models are working")
        return False
        
    except ImportError:
        print("❌ DeepFace not installed. Run: pip install deepface")
        return False
    except Exception as e:
        print(f"❌ Error testing DeepFace: {str(e)}")
        return False

def main():
    print("🔧 DeepFace Model Setup Tool")
    print("=" * 40)
    
    # Check if DeepFace is installed
    try:
        import deepface
        print("✅ DeepFace is installed")
    except ImportError:
        print("❌ DeepFace not installed")
        print("Please install it with: pip install deepface opencv-python tensorflow")
        return
    
    # Test if DeepFace is already working
    if test_deepface():
        print("\n🎉 DeepFace is already working! No action needed.")
        return
    
    print("\n⚠️  DeepFace models need to be downloaded...")
    
    # Ask user if they want to download
    response = input("\nDo you want to download the models now? (y/n): ").lower().strip()
    
    if response != 'y':
        print("Skipping model download.")
        print("\nAlternative solutions:")
        print("1. Use a different internet connection")
        print("2. Download models manually from: https://github.com/serengil/deepface_models/releases")
        print("3. The system will fall back to simple face detection")
        return
    
    # Download models
    if setup_deepface_models():
        print("\n🔄 Testing DeepFace after download...")
        if test_deepface():
            print("\n🎉 Success! DeepFace is now working.")
            print("You can now use face recognition in the attendance system.")
        else:
            print("\n⚠️  Models downloaded but DeepFace still not working.")
            print("The system will use simple face detection as fallback.")
    else:
        print("\n❌ Failed to download models.")
        print("The system will use simple face detection as fallback.")
    
    print("\n" + "=" * 40)
    print("Setup complete!")

if __name__ == "__main__":
    main()
