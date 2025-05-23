from flask import Blueprint, request, jsonify, session
from supabase import create_client
import logging
from datetime import datetime

faculty_bp = Blueprint("faculty", __name__)

# Supabase configuration
SUPABASE_URL = "https://hagfxtawcqlejisrlato.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTc4MTc0MiwiZXhwIjoyMDU3MzU3NzQyfQ.46lZ3y9-gFwbYqZpuXbcEEN2xCVUSOHdjNae4WST3vg"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@faculty_bp.route("/upload", methods=["POST"])
def upload_faculty_data():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"error": "Invalid data format"}), 400

        # Validate required fields
        for faculty in data:
            if not faculty.get("name"):
                return jsonify({"error": "Name is required for all faculty members"}), 400

        # Insert data into Supabase
        insert_response = supabase.table("faculty").insert(data).execute()

        if getattr(insert_response, "error", None):
            raise Exception(insert_response.error.message)

        return jsonify({
            "message": f"Successfully uploaded {len(data)} faculty members",
            "count": len(data)
        }), 200

    except Exception as e:
        logger.error(f"Error uploading faculty data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@faculty_bp.route("/list", methods=["GET"])
def get_faculty_list():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response = supabase.table("faculty").select("*").execute()
        return jsonify(response.data), 200
    except Exception as e:
        logger.error(f"Error fetching faculty list: {str(e)}")
        return jsonify({"error": str(e)}), 500

@faculty_bp.route("/<int:faculty_id>", methods=["GET"])
def get_faculty_details(faculty_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response = supabase.table("faculty").select("*").eq("id", faculty_id).execute()
        
        if not response.data:
            return jsonify({"error": "Faculty member not found"}), 404

        return jsonify(response.data[0]), 200
    except Exception as e:
        logger.error(f"Error fetching faculty details: {str(e)}")
        return jsonify({"error": str(e)}), 500

@faculty_bp.route("/<int:faculty_id>", methods=["PUT"])
def update_faculty(faculty_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        if "name" in data and not data["name"]:
            return jsonify({"error": "Name cannot be empty"}), 400

        # Update data in Supabase
        update_response = supabase.table("faculty").update(data).eq("id", faculty_id).execute()

        if getattr(update_response, "error", None):
            raise Exception(update_response.error.message)

        return jsonify({"message": "Faculty member updated successfully"}), 200
    except Exception as e:
        logger.error(f"Error updating faculty member: {str(e)}")
        return jsonify({"error": str(e)}), 500

@faculty_bp.route("/<int:faculty_id>", methods=["DELETE"])
def delete_faculty(faculty_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        delete_response = supabase.table("faculty").delete().eq("id", faculty_id).execute()

        if getattr(delete_response, "error", None):
            raise Exception(delete_response.error.message)

        return jsonify({"message": "Faculty member deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting faculty member: {str(e)}")
        return jsonify({"error": str(e)}), 500
