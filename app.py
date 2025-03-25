from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail
from config import Config
from otp_service import generate_otp, send_otp_email
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
try:
    app.config.from_object(Config)
    logger.info("Configuration loaded successfully")
    logger.debug(f"Mail settings: SERVER={app.config['MAIL_SERVER']}, PORT={app.config['MAIL_PORT']}, USERNAME={app.config['MAIL_USERNAME']}")
except Exception as e:
    logger.error(f"Error loading configuration: {str(e)}")
    raise

# Initialize extensions
try:
    mail = Mail(app)
    logger.info("Mail extension initialized successfully")
except Exception as e:
    logger.error(f"Error initializing mail: {str(e)}")
    raise

CORS(app, origins=["http://localhost:8080"])  # Allow only your frontend

# Hardcoded credentials - make sure these match what you're sending from frontend
VALID_EMAIL = "dhruviben.patel119539@marwadiuniversity.ac.in"
VALID_PASSWORD = "1234"
OTP_STORE = {}  # Dictionary to store OTPs temporarily

@app.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.json
        logger.debug(f"Received login request data: {data}")
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")

        logger.info(f"Processing login for email: {email}")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if email == VALID_EMAIL and password == VALID_PASSWORD:
            try:
                otp = generate_otp()
                logger.debug(f"Generated OTP: {otp} for {email}")
                
                OTP_STORE[email] = otp  # Store OTP temporarily
                
                try:
                    send_otp_email(email, otp, mail)
                    logger.info(f"OTP sent successfully to {email}")
                    return jsonify({"message": "OTP sent to email", "email": email}), 200
                except Exception as mail_error:
                    logger.error(f"Failed to send email: {str(mail_error)}")
                    return jsonify({"error": f"Failed to send OTP: {str(mail_error)}"}), 500
            except Exception as otp_error:
                logger.error(f"Error in OTP generation/storage: {str(otp_error)}")
                return jsonify({"error": str(otp_error)}), 500
        else:
            logger.warning(f"Invalid credentials for email: {email}")
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Unexpected error in login: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get("email")
        otp = data.get("otp")

        logger.info(f"Verifying OTP for email: {email}")

        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400

        stored_otp = OTP_STORE.get(email)
        if not stored_otp:
            return jsonify({"error": "OTP expired or not found"}), 400

        if stored_otp == otp:
            OTP_STORE.pop(email)  # Remove OTP after successful verification
            logger.info(f"OTP verified successfully for {email}")
            return jsonify({"message": "OTP verified", "success": True}), 200
            
        logger.warning(f"Invalid OTP attempt for {email}")
        return jsonify({"error": "Invalid OTP"}), 400
    except Exception as e:
        logger.error(f"Error in OTP verification: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
