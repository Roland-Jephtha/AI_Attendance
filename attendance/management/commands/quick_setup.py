from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from attendance.models import Student, Class
from django.db import transaction


class Command(BaseCommand):
    help = 'Quick setup for testing - creates sample classes and enrolls existing students'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Running quick setup...'))

        try:
            with transaction.atomic():
                # Create instructor if doesn't exist
                instructor, created = User.objects.get_or_create(
                    username='instructor',
                    defaults={
                        'email': 'instructor@school.edu',
                        'first_name': 'John',
                        'last_name': 'Teacher',
                        'is_staff': True,
                    }
                )
                if created:
                    instructor.set_password('instructor123')
                    instructor.save()
                    self.stdout.write(f'Created instructor: {instructor.username}')

                # Create sample classes
                sample_classes = [
                    ('CS101', 'Introduction to Computer Science'),
                    ('MATH201', 'Calculus I'),
                    ('ENG101', 'English Composition'),
                    ('PHYS101', 'General Physics'),
                ]

                created_classes = []
                for code, name in sample_classes:
                    class_obj, created = Class.objects.get_or_create(
                        code=code,
                        defaults={
                            'name': name,
                            'instructor': instructor,
                            'is_active': True
                        }
                    )
                    created_classes.append(class_obj)
                    if created:
                        self.stdout.write(f'Created class: {code} - {name}')

                # Get all active students
                students = Student.objects.filter(is_active=True)
                classes = Class.objects.filter(is_active=True)

                if students.exists() and classes.exists():
                    # Enroll all students in all classes
                    for student in students:
                        student.enrolled_classes.set(classes)
                        self.stdout.write(f'Enrolled {student.full_name} in all classes')
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully enrolled {students.count()} students in {classes.count()} classes'
                        )
                    )
                else:
                    if not students.exists():
                        self.stdout.write(self.style.WARNING('No students found. Please create student accounts first.'))
                    if not classes.exists():
                        self.stdout.write(self.style.WARNING('No classes created.'))

                # Show summary
                self.stdout.write('\n' + '='*50)
                self.stdout.write(self.style.SUCCESS('SETUP COMPLETE!'))
                self.stdout.write(f'Students: {Student.objects.filter(is_active=True).count()}')
                self.stdout.write(f'Classes: {Class.objects.filter(is_active=True).count()}')
                self.stdout.write('\nStudents can now:')
                self.stdout.write('1. Sign up at: http://localhost:8000/signup/')
                self.stdout.write('2. Register their face during signup')
                self.stdout.write('3. Mark attendance for their enrolled classes')
                self.stdout.write('='*50)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during setup: {str(e)}'))
            raise
