from django.shortcuts import render, get_object_or_404, redirect
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import base64
import logging
import requests

from .models import CustomUser, Student, Lecturer, Class, Attendance, FaceEncoding, AttendanceSession, Department, Level
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from . import faceplusplus_service

# Get the custom user model
User = get_user_model()





# Face++ Service Wrapper for Django views
class FacePPService:
    def __init__(self):
        self.available = True  # Always available if API keys are set

    def validate_image_quality(self, image_url):
        # For Face++, just check if a face is detected using image URL only
        try:
            # Print the full API response for debugging
            data = {
                'api_key': faceplusplus_service.FACEPP_API_KEY,
                'api_secret': faceplusplus_service.FACEPP_API_SECRET,
                'image_base64': image_url
            }
            response = requests.post(faceplusplus_service.FACEPP_DETECT_URL, data=data)
            print(image_url)
            print("[DEBUG] Face++ API response:", response.text)
            result = response.json()
            if 'faces' in result and len(result['faces']) > 0:
                return True, "Image quality is acceptable"
            else:
                return False, "No face detected in image"
        except Exception as e:
            return False, f"Error validating image: {str(e)}"

    def enroll_student_face(self, student, image_data, is_primary=False):
        # Save the image to MEDIA, store the path in the DB, and use the public URL for Face++
        import logging
        from .models import FaceEncoding
        from django.conf import settings
        from django.core.files.base import ContentFile
        import base64, os
        logger = logging.getLogger(__name__)
        if image_data.startswith('data:image'):
            image_data_base64 = image_data.split(',')[1]
        else:
            image_data_base64 = image_data
        img_bytes = base64.b64decode(image_data_base64)
        img_content = ContentFile(img_bytes)
        face_encoding = FaceEncoding.objects.create(
            student=student,
            is_primary=is_primary,
            detection_status='error',  # will update after detection
        )
        filename = f"{student.student_id}_{face_encoding.id}.jpg"
        face_encoding.image.save(filename, img_content)
        face_encoding.save()
        # Construct the public URL (for your records, not for Face++)
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        image_url = media_url.rstrip('/') + '/' + face_encoding.image.name.replace('\\', '/')
        print(f"MEDIA IMAGE URL (enrollment): {image_url}")
        try:
            logger.info(f"Calling Face++ to detect face token using base64 data (not image_url)")
            face_token = faceplusplus_service.detect_face_token_from_base64(image_data_base64)
            logger.info(f"Face++ returned face_token: {face_token}")
            if not face_token:
                face_encoding.detection_status = 'no_face'
                face_encoding.error_message = 'No face detected in image'
                face_encoding.save()
                raise ValueError("No face detected in image")
            face_encoding.encoding_data = face_token
            face_encoding.detection_status = 'success'
            face_encoding.error_message = ''
            face_encoding.save()
            return face_encoding
        except Exception as e:
            logger.error(f"Error enrolling student face: {str(e)}")
            face_encoding.detection_status = 'error'
            face_encoding.error_message = str(e)
            face_encoding.save()
            raise ValueError(f"Could not enroll face: {str(e)}")

    def recognize_student(self, image_data):
        # Use base64 image data for Face++ recognition (no Cloudinary)
        try:
            print(f"[DEBUG] image_data type: {type(image_data)}, length: {len(image_data)}")
            if image_data.startswith('data:image'):
                image_data_base64 = image_data.split(',')[1]
            else:
                image_data_base64 = image_data
            detected_token = faceplusplus_service.detect_face_token_from_base64(image_data_base64)
            print(f"[DEBUG] Face++ used base64 for recognition.")
            if not detected_token:
                return None, 0
            from .models import FaceEncoding
            best_match = None
            best_confidence = 0
            for fe in FaceEncoding.objects.all():
                result = faceplusplus_service.compare_face_tokens(detected_token, fe.encoding_data)
                confidence = result.get('confidence', 0)
                if confidence > best_confidence and confidence > 80:  # 80 is a typical threshold
                    best_match = fe.student
                    best_confidence = confidence
            if best_match:
                return best_match, best_confidence
            return None, 0
        except Exception as e:
            import logging
            logging.error(f"Error recognizing student: {str(e)}")
            print(f"[DEBUG] Error recognizing student: {str(e)}")
            return None, 0

# Global instance
face_service = FacePPService()

logger = logging.getLogger(__name__)






