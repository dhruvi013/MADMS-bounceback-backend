from flask import Blueprint, request, jsonify, session
from models.students import Student
from database.db import SessionLocal
import traceback  # add at the top if not already

student_bp = Blueprint('student', __name__)

@student_bp.route('/student', methods=['POST'])
def add_student():
    if 'user' not in session:  # Changed from 'user_id' to 'user' to match app.py
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    db = SessionLocal()
    try:
        student = Student(
            name=data.get('name', ''),
            enrollment_number=data.get('enrollment_number', ''),
            student_type=data.get('student_type', ''),
            batch_period=data.get('batch_period', ''),
            gr_no=data.get('gr_no', ''),
            pcm=data.get('pcm', ''),
            tenth=data.get('tenth', ''),
            twelfth=data.get('twelfth', ''),
            acpc=data.get('acpc', ''),
            admission_quota=data.get('admission_quota', ''),
            nationality=data.get('nationality', ''),
            gender=data.get('gender', '')
        )
        db.add(student)
        db.commit()
        return jsonify({"message": "Student added successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()



@student_bp.route('/student/search', methods=['GET'])
def search_students():
    if 'user' not in session:
        print("❌ Unauthorized access to search")
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('q', '').strip().lower()
    print("🔍 Searching students with query:", query)
    db = SessionLocal()
    try:
        students = db.query(Student).filter(
            (Student.name.ilike(f'{query}%')) | 
            (Student.enrollment_number.ilike(f'{query}%'))
        ).all()

        print(f"✅ Found {len(students)} students")
        results = [
            {
                'name': student.name,
                'enrollment_number': student.enrollment_number
            } for student in students
        ]
        return jsonify(results), 200
    except Exception as e:
        print("💥 Error in search_students:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
