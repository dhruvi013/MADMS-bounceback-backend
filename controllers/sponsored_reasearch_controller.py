from flask import Blueprint, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)
sponsored_research_bp = Blueprint("sponsored_research_bp", __name__, url_prefix="/sponsored-research")

# Supabase client
SUPABASE_URL = "https://hagfxtawcqlejisrlato.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3ODE3NDIsImV4cCI6MjA1NzM1Nzc0Mn0.UxsVfpzvKRVAYi--ngdrogY3CjOiB9Yz60DeNTcvDa0"  # ⚠️ use service_role for inserts if anon is restricted
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "sponsored_reasearch"

@sponsored_research_bp.route("/", methods=["POST"])
def add_sponsored_research():
    try:
        data = request.get_json(force=True)
        required_fields = ["Proj_id", "year", "title", "mentor", "approval_date", "grant_sanctioned"]

        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "All fields are required"}), 400

        record = {
            "Proj_id": data["Proj_id"].strip(),
            "year": int(data["year"]),
            "title": data["title"].strip(),
            "mentor": data["mentor"].strip(),
            "approval_date": data["approval_date"].strip(),
            "grant sactioned": int(data["grant_sanctioned"])  # use the column name with space
        }

        response = supabase.table(TABLE_NAME).insert(record).execute()

        inserted_record = response.data[0] if response.data else record
        return jsonify({"message": "Project added successfully", "project": inserted_record}), 200

    except Exception as e:
        logger.exception("Error adding sponsored research")
        return jsonify({"error": "Server error", "details": str(e)}), 500


@sponsored_research_bp.route("/", methods=["GET"])
def get_sponsored_research():
    try:
        response = supabase.table(TABLE_NAME).select("*").execute()
        return jsonify(response.data if response.data else []), 200
    except Exception as e:
        logger.exception("Error fetching sponsored research")
        return jsonify({"error": "Server error", "details": str(e)}), 500