# Authentication Views
def student_login(request):
    """Login view for both students and lecturers using email and password"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Please provide both email and password')
            return render(request, 'attendance/student_login.html')

        # Authenticate user with email and password
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)

                # Get user's full name for welcome message
                full_name = user.get_full_name() or user.username
                messages.success(request, f'Welcome back, {full_name}!')

                # Redirect based on position
                if user.position == 'lecturer' or user.is_staff:
                    return redirect('lecturer_dashboard')
                else:
                    return redirect('student_dashboard')
            else:
                messages.error(request, 'Your account is inactive. Please contact administrator.')
        else:
            messages.error(request, 'Invalid email or password')

    return render(request, 'attendance/student_login.html')


def student_signup(request):
    """Working student signup - guaranteed to work"""

    if request.method == 'POST':
        print("=" * 50)
        print("🚀 SIGNUP POST REQUEST RECEIVED")
        print("=" * 50)

        try:
            # Get form data
            employee_id = request.POST.get('employee_id', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            department_id = request.POST.get('department', '')
            department_id = request.POST.get('department', '')

            print(f"📝 Form Data Received:")
            print(f"   Employee ID: '{employee_id}'")
            print(f"   Name: '{first_name} {last_name}'")
            print(f"   Email: '{email}'")
            print(f"   Phone: '{phone}'")

            # Validation
            if not employee_id:
                print("❌ Missing employee ID")
                messages.error(request, 'Employee ID is required')
                return render(request, 'attendance/student_signup.html')

            if not first_name:
                print("❌ Missing first name")
                messages.error(request, 'First name is required')
                return render(request, 'attendance/student_signup.html')

            if not last_name:
                print("❌ Missing last name")
                messages.error(request, 'Last name is required')
                return render(request, 'attendance/student_signup.html')

            if not email:
                print("❌ Missing email")
                messages.error(request, 'Email is required')
                return render(request, 'attendance/student_signup.html')

            if not password:
                print("❌ Missing password")
                messages.error(request, 'Password is required')
                return render(request, 'attendance/student_signup.html')

            if password != confirm_password:
                print("❌ Passwords don't match")
                messages.error(request, 'Passwords do not match')
                return render(request, 'attendance/student_signup.html')

            # Check existing records more thoroughly
            if Student.objects.filter(student_id=employee_id).exists():
                print(f"❌ Employee ID {employee_id} already exists in Employee table")
                messages.error(request, f'Employee ID {employee_id} already exists')
                return render(request, 'attendance/student_signup.html')

            if User.objects.filter(username=employee_id).exists():
                print(f"❌ Username {employee_id} already exists in User table")
                messages.error(request, f'Employee ID {employee_id} already exists')
                return render(request, 'attendance/student_signup.html')


            if Student.objects.filter(user__email=email).exists():
                print(f"❌ Email {email} already exists")
                messages.error(request, f'Email {email} already exists')
                return render(request, 'attendance/student_signup.html')

            if User.objects.filter(email=email).exists():
                print(f"❌ Email {email} already exists in User table")
                messages.error(request, f'Email {email} already exists')
                return render(request, 'attendance/student_signup.html')

            print("✅ All validation passed")
            print(f"🔨 Creating account for {employee_id}...")

            user = CustomUser.objects.create_user(
                username=employee_id,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            print(f"✅ Django User created with ID: {user.id}")

            # Fetch the student profile created by the signal
            student = Student.objects.get(user=user)

            # Update student with additional information
            if department_id:
                try:
                    department = Department.objects.get(id=department_id)
                    student.department = department
                except Department.DoesNotExist:
                    pass

            if department_id:
                try:
                    department = Department.objects.get(id=department_id)
                    student.department = department
                except Department.DoesNotExist:
                    pass

            if phone:
                # Set phone on user, not student (student.phone is a property)
                user = user if hasattr(user, 'phone') else User.objects.get(pk=user.pk)
                user.phone = phone
                user.save()

            student.save()
            print(f"✅ Student record updated with ID: {student.id}")

            # Login user using email
            auth_user = authenticate(request, username=email, password=password)
            if auth_user:
                login(request, auth_user)
                print(f"✅ User {employee_id} logged in successfully with email!")
                print(f"🎯 Redirecting to face enrollment...")
                messages.success(request, f'Welcome {student.full_name}! Let\'s set up your face recognition.')
                return redirect('student_face_enrollment')
            else:
                print(f"❌ Authentication failed for {email}")
                messages.warning(request, 'Account created but login failed. Please log in manually.')
                return redirect('student_login')


        except Exception as e:
            print(f"💥 CRITICAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'System error: {str(e)}')
            return render(request, 'attendance/student_signup.html')
    else:
        print("📄 SIGNUP: Showing signup form (GET request)")
        # Get departments and levels for dropdowns
        departments = Department.objects.all().order_by('name')
        context = {
            'departments': departments,
        }
        return render(request, 'attendance/student_signup.html', context)


def signup_success(request):
    """Signup success page"""
    if not request.user.is_authenticated:
        return redirect('student_login')
    return render(request, 'attendance/signup_success.html')


def debug_signup(request):
    """Debug version of student signup for testing"""
    if request.method == 'POST':
        logger.info("DEBUG: Student signup POST request received")

        # Log all POST data
        for key, value in request.POST.items():
            if key not in ['password', 'confirm_password', 'csrfmiddlewaretoken']:
                logger.info(f"DEBUG: {key} = {value}")

        student_id = request.POST.get('student_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        logger.info(f"DEBUG: Processing signup for {student_id}")

        # Basic validation
        if not all([student_id, first_name, last_name, email, password, confirm_password]):
            logger.error("DEBUG: Missing required fields")
            messages.error(request, 'All required fields must be filled')
            return render(request, 'attendance/debug_signup.html')

        if password != confirm_password:
            logger.error("DEBUG: Passwords don't match")
            messages.error(request, 'Passwords do not match')
            return render(request, 'attendance/debug_signup.html')

        # Check for existing records
        if Student.objects.filter(student_id=student_id).exists():
            logger.error(f"DEBUG: Student ID {student_id} already exists")
            messages.error(request, 'Student ID already exists')
            return render(request, 'attendance/debug_signup.html')

        if Student.objects.filter(user__email=email).exists():
            logger.error(f"DEBUG: Email {email} already exists")
            messages.error(request, 'Email already exists')
            return render(request, 'attendance/debug_signup.html')

        try:
            with transaction.atomic():
                logger.info(f"DEBUG: Creating user for {student_id}")

                # Create Django user
                user = User.objects.create_user(
                    username=student_id,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                logger.info(f"DEBUG: User created successfully: {user.id}")

                # Create student record (only pass valid fields)
                student = Student.objects.get(user=user)
                if phone:
                    # Refresh user from DB to avoid stale object
                    user = User.objects.get(pk=user.pk)
                    user.phone = phone
                    user.save()
                
                logger.info(f"DEBUG: Student created successfully: {student.id}")

                # Authenticate and login
                logger.info(f"DEBUG: Attempting to authenticate {student_id}")
                auth_user = authenticate(request, username=student_id, password=password)

                if auth_user:
                    login(request, auth_user)
                    logger.info(f"DEBUG: User {student_id} logged in successfully")
                    messages.success(request, f'Account created and logged in! Redirecting to face enrollment...')
                    return redirect('student_face_enrollment')
                else:
                    logger.error(f"DEBUG: Authentication failed for {student_id}")
                    messages.warning(request, 'Account created but login failed. Please try logging in manually.')
                    return redirect('student_login')

        except Exception as e:
            logger.error(f"DEBUG: Error creating account: {str(e)}")
            messages.error(request, f'Error creating account: {str(e)}')

    return render(request, 'attendance/debug_signup.html')


def simple_test(request):
    """Simple test view to verify form submission works"""
    if request.method == 'POST':
        logger.info("Simple test POST received")
        messages.success(request, "Form submission works! POST data received.")

    return render(request, 'attendance/simple_test.html')


def minimal_signup(request):
    """Minimal signup test - no JavaScript"""
    if request.method == 'POST':
        logger.info("MINIMAL: POST request received")
        messages.success(request, "MINIMAL: Form submitted successfully!")

        # Just show the data, don't create account
        for key, value in request.POST.items():
            if key not in ['password', 'confirm_password', 'csrfmiddlewaretoken']:
                logger.info(f"MINIMAL: {key} = {value}")

    return render(request, 'attendance/minimal_signup.html')


def diagnostic(request):
    """Diagnostic view to check if Django is working"""
    from django.http import HttpResponse
    import json

    info = {
        'status': 'Django is working!',
        'method': request.method,
        'path': request.path,
        'user': str(request.user),
        'authenticated': request.user.is_authenticated,
        'session_key': request.session.session_key,
        'urls_working': True
    }

    return HttpResponse(
        f"<h1>Django Diagnostic</h1><pre>{json.dumps(info, indent=2)}</pre>",
        content_type='text/html'
    )


def student_logout(request):
    """Student logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('student_login')


