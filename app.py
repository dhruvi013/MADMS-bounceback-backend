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
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8080", "https://madms-bounceback.vercel.app"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

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
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Crucial for localhost-LAX/None for globally
app.config['SESSION_COOKIE_SECURE'] = True    # False because not using HTTPS locally/For render True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True

# ✅ Correct CORS setup
CORS(app, supports_credentials=True, origins=[
    # "http://localhost:8080",  # Local development
    # "https://madms-bounceback.vercel.app"  # Production Vercel domain
    "*"
])

Session(app)

# Hardcoded credentials for testing
# Allowed emails and single password (for testing)
ALLOWED_EMAILS = [
    "dhruviben.patel119539@marwadiuniversity.ac.in",
    "vidyasinha939@gmail.com",
    "rajvidave22@gmail.com"
]
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

        if email in [e.strip().lower() for e in ALLOWED_EMAILS] and password == VALID_PASSWORD:
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



@app.route("/upload-documents", methods=["POST"])
def upload_admission_docs():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        student_id = request.form.get("student_id")
        academic_year = request.form.get("academic_year")

        # ✅ Check if student exists in the students table
        student_check = supabase.table("students").select("id").eq("id", student_id).execute()
        if not student_check.data:
            return jsonify({"error": "Student not found"}), 400

        # ✅ Check if admission already exists for this student_id
        admission_check = supabase.table("student_admissions").select("id").eq("student_id", student_id).execute()
        if admission_check.data:
            return jsonify({"error": "Admission already submitted"}), 409

        # ✅ Handle file uploads (store in Supabase Storage and get public URLs)
        from services.supabase_service import upload_file_to_supabase

        registration_form = request.files.get("registration_form")
        tenth = request.files.get("tenth_marksheet")
        twelfth = request.files.get("twelfth_marksheet")
        gujcet = request.files.get("gujcet_marksheet")

        reg_url = upload_file_to_supabase(registration_form, f"{student_id}_registration.pdf")
        tenth_url = upload_file_to_supabase(tenth, f"{student_id}_tenth.pdf")
        twelfth_url = upload_file_to_supabase(twelfth, f"{student_id}_twelfth.pdf")
        gujcet_url = upload_file_to_supabase(gujcet, f"{student_id}_gujcet.pdf")

        # ✅ Insert admission data into student_admissions table
        # student_id here is a foreign key reference to students.id
        supabase.table("student_admissions").insert({
            "student_id": int(student_id),
            "academic_year": academic_year,
            "registration_form": reg_url,
            "tenth_marksheet": tenth_url,
            "twelfth_marksheet": twelfth_url,
            "gujcet_marksheet": gujcet_url
        }).execute()

        return jsonify({"message": "Documents uploaded successfully"}), 200

    except Exception as e:
        logger.error(f"Admission upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Use environment variables or default to production settings
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
