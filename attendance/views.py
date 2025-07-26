from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import logging

from .models import CustomUser, Student, Lecturer, Class, Attendance, FaceEncoding, AttendanceSession

# Get the custom user model
User = get_user_model()




# Lazy import for face recognition service with fallback
def get_face_recognition_service():
    try:
        # Try new DeepFace service first
        from .deepface_service import deepface_service
        if deepface_service.available:
            print("✅ Using DeepFace service")
            return deepface_service

        # Fall back to old service
        from .face_recognition_utils import face_recognition_service, get_fallback_service
        if face_recognition_service.available:
            print("✅ Using old face recognition service")
            return face_recognition_service
        else:
            # Fall back to simple service
            fallback = get_fallback_service()
            if fallback and fallback.available:
                print("✅ Using simple fallback service")
                return fallback

        print("❌ No face recognition service available")
        return None
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None

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
            student_id = request.POST.get('student_id', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')

            print(f"📝 Form Data Received:")
            print(f"   Student ID: '{student_id}'")
            print(f"   Name: '{first_name} {last_name}'")
            print(f"   Email: '{email}'")
            print(f"   Phone: '{phone}'")

            # Validation
            if not student_id:
                print("❌ Missing student ID")
                messages.error(request, 'Student ID is required')
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
            if Student.objects.filter(student_id=student_id).exists():
                print(f"❌ Student ID {student_id} already exists in Student table")
                messages.error(request, f'Student ID {student_id} already exists')
                return render(request, 'attendance/student_signup.html')

            if User.objects.filter(username=student_id).exists():
                print(f"❌ Username {student_id} already exists in User table")
                messages.error(request, f'Student ID {student_id} already exists')
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
            print(f"🔨 Creating account for {student_id}...")

            user = CustomUser.objects.create_user(
                username=student_id,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            print(f"✅ Django User created with ID: {user.id}")

            # Fetch the student profile created by the signal
            student = Student.objects.get(user=user)
            print(f"✅ Student record created with ID: {student.id}")

            # Login user using email
            auth_user = authenticate(request, username=email, password=password)
            if auth_user:
                login(request, auth_user)
                print(f"✅ User {student_id} logged in successfully with email!")
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
        return render(request, 'attendance/student_signup.html')


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
                student = Student.objects.create(
                    student_id=student_id,
                    user=user,
                    is_active=True
                )
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
        return redirect('login')


@login_required
def student_dashboard(request):
    """Student dashboard view - shows classes they can mark attendance for"""
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

        # Get recent attendance history
        recent_attendance = Attendance.objects.filter(
            student=student
        ).select_related('class_attended').order_by('-timestamp')[:10]

        context = {
            'student': student,
            'enrolled_classes': enrolled_classes,
            'classes_with_attendance': classes_with_attendance,
            'marked_class_ids': marked_class_ids,
            'recent_attendance': recent_attendance,
            'today': today,
        }
        return render(request, 'attendance/student_dashboard.html', context)

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found. Please contact administrator.')
        return redirect('student_login')


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
def student_mark_attendance(request, class_id):
    """Student view to mark their own attendance using face recognition"""
    try:
        # Get the student record for the logged-in user
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        # Get the class and verify student is enrolled
        class_obj = get_object_or_404(Class, id=class_id, is_active=True)

        if not student.enrolled_classes.filter(id=class_id).exists():
            messages.error(request, 'You are not enrolled in this class.')
            return redirect('student_dashboard')

        # Check if student has face encodings
        if not student.face_encodings.exists():
            messages.error(request, 'You need to enroll your face first. Please contact administrator.')
            return redirect('student_dashboard')

        # Check if attendance already marked today
        today = timezone.now().date()
        existing_attendance = Attendance.objects.filter(
            student=student,
            class_attended=class_obj,
            date=today
        ).first()

        context = {
            'student': student,
            'class': class_obj,
            'existing_attendance': existing_attendance,
            'today': today,
        }
        return render(request, 'attendance/student_mark_attendance.html', context)

    except Student.DoesNotExist:
        messages.error(request, 'Student record not found. Please contact administrator.')
        return redirect('student_login')


@login_required
def student_face_enrollment(request):
    """Student face enrollment view - for their own face registration"""
    try:
        # Get the student record for the logged-in user
        student = Student.objects.get(student_id=request.user.username, is_active=True)

        if request.method == 'POST':
            try:
                image_data = request.POST.get('image_data')
                is_primary = request.POST.get('is_primary') == 'true'

                if not image_data:
                    messages.error(request, 'No image data provided')
                    return render(request, 'attendance/student_face_enrollment.html', {'student': student})

                # Get face recognition service
                face_service = get_face_recognition_service()
                if not face_service or not face_service.available:
                    messages.error(request, 'Face recognition service not available. Please try again later.')
                    return render(request, 'attendance/student_face_enrollment.html', {'student': student})

                # Validate image quality
                try:
                    is_valid, message = face_service.validate_image_quality(image_data)
                    if not is_valid:
                        messages.error(request, f'Image validation failed: {message}')
                        context = {
                            'student': student,
                            'existing_encodings': student.face_encodings.count(),
                            'is_first_enrollment': student.face_encodings.count() == 0,
                        }
                        return render(request, 'attendance/student_face_enrollment.html', context)
                except Exception as validation_error:
                    logger.error(f"Error during image validation: {str(validation_error)}")
                    messages.warning(request, 'Image validation skipped due to service unavailability. Proceeding with enrollment.')
                    # Continue with enrollment even if validation fails

                # Enroll face
                face_encoding = face_service.enroll_student_face(
                    student=student,
                    image_data=image_data,
                    is_primary=is_primary or student.face_encodings.count() == 0  # First face is always primary
                )

                messages.success(request, 'Face registered successfully! You can now mark attendance using face recognition.')
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
            image_data = request.POST.get('image_data')
            is_primary = request.POST.get('is_primary') == 'true'

            if not image_data:
                messages.error(request, 'No image data provided')
                return render(request, 'attendance/face_enrollment.html', {'student': student})

            # Get face recognition service
            face_service = get_face_recognition_service()
            if not face_service or not face_service.available:
                messages.error(request, 'Face recognition service not available. Please install DeepFace.')
                return render(request, 'attendance/face_enrollment.html', {'student': student})

            # Validate image quality
            is_valid, message = face_service.validate_image_quality(image_data)
            if not is_valid:
                messages.error(request, f'Image validation failed: {message}')
                return render(request, 'attendance/face_enrollment.html', {'student': student})

            # Enroll face
            face_encoding = face_service.enroll_student_face(
                student=student,
                image_data=image_data,
                is_primary=is_primary
            )

            messages.success(request, 'Face enrolled successfully')
            return redirect('student_detail', student_id=student.student_id)

        except Exception as e:
            logger.error(f"Error enrolling face: {str(e)}")
            messages.error(request, f'Error enrolling face: {str(e)}')

    context = {
        'student': student,
        'existing_encodings': student.face_encodings.count(),
    }
    return render(request, 'attendance/face_enrollment.html', context)


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
    """API endpoint to recognize a face and mark attendance"""
    try:
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

        # We'll check enrollment and duplicate attendance after face recognition
        today = timezone.now().date()

        # Get face recognition service
        face_service = get_face_recognition_service()
        if not face_service or not face_service.available:
            return Response({
                'success': False,
                'message': 'Face recognition service not available. Please install DeepFace.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Save the captured image for attendance record
        def save_attendance_image(image_data, student_id, class_id):
            """Save the captured image during attendance marking"""
            try:
                import base64
                from io import BytesIO
                from PIL import Image
                from django.core.files.base import ContentFile
                from django.conf import settings
                import os

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
        face_service = get_face_recognition_service()
        if not face_service or not face_service.available:
            return Response({
                'success': False,
                'message': 'Face recognition service not available. Please install DeepFace.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        is_valid, message = face_service.validate_image_quality(image_data)

        return Response({
            'success': is_valid,
            'message': message
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error validating image: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error validating image: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
