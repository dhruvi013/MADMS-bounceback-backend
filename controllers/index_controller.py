import re
from flask import request, jsonify, session, Blueprint
# from services.supabase_service import upload_file_to_supabase

from supabase import create_client
import os
import logging
from flask import current_app as app
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

index_bp = Blueprint("index", __name__)

url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3ODE3NDIsImV4cCI6MjA1NzM1Nzc0Mn0.UxsVfpzvKRVAYi--ngdrogY3CjOiB9Yz60DeNTcvDa0"

# Initialize Supabase client with retry mechanism
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def init_supabase():
    try:
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise

try:
    supabase = init_supabase()
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Could not initialize Supabase client after retries: {str(e)}")
    supabase = None

def upload_academic_performance():
    if not supabase:
        logger.error("Supabase client is not initialized")
        return jsonify({"error": "Database connection is not available"}), 503
        
    if 'user' not in session:
        logger.warning("Unauthorized access attempt")
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Get form data
        data = request.get_json()
        logger.info(f"Received data: {data}")
        if not data:
            logger.warning("No JSON data provided in request")
            return jsonify({"error": "No JSON data provided"}), 400
            
        academic_year = data.get("academic_year")
        mean_cgpa = data.get("mean_cgpa")
        students_appeared = data.get("students_appeared")
        enrollment_number = data.get("enrollment_number")

        # Log received values
        logger.info(f"Received values - academic_year: {academic_year}, mean_cgpa: {mean_cgpa}, students_appeared: {students_appeared}, enrollment_number: {enrollment_number}")

        # Validate required fields
        if any(field is None for field in [academic_year, mean_cgpa, students_appeared, enrollment_number]):
            missing_fields = [field for field, value in {'academic_year': academic_year, 'mean_cgpa': mean_cgpa, 'students_appeared': students_appeared, 'enrollment_number': enrollment_number}.items() if value is None]
            logger.warning(f"Missing required fields: {missing_fields}")
            return jsonify({"error": "All fields are required", "missing_fields": missing_fields}), 400
            
        # Validate data types
        try:
            academic_year = str(academic_year).strip()
            mean_cgpa = float(mean_cgpa)
            students_appeared = bool(students_appeared)
            enrollment_number = str(enrollment_number).strip()
            if mean_cgpa < 0 or mean_cgpa > 10:
                raise ValueError("Invalid value range")
        except (ValueError, TypeError) as e:
            logger.warning(f"Data type validation failed: {str(e)}")
            return jsonify({"error": "Invalid data format: mean_cgpa must be between 0-10 and students_appeared must be a boolean value"}), 400

        # Check for existing record for the academic year
        try:
            existing_check = supabase.table("academic_performance_index") \
                .select("academic_year") \
                .eq("academic_year", academic_year) \
                .execute()
                
            if existing_check.data:
                logger.warning(f"Duplicate record attempt for academic year: {academic_year}")
                return jsonify({"error": "Record already exists for this academic year"}), 409

            # Create performance record
            performance_data = {
                "academic_year": academic_year,
                "mean_cgpa": mean_cgpa,
                "students_appeared": students_appeared,
                "enrollment_number": enrollment_number
            }
            
            logger.info(f"Attempting to insert record: {performance_data}")
            insert_result = supabase.table("academic_performance_index").insert(performance_data).execute()
            
            if not insert_result or not hasattr(insert_result, 'data'):
                logger.error(f"Invalid response from Supabase: {insert_result}")
                raise Exception("Invalid response from Supabase")
                
            if hasattr(insert_result, 'error') and insert_result.error:
                logger.error(f"Supabase insert error: {insert_result.error}")
                raise Exception(f"Supabase insert failed: {insert_result.error}")

            logger.info(f"Academic performance data added successfully: {insert_result.data}")
            return jsonify({"message": "Academic performance data added successfully"}), 200

        except Exception as se:
            logger.error(f"Supabase operation failed: {str(se)}", exc_info=True)
            if hasattr(se, 'error'):
                logger.error(f"Supabase error details: {se.error}")
            return jsonify({"error": "Database operation failed", "details": str(se)}), 500

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}", exc_info=True)
        return jsonify({"error": "Invalid data format"}), 400
    except Exception as e:
        logger.error(f"Academic performance upload error: {str(e)}", exc_info=True)
        return jsonify({"error": "Server error processing your request", "details": str(e)}), 500

@index_bp.route("/academic-performance", methods=["POST"])
def handle_upload():
    # Dummy session check for demo
    session['user'] = 'dhruvi@example.com'  # remove in production
    return upload_academic_performance()

# @index_bp.route("/academic-performance", methods=["GET"])
# def get_academic_performance():
#     # Dummy session check for demo
#     session['user'] = 'dhruvi@example.com'  # remove in production
#     if 'user' not in session:
#         return jsonify({"error": "Unauthorized"}), 401

#     try:
#         result = supabase.table("academic_performance_index") \
#             .select("*") \
#             .order("academic_year", desc=True) \
#             .execute()

#         return jsonify(result.data), 200

#     except Exception as e:
#         logger.error(f"Error fetching academic performance data: {str(e)}", exc_info=True)
#         return jsonify({"error": "Server error fetching data"}), 500