@login_required
def lecturer_dashboard(request):
    """Lecturer dashboard view - shows classes, students, and attendance management"""
    try:
        # Check if user is a lecturer (staff user)
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Lecturer privileges required.')
            return redirect('student_dashboard')

        # Get classes taught by this lecturer
        lecturer_classes = Class.objects.filter(
            instructor=request.user,
            is_active=True
        ).prefetch_related('students')

        # Get today's attendance sessions
        today = timezone.now().date()
        today_sessions = AttendanceSession.objects.filter(
            class_session__instructor=request.user,
            date=today
        ).select_related('class_session')

        # Add today's attendance count to each class
        for cls in lecturer_classes:
            today_attendance = Attendance.objects.filter(
                class_attended=cls,
                date=today,
                status='present'
            ).count()
            cls.attendance_today_count = today_attendance

        # Get recent attendance records
        recent_attendance = Attendance.objects.filter(
            class_attended__instructor=request.user
        ).select_related('student', 'class_attended').order_by('-timestamp')[:20]

        # Calculate statistics
        total_students = sum(cls.students.filter(is_active=True).count() for cls in lecturer_classes)
        total_classes = lecturer_classes.count()
        today_attendance_count = sum(session.present_count for session in today_sessions)

        context = {
            'lecturer': request.user,
            'lecturer_classes': lecturer_classes,
            'today_sessions': today_sessions,
            'recent_attendance': recent_attendance,
            'total_students': total_students,
            'total_classes': total_classes,
            'today_attendance_count': today_attendance_count,
            'today': today,
        }
        return render(request, 'attendance/lecturer_dashboard.html', context)

    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('student_login')


@login_required
def student_dashboard(request):
    """Student dashboard view - shows enrolled classes and attendance history"""
    try:
        # Get the student record for the logged-in user
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        # Get classes the student is enrolled in
        enrolled_classes = student.enrolled_classes.filter(is_active=True)

        # Get today's attendance records for this student
        today = timezone.now().date()
        today_attendance = Attendance.objects.filter(
            student=student,
            date=today
        ).select_related('class_attended')

        # Create a set of class IDs that have attendance marked today
        marked_class_ids = set(att.class_attended.id for att in today_attendance)

        # Add attendance info to each class
        classes_with_attendance = []
        for class_obj in enrolled_classes:
            attendance_record = today_attendance.filter(class_attended=class_obj).first()
            classes_with_attendance.append({
                'class': class_obj,
                'attendance': attendance_record,
                'is_marked': class_obj.id in marked_class_ids
            })

        # Get available classes for enrollment (not already enrolled)
        enrolled_class_ids = student.enrolled_classes.values_list('id', flat=True)
        available_classes = Class.objects.filter(
            is_active=True
        ).exclude(id__in=enrolled_class_ids)

        # Get recent attendance history
        recent_attendance = Attendance.objects.filter(
            student=student
        ).select_related('class_attended').order_by('-timestamp')[:10]

        # Calculate statistics
        total_enrolled = enrolled_classes.count()
        attended_today = len(marked_class_ids)

        context = {
            'student': student,
            'enrolled_classes': enrolled_classes,
            'available_classes': available_classes,
            'classes_with_attendance': classes_with_attendance,
            'marked_class_ids': marked_class_ids,
            'recent_attendance': recent_attendance,
            'today': today,
            'total_enrolled': total_enrolled,
            'attended_today': attended_today,
        }
        return render(request, 'attendance/student_dashboard.html', context)

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found. Please contact administrator.')
        return redirect('student_login')


