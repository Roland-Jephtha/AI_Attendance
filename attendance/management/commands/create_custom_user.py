"""
Management command to create users with the custom user model
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from attendance.models import Student, Lecturer, Class
from django.db import transaction


class Command(BaseCommand):
    help = 'Create users with the custom user model'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='User email address')
        parser.add_argument('--password', type=str, required=True, help='User password')
        parser.add_argument('--first-name', type=str, required=True, help='First name')
        parser.add_argument('--last-name', type=str, required=True, help='Last name')
        parser.add_argument('--position', type=str, choices=['lecturer', 'student'], required=True, help='User position')
        parser.add_argument('--student-id', type=str, help='Student ID (for students)')
        parser.add_argument('--phone', type=str, help='Phone number')
        parser.add_argument('--department', type=str, help='Department (for lecturers)')

    def handle(self, *args, **options):
        User = get_user_model()
        
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        position = options['position']
        student_id = options.get('student_id')
        phone = options.get('phone', '')
        department = options.get('department', '')

        # Validate inputs
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')

        if position == 'student' and not student_id:
            # Auto-generate student ID if not provided
            student_id = email.split('@')[0].upper()

        try:
            with transaction.atomic():
                # Create username from email
                username = email.split('@')[0]
                
                # Ensure username is unique
                original_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1

                # Create CustomUser
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    position=position,
                    phone=phone,
                    student_id=student_id if position == 'student' else None
                )

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created user: {user.username} ({email})')
                )

                # The signal handlers should automatically create Student/Lecturer records
                if position == 'student':
                    try:
                        student = Student.objects.get(user=user)
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Student profile created: {student.student_id}')
                        )
                    except Student.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING('⚠️  Student profile not created automatically')
                        )

                elif position == 'lecturer':
                    try:
                        lecturer = Lecturer.objects.get(user=user)
                        if department:
                            lecturer.department = department
                            lecturer.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Lecturer profile created: {lecturer.employee_id}')
                        )
                    except Lecturer.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING('⚠️  Lecturer profile not created automatically')
                        )

                # Show login information
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 User created successfully!')
                )
                self.stdout.write(f'Position: {position.title()}')
                self.stdout.write(f'Login Email: {email}')
                self.stdout.write(f'Password: {password}')
                
                if position == 'lecturer':
                    self.stdout.write(f'Dashboard: /lecturer/dashboard/')
                else:
                    self.stdout.write(f'Dashboard: /dashboard/')
                    self.stdout.write(f'Student ID: {student_id}')

        except Exception as e:
            raise CommandError(f'Error creating user: {str(e)}')
