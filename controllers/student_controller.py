from flask import Blueprint, request, jsonify, session
from models.students import Student
from database.db import SessionLocal
import traceback  # add at the top if not already

student_bp = Blueprint('student', __name__)

@student_bp.route('/submit-form', methods=['POST', 'OPTIONS'])
def submit_form():
    if request.method == 'OPTIONS':
        # Preflight request, send back the CORS headers
        response = jsonify({'message': 'CORS preflight success'})
        # Get the origin from the request
        origin = request.headers.get('Origin', '')
        # Allow both localhost and production domains
        if origin in ['http://localhost:8080', 'https://madms-assistant.vercel.app']:
            response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response, 200

    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    db = SessionLocal()

    try:
        students = []
        for item in data:
            student = Student(
                name=item.get('name', ''),
                enrollment_number=item.get('enrollment_number', ''),
                student_type=item.get('student_type', ''),
                batch_period=item.get('batch_period', ''),
                gr_no=item.get('gr_no', ''),
                pcm=item.get('pcm', ''),
                tenth=item.get('tenth', ''),
                twelfth=item.get('twelfth', ''),
                acpc=item.get('acpc', ''),
                admission_quota=item.get('admission_quota', ''),
                nationality=item.get('nationality', ''),
                gender=item.get('gender', ''),
            )
            students.append(student)

        db.bulk_save_objects(students)
        db.commit()

        return jsonify({'message': f'{len(students)} students added successfully'}), 200

    except Exception as e:
        db.rollback()
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

    finally:
        db.close()


@student_bp.route('/student/search', methods=['GET', 'OPTIONS'])
def search_students():
    if request.method == 'OPTIONS':
        # Preflight request, send back the CORS headers
        response = jsonify({'message': 'CORS preflight success'})
        # Get the origin from the request
        origin = request.headers.get('Origin', '')
        # Allow both localhost and production domains
        if origin in ['http://localhost:8080', 'https://madms-assistant.vercel.app']:
            response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response, 200

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