@login_required
def enroll_in_class(request, class_id):
    """Allow student to enroll in a class"""
    try:
        # Get student record
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        # Get the class
        class_obj = get_object_or_404(Class, id=class_id, is_active=True)

        # Check if already enrolled
        if student.enrolled_classes.filter(id=class_id).exists():
            messages.warning(request, f'You are already enrolled in {class_obj.code}')
        else:
            # Enroll student in class
            student.enrolled_classes.add(class_obj)
            messages.success(request, f'Successfully enrolled in {class_obj.code} - {class_obj.name}')

        return redirect('student_dashboard')

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found.')
        return redirect('student_login')
    except Exception as e:
        messages.error(request, f'Error enrolling in class: {str(e)}')
        return redirect('student_dashboard')


@login_required
def unenroll_from_class(request, class_id):
    """Allow student to unenroll from a class"""
    try:
        # Get student record
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        # Get the class
        class_obj = get_object_or_404(Class, id=class_id, is_active=True)

        # Check if enrolled
        if not student.enrolled_classes.filter(id=class_id).exists():
            messages.warning(request, f'You are not enrolled in {class_obj.code}')
        else:
            # Unenroll student from class
            student.enrolled_classes.remove(class_obj)
            messages.success(request, f'Successfully unenrolled from {class_obj.code} - {class_obj.name}')

        return redirect('student_dashboard')

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found.')
        return redirect('student_login')
    except Exception as e:
        messages.error(request, f'Error unenrolling from class: {str(e)}')
        return redirect('student_dashboard')


@login_required
def enroll_in_class(request, class_id):
    """Allow student to enroll in a class"""
    try:
        # Get student record
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        # Get the class
        class_obj = get_object_or_404(Class, id=class_id, is_active=True)

        # Check if already enrolled
        if student.enrolled_classes.filter(id=class_id).exists():
            messages.warning(request, f'You are already enrolled in {class_obj.code}')
        else:
            # Enroll student in class
            student.enrolled_classes.add(class_obj)
            messages.success(request, f'Successfully enrolled in {class_obj.code} - {class_obj.name}')

        return redirect('student_dashboard')

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found.')
        return redirect('student_login')
    except Exception as e:
        messages.error(request, f'Error enrolling in class: {str(e)}')
        return redirect('student_dashboard')


@login_required
def unenroll_from_class(request, class_id):
    """Allow student to unenroll from a class"""
    try:
        # Get student record
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        # Get the class
        class_obj = get_object_or_404(Class, id=class_id, is_active=True)

        # Check if enrolled
        if not student.enrolled_classes.filter(id=class_id).exists():
            messages.warning(request, f'You are not enrolled in {class_obj.code}')
        else:
            # Unenroll student from class
            student.enrolled_classes.remove(class_obj)
            messages.success(request, f'Successfully unenrolled from {class_obj.code} - {class_obj.name}')

        return redirect('student_dashboard')

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found.')
        return redirect('student_login')
    except Exception as e:
        messages.error(request, f'Error unenrolling from class: {str(e)}')
        return redirect('student_dashboard')


