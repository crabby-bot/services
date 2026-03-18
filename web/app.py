from flask import Flask, render_template, request, jsonify
from flask_talisman import Talisman
import os
import re
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

app = Flask(__name__)

# Security configuration
csp = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'"],
    'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com"],
    'img-src': ["'self'", "data:"],
    'frame-src': "'none'",
    'object-src': "'none'",
    'base-uri': "'self'",
    'form-action': "'self'",
}

Talisman(app, force_https=False, content_security_policy=csp,
         strict_transport_security=True, strict_transport_security_max_age=31536000,
         frame_options='SAMEORIGIN', referrer_policy='strict-origin-when-cross-origin')

# Configure logging
logging.basicConfig(filename='/home/crabby/services/web/demo_requests.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

def is_valid_email(email):
    """Basic email validation."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def send_email(to_email, subject, body):
    """Send email using SMTP."""
    try:
        # Get SMTP credentials from secrets server
        with open('/home/crabby/.secrets/smtp_credentials.json', 'r') as f:
            creds = json.load(f)

        # Create message
        msg = MIMEMultipart()
        msg['From'] = creds['from_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Establish SMTP connection
        with smtplib.SMTP(creds['smtp_host'], creds['smtp_port']) as server:
            server.starttls()
            server.login(creds['username'], creds['password'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        logging.error(f"Email send error: {str(e)}")
        return False

@app.route('/')
def hello_world():
    return render_template('index.html', hostname=os.uname().nodename)

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/examples')
def examples():
    return render_template('examples.html')

@app.route('/examples/apples-to-oaks')
def apples_to_oaks():
    return render_template('example_apples_to_oaks.html')

@app.route('/demo/request', methods=['POST'])
def demo_request():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        gdpr_consent = data.get('gdprConsent', False)

        # Validate email
        if not email or not is_valid_email(email):
            return jsonify({
                'status': 'error', 
                'message': 'Invalid email address'
            }), 400

        # Validate GDPR consent
        if not gdpr_consent:
            return jsonify({
                'status': 'error', 
                'message': 'GDPR consent required'
            }), 400

        # Log the request
        logging.info(f"Demo request from: {email}")

        # Send email
        email_sent = send_email(
            to_email='crabby@opencrabby.com',
            subject='OpenCrabby Demo Request (GDPR Consent Given)',
            body=f'Demo request from: {email}\n\nGDPR Consent: Yes\n\nPlease follow up with the potential user.'
        )

        if not email_sent:
            return jsonify({
                'status': 'error', 
                'message': 'Unable to send email'
            }), 500

        return jsonify({
            'status': 'success', 
            'message': 'Demo request received'
        })

    except Exception as e:
        logging.error(f"Demo request error: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': 'Unable to process request'
        }), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)