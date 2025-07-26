from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from attendance.models import Student, Class
from django.db import transaction


class Command(BaseCommand):
    help = 'Set up sample data for the attendance system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enroll-all',
            action='store_true',
            help='Enroll all existing students in all existing classes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up sample data...'))

        try:
            with transaction.atomic():
                # Create sample instructor if doesn't exist
                instructor, created = User.objects.get_or_create(
                    username='instructor1',
                    defaults={
                        'email': 'instructor@example.com',
                        'first_name': 'John',
                        'last_name': 'Instructor',
                        'is_staff': True,
                    }
                )
                if created:
                    instructor.set_password('instructor123')
                    instructor.save()
                    self.stdout.write(f'Created instructor: {instructor.username}')

                # Create sample classes if they don't exist
                sample_classes = [
                    {
                        'code': 'CS101',
                        'name': 'Introduction to Computer Science',
                        'description': 'Basic concepts of computer science and programming'
                    },
                    {
                        'code': 'MATH201',
                        'name': 'Calculus I',
                        'description': 'Differential and integral calculus'
                    },
                    {
                        'code': 'ENG101',
                        'name': 'English Composition',
                        'description': 'Academic writing and communication skills'
                    },
                    {
                        'code': 'PHYS101',
                        'name': 'General Physics',
                        'description': 'Mechanics, thermodynamics, and waves'
                    }
                ]

                created_classes = []
                for class_data in sample_classes:
                    class_obj, created = Class.objects.get_or_create(
                        code=class_data['code'],
                        defaults={
                            'name': class_data['name'],
                            'description': class_data['description'],
                            'instructor': instructor,
                            'is_active': True
                        }
                    )
                    created_classes.append(class_obj)
                    if created:
                        self.stdout.write(f'Created class: {class_obj.code} - {class_obj.name}')
                    else:
                        self.stdout.write(f'Class already exists: {class_obj.code}')

                # If --enroll-all flag is used, enroll all students in all classes
                if options['enroll_all']:
                    students = Student.objects.filter(is_active=True)
                    classes = Class.objects.filter(is_active=True)
                    
                    if not students.exists():
                        self.stdout.write(self.style.WARNING('No students found to enroll'))
                    elif not classes.exists():
                        self.stdout.write(self.style.WARNING('No classes found for enrollment'))
                    else:
                        for student in students:
                            # Enroll student in all classes
                            student.enrolled_classes.set(classes)
                            self.stdout.write(f'Enrolled {student.full_name} in all classes')
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully enrolled {students.count()} students in {classes.count()} classes'
                            )
                        )

                # Show current status
                total_students = Student.objects.filter(is_active=True).count()
                total_classes = Class.objects.filter(is_active=True).count()
                
                self.stdout.write('\n' + '='*50)
                self.stdout.write(self.style.SUCCESS('CURRENT STATUS:'))
                self.stdout.write(f'Total Students: {total_students}')
                self.stdout.write(f'Total Classes: {total_classes}')
                
                if total_students > 0:
                    self.stdout.write('\nStudents:')
                    for student in Student.objects.filter(is_active=True)[:10]:  # Show first 10
                        enrolled_count = student.enrolled_classes.count()
                        self.stdout.write(f'  - {student.full_name} ({student.student_id}) - {enrolled_count} classes')
                
                if total_classes > 0:
                    self.stdout.write('\nClasses:')
                    for class_obj in Class.objects.filter(is_active=True):
                        student_count = class_obj.students.count()
                        self.stdout.write(f'  - {class_obj.code}: {class_obj.name} - {student_count} students')

                self.stdout.write('\n' + '='*50)
                self.stdout.write(self.style.SUCCESS('Setup completed successfully!'))
                
                if not options['enroll_all'] and total_students > 0:
                    self.stdout.write('\nTo enroll all students in all classes, run:')
                    self.stdout.write('python manage.py setup_sample_data --enroll-all')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up sample data: {str(e)}'))
            raise
