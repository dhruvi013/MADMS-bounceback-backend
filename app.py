from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_mail import Mail
from flask_session import Session
from config import Config
from otp_service import generate_otp, send_otp_email
from datetime import timedelta, datetime
import logging
from supabase_client import SUPABASE_KEY, SUPABASE_URL
from controllers.student_controller import student_bp
from controllers.enrollment_controller import enrollment_bp
from controllers.index_controller import index_bp
from controllers.society_controller import society_bp
from controllers.magazine_controller import magazine_bp
from controllers.faculty_controller import faculty_bp
from controllers.faculty_qualifiction_controller import faculty_qualification_bp
from controllers.academic_reasearch_controller import academic_research_bp
from controllers.sponsored_reasearch_controller import sponsored_research_bp
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase admin client
supabase_admin = create_client(SUPABASE_URL, SUPABASE_KEY)

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ✅ CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8080", "https://accredit-assisstant.vercel.app"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# ✅ Register controllers
app.register_blueprint(student_bp)
app.register_blueprint(enrollment_bp)
app.register_blueprint(index_bp)
app.register_blueprint(magazine_bp)
app.register_blueprint(society_bp)
app.register_blueprint(faculty_bp, url_prefix='/faculty')
app.register_blueprint(faculty_qualification_bp)
app.register_blueprint(academic_research_bp)
app.register_blueprint(sponsored_research_bp)


# ✅ Load config
try:
    app.config.from_object(Config)
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Error loading configuration: {str(e)}")
    raise

# ✅ Session secret key (fallback for local dev)
if not app.config.get("SECRET_KEY"):
    app.config["SECRET_KEY"] = "super-secret-key"

# ✅ Flask-Mail setup
try:
    mail = Mail(app)
    logger.info("Mail initialized successfully")
except Exception as e:
    logger.error(f"Mail initialization error: {str(e)}")
    raise

# ✅ Flask Session Configuration
app.config['SECRET_KEY'] = 'your_generated_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # Local dev
app.config['SESSION_COOKIE_SECURE'] = False     # Local dev
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True

Session(app)

# ✅ Hardcoded users (testing only)
ALLOWED_EMAILS = {
    "dhruviben.patel119539@marwadiuniversity.ac.in": "admin",
    "vidyasinha939@gmail.com": "admin",
    "rajvidave22@gmail.com": "admin",
    "vidyabhartisinha.119394@marwadiuniversity.ac.in": "user",
    "rajvi.dave119704@marwadiuniversity.ac.in": "user"
}
VALID_PASSWORD = "1234"

# ✅ OTP Store (with expiry)
OTP_STORE = {}

# ========================= AUTH ROUTES =========================

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
                "role": ALLOWED_EMAILS[email],
                "expires_at": datetime.utcnow() + timedelta(minutes=5)  # OTP expires in 5 mins
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
        if stored_data:
            # ✅ Check OTP expiry
            if datetime.utcnow() > stored_data["expires_at"]:
                OTP_STORE.pop(email)
                return jsonify({"error": "OTP expired, please login again"}), 400

            if stored_data["otp"] == otp:
                role = stored_data["role"]
                OTP_STORE.pop(email)

                session['user'] = email
                session['role'] = role
                session['last_active'] = datetime.utcnow().timestamp()

                logger.debug(f"Session created for {email} with role {role}")

                return jsonify({
                    "message": "OTP verified",
                    "success": True,
                    "role": role
                }), 200

        return jsonify({"error": "Invalid OTP"}), 400
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/auth/google-login", methods=["POST"])
def google_login():
    data = request.json
    access_token = data.get("access_token")

    if not access_token:
        return jsonify({"error": "No token provided"}), 400

    try:
        user_info = supabase_admin.auth.get_user(access_token)
        email = user_info.user.email  # ✅ Correct way
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        return jsonify({"error": "Invalid token"}), 401

    session['user'] = email
    session['role'] = 'user'
    session['last_active'] = datetime.utcnow().timestamp()

    return jsonify({"message": "Logged in via Google", "email": email}), 200


@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# ========================= PROTECTED ROUTES =========================

@app.route("/dashboard", methods=["GET"])
def dashboard():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"message": f"Welcome, {session['user']}!"}), 200

# ========================= SESSION CHECKER =========================

@app.before_request
def session_checker():
    authenticated_endpoints = [
        'dashboard',
        'submit_form',
        'faculty.upload_faculty_data',
        'faculty.get_faculty_list',
        'faculty.get_faculty_details',
        'faculty.update_faculty',
        'faculty.delete_faculty',
        'faculty.upload_faculty',
        "faculty.list_faculty",
        "faculty.delete_faculty",
        "/upload",
        "/faculty",
        'faculty_qualification_bp.add_faculty_qualification',
        'faculty_qualification_bp.get_faculty_qualification',   
        "academic_research_bp.add_academic_research",
        "academic_research_bp.get_academic_research",
        "sponsored_research_bp.add_sponsored_research",   # ✅ New POST route
        "sponsored_research_bp.get_sponsored_research",   # ✅ New GET route
        ]

    admin_endpoints = [
        'faculty.upload_faculty_data',
        'faculty.update_faculty',
        'faculty.delete_faculty',
    ]

    if request.method == "OPTIONS":
        return

    if request.endpoint in authenticated_endpoints:
        if 'user' not in session or 'role' not in session:
            return jsonify({"error": "Unauthorized, please log in"}), 401

        last_active = session.get('last_active')
        if last_active and (datetime.utcnow().timestamp() - last_active > 1800):
            session.clear()
            return jsonify({"error": "Session expired, please log in again"}), 401

        session['last_active'] = datetime.utcnow().timestamp()

        if request.endpoint in admin_endpoints:
            if session.get('role') != 'admin':
                return jsonify({"error": "Forbidden, requires admin privileges"}), 403

# ========================= APP START =========================

if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development")

    if env == "development":
        app.run(host="localhost", port=5000, debug=True)
    else:
        port = int(os.environ.get("PORT", 10000))
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
        app.config['SESSION_COOKIE_SECURE'] = True
        app.run(host="0.0.0.0", port=port)
