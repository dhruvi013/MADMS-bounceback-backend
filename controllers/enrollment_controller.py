import re
from flask import Flask, request, jsonify, session
from supabase import create_client
import logging
from flask import Blueprint

# app = Flask(__name__)
# app.secret_key = "supersecretkey"  # required for session

enrollment_bp = Blueprint("enrollment", __name__)

# Supabase setup
url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWppc3JsYXRvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTc4MTc0MiwiZXhwIjoyMDU3MzU3NzQyfQ.46lZ3y9-gFwbYqZpuXbcEEN2xCVUSOHdjNae4WST3vg"
supabase = create_client(url, key)

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Upload function
def upload_file_to_supabase(file, filename):
    bucket_name = "enrollment-upload"

    file.seek(0)
    file_bytes = file.read()
    content_type = file.content_type or "application/pdf"

    try:
        response = supabase.storage.from_(bucket_name).upload(
            filename,
            file_bytes,
            {
                "content-type": content_type,
                "x-upsert": "true"
            }
        )

        # Supabase returns an UploadResponse object — treat that as success
        if not response or not hasattr(response, "path"):
            raise Exception(f"Unexpected response from Supabase: {response}")

        # Return the public URL
        return supabase.storage.from_(bucket_name).get_public_url(filename)

    except Exception as e:
        raise Exception(f"Upload to Supabase failed: {str(e)}")

@enrollment_bp.route("/upload-documents", methods=["POST"])
def upload_admission_docs():
    # Dummy session check for demo
    session['user'] = 'vidyasinha939@gmail.com'  # remove in production
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        enrollment_number = request.form.get("enrollment_number", "").strip()
        if not enrollment_number:
            return jsonify({"error": "Enrollment number is required"}), 400

        # Get files from form
        registration_form = request.files.get("registration_form")
        tenth = request.files.get("tenth_marksheet")
        twelfth = request.files.get("twelfth_marksheet")
        gujcet = request.files.get("gujcet_marksheet")

        if not all([registration_form, tenth, twelfth, gujcet]):
            return jsonify({"error": "All documents must be uploaded"}), 400

        # Upload each file and get public URL
        reg_url = upload_file_to_supabase(registration_form, f"{enrollment_number}_registration.pdf")
        tenth_url = upload_file_to_supabase(tenth, f"{enrollment_number}_tenth.pdf")
        twelfth_url = upload_file_to_supabase(twelfth, f"{enrollment_number}_twelfth.pdf")
        gujcet_url = upload_file_to_supabase(gujcet, f"{enrollment_number}_gujcet.pdf")

        logger.info(f"Uploaded documents for {enrollment_number}")

        # Insert into Supabase table
        insert_response = supabase.table("student_admissions").insert({
            "enrollment_number": enrollment_number,
            "registration_form": reg_url,
            "tenth_marksheet": tenth_url,
            "twelfth_marksheet": twelfth_url,
            "gujcet_marksheet": gujcet_url
        }).execute()

        if getattr(insert_response, "error", None):
            raise Exception(insert_response.error.message)

        return jsonify({"message": "Documents uploaded successfully"}), 200

        return jsonify({"message": "Documents uploaded successfully"}), 200

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return jsonify({"error": str(e)}), 500  # return full error message

if __name__ == "__main__":
    app.run(debug=True)