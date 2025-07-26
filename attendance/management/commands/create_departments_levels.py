from django.core.management.base import BaseCommand
from attendance.models import Department, Level


class Command(BaseCommand):
    help = 'Create sample departments and levels for the attendance system'

    def handle(self, *args, **options):
        # Create Departments
        departments_data = [
            {
                'name': 'Computer Science',
                'description': 'Department of Computer Science and Information Technology'
            },
            {
                'name': 'Engineering',
                'description': 'Department of Engineering and Applied Sciences'
            },
            {
                'name': 'Business Administration',
                'description': 'Department of Business Administration and Management'
            },
            {
                'name': 'Mathematics',
                'description': 'Department of Mathematics and Statistics'
            },
            {
                'name': 'Physics',
                'description': 'Department of Physics and Applied Physics'
            },
            {
                'name': 'Chemistry',
                'description': 'Department of Chemistry and Chemical Sciences'
            },
            {
                'name': 'Biology',
                'description': 'Department of Biology and Life Sciences'
            },
            {
                'name': 'Economics',
                'description': 'Department of Economics and Finance'
            },
            {
                'name': 'Psychology',
                'description': 'Department of Psychology and Behavioral Sciences'
            },
            {
                'name': 'English',
                'description': 'Department of English Language and Literature'
            }
        ]

        departments_created = 0
        for dept_data in departments_data:
            department, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'description': dept_data['description']}
            )
            if created:
                departments_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created department: {department.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Department already exists: {department.name}')
                )

        # Create Levels
        levels_data = [
            {
                'name': '100 Level',
                'code': '100',
                'description': 'First year undergraduate level'
            },
            {
                'name': '200 Level',
                'code': '200',
                'description': 'Second year undergraduate level'
            },
            {
                'name': '300 Level',
                'code': '300',
                'description': 'Third year undergraduate level'
            },
            {
                'name': '400 Level',
                'code': '400',
                'description': 'Fourth year undergraduate level'
            },
            {
                'name': '500 Level',
                'code': '500',
                'description': 'Fifth year undergraduate level'
            },
            {
                'name': 'Masters Level',
                'code': 'MSC',
                'description': 'Masters degree level'
            },
            {
                'name': 'PhD Level',
                'code': 'PHD',
                'description': 'Doctoral degree level'
            }
        ]

        levels_created = 0
        for level_data in levels_data:
            level, created = Level.objects.get_or_create(
                code=level_data['code'],
                defaults={
                    'name': level_data['name'],
                    'description': level_data['description']
                }
            )
            if created:
                levels_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created level: {level.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Level already exists: {level.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {departments_created} departments and {levels_created} levels'
            )
        )
