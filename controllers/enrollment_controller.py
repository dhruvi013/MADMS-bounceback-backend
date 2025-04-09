from flask import request, jsonify
from services.supabase_service import upload_file_to_supabase
from supabase import create_client
import os

url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWp"
supabase = create_client(url, key)

def upload_admission_docs():
    student_id = request.form.get("student_id")
    academic_year = request.form.get("academic_year")

    # ✅ Check if student exists using student_id (not id)
    exists = supabase.table("students").select("student_id").eq("student_id", student_id).execute()
    if not exists.data:
        return jsonify({"error": "Student not found"}), 400

    # ✅ Check if admission record already exists
    admission_exists = supabase.table("student_admissions").select("student_id").eq("student_id", student_id).execute()
    if admission_exists.data:
        return jsonify({"error": "Admission already submitted"}), 409

    # ✅ Handle files
    registration_form = request.files.get("registration_form")
    tenth = request.files.get("tenth_marksheet")
    twelfth = request.files.get("twelfth_marksheet")
    gujcet = request.files.get("gujcet_marksheet")

    try:
        reg_url = upload_file_to_supabase(registration_form, f"{student_id}_registration.pdf")
        tenth_url = upload_file_to_supabase(tenth, f"{student_id}_tenth.pdf")
        twelfth_url = upload_file_to_supabase(twelfth, f"{student_id}_twelfth.pdf")
        gujcet_url = upload_file_to_supabase(gujcet, f"{student_id}_gujcet.pdf")

        # ✅ Insert the admission row
        supabase.table("student_admissions").insert({
            "student_id": int(student_id),
            "academic_year": academic_year,
            "registration_form": reg_url,
            "tenth_marksheet": tenth_url,
            "twelfth_marksheet": twelfth_url,
            "gujcet_marksheet": gujcet_url
        }).execute()

        return jsonify({"message": "Documents uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
