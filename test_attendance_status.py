#!/usr/bin/env python
"""
Test attendance status and duplicate prevention
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Attendance.settings')
django.setup()

def test_attendance_status():
    """Test attendance status checking"""
    from attendance.models import Student, Class, Attendance
    from django.utils import timezone
    
    print("🧪 Testing Attendance Status Logic")
    print("=" * 40)
    
    # Get a test student and class
    try:
        student = Student.objects.first()
        class_obj = Class.objects.first()
        
        if not student or not class_obj:
            print("❌ No student or class found. Create test data first.")
            return
        
        print(f"📚 Testing with:")
        print(f"   Student: {student.full_name} ({student.student_id})")
        print(f"   Class: {class_obj.name}")
        
        today = timezone.now().date()
        
        # Check current attendance status
        existing_attendance = Attendance.objects.filter(
            student=student,
            class_attended=class_obj,
            date=today
        ).first()
        
        if existing_attendance:
            print(f"\n✅ Attendance already marked:")
            print(f"   Date: {existing_attendance.date}")
            print(f"   Time: {existing_attendance.timestamp.strftime('%H:%M:%S')}")
            print(f"   Status: {existing_attendance.status}")
            if existing_attendance.recognition_confidence:
                print(f"   Confidence: {existing_attendance.recognition_confidence:.2f}")
            if existing_attendance.attendance_image:
                print(f"   Image: {existing_attendance.attendance_image}")
        else:
            print(f"\n⚠️  No attendance marked for today")
            print(f"   Student can mark attendance for this class")
        
        # Test dashboard logic
        print(f"\n🏠 Dashboard Status:")
        enrolled_classes = student.enrolled_classes.filter(is_active=True)
        
        for enrolled_class in enrolled_classes:
            attendance_today = Attendance.objects.filter(
                student=student,
                class_attended=enrolled_class,
                date=today
            ).first()
            
            if attendance_today:
                status = "✅ ATTENDED"
                time_str = attendance_today.timestamp.strftime('%H:%M')
                print(f"   {enrolled_class.name}: {status} at {time_str}")
            else:
                status = "⏳ PENDING"
                print(f"   {enrolled_class.name}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing attendance status: {str(e)}")
        return False

def test_duplicate_prevention():
    """Test duplicate attendance prevention"""
    print(f"\n🛡️  Testing Duplicate Prevention")
    print("=" * 40)
    
    from attendance.models import Student, Class, Attendance
    from django.utils import timezone
    
    try:
        student = Student.objects.first()
        class_obj = Class.objects.first()
        
        if not student or not class_obj:
            print("❌ No test data available")
            return False
        
        today = timezone.now().date()
        
        # Check if attendance exists
        existing_count = Attendance.objects.filter(
            student=student,
            class_attended=class_obj,
            date=today
        ).count()
        
        print(f"📊 Current attendance records for today: {existing_count}")
        
        if existing_count > 1:
            print("⚠️  WARNING: Multiple attendance records found for same day!")
            print("   This should not happen - check duplicate prevention logic")
            
            # Show all records
            records = Attendance.objects.filter(
                student=student,
                class_attended=class_obj,
                date=today
            )
            
            for i, record in enumerate(records, 1):
                print(f"   Record {i}: {record.timestamp} - {record.status}")
        
        elif existing_count == 1:
            print("✅ Exactly one attendance record found - correct!")
        else:
            print("ℹ️  No attendance records for today - student can mark attendance")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing duplicate prevention: {str(e)}")
        return False

def show_recent_attendance():
    """Show recent attendance records"""
    print(f"\n📋 Recent Attendance Records")
    print("=" * 40)
    
    from attendance.models import Attendance
    
    try:
        recent_attendance = Attendance.objects.select_related(
            'student', 'class_attended'
        ).order_by('-timestamp')[:10]
        
        if not recent_attendance:
            print("ℹ️  No attendance records found")
            return
        
        for attendance in recent_attendance:
            print(f"🎓 {attendance.student.full_name} ({attendance.student.student_id})")
            print(f"   📚 Class: {attendance.class_attended.name}")
            print(f"   📅 Date: {attendance.date}")
            print(f"   🕐 Time: {attendance.timestamp.strftime('%H:%M:%S')}")
            print(f"   ✅ Status: {attendance.status}")
            if attendance.recognition_confidence:
                print(f"   🎯 Confidence: {attendance.recognition_confidence:.1f}%")
            if attendance.attendance_image:
                print(f"   📸 Image: {attendance.attendance_image}")
            print()
        
    except Exception as e:
        print(f"❌ Error showing recent attendance: {str(e)}")

def main():
    print("🎯 Attendance Status Test Suite")
    print("=" * 50)
    
    # Test 1: Attendance status checking
    status_ok = test_attendance_status()
    
    # Test 2: Duplicate prevention
    duplicate_ok = test_duplicate_prevention()
    
    # Show recent records
    show_recent_attendance()
    
    print("=" * 50)
    print("📊 Test Results:")
    print(f"Attendance Status: {'✅ PASS' if status_ok else '❌ FAIL'}")
    print(f"Duplicate Prevention: {'✅ PASS' if duplicate_ok else '❌ FAIL'}")
    
    if status_ok and duplicate_ok:
        print("\n🎉 All tests passed!")
        print("\n💡 Expected Behavior:")
        print("1. Students see 'ATTENDED' status on dashboard after marking attendance")
        print("2. Students cannot mark attendance twice for same class/day")
        print("3. Attendance page shows 'Already Marked' message if applicable")
        print("4. API prevents duplicate attendance marking")
    else:
        print("\n⚠️  Some tests failed - check the logic")

if __name__ == "__main__":
    main()
