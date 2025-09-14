import os
import traceback
import jwt
import pandas as pd  # 👈 add this
from functools import wraps
from flask import Blueprint, request, jsonify, session
from database.db import SessionLocal
from models.faculty import Faculty

faculty_bp = Blueprint('faculty', __name__)

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-supabase-jwt-secret")

# ---------------- Upload Faculty Data ----------------
@faculty_bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_faculty():
    if request.method == 'OPTIONS':
        return jsonify({"message": "Faculty uploaded successfully"}), 200

    db = SessionLocal()
    try:
        # ✅ Expect file in FormData
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        # ✅ Use pandas to read Excel file
        df = pd.read_excel(file)

        required_columns = ["name"]
        for col in required_columns:
            if col not in df.columns:
                return jsonify({"error": f"Missing required column: {col}"}), 400

        faculty_members = []
        for _, row in df.iterrows():
            faculty = Faculty(
                name=row.get("name", ""),
                appointment_letter=row.get("appointment_letter", ""),
                salary_slip=row.get("salary_slip", ""),
                specialization=row.get("specialization", ""),
                subject_allocation=row.get("subject_allocation", ""),
                type=row.get("type", ""),
            )
            faculty_members.append(faculty)

        db.bulk_save_objects(faculty_members)
        db.commit()

        return jsonify({"message": f"{len(faculty_members)} faculty members added successfully"}), 200

    except Exception as e:
        db.rollback()
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
