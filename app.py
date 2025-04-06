from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_mail import Mail
from flask_session import Session
from config import Config
from otp_service import generate_otp, send_otp_email
from datetime import timedelta, datetime
import logging
from supabase_client import supabase
from controllers.student_controller import student_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Register the controller (Blueprint)
app.register_blueprint(student_bp)


# Load configuration
try:
    app.config.from_object(Config)
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Error loading configuration: {str(e)}")
    raise

# Secret key required for sessions
if not app.config.get("SECRET_KEY"):
    app.config["SECRET_KEY"] = "super-secret-key"  # fallback, not for prod

# Initialize Mail
try:
    mail = Mail(app)
    logger.info("Mail extension initialized successfully")
except Exception as e:
    logger.error(f"Error initializing mail: {str(e)}")
    raise

# ✅ Flask Session Configuration (fixed)
app.config['SECRET_KEY'] = 'your_generated_secret_key'  # Must not be None
app.config['SESSION_TYPE'] = 'filesystem'  # Store session in server filesystem
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Crucial for localhost
app.config['SESSION_COOKIE_SECURE'] = False    # False because not using HTTPS locally
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True

# ✅ Correct CORS setup
CORS(app, supports_credentials=True, origins=[
    "http://localhost:8080"  # 👈 must match exactly!
])

Session(app)

# Hardcoded credentials for testing
VALID_EMAIL = "dhruviben.patel119539@marwadiuniversity.ac.in"
VALID_PASSWORD = "1234"
OTP_STORE = {}

@app.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if email == VALID_EMAIL and password == VALID_PASSWORD:
            otp = generate_otp()
            OTP_STORE[email] = otp
            send_otp_email(email, otp, mail)
            return jsonify({"message": "OTP sent to email", "email": email}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    try:
        data = request.json
        email = data.get("email")
        otp = data.get("otp")

        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400

        if OTP_STORE.get(email) == otp:
            OTP_STORE.pop(email)
            session['user'] = email
            session['last_active'] = datetime.utcnow().timestamp()

            # Debugging logs
            print("✅ SESSION SET:")
            print("session_user:", session.get("user"))
            print("last_active:", session.get("last_active"))

            logger.debug(f"Session created: {session}")

            return jsonify({"message": "OTP verified", "success": True}), 200

        return jsonify({"error": "Invalid OTP"}), 400
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    

@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/submit-form", methods=["POST", "OPTIONS"])
def submit_form():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin"))
        response.headers.add("Access-Control-Allow-Credentials", "true")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response

    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        # Save to Supabase
        response = supabase.table("students").insert(data).execute()

        return jsonify({"message": "Form submitted successfully", "response": response.data}), 200
    except Exception as e:
        logger.error(f"Form submission error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Dashboard Route (test auth)
@app.route("/dashboard", methods=["GET"])
def dashboard():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"message": f"Welcome, {session['user']}!"}), 200


@app.before_request
def session_checker():
    protected_endpoints = ['dashboard', 'submit_form']

    if request.method == "OPTIONS":
        return

    if request.endpoint in protected_endpoints:
        if 'user' not in session:
            return jsonify({"error": "Unauthorized, please log in"}), 401

        last_active = session.get('last_active')
        if last_active and (datetime.utcnow().timestamp() - last_active > 1800):  # 30 mins
            session.clear()
            return jsonify({"error": "Session expired, please log in again"}), 401

        session['last_active'] = datetime.utcnow().timestamp()

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)