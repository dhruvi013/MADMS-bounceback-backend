from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_mail import Mail
from flask_session import Session
from config import Config
from otp_service import generate_otp, send_otp_email
from datetime import timedelta
import logging
