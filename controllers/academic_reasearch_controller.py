from flask import Blueprint, request, jsonify, session
from supabase import create_client
import logging

logger = logging.getLogger(__name__)
academic_research_bp = Blueprint("academic_research_bp", __name__, url_prefix="/academic-research")

# Supabase client
SUPABASE_URL = "https://hagfxtawcqlejisrlato.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3ODE3NDIsImV4cCI6MjA1NzM1Nzc0Mn0.UxsVfpzvKRVAYi--ngdrogY3CjOiB9Yz60DeNTcvDa0"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@academic_research_bp.route("/", methods=["POST"])
def add_academic_research():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        required_fields = ["title", "authors", "journal", "year", "listedIn", "publicationType"]
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "All fields are required"}), 400

        record = {
            "title_of_paper": str(data["title"]).strip(),
            "authors": str(data["authors"]).strip(),
            "journal": str(data["journal"]).strip(),
            "year": int(data["year"]),
            "listed_in": str(data["listedIn"]).strip(),
            "type_of_publication": str(data["publicationType"]).strip()
        }

        result = supabase.table("academic_reasearch").insert(record).execute()

        if result.error:
            return jsonify({"error": str(result.error)}), 500

        # Include the inserted record with the generated id
        inserted_record = result.data[0] if result.data else record
        return jsonify({"message": "Research paper added successfully", "paper": inserted_record}), 200

    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500


@academic_research_bp.route("/", methods=["GET"])
def get_academic_research():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # o Correct table name
        result = supabase.table("academic_reasearch").select("*").execute()
        return jsonify(result.data if result.data else []), 200
    except Exception as e:
        logger.exception("Error fetching research papers")
        return jsonify({"error": "Server error", "details": str(e)}), 500
