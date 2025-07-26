#!/usr/bin/env python
"""
Simple test to verify DeepFace works with the threading approach
"""

import numpy as np
import threading
import time

def test_deepface_basic():
    """Test basic DeepFace functionality"""
    try:
        from deepface import DeepFace
        print("✅ DeepFace imported successfully")
        
        # Create a test image
        test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        print("✅ Test image created")
        
        # Test with threading (like our fix)
        result = {'embedding': None, 'error': None}
        
        def generate_embedding():
            try:
                print("🔄 Generating embedding...")
                embedding = DeepFace.represent(
                    img_path=test_image,
                    model_name='OpenFace',  # Use the model we downloaded
                    detector_backend='opencv',
                    enforce_detection=False
                )
                result['embedding'] = embedding
                print("✅ Embedding generated successfully")
            except Exception as e:
                result['error'] = e
                print(f"❌ Error generating embedding: {str(e)}")
        
        # Run in thread with timeout
        print("🚀 Starting embedding generation thread...")
        thread = threading.Thread(target=generate_embedding)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)  # 30 second timeout
        
        if thread.is_alive():
            print("❌ Thread timed out")
            return False
        
        if result['error']:
            print(f"❌ Error: {result['error']}")
            return False
        
        if result['embedding']:
            embedding_array = np.array(result['embedding'][0]['embedding'])
            print(f"✅ Success! Embedding shape: {embedding_array.shape}")
            return True
        else:
            print("❌ No embedding generated")
            return False
            
    except ImportError:
        print("❌ DeepFace not installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    print("🧪 Simple DeepFace Test")
    print("=" * 30)
    
    if test_deepface_basic():
        print("\n🎉 DeepFace is working correctly!")
        print("The face enrollment should work now.")
    else:
        print("\n⚠️  DeepFace test failed.")
        print("The system will use fallback face detection.")
    
    print("\n" + "=" * 30)

if __name__ == "__main__":
    main()
