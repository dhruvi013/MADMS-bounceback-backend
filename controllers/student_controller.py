from flask import Blueprint, request, jsonify, session
from models.students import Student
from database.db import SessionLocal

student_bp = Blueprint('student', __name__)

@student_bp.route('/student', methods=['POST'])
def add_student():
    if 'user' not in session:  # Changed from 'user_id' to 'user' to match app.py
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    db = SessionLocal()
    try:
        student = Student(
            name=data['name'],
            enrollment_number=data['enrollment_number'],
            student_type=data['student_type'],
            batch_period=data['batch_period'],
            gr_no=data['gr_no']
        )
        db.add(student)
        db.commit()
        return jsonify({"message": "Student added successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
