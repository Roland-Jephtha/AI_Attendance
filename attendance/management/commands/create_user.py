"""
Management command to create users with positions
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from attendance.models import Student, Class
from django.db import transaction


class Command(BaseCommand):
    help = 'Create users with specified positions (lecturer or student)'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='User email address')
        parser.add_argument('--password', type=str, required=True, help='User password')
        parser.add_argument('--first-name', type=str, required=True, help='First name')
        parser.add_argument('--last-name', type=str, required=True, help='Last name')
        parser.add_argument('--position', type=str, choices=['lecturer', 'student'], required=True, help='User position')
        parser.add_argument('--student-id', type=str, help='Student ID (required for students)')
        parser.add_argument('--phone', type=str, help='Phone number (for students)')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        position = options['position']
        student_id = options.get('student_id')
        phone = options.get('phone', '')

        # Validate inputs
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')

        if position == 'student' and not student_id:
            raise CommandError('Student ID is required for students')

        if position == 'student' and Student.objects.filter(student_id=student_id).exists():
            raise CommandError(f'Student with ID {student_id} already exists')

        try:
            with transaction.atomic():
                # Create Django user
                if position == 'lecturer':
                    # Use email as username for lecturers
                    username = email.split('@')[0]  # Use part before @ as username
                    is_staff = True
                else:
                    # Use student_id as username for students
                    username = student_id
                    is_staff = False

                # Ensure username is unique
                original_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff
                )

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created Django user: {user.username} ({email})')
                )

                # Create student record if needed
                if position == 'student':
                    student = Student.objects.create(
                        student_id=student_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        is_active=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created student record: {student.student_id}')
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
