from flask import Blueprint, request, jsonify, session
from supabase import create_client
import logging

magazine_bp = Blueprint("magazine", __name__)

# Supabase configuration
SUPABASE_URL = "https://hagfxtawcqlejisrlato.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTc4MTc0MiwiZXhwIjoyMDU3MzU3NzQyfQ.46lZ3y9-gFwbYqZpuXbcEEN2xCVUSOHdjNae4WST3vg" # Replace with your actual secret service key
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_file_to_bucket(file, filename):
    bucket_name = "magazines"

    file.seek(0)
    file_bytes = file.read()
    content_type = file.content_type or "image/jpeg"

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

@magazine_bp.route("/upload-magazine", methods=["POST"])
def upload_magazine():
    session["user"] = "admin@example.com"  # For testing only

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        year = request.form.get("yearPublished", "").strip()
        magazine_file = request.files.get("magazineFront")

        if not year or not magazine_file:
            return jsonify({"error": "All fields are required"}), 400

        filename = f"{year}_magazine_front.jpg"
        public_url = upload_file_to_bucket(magazine_file, filename)

        # Insert into Supabase table
        insert_response = supabase.table("magazines").insert({
            "publication_year": year,
            "front_page": public_url
        }).execute()

        if getattr(insert_response, "error", None):
            raise Exception(insert_response.error.message)

        return jsonify({"message": "Magazine uploaded successfully"}), 200

    except Exception as e:
        logger.error(f"Error uploading magazine: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

@magazine_bp.route("/upload-magazine", methods=["GET"])
def get_magazines():
    try:
        # This returns an APIResponse object which contains .data
        response = supabase.table("magazines").select("*").execute()

        # Just access response.data safely
        magazines = [
            {
                "id": mag.get("id"),
                "magazineFrontUrl": mag.get("front_page"),
                "yearPublished": mag.get("publication_year"),
            }
            for mag in (response.data or [])
        ]

        return jsonify(magazines), 200

    except Exception as e:
        logger.error(f"Error fetching magazines: {str(e)}")
        return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(debug=True)