# AI Attendance System

A facial recognition-based attendance system built with Django and DeepFace. Students can sign up, register their faces, and mark attendance using facial recognition.

## Features

- **Student Registration & Authentication**: Students can create accounts and log in
- **Face Registration**: Integrated face enrollment during signup process
- **Facial Recognition Attendance**: Students use their camera to mark attendance
- **Multi-Class Support**: Students can be enrolled in multiple classes
- **Real-time Recognition**: Live camera feed for attendance marking
- **Admin Dashboard**: Manage students, classes, and view attendance reports
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Backend**: Django 4.2.7
- **Face Recognition**: DeepFace with TensorFlow
- **Frontend**: Bootstrap 5, JavaScript (Camera API)
- **Database**: SQLite (default, can be changed to PostgreSQL/MySQL)
- **Computer Vision**: OpenCV, Pillow

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

4. **Quick Setup** (creates sample classes):
   ```bash
   python manage.py quick_setup
   ```

5. **Start Server**:
   ```bash
   python manage.py runserver
   ```

## Usage

### For Students

1. **Sign Up**: Visit `http://localhost:8000/signup/`
   - Fill in student details
   - Create password
   - Automatically redirected to face registration

2. **Face Registration**:
   - Allow camera access
   - Position face in center
   - Capture clear image
   - Complete registration

3. **Mark Attendance**:
   - Log in to student dashboard
   - Select a class
   - Use face recognition to mark attendance
   - View attendance history

### For Administrators

1. **Admin Panel**: Visit `http://localhost:8000/admin/`
   - Manage students and classes
   - View attendance records
   - Configure system settings

2. **Enroll Students in Classes**:
   ```bash
   python manage.py enroll_student STUDENT_ID --classes CS101 MATH201
   # or enroll in all classes:
   python manage.py enroll_student STUDENT_ID --all-classes
   ```

## System Workflow

1. **Student Registration**:
   - Student creates account with personal details
   - System creates Django user and Student record
   - Auto-login and redirect to face registration

2. **Face Registration**:
   - Camera captures student's face
   - DeepFace validates image quality
   - Face encoding stored in database
   - Student ready to mark attendance

3. **Attendance Marking**:
   - Student selects class from dashboard
   - Camera captures face for recognition
   - System matches against stored encodings
   - Attendance marked with timestamp and confidence

## Key Components

### Models
- **Student**: Student information and enrollment
- **Class**: Course information and instructor
- **Attendance**: Attendance records with timestamps
- **FaceEncoding**: Stored face encodings for recognition
- **AttendanceSession**: Daily attendance sessions per class

### Views
- **Student Authentication**: Login, signup, logout
- **Face Enrollment**: Camera-based face registration
- **Attendance Marking**: Real-time face recognition
- **Dashboard**: Student and admin interfaces

### API Endpoints
- `/api/recognize-face/`: Face recognition for attendance
- `/api/validate-image/`: Image quality validation
- `/api/attendance-status/`: Real-time attendance status

## Configuration

### Face Recognition Settings (in settings.py)
```python
FACE_RECOGNITION_THRESHOLD = 0.6  # Recognition sensitivity
FACE_ENCODINGS_DIR = BASE_DIR / 'media' / 'face_encodings'
```

### DeepFace Configuration
- Model: VGG-Face (can be changed to Facenet, OpenFace, etc.)
- Detector: OpenCV (can be changed to MTCNN, RetinaFace, etc.)
- Distance Metric: Cosine similarity

## Troubleshooting

### DeepFace Not Available
If you see "DeepFace not available" messages:
```bash
pip install deepface opencv-python tensorflow
```

### Camera Access Issues
- Ensure HTTPS for production (camera requires secure context)
- Check browser permissions for camera access
- Test with different browsers if needed

### Face Recognition Accuracy
- Ensure good lighting during face registration
- Use clear, front-facing photos
- Register multiple face angles if needed
- Adjust FACE_RECOGNITION_THRESHOLD if needed

## Management Commands

- `python manage.py quick_setup`: Create sample classes and enroll students
- `python manage.py setup_sample_data --enroll-all`: Comprehensive setup
- `python manage.py enroll_student STUDENT_ID --classes CS101`: Enroll specific student

## Security Notes

- Face encodings are stored as numerical vectors, not images
- Student passwords are hashed using Django's built-in security
- CSRF protection enabled for all forms
- Camera access requires user permission

## Future Enhancements

- [ ] Mobile app for attendance
- [ ] Bulk student import from CSV
- [ ] Advanced reporting and analytics
- [ ] Integration with LMS systems
- [ ] Multi-language support
- [ ] Attendance notifications

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django and DeepFace documentation
3. Ensure all dependencies are properly installed
