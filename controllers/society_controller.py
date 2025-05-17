from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import base64
import io
from supabase_client import supabase

society_bp = Blueprint('society', __name__)

def upload_base64_to_bucket(bucket_path, base64_data, filename):
    # Remove data URL prefix if exists
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]

    file_bytes = base64.b64decode(base64_data)
    file_path = f"{bucket_path}/{filename}"
    bucket = supabase.storage.from_('societies')
    bucket.upload(file_path, file_bytes, {"content-type": "application/octet-stream"})
    return bucket.get_public_url(file_path)

@society_bp.route('/api/societies', methods=['POST'])
def add_society_event():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        event_name = data.get('eventName')
        event_date_str = data.get('date')
        society_name = data.get('societyName')

        if not event_date_str:
            return jsonify({"error": "Missing event date"}), 400

        event_date = datetime.strptime(event_date_str, "%d/%m/%Y").date()

        logo_base64 = data.get('logo')
        report_base64 = data.get('reportPDF')

        logo_url = ''
        report_url = ''

        if logo_base64:
            logo_filename = secure_filename(f"{event_name}_logo.png")
            logo_url = upload_base64_to_bucket("logos", logo_base64, logo_filename)

        if report_base64:
            report_filename = secure_filename(f"{event_name}_report.pdf")
            report_url = upload_base64_to_bucket("reports", report_base64, report_filename)

        response = supabase.table('society_activities').insert({
            "event_name": event_name,
            "event_date": event_date.isoformat(),
            "society_name": society_name,
            "society_logo": logo_url,
            "upload_report": report_url
        }).execute()

        if hasattr(response, 'error') and response.error:
            error_msg = getattr(response.error, 'message', str(response.error))
            return jsonify({"error": error_msg}), 500

        return jsonify({"message": "Society event saved successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
