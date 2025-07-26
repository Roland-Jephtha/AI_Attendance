# Attendance Timeout Setup

This document explains how to set up automatic attendance timeout functionality that resets attendance records after 15 hours.

## Overview

The system includes a management command that automatically removes attendance records that are older than 15 hours. This ensures that students cannot mark attendance too far in advance and that attendance records remain current.

## Management Command

### Basic Usage

```bash
# Reset attendance records older than 15 hours (default)
python manage.py reset_expired_attendance

# Reset attendance records older than a custom number of hours
python manage.py reset_expired_attendance --hours 12

# Dry run to see what would be reset without actually doing it
python manage.py reset_expired_attendance --dry-run
```

### Command Options

- `--hours`: Number of hours after which attendance should be reset (default: 15)
- `--dry-run`: Show what would be reset without actually doing it

## Automated Scheduling

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to run daily or every few hours
4. Set action to run the command:
   ```
   Program: python
   Arguments: manage.py reset_expired_attendance
   Start in: C:\Users\Jeph\Desktop\AI_Attendance
   ```

### Linux/Mac (Cron Job)

Add to crontab (`crontab -e`):

```bash
# Run every 4 hours
0 */4 * * * cd /path/to/AI_Attendance && python manage.py reset_expired_attendance

# Run daily at 2 AM
0 2 * * * cd /path/to/AI_Attendance && python manage.py reset_expired_attendance
```

### Django-Crontab (Recommended for Django projects)

1. Install django-crontab:
   ```bash
   pip install django-crontab
   ```

2. Add to INSTALLED_APPS in settings.py:
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'django_crontab',
   ]
   ```

3. Add to settings.py:
   ```python
   CRONJOBS = [
       ('0 */4 * * *', 'attendance.management.commands.reset_expired_attendance.Command'),
   ]
   ```

4. Install the cron job:
   ```bash
   python manage.py crontab add
   ```

## How It Works

1. The command finds all attendance records with timestamps older than the specified hours
2. It only affects records with status 'present' or 'late' (not 'absent')
3. The records are completely removed from the database
4. This allows students to mark attendance again for the same class on the same day

## Logging

The command provides detailed output about what it's doing:
- Number of records found
- Number of records reset
- In dry-run mode, shows which records would be affected

## Best Practices

1. Run the command regularly (every 4-6 hours) to keep attendance current
2. Use dry-run mode first to verify the command works as expected
3. Monitor the logs to ensure the command is running successfully
4. Consider running it during low-traffic hours to minimize database impact

## Troubleshooting

If the command fails:
1. Check database connectivity
2. Ensure the Django environment is properly set up
3. Verify file permissions
4. Check the Django logs for detailed error messages
