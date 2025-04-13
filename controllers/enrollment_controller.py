import re
from flask import request, jsonify, session, Blueprint
from services.supabase_service import upload_file_to_supabase
from supabase import create_client
import os
import logging
from flask import current_app as app

logger = logging.getLogger(__name__)

enrollment_bp = Blueprint("enrollment", __name__)

url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3ODE3NDIsImV4cCI6MjA1NzM1Nzc0Mn0.UxsVfpzvKRVAYi--ngdrogY3CjOiB9Yz60DeNTcvDa0"
supabase = create_client(url, key)

def upload_admission_docs():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Get form data
        enrollment_number = request.form.get("enrollment_number", "").strip()
        name = request.form.get("name", "").strip()

        if not enrollment_number:
            return jsonify({"error": "Enrollment number is required"}), 400

        # 1. First find student by exact enrollment number match
        student_query = supabase.table("students") \
            .select("*") \
            .eq("enrollment_number", enrollment_number) \
            .execute()
        
        logger.info(f"[DEBUG] Student query result: {student_query.data}")

        if not student_query.data:
            return jsonify({"error": "Student not found with this enrollment number"}), 404

        # 2. Check for existing admission
        duplicate_check = supabase.table("student_admissions") \
            .select("enrollment_number") \
            .eq("enrollment_number", enrollment_number) \
            .execute()
            
        if duplicate_check.data:
            return jsonify({"error": "Admission already submitted for this enrollment number"}), 409

        # 3. Validate all documents
        required_files = ["registration_form", "tenth_marksheet", 
                         "twelfth_marksheet", "gujcet_marksheet"]
        files = {key: request.files.get(key) for key in required_files}
        
        if any(not file for file in files.values()):
            return jsonify({"error": "All documents must be uploaded"}), 400

        # 4. Upload files
        file_urls = {}
        for file_key, file in files.items():
            filename = f"{enrollment_number}_{file_key}.pdf"
            file_urls[file_key] = upload_file_to_supabase(file, filename)

        # 5. Create admission record
        admission_data = {
            "enrollment_number": enrollment_number,
            "name": name,
            **file_urls
        }
        
        supabase.table("student_admissions").insert(admission_data).execute()

        return jsonify({"message": "Documents uploaded successfully"}), 200

    except Exception as e:
        logger.error(f"Admission upload error: {str(e)}", exc_info=True)
        return jsonify({"error": "Server error processing your request"}), 500

@enrollment_bp.route("/upload-documents", methods=["POST"])
def handle_upload():
    return upload_admission_docs()