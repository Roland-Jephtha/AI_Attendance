from django.urls import path
from . import views

urlpatterns = [
    # Student Authentication
    path('', views.student_login, name='student_login'),
    path('login/', views.student_login, name='student_login'),
    path('signup/', views.student_signup, name='student_signup'),
    path('debug-signup/', views.debug_signup, name='debug_signup'),
    path('simple-test/', views.simple_test, name='simple_test'),
    path('minimal-signup/', views.minimal_signup, name='minimal_signup'),
    path('diagnostic/', views.diagnostic, name='diagnostic'),
    path('signup-success/', views.signup_success, name='signup_success'),
    path('logout/', views.student_logout, name='student_logout'),

    # Lecturer Dashboard
    path('lecturer/dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/attendance-history/', views.lecturer_attendance_history, name='lecturer_attendance_history'),
    path('lecturer/attendance/<int:class_id>/', views.lecturer_attendance_session, name='lecturer_attendance_session'),

    # Student Dashboard
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('attendance-history/', views.student_attendance_history, name='student_attendance_history'),
    path('enroll-face/', views.student_face_enrollment, name='student_face_enrollment'),
    path('enroll-class/<int:class_id>/', views.enroll_in_class, name='enroll_in_class'),
    path('unenroll-class/<int:class_id>/', views.unenroll_from_class, name='unenroll_from_class'),

    # Admin URLs (for staff/instructors)
    path('admin-dashboard/', views.dashboard, name='admin_dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/register/', views.student_register, name='student_register'),
    path('students/<str:student_id>/', views.student_detail, name='student_detail'),
    path('students/<str:student_id>/enroll-face/', views.face_enrollment, name='face_enrollment'),

    # Class URLs
    path('classes/', views.class_list, name='class_list'),
    path('classes/<int:class_id>/', views.class_detail, name='class_detail'),
    path('classes/<int:class_id>/attendance/', views.take_attendance, name='take_attendance'),
    path('classes/<int:class_id>/history/', views.attendance_history, name='class_attendance_history'),

    # Attendance URLs
    path('attendance/history/', views.attendance_history, name='attendance_history'),

    # API URLs
    path('api/recognize-face/', views.api_recognize_face, name='api_recognize_face'),
    path('api/validate-image/', views.api_validate_image, name='api_validate_image'),
    path('api/attendance-status/<int:class_id>/', views.api_attendance_status, name='api_attendance_status'),
]
