from flask import request, jsonify, session, Blueprint
from supabase import create_client
import logging

logger = logging.getLogger(__name__)
faculty_qualification_bp = Blueprint(
    "faculty_qualification_bp", __name__, url_prefix="/faculty-qualification"
)

# Supabase credentials
url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3ODE3NDIsImV4cCI6MjA1NzM1Nzc0Mn0.UxsVfpzvKRVAYi--ngdrogY3CjOiB9Yz60DeNTcvDa0"
supabase = create_client(url, key)


def insert_faculty_qualification():
    if not supabase:
        logger.error("Supabase client not initialized")
        return jsonify({"error": "Database connection unavailable"}), 503

    if "user" not in session:
        logger.warning("Unauthorized request")
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        logger.info(f"Received data: {data}")

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        fac_name = data.get("faculty_name")
        qualification = data.get("qualification")
        designation = data.get("designation")

        # Validation
        if not fac_name or not qualification or not designation:
            return jsonify({"error": "All fields are required"}), 400

        record = {
            "fac_name": fac_name.strip(),
            "Qualification": qualification.strip(),
            "Designation": designation.strip(),
        }

        result = supabase.table("faculty_qualification").insert(record).execute()

        if hasattr(result, "error") and result.error:
            logger.error(f"Insert error: {result.error}")
            return jsonify({"error": str(result.error)}), 500

        logger.info("Faculty qualification record inserted successfully")
        return jsonify({"message": "Faculty qualification added successfully"}), 200

    except Exception as e:
        logger.error(f"Error inserting faculty qualification: {str(e)}", exc_info=True)
        return jsonify({"error": "Server error", "details": str(e)}), 500


# Routes
@faculty_qualification_bp.route("/", methods=["POST"])
def add_faculty_qualification():
    session["user"] = "dhruvi@example.com"  # dummy login for testing
    return insert_faculty_qualification()


@faculty_qualification_bp.route("/", methods=["GET"])
def get_faculty_qualification():
    if not supabase:
        return jsonify({"error": "Database connection unavailable"}), 503

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result = supabase.table("faculty_qualification").select("*").execute()
        return jsonify(result.data), 200
    except Exception as e:
        logger.error(f"Error fetching faculty qualification records: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch data"}), 500