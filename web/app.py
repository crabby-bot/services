from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from flask_talisman import Talisman
import os
import re
import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Security configuration
csp = {
    "default-src": "'self'",
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "img-src": ["'self'", "data:"],
    "frame-src": "'none'",
    "object-src": "'none'",
    "base-uri": "'self'",
    "form-action": "'self'",
}

Talisman(app, force_https=False, content_security_policy=csp,
         strict_transport_security=True, strict_transport_security_max_age=31536000,
         frame_options="SAMEORIGIN", referrer_policy="strict-origin-when-cross-origin")

logging.basicConfig(filename="/home/crabby/services/web/demo_requests.log", level=logging.INFO,
                    format="%(asctime)s - %(message)s")

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")


def load_examples():
    """Scan the examples/ folder and return list of example metadata."""
    examples = []
    if not os.path.isdir(EXAMPLES_DIR):
        return examples
    for name in sorted(os.listdir(EXAMPLES_DIR)):
        meta_path = os.path.join(EXAMPLES_DIR, name, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                meta["slug"] = name
                if meta.get("status", "live") == "live":
                    examples.append(meta)
            except Exception:
                pass
    return examples


def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email) is not None


def send_email(to_email, subject, body):
    try:
        with open("/home/crabby/.secrets/smtp_credentials.json") as f:
            creds = json.load(f)
        msg = MIMEMultipart()
        msg["From"] = creds["from_email"]
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(creds["smtp_host"], creds["smtp_port"]) as server:
            server.starttls()
            server.login(creds["username"], creds["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        logging.error(f"Email send error: {e}")
        return False


# ── Main routes ──────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", hostname=os.uname().nodename)


@app.route("/demo")
def demo():
    return render_template("demo.html")


@app.route("/examples")
def examples():
    return render_template("examples.html", examples=load_examples())


# ── Dynamic example routes ────────────────────────────────────────
# Each example lives in examples/<slug>/ with its own index.html and assets.
# Crabby adds a new folder + meta.json — no code changes needed.

@app.route("/examples/<slug>")
def example_page(slug):
    example_dir = os.path.join(EXAMPLES_DIR, slug)
    if not os.path.isdir(example_dir):
        abort(404)
    return send_from_directory(example_dir, "index.html")


@app.route("/examples/<slug>/<path:filename>")
def example_file(slug, filename):
    example_dir = os.path.join(EXAMPLES_DIR, slug)
    if not os.path.isdir(example_dir):
        abort(404)
    return send_from_directory(example_dir, filename)


# ── Demo request ─────────────────────────────────────────────────

@app.route("/demo/request", methods=["POST"])
def demo_request():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        gdpr_consent = data.get("gdprConsent", False)
        if not email or not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email address"}), 400
        if not gdpr_consent:
            return jsonify({"status": "error", "message": "GDPR consent required"}), 400
        logging.info(f"Demo request from: {email}")
        email_sent = send_email(
            to_email="crabby@opencrabby.com",
            subject="OpenCrabby Demo Request (GDPR Consent Given)",
            body=f"Demo request from: {email}\n\nGDPR Consent: Yes"
        )
        if not email_sent:
            return jsonify({"status": "error", "message": "Unable to send email"}), 500
        return jsonify({"status": "success", "message": "Demo request received"})
    except Exception as e:
        logging.error(f"Demo request error: {e}")
        return jsonify({"status": "error", "message": "Unable to process request"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
