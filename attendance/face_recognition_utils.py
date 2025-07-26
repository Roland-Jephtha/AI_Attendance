import os
import json
import base64
import numpy as np
from PIL import Image
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
import logging

# Try to import DeepFace, but make it optional for initial setup
try:
    import cv2
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("Warning: DeepFace not installed. Face recognition features will be disabled.")
    print("Install with: pip install deepface opencv-python")

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Service class for face recognition operations using DeepFace"""

    def __init__(self):
        self.available = DEEPFACE_AVAILABLE
        self.model_initialized = False
        if self.available:
            # Try different models in order of preference (lighter models first)
            self.model_options = ['OpenFace', 'Facenet', 'VGG-Face', 'DeepFace']
            self.detector_backend = 'opencv'  # opencv is most reliable
            self.distance_metric = 'cosine'
            self.threshold = getattr(settings, 'FACE_RECOGNITION_THRESHOLD', 0.6)
            self.model_name = None  # Will be set when model is successfully initialized
        else:
            self.model_name = None
            self.detector_backend = None
            self.distance_metric = None
            self.threshold = 0.6

    def initialize_model(self):
        """Initialize the face recognition model with fallback options"""
        if not self.available or self.model_initialized:
            return self.model_initialized

        for model_name in self.model_options:
            try:
                logger.info(f"Trying to initialize {model_name} model...")

                # Test the model with a small dummy image
                import numpy as np
                dummy_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

                # Try to generate an embedding (this will download the model if needed)
                embedding = DeepFace.represent(
                    img_path=dummy_image,
                    model_name=model_name,
                    detector_backend=self.detector_backend,
                    enforce_detection=False
                )

                if embedding:
                    self.model_name = model_name
                    self.model_initialized = True
                    logger.info(f"Successfully initialized {model_name} model")
                    return True

            except Exception as e:
                logger.warning(f"Failed to initialize {model_name}: {str(e)}")
                continue

        logger.error("Failed to initialize any face recognition model")
        return False
    
    def preprocess_image(self, image_data):
        """
        Preprocess image data from base64 or file
        Returns: PIL Image object
        """
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
    
    def detect_faces(self, image):
        """
        Detect faces in an image
        Returns: List of face regions
        """
        if not self.available:
            raise ValueError("DeepFace not available. Please install with: pip install deepface opencv-python")

        # Initialize model if not already done
        if not self.model_initialized:
            if not self.initialize_model():
                raise ValueError("Could not initialize face recognition model")

        try:
            # Convert PIL image to numpy array
            img_array = np.array(image)

            # Use DeepFace to detect faces with timeout handling
            import threading

            result = {'faces': None, 'error': None}

            def extract_faces():
                try:
                    faces = DeepFace.extract_faces(
                        img_path=img_array,
                        detector_backend=self.detector_backend,
                        enforce_detection=False
                    )
                    result['faces'] = faces
                except Exception as e:
                    result['error'] = e

            # Run face extraction in a separate thread with timeout
            thread = threading.Thread(target=extract_faces)
            thread.daemon = True
            thread.start()
            thread.join(timeout=15)  # 15 second timeout

            if thread.is_alive():
                logger.warning("Face detection timed out")
                return []

            if result['error']:
                logger.error(f"Error detecting faces: {str(result['error'])}")
                return []

            return result['faces'] or []

        except Exception as e:
            logger.error(f"Error detecting faces: {str(e)}")
            return []
    
    def generate_face_encoding(self, image):
        """
        Generate face encoding using DeepFace
        Returns: Face encoding as numpy array
        """
        if not self.available:
            raise ValueError("DeepFace not available. Please install with: pip install deepface opencv-python")

        # Initialize model if not already done
        if not self.model_initialized:
            if not self.initialize_model():
                raise ValueError("Could not initialize face recognition model. Please check your internet connection and try again.")

        try:
            # Convert PIL image to numpy array
            img_array = np.array(image)

            # Generate embedding with cross-platform timeout handling
            import threading
            import time

            result = {'embedding': None, 'error': None}

            def generate_embedding():
                try:
                    embedding = DeepFace.represent(
                        img_path=img_array,
                        model_name=self.model_name,
                        detector_backend=self.detector_backend,
                        enforce_detection=False
                    )
                    result['embedding'] = embedding
                except Exception as e:
                    result['error'] = e

            # Run embedding generation in a separate thread with timeout
            thread = threading.Thread(target=generate_embedding)
            thread.daemon = True
            thread.start()
            thread.join(timeout=30)  # 30 second timeout

            if thread.is_alive():
                # Thread is still running, meaning it timed out
                raise TimeoutError("Face encoding generation timed out")

            if result['error']:
                raise result['error']

            if result['embedding']:
                return np.array(result['embedding'][0]['embedding'])
            else:
                raise ValueError("No face detected in image")

        except TimeoutError:
            logger.error("Face encoding generation timed out")
            raise ValueError("Face recognition timed out. Please try again with a clearer image.")
        except Exception as e:
            logger.error(f"Error generating face encoding: {str(e)}")
            if "download" in str(e).lower() or "timeout" in str(e).lower():
                raise ValueError("Model download failed. Please check your internet connection or try again later.")
            raise ValueError("Could not generate face encoding")
    
    def compare_faces(self, encoding1, encoding2):
        """
        Compare two face encodings
        Returns: Distance between encodings
        """
        try:
            if isinstance(encoding1, str):
                encoding1 = np.array(json.loads(encoding1))
            if isinstance(encoding2, str):
                encoding2 = np.array(json.loads(encoding2))
            
            # Calculate cosine distance
            distance = np.linalg.norm(encoding1 - encoding2)
            
            return distance
        except Exception as e:
            logger.error(f"Error comparing faces: {str(e)}")
            return float('inf')
    
    def recognize_student(self, image_data):
        """
        Recognize a student from image data
        Returns: (student, confidence) or (None, 0)
        """
        try:
            # Preprocess the image
            image = self.preprocess_image(image_data)
            
            # Generate encoding for the input image
            input_encoding = self.generate_face_encoding(image)
            
            # Get all face encodings from database
            face_encodings = FaceEncoding.objects.select_related('student').all()
            
            best_match = None
            best_distance = float('inf')
            
            for face_encoding in face_encodings:
                try:
                    stored_encoding = json.loads(face_encoding.encoding_data)
                    distance = self.compare_faces(input_encoding, stored_encoding)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_match = face_encoding.student
                        
                except Exception as e:
                    logger.error(f"Error processing encoding for student {face_encoding.student.student_id}: {str(e)}")
                    continue
            
            # Check if the best match is within threshold
            if best_match and best_distance < self.threshold:
                confidence = max(0, 1 - (best_distance / self.threshold))
                return best_match, confidence
            else:
                return None, 0
                
        except Exception as e:
            logger.error(f"Error recognizing student: {str(e)}")
            return None, 0
    
    def enroll_student_face(self, student, image_data, is_primary=False):
        """
        Enroll a student's face for recognition
        Returns: FaceEncoding object or None
        """
        try:
            # Preprocess the image
            image = self.preprocess_image(image_data)
            
            # Detect faces
            faces = self.detect_faces(image)
            if not faces:
                raise ValueError("No face detected in image")
            
            # Generate encoding
            encoding = self.generate_face_encoding(image)
            
            # Save image
            img_buffer = BytesIO()
            image.save(img_buffer, format='JPEG')
            img_content = ContentFile(img_buffer.getvalue())
            
            # Import here to avoid circular imports
            from .models import FaceEncoding

            # Create FaceEncoding object
            face_encoding = FaceEncoding.objects.create(
                student=student,
                encoding_data=json.dumps(encoding.tolist()),
                is_primary=is_primary
            )
            
            # Save the image
            filename = f"{student.student_id}_{face_encoding.id}.jpg"
            face_encoding.image.save(filename, img_content)
            
            return face_encoding
            
        except Exception as e:
            logger.error(f"Error enrolling student face: {str(e)}")
            raise ValueError(f"Could not enroll face: {str(e)}")
    
    def validate_image_quality(self, image_data):
        """
        Validate image quality for face recognition
        Returns: (is_valid, message)
        """
        try:
            image = self.preprocess_image(image_data)
            
            # Check image size
            width, height = image.size
            if width < 100 or height < 100:
                return False, "Image too small (minimum 100x100 pixels)"
            
            # Detect faces
            faces = self.detect_faces(image)
            if not faces:
                return False, "No face detected in image"
            
            if len(faces) > 1:
                return False, "Multiple faces detected. Please use image with single face"
            
            return True, "Image quality is acceptable"
            
        except Exception as e:
            return False, f"Error validating image: {str(e)}"


# Global instance with fallback
face_recognition_service = FaceRecognitionService()

# Fallback service
def get_fallback_service():
    """Get fallback face service when DeepFace is not available"""
    try:
        from .simple_face_service import simple_face_service
        return simple_face_service
    except ImportError:
        return None
