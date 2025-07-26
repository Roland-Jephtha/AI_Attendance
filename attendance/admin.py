from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import transaction
from django import forms
from .models import CustomUser, Student, Lecturer, Class, Attendance, FaceEncoding, AttendanceSession, Department, Level

User = get_user_model()


class CustomUserCreationForm(forms.ModelForm):
    """Custom user creation form"""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'position')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user




class CustomUserChangeForm(forms.ModelForm):
    """Custom user change form"""
    class Meta:
        model = User
        fields = '__all__'






@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Custom User admin with position management and email login"""

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ['email', 'username', 'first_name', 'last_name', 'position', 'is_active', 'date_joined']
    list_filter = ['position', 'is_active', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'student_id']
    ordering = ['email']

    # Fieldsets for editing existing users
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Position & Details', {'fields': ('position', 'student_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fieldsets for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'position', 'password1', 'password2'),
        }),
    )




@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    """Admin for Lecturer model"""
    list_display = ['user', 'employee_id', 'department', 'is_active']
    list_filter = ['department', 'is_active']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'employee_id']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Lecturer Details', {
            'fields': ('employee_id', 'department', 'office_location', 'specialization')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


admin.site.register(Department)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    """Admin for Level model"""
    list_display = ['name', 'code', 'description', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'user', 'department', 'level', 'semester', 'enrolled_classes_count', 'face_encodings_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'enrolled_classes', 'department', 'level', 'semester', 'year_of_study']
    search_fields = ['student_id', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at']
    filter_horizontal = ['enrolled_classes']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Student Details', {
            'fields': ('student_id', 'department', 'level', 'semester', 'year_of_study')
        }),
        ('Enrollment', {
            'fields': ('enrolled_classes',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def enrolled_classes_count(self, obj):
        return obj.enrolled_classes.count()
    enrolled_classes_count.short_description = 'Classes'

    def face_encodings_count(self, obj):
        count = obj.face_encodings.count()
        if count > 0:
            url = reverse('admin:attendance_faceencoding_changelist') + f'?student__id__exact={obj.id}'
            return format_html('<a href="{}">{} encodings</a>', url, count)
        return '0 encodings'
    face_encodings_count.short_description = 'Face Encodings'


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'instructor', 'students_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'instructor']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at']

    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = 'Students'


@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ['student', 'is_primary', 'image_preview', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']
    readonly_fields = ['created_at', 'encoding_data', 'image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return 'No image'
    image_preview.short_description = 'Preview'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_attended', 'date', 'status', 'recognition_confidence', 'marked_by_recognition', 'timestamp']
    list_filter = ['status', 'marked_by_recognition', 'date', 'class_attended']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name', 'class_attended__code']
    readonly_fields = ['timestamp']
    date_hierarchy = 'date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'class_attended')


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['class_session', 'date', 'attendance_rate_display', 'present_count', 'total_students', 'is_active', 'start_time']
    list_filter = ['is_active', 'date', 'class_session']
    search_fields = ['class_session__code', 'class_session__name']
    readonly_fields = ['start_time', 'end_time', 'attendance_rate']
    date_hierarchy = 'date'

    def attendance_rate_display(self, obj):
        rate = obj.attendance_rate
        if rate >= 80:
            color = 'green'
        elif rate >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    attendance_rate_display.short_description = 'Attendance Rate'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('class_session', 'created_by')


# Customize admin site
admin.site.site_header = 'AI Attendance System Administration'
admin.site.site_title = 'AI Attendance Admin'
admin.site.index_title = 'Welcome to AI Attendance System Administration'