@login_required
def lecturer_attendance_history(request):
    """Lecturer attendance history view - shows all attendance records across their classes with search functionality"""
    try:
        # Check if user is a lecturer
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Lecturer privileges required.')
            return redirect('student_dashboard')

        # Get search parameters
        search_query = request.GET.get('search', '').strip()
        class_filter = request.GET.get('class_filter', '')
        status_filter = request.GET.get('status_filter', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        student_filter = request.GET.get('student_filter', '')
        department_filter = request.GET.get('department_filter', '')
        level_filter = request.GET.get('level_filter', '')
        semester_filter = request.GET.get('semester_filter', '')

        # Base queryset - all attendance records for lecturer's classes
        attendance_records = Attendance.objects.filter(
            class_attended__instructor=request.user
        ).select_related('student', 'class_attended').order_by('-date', '-timestamp')

        # Apply filters
        if search_query:
            attendance_records = attendance_records.filter(
                Q(student__user__first_name__icontains=search_query) |
                Q(student__user__last_name__icontains=search_query) |
                Q(student__student_id__icontains=search_query) |
                Q(class_attended__name__icontains=search_query) |
                Q(class_attended__code__icontains=search_query)
            )

        if class_filter:
            attendance_records = attendance_records.filter(class_attended__id=class_filter)

        if status_filter:
            attendance_records = attendance_records.filter(status=status_filter)

        if student_filter:
            attendance_records = attendance_records.filter(student__id=student_filter)

        if department_filter:
            attendance_records = attendance_records.filter(student__department__id=department_filter)

        if level_filter:
            attendance_records = attendance_records.filter(student__level__id=level_filter)

        if semester_filter:
            attendance_records = attendance_records.filter(student__semester=semester_filter)

        if date_from:
            try:
                from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(date__gte=from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(date__lte=to_date)
            except ValueError:
                pass

        # Get lecturer's classes for filter dropdown
        lecturer_classes = Class.objects.filter(
            instructor=request.user,
            is_active=True
        ).order_by('code')

        # Get all students from lecturer's classes for filter dropdown
        lecturer_students = Student.objects.filter(
            enrolled_classes__instructor=request.user,
            is_active=True
        ).distinct().order_by('user__first_name', 'user__last_name')

        # Get departments and levels for filter dropdowns
        departments = Department.objects.filter(
            students__enrolled_classes__instructor=request.user
        ).distinct().order_by('name')

        levels = Level.objects.filter(
            students__enrolled_classes__instructor=request.user
        ).distinct().order_by('code')

        # Semester choices
        semester_choices = Student.SEMESTER_CHOICES

        # Get departments and levels for filter dropdowns
        departments = Department.objects.filter(
            students__enrolled_classes__instructor=request.user
        ).distinct().order_by('name')

        levels = Level.objects.filter(
            students__enrolled_classes__instructor=request.user
        ).distinct().order_by('code')

        # Semester choices
        semester_choices = Student.SEMESTER_CHOICES

        # Calculate statistics
        total_records = attendance_records.count()
        present_count = attendance_records.filter(status='present').count()
        late_count = attendance_records.filter(status='late').count()
        absent_count = attendance_records.filter(status='absent').count()

        attendance_rate = round((present_count / total_records * 100), 1) if total_records > 0 else 0

        context = {
            'lecturer': request.user,
            'attendance_records': attendance_records,
            'lecturer_classes': lecturer_classes,
            'lecturer_students': lecturer_students,
            'departments': departments,
            'levels': levels,
            'semester_choices': semester_choices,
            'search_query': search_query,
            'class_filter': class_filter,
            'status_filter': status_filter,
            'student_filter': student_filter,
            'department_filter': department_filter,
            'level_filter': level_filter,
            'semester_filter': semester_filter,
            'date_from': date_from,
            'date_to': date_to,
            'total_records': total_records,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': absent_count,
            'attendance_rate': attendance_rate,
        }
        return render(request, 'attendance/lecturer_attendance_history.html', context)

    except Exception as e:
        messages.error(request, f'Error loading attendance history: {str(e)}')
        return redirect('lecturer_dashboard')





@login_required
def lecturer_attendance_session(request, class_id):
    """Lecturer attendance session - where students mark attendance using face recognition"""
    try:
        # Check if user is a lecturer
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Lecturer privileges required.')
            return redirect('student_dashboard')

        # Get the class and verify lecturer owns it
        class_obj = get_object_or_404(Class, id=class_id, instructor=request.user, is_active=True)

        # Get or create today's attendance session
        today = timezone.now().date()
        session, created = AttendanceSession.objects.get_or_create(
            class_session=class_obj,
            date=today,
            defaults={
                'created_by': request.user,
                'total_students': class_obj.students.filter(is_active=True).count()
            }
        )

        # Get today's attendance records for this class
        today_attendance = Attendance.objects.filter(
            class_attended=class_obj,
            date=today
        ).select_related('student').order_by('-timestamp')

        # Get enrolled students
        enrolled_students = class_obj.students.filter(is_active=True)

        # Create attendance status for each student
        attendance_status = []
        marked_student_ids = set(att.student.id for att in today_attendance)

        for student in enrolled_students:
            attendance_record = today_attendance.filter(student=student).first()
            attendance_status.append({
                'student': student,
                'attendance': attendance_record,
                'is_marked': student.id in marked_student_ids
            })

        context = {
            'lecturer': request.user,
            'class': class_obj,
            'session': session,
            'today_attendance': today_attendance,
            'attendance_status': attendance_status,
            'enrolled_students': enrolled_students,
            'today': today,
            'session_created': created,
        }
        return render(request, 'attendance/lecturer_attendance_session.html', context)

    except Exception as e:
        messages.error(request, f'Error loading attendance session: {str(e)}')
        return redirect('lecturer_dashboard')



@login_required
def student_attendance_history(request):
    """Student attendance history view - shows all attendance records with search functionality"""
    try:
        # Get the student record for the logged-in user
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        # Get search parameters
        search_query = request.GET.get('search', '').strip()
        class_filter = request.GET.get('class_filter', '')
        status_filter = request.GET.get('status_filter', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # Base queryset
        attendance_records = Attendance.objects.filter(
            student=student
        ).select_related('class_attended').order_by('-date', '-timestamp')

        # Apply filters
        if search_query:
            attendance_records = attendance_records.filter(
                Q(class_attended__name__icontains=search_query) |
                Q(class_attended__code__icontains=search_query)
            )

        if class_filter:
            attendance_records = attendance_records.filter(class_attended__id=class_filter)

        if status_filter:
            attendance_records = attendance_records.filter(status=status_filter)

        if date_from:
            try:
                from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(date__gte=from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
                attendance_records = attendance_records.filter(date__lte=to_date)
            except ValueError:
                pass

        # Get student's enrolled classes for filter dropdown
        enrolled_classes = student.enrolled_classes.filter(is_active=True).order_by('code')

        # Calculate statistics
        total_records = attendance_records.count()
        present_count = attendance_records.filter(status='present').count()
        late_count = attendance_records.filter(status='late').count()
        absent_count = attendance_records.filter(status='absent').count()

        attendance_rate = round((present_count / total_records * 100), 1) if total_records > 0 else 0

        context = {
            'student': student,
            'attendance_records': attendance_records,
            'enrolled_classes': enrolled_classes,
            'search_query': search_query,
            'class_filter': class_filter,
            'status_filter': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'total_records': total_records,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': absent_count,
            'attendance_rate': attendance_rate,
        }
        return render(request, 'attendance/student_attendance_history.html', context)

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found. Please contact administrator.')
        return redirect('student_login')
    except Exception as e:
        messages.error(request, f'Error loading attendance history: {str(e)}')
        return redirect('student_dashboard')


@login_required
def student_face_enrollment(request):
    """Student face enrollment view - for their own face registration"""
    try:
        # Get the student record for the logged-in user
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        if request.method == 'POST':
            try:
                # Accept multiple images: image_data_list[] from POST (as list)
                image_data_list = request.POST.getlist('image_data_list')
                is_primary = request.POST.get('is_primary') == 'true'

                if not image_data_list or len(image_data_list) == 0:
                    messages.error(request, 'No images provided. Please upload at least one image.')
                    return render(request, 'attendance/student_face_enrollment.html', {'student': student})

                # Use global face_service instance directly

                errors = []
                enrolled_count = 0
                for idx, image_data in enumerate(image_data_list):
                    try:
                        is_valid, message = face_service.validate_image_quality(image_data)
                        if not is_valid:
                            errors.append(f'Image {idx+1}: {message}')
                            continue
                        face_service.enroll_student_face(
                            student=student,
                            image_data=image_data,
                            is_primary=(is_primary or student.face_encodings.count() == 0) and enrolled_count == 0
                        )
                        enrolled_count += 1
                    except Exception as validation_error:
                        logger.error(f"Error during image validation/enrollment: {str(validation_error)}")
                        errors.append(f'Image {idx+1}: Error during enrollment')

                if enrolled_count > 0:
                    messages.success(request, f'{enrolled_count} face image(s) registered successfully! Your lecturers can now mark your attendance using face recognition.')
                if errors:
                    for err in errors:
                        messages.error(request, err)
                if enrolled_count > 0:
                    return redirect('student_dashboard')

            except Exception as e:
                logger.error(f"Error enrolling face: {str(e)}")
                messages.error(request, f'Error registering face: {str(e)}')

        context = {
            'student': student,
            'existing_encodings': student.face_encodings.count(),
            'is_first_enrollment': student.face_encodings.count() == 0,
        }
        return render(request, 'attendance/student_face_enrollment.html', context)

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found. Please contact administrator.')
        return redirect('student_login')


def dashboard(request):
    """Admin dashboard view"""
    classes = Class.objects.filter(is_active=True)
    recent_sessions = AttendanceSession.objects.select_related('class_session').order_by('-start_time')[:5]
    total_students = Student.objects.filter(is_active=True).count()
    total_classes = classes.count()

    context = {
        'classes': classes,
        'recent_sessions': recent_sessions,
        'total_students': total_students,
        'total_classes': total_classes,
    }
    return render(request, 'attendance/admin_dashboard.html', context)


def student_list(request):
    """List all students"""
    students = Student.objects.filter(is_active=True).prefetch_related('enrolled_classes')
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'students': page_obj,
    }
    return render(request, 'attendance/student_list.html', context)


def student_detail(request, student_id):
    """Student detail view"""
    student = get_object_or_404(Student, student_id=student_id)
    face_encodings = student.face_encodings.all()
    recent_attendance = student.attendance_records.select_related('class_attended').order_by('-timestamp')[:10]

    context = {
        'student': student,
        'face_encodings': face_encodings,
        'recent_attendance': recent_attendance,
    }
    return render(request, 'attendance/student_detail.html', context)


def student_register(request):
    """Student registration view"""
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone', '')

            # Check if student already exists
            if Student.objects.filter(student_id=student_id).exists():
                messages.error(request, 'Student ID already exists')
                return render(request, 'attendance/student_register.html')

            if Student.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return render(request, 'attendance/student_register.html')

            # Create student
            student = Student.objects.create(
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone
            )

            messages.success(request, f'Student {student.full_name} registered successfully')
            return redirect('student_detail', student_id=student.student_id)

        except Exception as e:
            logger.error(f"Error registering student: {str(e)}")
            messages.error(request, 'Error registering student')

    return render(request, 'attendance/student_register.html')


def face_enrollment(request, student_id):
    """Face enrollment view for a student"""
    student = get_object_or_404(Student, student_id=student_id)

    if request.method == 'POST':
        try:
            # Accept multiple images: image_data_list[] from POST (as list)
            image_data_list = request.POST.getlist('image_data_list')
            is_primary = request.POST.get('is_primary') == 'true'

            if not image_data_list or len(image_data_list) == 0:
                messages.error(request, 'No images provided. Please upload at least one image.')
                return render(request, 'attendance/face_enrollment.html', {'student': student})

            # Get face recognition service
            # Use Face++ service
            face_service = face_service

            errors = []
            enrolled_count = 0
            for idx, image_data in enumerate(image_data_list):
                try:
                    is_valid, message = face_service.validate_image_quality(image_data)
                    if not is_valid:
                        errors.append(f'Image {idx+1}: {message}')
                        continue
                    face_service.enroll_student_face(
                        student=student,
                        image_data=image_data,
                        is_primary=(is_primary or student.face_encodings.count() == 0) and enrolled_count == 0
                    )
                    enrolled_count += 1
                except Exception as validation_error:
                    logger.error(f"Error during image validation/enrollment: {str(validation_error)}")
                    errors.append(f'Image {idx+1}: Error during enrollment')

            if enrolled_count > 0:
                messages.success(request, f'{enrolled_count} face image(s) enrolled successfully!')
            if errors:
                for err in errors:
                    messages.error(request, err)
            if enrolled_count > 0:
                return redirect('student_detail', student_id=student.student_id)

        except Exception as e:
            logger.error(f"Error enrolling face: {str(e)}")
            messages.error(request, f'Error enrolling face: {str(e)}')

    context = {
        'employee': student,
        'existing_encodings': student.face_encodings.count(),
    }
    return render(request, 'attendance/employee_face_enrollment.html', context)


def class_list(request):
    """List all classes"""
    classes = Class.objects.filter(is_active=True).select_related('instructor')
    context = {'classes': classes}
    return render(request, 'attendance/class_list.html', context)


def class_detail(request, class_id):
    """Class detail view"""
    class_obj = get_object_or_404(Class, id=class_id)
    students = class_obj.students.filter(is_active=True)
    recent_sessions = class_obj.attendance_sessions.order_by('-start_time')[:10]

    context = {
        'class': class_obj,
        'students': students,
        'recent_sessions': recent_sessions,
        'total_students': students.count(),
    }
    return render(request, 'attendance/class_detail.html', context)


def take_attendance(request, class_id):
    """Take attendance for a class"""
    class_obj = get_object_or_404(Class, id=class_id)

    # Get or create today's attendance session
    today = timezone.now().date()
    session, created = AttendanceSession.objects.get_or_create(
        class_session=class_obj,
        date=today,
        defaults={
            'created_by': request.user if request.user.is_authenticated else None,
            'total_students': class_obj.students.filter(is_active=True).count()
        }
    )

    # Get today's attendance records
    attendance_records = Attendance.objects.filter(
        class_attended=class_obj,
        date=today
    ).select_related('student')

    present_students = [record.student.student_id for record in attendance_records if record.status == 'present']

    context = {
        'class': class_obj,
        'session': session,
        'attendance_records': attendance_records,
        'present_students': present_students,
        'total_students': session.total_students,
        'present_count': len(present_students),
    }
    return render(request, 'attendance/take_attendance.html', context)


def attendance_history(request, class_id=None):
    """View attendance history"""
    if class_id:
        class_obj = get_object_or_404(Class, id=class_id)
        attendance_records = Attendance.objects.filter(class_attended=class_obj)
        context_class = class_obj
    else:
        attendance_records = Attendance.objects.all()
        context_class = None

    # Filter by date if provided
    date_filter = request.GET.get('date')
    if date_filter:
        attendance_records = attendance_records.filter(date=date_filter)

    # Filter by student if provided
    student_filter = request.GET.get('student')
    if student_filter:
        attendance_records = attendance_records.filter(student__student_id=student_filter)

    attendance_records = attendance_records.select_related('student', 'class_attended').order_by('-timestamp')

    paginator = Paginator(attendance_records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'attendance_records': page_obj,
        'class': context_class,
        'date_filter': date_filter,
        'student_filter': student_filter,
    }
    return render(request, 'attendance/attendance_history.html', context)


# API Views for Face Recognition
@api_view(['POST'])
def api_recognize_face(request):
    """API endpoint to recognize a face and mark attendance - Lecturer only"""
    try:
        # Check if user is authenticated and is a lecturer
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check if user is a lecturer
        if not hasattr(request.user, 'position') or request.user.position != 'lecturer':
            return Response({
                'success': False,
                'message': 'Only lecturers can mark attendance'
            }, status=status.HTTP_403_FORBIDDEN)

        # Use request.data instead of json.loads(request.body)
        image_data = request.data.get('image_data')
        class_id = request.data.get('class_id')

        if not image_data or not class_id:
            return Response({
                'success': False,
                'message': 'Missing image_data or class_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        # For lecturer sessions, we don't require student authentication
        # The face recognition will identify the student
        student = None  # Will be set by face recognition

        # Get the class
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Class not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the lecturer is the instructor of this class
        if class_obj.instructor != request.user:
            return Response({
                'success': False,
                'message': 'You can only take attendance for your own classes'
            }, status=status.HTTP_403_FORBIDDEN)

        # We'll check enrollment and duplicate attendance after face recognition
        today = timezone.now().date()

        # Get face recognition service
        # Use Face++ service (global instance)

        # Save the captured image for attendance record
        def save_attendance_image(image_data, student_id, class_id):
            """Save the captured image during attendance marking"""
            try:
                from io import BytesIO
                from PIL import Image
                from django.core.files.base import ContentFile
                from django.conf import settings

                # Create attendance images directory
                attendance_images_dir = os.path.join(settings.MEDIA_ROOT, 'attendance_images')
                os.makedirs(attendance_images_dir, exist_ok=True)

                # Process image data
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]

                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))

                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # Save image with timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"attendance_{student_id}_{class_id}_{timestamp}.jpg"
                filepath = os.path.join(attendance_images_dir, filename)

                image.save(filepath, 'JPEG', quality=85)
                print(f"✅ Saved attendance image: {filepath}")

                return filename

            except Exception as e:
                print(f"⚠️  Error saving attendance image: {str(e)}")
                return None

        # Validate image quality before recognition
        is_valid, validation_message = face_service.validate_image_quality(image_data)
        if not is_valid:
            # Save the invalid image for debugging
            save_attendance_image(image_data, 'invalid', class_id)
            return Response({
                'success': False,
                'message': f'Image validation failed: {validation_message}',
                'confidence': 0
            }, status=status.HTTP_200_OK)

        # Recognize the student using face recognition
        recognized_student, confidence = face_service.recognize_student(image_data)

        if not recognized_student:
            # Save the unrecognized image for debugging
            save_attendance_image(image_data, 'unknown', class_id)

            return Response({
                'success': False,
                'message': 'Student not recognized',
                'confidence': 0
            }, status=status.HTTP_200_OK)

        # Use the recognized student for attendance
        student = recognized_student

        # Check if student is enrolled in this class
        if not student.enrolled_classes.filter(id=class_id).exists():
            return Response({
                'success': False,
                'message': f'Student {student.full_name} is not enrolled in this class',
                'student_name': student.full_name,
                'student_id': student.student_id,
                'confidence': confidence
            }, status=status.HTTP_200_OK)

        # Check if attendance already marked today
        existing_attendance = Attendance.objects.filter(
            student=student,
            class_attended=class_obj,
            date=today
        ).first()

        if existing_attendance:
            return Response({
                'success': False,
                'message': f'{student.full_name} has already marked attendance today at {existing_attendance.timestamp.strftime("%H:%M")}',
                'already_marked': True,
                'student_name': student.full_name,
                'attendance_time': existing_attendance.timestamp.strftime("%H:%M"),
                'status': existing_attendance.status
            }, status=status.HTTP_200_OK)

        # Save the attendance image
        attendance_image_filename = save_attendance_image(image_data, student.student_id, class_id)

        # Mark attendance
        today = timezone.now().date()

        with transaction.atomic():
            # Get or create attendance session
            session, created = AttendanceSession.objects.get_or_create(
                class_session=class_obj,
                date=today,
                defaults={
                    'created_by': request.user if request.user.is_authenticated else None,
                    'total_students': class_obj.students.filter(is_active=True).count()
                }
            )

            # Check if attendance already marked
            attendance, attendance_created = Attendance.objects.get_or_create(
                student=student,
                class_attended=class_obj,
                date=today,
                defaults={
                    'status': 'present',
                    'recognition_confidence': confidence,
                    'marked_by_recognition': True,
                    'attendance_image': attendance_image_filename  # Save image filename
                }
            )

            if not attendance_created:
                # Update existing attendance
                attendance.status = 'present'
                attendance.recognition_confidence = confidence
                attendance.timestamp = timezone.now()
                if attendance_image_filename:
                    attendance.attendance_image = attendance_image_filename
                attendance.save()

                message = f'Attendance updated for {student.full_name}'
            else:
                message = f'Attendance marked for {student.full_name}'

                # Update session present count
                session.present_count = Attendance.objects.filter(
                    class_attended=class_obj,
                    date=today,
                    status='present'
                ).count()
                session.save()

        return Response({
            'success': True,
            'message': message,
            'student_name': student.full_name,
            'student_id': student.student_id,
            'confidence': confidence,
            'timestamp': attendance.timestamp.isoformat(),
            'status': attendance.status
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in face recognition API: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def api_validate_image(request):
    """API endpoint to validate image quality for face recognition"""
    try:
        # Use request.data instead of json.loads(request.body)
        image_data = request.data.get('image_data')

        if not image_data:
            return Response({
                'success': False,
                'message': 'Missing image_data'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get face recognition service
        # Use Face++ service

        is_valid, message = face_service.validate_image_quality(image_data)

        return Response({
            'success': is_valid,
            'message': message
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error validating image: {str(e)}\n{tb}")
        return Response({
            'success': False,
            'message': f'Error validating image: {str(e)}',
            'traceback': tb
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
def api_attendance_status(request, class_id):
    """API endpoint to get current attendance status for a class"""
    try:
        class_obj = get_object_or_404(Class, id=class_id)
        today = timezone.now().date()

        # Get today's attendance records
        attendance_records = Attendance.objects.filter(
            class_attended=class_obj,
            date=today
        ).select_related('student')

        present_students = []
        for record in attendance_records:
            if record.status == 'present':
                present_students.append({
                    'student_id': record.student.student_id,
                    'name': record.student.full_name,
                    'timestamp': record.timestamp.isoformat(),
                    'confidence': record.recognition_confidence
                })

        total_students = class_obj.students.filter(is_active=True).count()

        return Response({
            'success': True,
            'class_name': class_obj.name,
            'class_code': class_obj.code,
            'date': today.isoformat(),
            'total_students': total_students,
            'present_count': len(present_students),
            'attendance_rate': round((len(present_students) / total_students * 100), 2) if total_students > 0 else 0,
            'present_students': present_students
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting attendance status: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting attendance status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
