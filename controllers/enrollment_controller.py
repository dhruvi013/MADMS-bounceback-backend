from flask import request, jsonify, session
from services.supabase_service import upload_file_to_supabase
from supabase import create_client
import os
import logging

logger = logging.getLogger(__name__)

url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3ODE3NDIsImV4cCI6MjA1NzM1Nzc0Mn0.UxsVfpzvKRVAYi--ngdrogY3CjOiB9Yz60DeNTcvDa0"
supabase = create_client(url, key)

def upload_admission_docs():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        student_id = request.form.get("student_id")
        academic_year = request.form.get("academic_year")

        # ✅ Check if student exists using student_id
        student_check = supabase.table("students").select("student_id").eq("student_id", student_id).execute()
        if not student_check.data:
            return jsonify({"error": "Student not found"}), 400

        # ✅ Check for duplicate admission
        admission_check = supabase.table("student_admissions").select("student_id").eq("student_id", student_id).execute()
        if admission_check.data:
            return jsonify({"error": "Admission already submitted"}), 409

        # ✅ Handle file uploads
        registration_form = request.files.get("registration_form")
        tenth = request.files.get("tenth_marksheet")
        twelfth = request.files.get("twelfth_marksheet")
        gujcet = request.files.get("gujcet_marksheet")

        reg_url = upload_file_to_supabase(registration_form, f"{student_id}_registration.pdf")
        tenth_url = upload_file_to_supabase(tenth, f"{student_id}_tenth.pdf")
        twelfth_url = upload_file_to_supabase(twelfth, f"{student_id}_twelfth.pdf")
        gujcet_url = upload_file_to_supabase(gujcet, f"{student_id}_gujcet.pdf")

        # ✅ Insert into database
        supabase.table("student_admissions").insert({
            "student_id": int(student_id),
            "registration_form": reg_url,
            "tenth_marksheet": tenth_url,
            "twelfth_marksheet": twelfth_url,
            "gujcet_marksheet": gujcet_url
        }).execute()

        return jsonify({"message": "Documents uploaded successfully"}), 200

    except Exception as e:
        logger.error(f"Admission upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500
