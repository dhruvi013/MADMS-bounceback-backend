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


# @student_bp.route('/student/search', methods=['GET', 'OPTIONS'])
# def search_students():
#     if request.method == 'OPTIONS':
#         # Preflight request, send back the CORS headers
#         response = jsonify({'message': 'CORS preflight success'})
#         origin = request.headers.get('Origin', '')
#         if origin in ['http://localhost:8080', 'https://madms-assistant.vercel.app']:
#             response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#         response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
#         return response, 200

#     if 'user' not in session:
#         print("❌ Unauthorized access to search")
#         return jsonify({'error': 'Unauthorized'}), 401

#     query = request.args.get('q', '').strip().lower()
#     print("🔍 Searching students with query:", query)
#     db = SessionLocal()
#     try:
#         if query.isdigit():
#             # Only search and fetch enrollment_number
#             results = db.query(Student.enrollment_number).filter(
#                 Student.enrollment_number.ilike(f'{query}%')
#             ).all()
#         else:
#             # Name queries are ignored as per your new requirement
#             results = []

#         print(f"✅ Found {len(results)} enrollment numbers")
#         enrollment_list = [{'enrollment_number': r.enrollment_number} for r in results]
#         return jsonify(enrollment_list), 200
#     except Exception as e:
#         print("💥 Error in search_students:", e)
#         traceback.print_exc()
#         return jsonify({'error': str(e)}), 500
#     finally:
#         db.close()

@student_bp.route('/student/search', methods=['GET', 'OPTIONS'])
def search_students():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight success'})
        origin = request.headers.get('Origin', '')
        if origin in ['http://localhost:8080', 'https://madms-assistant.vercel.app']:
            response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response, 200

    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('q', '').strip().lower()
    db = SessionLocal()
    try:
        # Only search and fetch enrollment_number
        results = db.query(Student.enrollment_number).filter(
        Student.enrollment_number.ilike(f'{query}%')
        ).all()

        enrollment_list = [{'enrollment_number': r.enrollment_number} for r in results]
        return jsonify(enrollment_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
