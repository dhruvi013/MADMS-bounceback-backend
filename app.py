from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_mail import Mail
from flask_session import Session
from config import Config
from otp_service import generate_otp, send_otp_email
from datetime import timedelta
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

# Flask Session Configuration
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions in files (can be redis or database)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True  # Prevent session tampering
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Auto-expire session after 30 minutes

Session(app)

# Hardcoded credentials - make sure these match what you're sending from frontend
VALID_EMAIL = "vidyasinha939@gmail.com"
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
            
            # Start user session
            session['user'] = email
            session['last_active'] = timedelta(seconds=int(request.environ.get('werkzeug.request_time', 0)))  # Track user activity
            
            logger.info(f"OTP verified successfully for {email}, session started")
            return jsonify({"message": "OTP verified", "success": True}), 200
            
        logger.warning(f"Invalid OTP attempt for {email}")
        return jsonify({"error": "Invalid OTP"}), 400
    except Exception as e:
        logger.error(f"Error in OTP verification: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()  # Clear session on logout
    logger.info("User logged out, session cleared")
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/dashboard", methods=["GET"])
def dashboard():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized, please log in"}), 401
    
    return jsonify({"message": "Welcome to the Dashboard", "user": session['user']}), 200

# Function to check session timeout and activity
def is_session_expired():
    if 'user' not in session:
        return True  # No session found, must login
    if 'last_active' in session:
        inactive_time = timedelta(minutes=10)  # Auto logout after 10 mins of inactivity
        if session['last_active'] + inactive_time < timedelta(seconds=int(request.environ.get('werkzeug.request_time', 0))):
            session.clear()  # Clear session if inactive
            return True
    session['last_active'] = timedelta(seconds=int(request.environ.get('werkzeug.request_time', 0)))  # Update activity
    return False

@app.before_request
def session_checker():
    if request.endpoint in ['dashboard'] and is_session_expired():
        return redirect(url_for('login'))  # Redirect to login if session expired

if __name__ == "__main__":
    app.run(debug=True)
