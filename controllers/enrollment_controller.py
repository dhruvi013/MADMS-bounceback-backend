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
    # CORS headers are now handled in the app.py route handler
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        enrollment_number = request.form.get("enrollment_number")
        name = request.form.get("name")  # ✅ New field for renamed column

        if not enrollment_number:
            return jsonify({"error": "Missing enrollment_number"}), 400

        enrollment_number = enrollment_number.strip()
        if not enrollment_number:
            return jsonify({"error": "Enrollment number is required"}), 400

        # ✅ Check if student exists
        student_check = supabase.table("students").select("enrollment_number").eq("enrollment_number", enrollment_number).execute()
        if not student_check.data:
            return jsonify({"error": "Student not found"}), 400

        # ✅ Check for duplicate admission
        print(f"[DEBUG] enrollment_number received: '{enrollment_number}'")
        student_check = supabase.table("students").select("enrollment_number").eq("enrollment_number", enrollment_number).execute()
        print(f"[DEBUG] Supabase query result: {student_check.data}")
        if student_check.data:
            return jsonify({"error": "Admission already submitted"}), 409

        # ✅ Handle file uploads
        registration_form = request.files.get("registration_form")
        tenth = request.files.get("tenth_marksheet")
        twelfth = request.files.get("twelfth_marksheet")
        gujcet = request.files.get("gujcet_marksheet")

        if not all([registration_form, tenth, twelfth, gujcet]):
            return jsonify({"error": "All documents must be uploaded"}), 400

        reg_url = upload_file_to_supabase(registration_form, f"{enrollment_number}_registration.pdf")
        tenth_url = upload_file_to_supabase(tenth, f"{enrollment_number}_tenth.pdf")
        twelfth_url = upload_file_to_supabase(twelfth, f"{enrollment_number}_twelfth.pdf")
        gujcet_url = upload_file_to_supabase(gujcet, f"{enrollment_number}_gujcet.pdf")
        logger.info("enrollment_number", enrollment_number,
            "name", name,  # fallback if name not provided
            "registration_form",reg_url,
            "tenth_marksheet", tenth_url,
            "twelfth_marksheet", twelfth_url,
            "gujcet_marksheet", gujcet_url
)
        # ✅ Insert into Supabase
        supabase.table("student_admissions").insert({
            "enrollment_number": enrollment_number,
            "name": name or "2024-2025",  # fallback if name not provided
            "registration_form": reg_url,
            "tenth_marksheet": tenth_url,
            "twelfth_marksheet": twelfth_url,
            "gujcet_marksheet": gujcet_url
        }).execute()

        return jsonify({"message": "Documents uploaded successfully"}), 200

    except Exception as e:
        logger.error(f"Admission upload error: {str(e)}")
        return jsonify({"error": "Something went wrong on the server"}), 500

@enrollment_bp.route("/upload-documents", methods=["POST"])
def handle_upload():
    return upload_admission_docs()
