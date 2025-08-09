"""
Simple DeepFace service using file-based approach
Following the recommended DeepFace workflow
"""

import os
import json
import base64
import logging
from io import BytesIO
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Try to import DeepFace and preload model
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    print("✅ DeepFace imported successfully")

    # Model options (from fastest to most accurate)
    AVAILABLE_MODELS = {
        'SFace': {'speed': 'fastest', 'accuracy': 'good', 'size': 'small'},
        'Facenet': {'speed': 'fast', 'accuracy': 'very good', 'size': 'medium'},
        'ArcFace': {'speed': 'medium', 'accuracy': 'excellent', 'size': 'medium'},
        'VGG-Face': {'speed': 'slow', 'accuracy': 'excellent', 'size': 'large'},
        'OpenFace': {'speed': 'medium', 'accuracy': 'good', 'size': 'small'},
    }

    # Try to preload models (start with faster ones)
    PRELOADED_MODELS = {}
    MODEL_PRELOADED = False

    # Try to preload the default model
    DEFAULT_MODEL = 'ArcFace'  # More accurate, still reasonably fast

    try:
        if DEFAULT_MODEL == 'VGG-Face':
            from deepface.basemodels import VGGFace
            PRELOADED_MODELS['VGG-Face'] = VGGFace.loadModel()
        elif DEFAULT_MODEL == 'Facenet':
            from deepface.basemodels import Facenet
            PRELOADED_MODELS['Facenet'] = Facenet.loadModel()
        elif DEFAULT_MODEL == 'ArcFace':
            from deepface.basemodels import ArcFace
            PRELOADED_MODELS['ArcFace'] = ArcFace.loadModel()
        elif DEFAULT_MODEL == 'OpenFace':
            from deepface.basemodels import OpenFace
            PRELOADED_MODELS['OpenFace'] = OpenFace.loadModel()
        # SFace doesn't have a separate basemodel import

        print(f"✅ {DEFAULT_MODEL} model preloaded successfully (43MB)")
        print("   Note: DeepFace.find() loads models internally, but preloading helps with startup")
        MODEL_PRELOADED = True
    except Exception as e:
        print(f"⚠️  Could not preload {DEFAULT_MODEL} model: {str(e)}")
        print("   Model will be loaded on demand when first used")
        MODEL_PRELOADED = False

except ImportError:
    DEEPFACE_AVAILABLE = False
    PRELOADED_MODELS = {}
    MODEL_PRELOADED = False
    AVAILABLE_MODELS = {}
    DEFAULT_MODEL = None
    print("❌ DeepFace not available")


