import re
from flask import request, jsonify, session, Blueprint
from services.supabase_service import upload_file_to_supabase
from supabase import create_client
import os
import logging
from flask import current_app as app

logger = logging.getLogger(__name__)

index_bp = Blueprint("index", __name__)

url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3ODE3NDIsImV4cCI6MjA1NzM1Nzc0Mn0.UxsVfpzvKRVAYi--ngdrogY3CjOiB9Yz60DeNTcvDa0"
supabase = create_client(url, key)

def upload_academic_performance():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Get form data
        academic_year = request.form.get("academic_year", "").strip()
        mean_cgpa = request.form.get("mean_cgpa", "").strip()
        students_appeared = request.form.get("students_appeared", "").strip()

        if not all([academic_year, mean_cgpa, students_appeared]):
            return jsonify({"error": "All fields are required"}), 400

        # Check for existing record for the academic year
        existing_check = supabase.table("academic_performance_index") \
            .select("academic_year") \
            .eq("academic_year", academic_year) \
            .execute()
            
        if existing_check.data:
            return jsonify({"error": "Record already exists for this academic year"}), 409

        # Create performance record
        performance_data = {
            "academic_year": academic_year,
            "mean_cgpa": float(mean_cgpa),
            "students_appeared": int(students_appeared)
        }
        
        supabase.table("academic_performance_index").insert(performance_data).execute()

        return jsonify({"message": "Academic performance data added successfully"}), 200

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}", exc_info=True)
        return jsonify({"error": "Invalid data format"}), 400
    except Exception as e:
        logger.error(f"Academic performance upload error: {str(e)}", exc_info=True)
        return jsonify({"error": "Server error processing your request"}), 500

@index_bp.route("/academic-performance", methods=["POST"])
def handle_upload():
    return upload_academic_performance()

@index_bp.route("/academic-performance", methods=["GET"])
def get_academic_performance():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result = supabase.table("academic_performance_index") \
            .select("*") \
            .order("academic_year", desc=True) \
            .execute()

        return jsonify(result.data), 200

    except Exception as e:
        logger.error(f"Error fetching academic performance data: {str(e)}", exc_info=True)
        return jsonify({"error": "Server error fetching data"}), 500