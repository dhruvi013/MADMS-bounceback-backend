from flask import Blueprint, request, jsonify
from services.supabase_service import upload_file_to_supabase
import logging

upload_routes = Blueprint('upload_routes', __name__)
logger = logging.getLogger(__name__)

@upload_routes.route('/upload-documents', methods=['POST'])
def upload_documents():
    try:
        name = request.form.get('name')
        enrollment_number = request.form.get('enrollment_number')
        
        if not name or not enrollment_number:
            return jsonify({'message': 'Name and enrollment number are required.'}), 400

        required_fields = ['registrationForm', 'marksheet10th', 'marksheet12th', 'gujcetResult']
        uploaded_urls = {}

        for field in required_fields:
            file = request.files.get(field)
            if file:
                # Optional: Generate a path like "documents/enrollment_number/filename.pdf"
                path = f"documents/{enrollment_number}/{field}.pdf"
                url = upload_file_to_supabase(file, path)
                uploaded_urls[field] = url
            else:
                return jsonify({'message': f'Missing file: {field}'}), 400

        # Return uploaded file URLs
        return jsonify({
            'message': 'Files uploaded successfully.',
            'files': uploaded_urls
        }), 200

    except Exception as e:
        logger.exception("Error in uploading documents")
        return jsonify({'message': 'Something went wrong on the server.'}), 500
