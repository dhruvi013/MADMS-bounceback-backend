from flask import Blueprint, request, jsonify, session
from supabase import create_client
import logging
import uuid

achievement_bp = Blueprint("achievement", __name__)

# Supabase config
SUPABASE_URL = "https://hagfxtawcqlejisrlato.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTc4MTc0MiwiZXhwIjoyMDU3MzU3NzQyfQ.46lZ3y9-gFwbYqZpuXbcEEN2xCVUSOHdjNae4WST3vg"  # secure this!
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_file_to_bucket(file, filename):
    bucket_name = "achievements"

    file.seek(0)
    file_bytes = file.read()
    content_type = file.content_type or "application/pdf"

    try:
        response = supabase.storage.from_(bucket_name).upload(
            path=filename,
            file=file_bytes,
            file_options={
                "content-type": content_type,
                "x-upsert": "true"
            }
        )

        if not response or not hasattr(response, "path"):
            raise Exception("Upload failed or unexpected response")

        return supabase.storage.from_(bucket_name).get_public_url(filename)

    except Exception as e:
        raise Exception(f"Upload to Supabase failed: {str(e)}")


@achievement_bp.route("/upload-achievement", methods=["POST"])
def upload_achievement():
    session["user"] = "admin@example.com"  # testing only

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        enrollment_number = request.form.get("enrollmentNumber", "").strip()
        event_name = request.form.get("eventName", "").strip()
        organized_by = request.form.get("organizedBy", "").strip()
        date = request.form.get("date", "").strip()
        achievement = request.form.get("achievement", "").strip()
        document_proof = request.files.get("documentProof")

        if not all([enrollment_number, event_name, organized_by, date, achievement]):
            return jsonify({"error": "All fields except proof are required"}), 400

        proof_url = ""
        if document_proof:
            filename = f"{uuid.uuid4()}_{document_proof.filename}"
            proof_url = upload_file_to_bucket(document_proof, filename)

        # Insert data into Supabase
        insert_response = supabase.table("achievements").insert({
            "student_name": enrollment_number,
            "event_name": event_name,
            "organized_by": organized_by,
            "event_date": date,
            "achievement": achievement,
            "proof_url": proof_url
        }).execute()

        if getattr(insert_response, "error", None):
            raise Exception(insert_response.error.message)

        return jsonify({"message": "Achievement uploaded successfully"}), 200

    except Exception as e:
        logger.error(f"Error uploading achievement: {str(e)}")
        return jsonify({"error": str(e)}), 500
