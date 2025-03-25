import random
import string
from flask_mail import Message
import logging

logger = logging.getLogger(__name__)

def generate_otp():
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp, mail):
    """Send OTP via email using Flask-Mail."""
    try:
        logger.info(f"Preparing to send OTP email to {email}")
        msg = Message(
            subject="Your OTP Code",
            sender="dhruvipatrl1611@gmail.com",  # Use the same email as in config
            recipients=[email],
            body=f"Your OTP code is: {otp}"
        )
        mail.send(msg)
        logger.info(f"OTP email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")
