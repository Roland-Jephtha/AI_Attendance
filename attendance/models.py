from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import os


class CustomUser(AbstractUser):
    """Custom User model with position field"""

    POSITION_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
    ]

    position = models.CharField(
        max_length=10,
        choices=POSITION_CHOICES,
        default='student',
        help_text='User position in the system'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_position_display()})"

    def save(self, *args, **kwargs):
        # Set is_staff based on position
        if self.position == 'lecturer':
            self.is_staff = True
        else:
            self.is_staff = False

        # Auto-generate student_id for students if not provided
        if self.position == 'student' and not self.student_id:
            # Generate student ID based on username or email
            base_id = self.username or self.email.split('@')[0] if self.email else 'STU'
            self.student_id = base_id.upper()

        super().save(*args, **kwargs)

    @property
    def is_lecturer(self):
        return self.position == 'lecturer'

    @property
    def is_student(self):
        return self.position == 'student'

    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username']




class Department(models.Model):
    """Model for departments"""
    name = models.CharField(max_length=100, unique=True, null = True)
    description = models.TextField(blank=True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Departments"
        ordering = ['name']

    def __str__(self):
        return self.name


class Level(models.Model):
    """Model for academic levels (e.g., 100, 200, 300, 400)"""
    name = models.CharField(max_length=50, unique=True)  # e.g., "100 Level", "200 Level"
    code = models.CharField(max_length=10, unique=True)  # e.g., "100", "200"
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.name




class Lecturer(models.Model):
    """Model for lecturer-specific information"""
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='lecturer_profile')
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    office_location = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.department}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username


class Class(models.Model):
    """Model for different classes/courses"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='taught_classes', limit_choices_to={'position': 'lecturer'})
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Student(models.Model):
    """Model for student-specific information"""
    SEMESTER_CHOICES = [
        ('1', 'First Semester'),
        ('2', 'Second Semester'),
    ]

    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, related_name='student_profile', null = True)
    student_id = models.CharField(max_length=20, unique=True)
    enrolled_classes = models.ManyToManyField(Class, related_name='students', blank=True)
    year_of_study = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    semester = models.CharField(max_length=1, choices=SEMESTER_CHOICES, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name() or self.user.username}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    @property
    def phone(self):
        return self.user.phone


def face_image_upload_path(instance, filename):
    """Generate upload path for face images"""
    return f'face_images/{instance.student.student_id}/{filename}'


class FaceEncoding(models.Model):
    """Model to store face encodings for students"""
    DETECTION_STATUS_CHOICES = [
        ('success', 'Success'),
        ('no_face', 'No Face Detected'),
        ('error', 'Error'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='face_encodings')
    image = models.ImageField(upload_to=face_image_upload_path)
    encoding_data = models.TextField(blank=True, null=True)  # JSON string of face encoding
    is_primary = models.BooleanField(default=False)
    detection_status = models.CharField(max_length=20, choices=DETECTION_STATUS_CHOICES, default='success')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"Face encoding for {self.student.full_name} ({self.detection_status})"

    def delete(self, *args, **kwargs):
        # Delete the image file when the model instance is deleted
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)


class Attendance(models.Model):
    """Model to track attendance records"""
    ATTENDANCE_STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records', null = True)
    class_attended = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS_CHOICES, default='present')
    recognition_confidence = models.FloatField(null=True, blank=True)
    marked_by_recognition = models.BooleanField(default=True)
    attendance_image = models.CharField(max_length=255, blank=True, null=True, help_text="Filename of captured attendance image")
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['student', 'class_attended', 'date']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.student.full_name} - {self.class_attended.code} - {self.date} ({self.status})"

    @property
    def success_status(self):
        """Return success status for frontend"""
        return self.status == 'present'


class AttendanceSession(models.Model):
    """Model to track attendance taking sessions"""
    class_session = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_sessions')
    date = models.DateField(default=timezone.now)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    total_students = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    created_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='created_sessions')

    class Meta:
        unique_together = ['class_session', 'date']
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.class_session.code} - {self.date}"

    def end_session(self):
        """End the attendance session"""
        self.end_time = timezone.now()
        self.is_active = False
        self.save()

    @property
    def attendance_rate(self):
        """Calculate attendance rate as percentage"""
        if self.total_students == 0:
            return 0
        return round((self.present_count / self.total_students) * 100, 2)

    def __str__(self):
        return f"{self.class_session.code} - {self.date} ({self.present_count}/{self.total_students})"


# Signal handlers to automatically create Student/Lecturer records
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create Student or Lecturer profile when CustomUser is created"""
    if created:
        if instance.position == 'student':
            # Create Student record
            Student.objects.create(
                user=instance,
                student_id=instance.student_id or instance.username,
                is_active=True
            )
            print(f"✅ Created Student profile for {instance.username}")

        elif instance.position == 'lecturer':
            # Create Lecturer record
            Lecturer.objects.create(
                user=instance,
                employee_id=instance.username,
                is_active=True
            )
            print(f"✅ Created Lecturer profile for {instance.username}")





@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Update Student or Lecturer profile when CustomUser is saved"""
    if instance.position == 'student':
        # Update or create Student record
        obj, created = Student.objects.get_or_create(
            user=instance,
            defaults={
                'student_id': instance.student_id or instance.username,
                'is_active': True
            }
        )
        if not created and obj:
            obj.student_id = instance.student_id or instance.username
            obj.is_active = True
            obj.save()

    elif instance.position == 'lecturer':
        # Update or create Lecturer record
        obj, created = Lecturer.objects.get_or_create(
            user=instance,
            defaults={
                'employee_id': instance.username,
                'is_active': True
            }
        )
        if not created and obj:
            obj.employee_id = instance.username
            obj.is_active = True
            obj.save()
