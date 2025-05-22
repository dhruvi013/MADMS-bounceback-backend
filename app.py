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
from controllers.enrollment_controller import enrollment_bp
from controllers.index_controller import index_bp
from controllers.society_controller import society_bp
from controllers.magazine_controller import magazine_bp
import os
# from controllers.enrollment_controller import upload_admission_docs
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8081", "https://madms-assistant.vercel.app"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Register the controller (Blueprint)
app.register_blueprint(student_bp)
app.register_blueprint(enrollment_bp)
app.register_blueprint(index_bp)
app.register_blueprint(magazine_bp)
app.register_blueprint(society_bp) 

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
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Crucial for localhost
app.config['SESSION_COOKIE_SECURE'] = True    # False because not using HTTPS locally
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True

# # ✅ Correct CORS setup
# CORS(app, supports_credentials=True, origins=[
#     # "http://localhost:8080",  # Local development
#     # "https://madms-bounceback.vercel.app"  # Production Vercel domain
#     "*"
# ])

Session(app)

# Hardcoded credentials for testing
# Allowed emails and single password (for testing)
ALLOWED_EMAILS = {
    "dhruviben.patel119539@marwadiuniversity.ac.in": "admin",
    "vidyasinha939@gmail.com": "admin",
    "rajvi.dave119704@marwadiuniversity.ac.in": "user"
}
VALID_PASSWORD = "1234"
OTP_STORE = {}

@app.route("/auth/login", methods=["POST"])
def login():    
    try:
        data = request.json
        email = data.get("email", "").strip().lower()
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if email in ALLOWED_EMAILS and password == VALID_PASSWORD:
            otp = generate_otp()
            OTP_STORE[email] = {
                "otp": otp,
                "role": ALLOWED_EMAILS[email]
            }
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

        stored_data = OTP_STORE.get(email)
        if stored_data and stored_data["otp"] == otp:
            role = stored_data["role"]
            OTP_STORE.pop(email)
            session['user'] = email
            session['role'] = role
            session['last_active'] = datetime.utcnow().timestamp()

            # Debugging logs
            print("✅ SESSION SET:")
            print("session_user:", session.get("user"))
            print("session_role:", session.get("role"))
            print("last_active:", session.get("last_active"))

            logger.debug(f"Session created: {session}")

            return jsonify({
                "message": "OTP verified", 
                "success": True,
                "role": role
            }), 200

        return jsonify({"error": "Invalid OTP"}), 400
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200




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
    # Development will be the default when running locally
    env = os.environ.get("FLASK_ENV", "development")

    if env == "development":
        app.run(host="localhost", port=5000, debug=True)
    else:
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)