class DeepFaceService:
    def force_clear_arcface_cache(self):
        """Delete ArcFace representations cache to fix mismatches"""
        cache_file = os.path.join(self.face_db_path, 'representations_arcface.pkl')
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"🗑️  Deleted ArcFace cache: {cache_file}")
        else:
            print(f"ℹ️  ArcFace cache not found: {cache_file}")
    """Simple DeepFace service using file-based approach"""
    
    def __init__(self):
        self.available = DEEPFACE_AVAILABLE
        self.model_preloaded = MODEL_PRELOADED
        self.preloaded_models = PRELOADED_MODELS
        self.face_db_path = os.path.join(settings.MEDIA_ROOT, 'face_db')
        self.debug_mode = False  # Disable debug mode for real recognition

        # Create face database directory
        os.makedirs(self.face_db_path, exist_ok=True)

        # Ensure weights directory exists and is persistent
        self.ensure_weights_directory()

        if self.available:
            # Use ArcFace - more accurate than OpenFace, still fast
            self.model_name = 'ArcFace'
            print(f"✅ DeepFace service initialized with {self.model_name} (medium size, high accuracy)")
            if self.model_preloaded:
                print("✅ Using preloaded model for better performance")
            else:
                print("⚠️  Model will be loaded on demand")
        else:
            print("❌ DeepFace service not available")

    def ensure_weights_directory(self):
        """Ensure DeepFace weights directory exists and is persistent"""
        import os
        from pathlib import Path

        # DeepFace weights directory
        weights_dir = Path.home() / '.deepface' / 'weights'
        weights_dir.mkdir(parents=True, exist_ok=True)

        print(f"✅ DeepFace weights directory: {weights_dir}")


        # Check for ArcFace weights (43MB)
        arcface_weights = weights_dir / 'arcface_weights.h5'
        if arcface_weights.exists():
            size_mb = arcface_weights.stat().st_size / (1024 * 1024)
            print(f"✅ ArcFace weights found: {arcface_weights} ({size_mb:.1f} MB)")
        else:
            print(f"⚠️  ArcFace weights not found, will download on first use (43MB)")

        # Also check for other models
        other_models = {
            'vgg_face_weights.h5': 'VGG-Face (553MB)',
            'facenet_weights.h5': 'Facenet (92MB)',
            'openface_weights.h5': 'OpenFace (17MB)',
        }

        for filename, description in other_models.items():
            weight_file = weights_dir / filename
            if weight_file.exists():
                size_mb = weight_file.stat().st_size / (1024 * 1024)
                print(f"✅ {description}: Available ({size_mb:.1f} MB)")
            else:
                print(f"⚠️  {description}: Not downloaded")

        return weights_dir
    
    def preprocess_image(self, image_data):
        """Convert base64 image data to PIL Image"""
        try:
            if isinstance(image_data, str):
                # Handle base64 encoded image
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
            else:
                # Handle file upload
                image = Image.open(image_data)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise ValueError("Invalid image data")
    
    def enroll_student_face(self, student, image_data, is_primary=False):
        """
        Enroll student face using DeepFace file-based approach
        Reject blurry images at enrollment.
        """
        try:
            # Import here to avoid circular imports
            from .models import FaceEncoding

            print(f"🎯 Enrolling face for student: {student.student_id}")

            # Preprocess image
            image = self.preprocess_image(image_data)
            print("✅ Image preprocessed successfully")

            # Check for blurry image (simple variance of Laplacian)
            try:
                import numpy as np
                import cv2
                img_np = np.array(image)
                img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                laplacian_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
                print(f"🔍 Image blur (variance of Laplacian): {laplacian_var:.2f}")
                if laplacian_var < 30:
                    reason = "Image is too blurry for enrollment. Please use a clearer photo."
                    print(f"❌ Enrollment rejected: {reason}")
                    raise ValueError(reason)
            except Exception as e:
                print(f"⚠️  Could not compute blur: {e}")

            # Create student directory in face_db
            student_face_dir = os.path.join(self.face_db_path, student.student_id)
            os.makedirs(student_face_dir, exist_ok=True)
            print(f"✅ Created directory: {student_face_dir}")

            # Save image to buffer
            img_buffer = BytesIO()
            image.save(img_buffer, format='JPEG')
            img_content = ContentFile(img_buffer.getvalue())

            # Create FaceEncoding record
            face_encoding = FaceEncoding.objects.create(
                student=student,
                encoding_data="file_based",  # We use file-based approach
                is_primary=is_primary
            )
            print(f"✅ Created FaceEncoding record: {face_encoding.id}")

            # Save image to Django media
            filename = f"{student.student_id}_{face_encoding.id}.jpg"
            face_encoding.image.save(filename, img_content)
            print(f"✅ Saved to Django media: {filename}")

            # Save image to face_db directory for DeepFace
            face_db_filename = f"face_{face_encoding.id}.jpg"
            face_db_filepath = os.path.join(student_face_dir, face_db_filename)

            # Reset buffer position
            img_buffer.seek(0)
            with open(face_db_filepath, 'wb') as f:
                f.write(img_buffer.getvalue())

            print(f"✅ Saved to face_db: {face_db_filepath}")

            # Do NOT call DeepFace.analyze with actions like 'age', 'gender', 'emotion', or 'race'.
            # This prevents DeepFace from downloading unnecessary models. Only face recognition is used.
            # If you want to test the image, use DeepFace.find or DeepFace.verify with the OpenFace model only.
            # print(f"✅ Skipping DeepFace.analyze to avoid extra model downloads")

            return face_encoding

        except Exception as e:
            logger.error(f"Error enrolling student face: {str(e)}")
            print(f"❌ Error enrolling face: {str(e)}")
            raise ValueError(f"Could not enroll face: {str(e)}")
    
    def clear_representations_cache(self):
        """Clear the cached representations file to force regeneration"""
        try:
            cache_files = [
                'representations_openface.pkl',
                'representations_vgg-face.pkl',
                'representations_facenet.pkl',
                'representations_arcface.pkl'
            ]

            for cache_file in cache_files:
                cache_path = os.path.join(self.face_db_path, cache_file)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    print(f"🗑️  Removed cache file: {cache_file}")

        except Exception as e:
            print(f"⚠️  Error clearing cache: {str(e)}")

    def debug_face_database(self):
        """Debug function to check what's in the face database"""
        print("🔍 Debugging face database...")
        print(f"   Face DB path: {self.face_db_path}")

        if not os.path.exists(self.face_db_path):
            print("❌ Face database directory doesn't exist")
            return

        # Check for cache files
        cache_files = [f for f in os.listdir(self.face_db_path) if f.endswith('.pkl')]
        if cache_files:
            print(f"📦 Found cache files: {cache_files}")
            print("   Note: Delete these if you added new faces and recognition isn't working")

        # List all student directories
        student_dirs = [d for d in os.listdir(self.face_db_path)
                       if os.path.isdir(os.path.join(self.face_db_path, d))]

        print(f"📁 Found {len(student_dirs)} student directories:")

        for student_dir in student_dirs:
            student_path = os.path.join(self.face_db_path, student_dir)
            face_files = [f for f in os.listdir(student_path)
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"   📂 {student_dir}: {len(face_files)} face images")
            for face_file in face_files:
                face_path = os.path.join(student_path, face_file)
                size_kb = os.path.getsize(face_path) / 1024
                print(f"      📄 {face_file} ({size_kb:.1f} KB)")

    def recognize_student(self, image_data):
        """
        Recognize student using DeepFace.find()
        """
        if not self.available:
            print("❌ DeepFace not available for recognition")
            return None, 0

        try:
            print("🔍 Starting face recognition...")

            # Debug the face database first
            self.debug_face_database()

            # DEBUG MODE: For testing, always return the first student if available
            if self.debug_mode:
                print("🐛 DEBUG MODE: Checking for any available student...")
                from .models import Student

                # Get first student from face database
                if os.path.exists(self.face_db_path):
                    student_dirs = [d for d in os.listdir(self.face_db_path)
                                   if os.path.isdir(os.path.join(self.face_db_path, d))]

                    if student_dirs:
                        student_id = student_dirs[0]
                        try:
                            student = Student.objects.get(student_id=student_id)
                            print(f"🐛 DEBUG: Returning student {student.full_name} (confidence: 0.85)")
                            return student, 0.85
                        except Student.DoesNotExist:
                            print(f"🐛 DEBUG: Student {student_id} not found in database")

                print("🐛 DEBUG: No students available, proceeding with normal recognition...")

            # Preprocess image
            image = self.preprocess_image(image_data)


            # Save temporary image for recognition with robust diagnostics
            import getpass
            import platform
            import stat
            import traceback

            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_image_path = os.path.join(temp_dir, 'recognition_temp.jpg')

            print(f"🛠️ Diagnostics before saving temp image:")
            print(f"   Current user: {getpass.getuser()}")
            print(f"   Platform: {platform.platform()}")
            print(f"   Working directory: {os.getcwd()}")
            print(f"   Temp dir: {temp_dir}")
            print(f"   Temp image path: {temp_image_path}")
            print(f"   Temp dir exists: {os.path.exists(temp_dir)}")
            if os.path.exists(temp_dir):
                try:
                    perms = oct(os.stat(temp_dir).st_mode)[-3:]
                    print(f"   Temp dir permissions: {perms}")
                except Exception as e:
                    print(f"   Could not get temp dir permissions: {e}")

            # Try saving the image and catch any errors
            try:
                image.save(temp_image_path, 'JPEG')
                print(f"✅ Saved temp image: {temp_image_path}")
            except Exception as e:
                print(f"❌ Exception while saving temp image: {e}")
                print(traceback.format_exc())
                logger.error(f"Exception while saving temp image: {e}")
                return None, 0

            # Check if file exists after save
            if not os.path.exists(temp_image_path):
                logger.error(f"Recognition error: Temp image {temp_image_path} does not exist after save!")
                print(f"❌ Recognition error: Temp image {temp_image_path} does not exist after save!")
                # List files in temp dir for debugging
                try:
                    print(f"   Files in temp dir: {os.listdir(temp_dir)}")
                except Exception as e:
                    print(f"   Could not list files in temp dir: {e}")
                return None, 0

            # Use DeepFace.find to search in face database
            print(f"🔍 Searching in face database: {self.face_db_path}")

            # DeepFace.find() doesn't accept 'model' parameter, it loads the model internally
            # But having preloaded models still helps with overall performance
            if self.model_preloaded:
                print(f"✅ Using {self.model_name} model for recognition (preloaded for faster startup)")
            else:
                print(f"⚠️  Loading {self.model_name} model on demand")

            results = DeepFace.find(
                img_path=temp_image_path,
                db_path=self.face_db_path,
                model_name=self.model_name,
                enforce_detection=False
            )
            print(f"✅ DeepFace.find completed, results: {len(results)} dataframes")
            # Process results with better debugging
            print(f"📊 Results analysis:")
            print(f"   Number of result dataframes: {len(results)}")

            if len(results) > 0:
                df = results[0]
                print(f"   Dataframe shape: {df.shape}")
                print(f"   Dataframe empty: {df.empty}")

                if not df.empty:
                    print(f"   Columns: {list(df.columns)}")
                    print(f"   Number of matches: {len(df)}")

                    # Determine the distance column name based on model
                    distance_col = f"{self.model_name}_cosine"
                    if distance_col not in df.columns:
                        # Fallback to common distance column names
                        possible_cols = ['distance', 'OpenFace_cosine', 'VGG-Face_cosine', 'Facenet_cosine', 'ArcFace_cosine']
                        distance_col = None
                        for col in possible_cols:
                            if col in df.columns:
                                distance_col = col
                                break

                        if distance_col is None:
                            print(f"❌ No distance column found in: {list(df.columns)}")
                            return None, 0

                    print(f"📏 Using distance column: {distance_col}")

                    # Show all matches for debugging
                    for i, row in df.iterrows():
                        identity_path = row['identity']
                        distance = row[distance_col]
                        print(f"   Match {i+1}: {identity_path} (distance: {distance:.4f})")

                    # Get the best match (lowest distance)
                    best_match = df.iloc[0]
                    identity_path = best_match['identity']
                    distance = best_match[distance_col]

                    print(f"✅ Best match selected: {identity_path}, distance: {distance:.4f}")

                    # For ArcFace, use the recommended threshold
                    threshold = 0.6  # ArcFace threshold for balanced precision/recall

                    print(f"🎯 Using ArcFace threshold: {threshold}")
                    print(f"🔍 Distance check: {distance:.4f} <= {threshold} = {distance <= threshold}")

                    if distance <= threshold:
                        # Extract student ID from path
                        # Path format: face_db/STUDENT_ID/face_X.jpg
                        path_parts = identity_path.replace('\\', '/').split('/')
                        if len(path_parts) >= 2:
                            student_id = path_parts[-2]  # Get student ID from directory name

                            print(f"🔍 Extracted student ID: {student_id}")
                            print(f"🔍 Match distance: {distance:.4f}")

                            # Find student
                            from .models import Student
                            try:
                                student = Student.objects.get(student_id=student_id)
                                confidence = max(0, 1 - (distance / threshold))  # Convert distance to confidence
                                print(f"✅ Recognized student: {student.full_name} (confidence: {confidence:.2f})")
                                return student, confidence
                            except Student.DoesNotExist:
                                print(f"❌ Student {student_id} not found in database")
                                return None, 0
                        else:
                            print(f"❌ Could not extract student ID from path: {identity_path}")
                            return None, 0
                    else:
                        print(f"❌ Distance {distance:.4f} exceeds strict threshold {threshold}")
                        return None, 0
                else:
                    print("❌ Results dataframe is empty")
                    print("🔄 This might be due to cached representations. Clearing cache and retrying...")

                    # Check for possible reasons before retrying
                    # 1. Check image size
                    width, height = image.size
                    if width < 100 or height < 100:
                        reason = f"Image too small ({width}x{height}). Minimum size is 100x100 pixels."
                        print(f"❌ Not recognized: {reason}")
                        return None, reason

                    # 2. Check for blurry image (simple variance of Laplacian)
                    try:
                        import numpy as np
                        import cv2
                        img_np = np.array(image)
                        img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                        laplacian_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
                        print(f"🔍 Image blur (variance of Laplacian): {laplacian_var:.2f}")
                        if laplacian_var < 30:
                            reason = "Image is too blurry for recognition. Please use a clearer photo."
                            print(f"❌ Not recognized: {reason}")
                            return None, reason
                    except Exception as e:
                        print(f"⚠️  Could not compute blur: {e}")

                    # 3. Check if DeepFace detected any faces at all
                    try:
                        faces = DeepFace.extract_faces(img_path=temp_image_path, detector_backend='opencv', enforce_detection=False)
                        if not faces or len(faces) == 0:
                            reason = "No face detected in the image. Please ensure your face is clearly visible."
                            print(f"❌ Not recognized: {reason}")
                            return None, reason
                    except Exception as e:
                        print(f"⚠️  Could not check for faces: {e}")

                    # Clear cache and try once more
                    self.clear_representations_cache()

                    print("🔄 Retrying recognition after clearing cache...")
                    results_retry = DeepFace.find(
                        img_path=temp_image_path,
                        db_path=self.face_db_path,
                        model_name=self.model_name,
                        enforce_detection=False
                    )

                    # Clean up temp file after retry
                    try:
                        os.remove(temp_image_path)
                    except Exception as e:
                        print(f"⚠️  Could not remove temp image after retry: {e}")

                    if len(results_retry) > 0 and not results_retry[0].empty:
                        print("✅ Retry successful! Processing results...")
                        df_retry = results_retry[0]

                        # Process retry results
                        # Use the same distance column logic
                        retry_distance_col = f"{self.model_name}_cosine"
                        if retry_distance_col not in df_retry.columns:
                            possible_cols = ['distance', 'OpenFace_cosine', 'VGG-Face_cosine', 'Facenet_cosine', 'ArcFace_cosine']
                            retry_distance_col = None
                            for col in possible_cols:
                                if col in df_retry.columns:
                                    retry_distance_col = col
                                    break

                        if retry_distance_col is None:
                            print(f"❌ No distance column found in retry results")
                            return None, "No distance column found in retry results."

                        best_match = df_retry.iloc[0]
                        identity_path = best_match['identity']
                        distance = best_match[retry_distance_col]

                        print(f"✅ Retry match: {identity_path}, distance: {distance:.4f}")

                        threshold = 0.6  # ArcFace threshold for balanced precision/recall
                        if distance <= threshold:
                            path_parts = identity_path.replace('\\', '/').split('/')
                            if len(path_parts) >= 2:
                                student_id = path_parts[-2]

                                from .models import Student
                                try:
                                    student = Student.objects.get(student_id=student_id)
                                    confidence = max(0, 1 - (distance / threshold))

                                    print(f"✅ Recognized student after retry: {student.full_name} (confidence: {confidence:.2f})")
                                    return student, confidence
                                except Student.DoesNotExist:
                                    print(f"❌ Student {student_id} not found in database")
                                    return None, "Student not found in database."
                            else:
                                print(f"❌ Could not extract student ID from path: {identity_path}")
                                return None, "Could not extract student ID from path."
                        else:
                            print(f"❌ Retry distance {distance:.4f} exceeds threshold {threshold}")
                            return None, f"Face found, but not close enough to any student (distance {distance:.4f} > {threshold})."
                    else:
                        print("❌ Retry also returned empty results")
                        return None, "No matching student found. Possible reasons: blurry image, no face detected, or not enrolled."
            else:
                print("❌ No result dataframes returned")
                # Clean up temp file if it still exists
                try:
                    os.remove(temp_image_path)
                except Exception as e:
                    print(f"⚠️  Could not remove temp image: {e}")
                return None, 0
                
        except Exception as e:
            logger.error(f"Error recognizing student: {str(e)}")
            print(f"❌ Recognition error: {str(e)}")
            # Clean up temp file if it still exists
            try:
                os.remove(temp_image_path)
            except Exception as ex:
                print(f"⚠️  Could not remove temp image after exception: {ex}")
            return None, 0
    
    def validate_image_quality(self, image_data):
        """Basic image validation"""
        try:
            image = self.preprocess_image(image_data)
            
            # Check image size
            width, height = image.size
            if width < 100 or height < 100:
                return False, "Image too small (minimum 100x100 pixels)"
            
            return True, "Image quality is acceptable"
            
        except Exception as e:
            return False, f"Error validating image: {str(e)}"


# Global instance
deepface_service = DeepFaceService()

