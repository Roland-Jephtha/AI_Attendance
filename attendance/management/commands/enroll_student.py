from django.core.management.base import BaseCommand
from attendance.models import Student, Class
from django.db import transaction


class Command(BaseCommand):
    help = 'Enroll a student in classes'

    def add_arguments(self, parser):
        parser.add_argument('student_id', type=str, help='Student ID to enroll')
        parser.add_argument(
            '--classes',
            nargs='+',
            help='Class codes to enroll the student in (space-separated)',
            required=False
        )
        parser.add_argument(
            '--all-classes',
            action='store_true',
            help='Enroll student in all available classes',
        )

    def handle(self, *args, **options):
        student_id = options['student_id']
        class_codes = options.get('classes', [])
        enroll_all = options['all_classes']

        try:
            # Get the student
            student = Student.objects.get(student_id=student_id, is_active=True)
            self.stdout.write(f'Found student: {student.full_name} ({student.student_id})')

            if enroll_all:
                # Enroll in all classes
                classes = Class.objects.filter(is_active=True)
                if not classes.exists():
                    self.stdout.write(self.style.WARNING('No active classes found'))
                    return
                
                student.enrolled_classes.set(classes)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Enrolled {student.full_name} in all {classes.count()} classes'
                    )
                )
                
                # List the classes
                for class_obj in classes:
                    self.stdout.write(f'  - {class_obj.code}: {class_obj.name}')

            elif class_codes:
                # Enroll in specific classes
                enrolled_classes = []
                not_found_classes = []
                
                for class_code in class_codes:
                    try:
                        class_obj = Class.objects.get(code=class_code, is_active=True)
                        student.enrolled_classes.add(class_obj)
                        enrolled_classes.append(class_obj)
                        self.stdout.write(f'Enrolled in: {class_obj.code} - {class_obj.name}')
                    except Class.DoesNotExist:
                        not_found_classes.append(class_code)
                        self.stdout.write(self.style.WARNING(f'Class not found: {class_code}'))

                if enrolled_classes:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully enrolled {student.full_name} in {len(enrolled_classes)} classes'
                        )
                    )
                
                if not_found_classes:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Could not find classes: {", ".join(not_found_classes)}'
                        )
                    )

            else:
                # Show current enrollments and available classes
                current_classes = student.enrolled_classes.all()
                available_classes = Class.objects.filter(is_active=True).exclude(
                    id__in=current_classes.values_list('id', flat=True)
                )

                self.stdout.write(f'\nCurrent enrollments for {student.full_name}:')
                if current_classes.exists():
                    for class_obj in current_classes:
                        self.stdout.write(f'  - {class_obj.code}: {class_obj.name}')
                else:
                    self.stdout.write('  No current enrollments')

                self.stdout.write(f'\nAvailable classes to enroll in:')
                if available_classes.exists():
                    for class_obj in available_classes:
                        self.stdout.write(f'  - {class_obj.code}: {class_obj.name}')
                else:
                    self.stdout.write('  No available classes')

                self.stdout.write('\nUsage examples:')
                self.stdout.write(f'  python manage.py enroll_student {student_id} --classes CS101 MATH201')
                self.stdout.write(f'  python manage.py enroll_student {student_id} --all-classes')

        except Student.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Student not found: {student_id}'))
            
            # Show available students
            students = Student.objects.filter(is_active=True)[:10]
            if students.exists():
                self.stdout.write('\nAvailable students:')
                for student in students:
                    self.stdout.write(f'  - {student.student_id}: {student.full_name}')
            else:
                self.stdout.write('\nNo active students found')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error enrolling student: {str(e)}'))
            raise
