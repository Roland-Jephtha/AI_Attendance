#!/usr/bin/env python
"""
Clear DeepFace representations cache
Run this when face recognition isn't working properly
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def clear_face_cache():
    """Clear all DeepFace cache files"""
    from django.conf import settings
    
    face_db_path = os.path.join(settings.MEDIA_ROOT, 'face_db')
    
    print("🗑️  Clearing DeepFace cache files...")
    print(f"Face DB path: {face_db_path}")
    
    if not os.path.exists(face_db_path):
        print("❌ Face database directory doesn't exist")
        return
    
    # Cache files to remove
    cache_files = [
        'representations_openface.pkl',
        'representations_vgg-face.pkl', 
        'representations_facenet.pkl',
        'representations_arcface.pkl',
        'representations_deepface.pkl'
    ]
    
    removed_count = 0
    
    for cache_file in cache_files:
        cache_path = os.path.join(face_db_path, cache_file)
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                size_kb = 0  # Can't get size after removal
                print(f"✅ Removed: {cache_file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {cache_file}: {str(e)}")
        else:
            print(f"⚠️  Not found: {cache_file}")
    
    print(f"\n📊 Summary: Removed {removed_count} cache files")
    
    if removed_count > 0:
        print("\n🎉 Cache cleared successfully!")
        print("Next face recognition will regenerate the cache with current faces.")
    else:
        print("\n💡 No cache files found to remove.")
    
    # Show current face database status
    print(f"\n📁 Current face database contents:")
    
    try:
        student_dirs = [d for d in os.listdir(face_db_path) 
                       if os.path.isdir(os.path.join(face_db_path, d))]
        
        print(f"Found {len(student_dirs)} student directories:")
        
        for student_dir in student_dirs:
            student_path = os.path.join(face_db_path, student_dir)
            face_files = [f for f in os.listdir(student_path) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"   📂 {student_dir}: {len(face_files)} face images")
            
    except Exception as e:
        print(f"Error reading face database: {str(e)}")

def main():
    print("🧹 DeepFace Cache Cleaner")
    print("=" * 30)
    
    clear_face_cache()
    
    print("\n" + "=" * 30)
    print("💡 What this does:")
    print("- Removes cached face representations")
    print("- Forces DeepFace to regenerate cache on next recognition")
    print("- Helps when new faces aren't being recognized")
    
    print("\n🚀 Next steps:")
    print("1. Try face recognition again")
    print("2. DeepFace will rebuild the cache automatically")
    print("3. Recognition should work with updated faces")

if __name__ == "__main__":
    main()
