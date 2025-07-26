"""
Simple face detection service as fallback when DeepFace is not available
Uses OpenCV's built-in Haar cascades for basic face detection
"""

import os
import json
import base64
import numpy as np
from PIL import Image
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

# Try to import OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV not available. Face detection will be limited.")


class SimpleFaceService:
    """Simple face detection service using OpenCV Haar cascades"""
    
    def __init__(self):
        self.available = OPENCV_AVAILABLE
        if self.available:
            # Load Haar cascade for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            self.threshold = 0.8  # Simplified threshold
    
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
        Detect faces in an image using OpenCV
        Returns: List of face regions
        """
        if not self.available:
            return []
            
        try:
            # Convert PIL image to OpenCV format
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            return faces
        except Exception as e:
            logger.error(f"Error detecting faces: {str(e)}")
            return []
    
    def generate_face_encoding(self, image):
        """
        Generate a simple face "encoding" using basic image features
        This is not as sophisticated as DeepFace but works as a fallback
        """
        try:
            # Convert to grayscale and resize to standard size
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Detect face region
            faces = self.detect_faces(image)
            if len(faces) == 0:
                raise ValueError("No face detected in image")
            
            # Use the largest face
            (x, y, w, h) = max(faces, key=lambda face: face[2] * face[3])
            face_region = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_resized = cv2.resize(face_region, (64, 64))
            
            # Create simple feature vector (histogram + basic features)
            hist = cv2.calcHist([face_resized], [0], None, [256], [0, 256])
            
            # Add some basic statistical features
            mean_val = np.mean(face_resized)
            std_val = np.std(face_resized)
            
            # Combine features into a simple encoding
            encoding = np.concatenate([
                hist.flatten()[:128],  # First 128 histogram bins
                [mean_val, std_val]    # Basic statistics
            ])
            
            return encoding
            
        except Exception as e:
            logger.error(f"Error generating simple face encoding: {str(e)}")
            raise ValueError("Could not generate face encoding")
    
    def compare_faces(self, encoding1, encoding2):
        """
        Compare two face encodings using simple distance
        """
        try:
            if isinstance(encoding1, str):
                encoding1 = np.array(json.loads(encoding1))
            if isinstance(encoding2, str):
                encoding2 = np.array(json.loads(encoding2))
            
            # Calculate Euclidean distance
            distance = np.linalg.norm(encoding1 - encoding2)
            
            return distance
        except Exception as e:
            logger.error(f"Error comparing faces: {str(e)}")
            return float('inf')
    
    def validate_image_quality(self, image_data):
        """
        Validate image quality for face recognition
        """
        try:
            image = self.preprocess_image(image_data)
            
            # Check image size
            width, height = image.size
            if width < 100 or height < 100:
                return False, "Image too small (minimum 100x100 pixels)"
            
            # Detect faces
            faces = self.detect_faces(image)
            if len(faces) == 0:
                return False, "No face detected in image"
            
            if len(faces) > 1:
                return False, "Multiple faces detected. Please use image with single face"
            
            # Check face size
            (x, y, w, h) = faces[0]
            if w < 50 or h < 50:
                return False, "Face too small in image"
            
            return True, "Image quality is acceptable"
            
        except Exception as e:
            return False, f"Error validating image: {str(e)}"
    
    def enroll_student_face(self, student, image_data, is_primary=False):
        """
        Enroll a student's face using simple face detection
        """
        try:
            # Import here to avoid circular imports
            from .models import FaceEncoding
            
            # Preprocess the image
            image = self.preprocess_image(image_data)
            
            # Validate image
            is_valid, message = self.validate_image_quality(image_data)
            if not is_valid:
                raise ValueError(message)
            
            # Generate encoding
            encoding = self.generate_face_encoding(image)
            
            # Save image
            img_buffer = BytesIO()
            image.save(img_buffer, format='JPEG')
            img_content = ContentFile(img_buffer.getvalue())
            
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
    
    def recognize_student(self, image_data):
        """
        Simple student recognition using basic face matching
        """
        try:
            # Import here to avoid circular imports
            from .models import FaceEncoding
            
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
            
            # Simple threshold for matching (adjust as needed)
            threshold = 50.0  # This may need tuning
            
            if best_match and best_distance < threshold:
                confidence = max(0, 1 - (best_distance / threshold))
                return best_match, confidence
            else:
                return None, 0
                
        except Exception as e:
            logger.error(f"Error recognizing student: {str(e)}")
            return None, 0


# Global instance
simple_face_service = SimpleFaceService()
