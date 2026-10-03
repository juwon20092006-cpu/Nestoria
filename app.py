from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

import os
import json
import base64

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

app = Flask(__name__)

# ---- Upload config ----
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB per file
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB total

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# Routes
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/jobs")
def jobs():
    jobs_data = [
        {
            "id": 1,
            "title": "Senior Real Estate Agent",
            "company": "Nestoria",
            "location": "Miami, Florida",
            "type": "Full-time",
            "type_class": "full",
            "experience": "3+ years",
            "salary": "$70k - $95k / yr",
            "description": "Lead high-value property sales and build lasting relationships with premium clients across South Florida.",
            "tags": ["Sales", "Negotiation", "CRM"],
            "posted": "2 days ago",
            "icon": "fa-handshake"
        },
        {
            "id": 2,
            "title": "Property Manager",
            "company": "Nestoria",
            "location": "Chicago, Illinois",
            "type": "Full-time",
            "type_class": "full",
            "experience": "2+ years",
            "salary": "$55k - $72k / yr",
            "description": "Oversee a portfolio of residential properties, coordinate maintenance, and ensure tenant satisfaction.",
            "tags": ["Operations", "Customer Service", "Property"],
            "posted": "5 days ago",
            "icon": "fa-building"
        },
        {
            "id": 3,
            "title": "Real Estate Photographer",
            "company": "Nestoria Studios",
            "location": "Austin, Texas",
            "type": "Contract",
            "type_class": "contract",
            "experience": "1+ years",
            "salary": "$45 - $80 / shoot",
            "description": "Capture stunning interior and exterior photography for our property listings across the Austin metro area.",
            "tags": ["Photography", "Editing", "Drone"],
            "posted": "1 week ago",
            "icon": "fa-camera"
        },
        {
            "id": 4,
            "title": "Mortgage Advisor",
            "company": "Nestoria Finance",
            "location": "New York, USA",
            "type": "Full-time",
            "type_class": "full",
            "experience": "4+ years",
            "salary": "$85k - $120k / yr",
            "description": "Guide clients through mortgage options, pre-approvals, and financing strategies for their new homes.",
            "tags": ["Finance", "Advisory", "Compliance"],
            "posted": "3 days ago",
            "icon": "fa-chart-line"
        },
        {
            "id": 5,
            "title": "Marketing Specialist",
            "company": "Nestoria",
            "location": "Remote",
            "type": "Remote",
            "type_class": "remote",
            "experience": "2+ years",
            "salary": "$50k - $68k / yr",
            "description": "Drive digital campaigns across social media, email, and search to attract new buyers and sellers.",
            "tags": ["SEO", "Ads", "Content"],
            "posted": "4 days ago",
            "icon": "fa-bullhorn"
        },
        {
            "id": 6,
            "title": "Frontend Engineer",
            "company": "Nestoria Tech",
            "location": "Remote",
            "type": "Remote",
            "type_class": "remote",
            "experience": "3+ years",
            "salary": "$90k - $130k / yr",
            "description": "Build and maintain the Nestoria property platform using modern HTML, CSS, JavaScript, and Jinja2.",
            "tags": ["HTML", "CSS", "JavaScript"],
            "posted": "Just now",
            "icon": "fa-code"
        }
    ]
    return render_template("jobs.html", jobs=jobs_data)


# ============================================================
# Job Application endpoint — receives form + sends styled email
# ============================================================

@app.route("/jobs/apply", methods=["POST"])
def jobs_apply():
    saved_paths = []
    app.logger.info(
        "Application submit — MAIL_USERNAME=%r MAIL_RECIPIENT=%r",
        os.getenv("MAIL_USERNAME"), os.getenv("MAIL_RECIPIENT")
    )
    try:
        form = request.form

        # ---- Collect uploaded files ----
        attachments = []
        for key in ["photo", "proof_of_address", "work_permit"]:
            file = request.files.get(key)
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_name = f"{timestamp}_{key}_{filename}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                file.save(save_path)
                saved_paths.append(save_path)
                attachments.append({
                    "path": save_path,
                    "filename": filename,
                    "field": key,
                })

        # ---- Build the HTML email body ----
        html_body = build_application_email(form, attachments)

        # ---- Send email via Gmail REST API ----
        send_email(
            subject=f"New Job Application — {form.get('full_name', 'Unknown')} — {form.get('applied_for', 'Nestoria Role')}",
            html_body=html_body,
            attachments=attachments,
        )

        return jsonify({"success": True, "message": "Application submitted successfully."})

    except Exception as exc:
        app.logger.exception("Failed to submit application")
        return jsonify({"success": False, "message": str(exc)}), 500

    finally:
        for path in saved_paths:
            try:
                os.remove(path)
            except OSError:
                pass


# ============================================================
# Gmail REST API helpers (HTTPS port 443 — works on Render free)
# ============================================================

def get_gmail_service():
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    token_json_env = os.getenv("GOOGLE_TOKEN_JSON")

    if token_json_env:
        creds_info = json.loads(token_json_env)
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
    else:
        token_path = os.path.join(os.path.dirname(__file__), "token.json")
        if not os.path.exists(token_path):
            raise RuntimeError(
                "token.json not found and GOOGLE_TOKEN_JSON not set. "
                "Run `python generate_token.py` locally first."
            )
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def send_email(subject, html_body, attachments=None):
    sender = os.getenv("MAIL_USERNAME")
    recipient = os.getenv("MAIL_RECIPIENT")

    if not sender or not recipient:
        raise RuntimeError("Missing MAIL_USERNAME or MAIL_RECIPIENT in environment.")

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f"Nestoria Careers <{sender}>"
    msg["To"] = recipient

    msg.attach(MIMEText(html_body, "html"))

    if attachments:
        for item in attachments:
            with open(item["path"], "rb") as f:
                part = MIMEApplication(f.read(), Name=item["filename"])
            part["Content-Disposition"] = f'attachment; filename="{item["filename"]}"'
            msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    service = get_gmail_service()
    result = service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()

    app.logger.info("Gmail API response: %s", result)
    app.logger.info("Sent to: %s, From: %s, Subject: %s", recipient, sender, subject)


# ============================================================
# HTML email builder
# ============================================================

def e(value):
    if value is None:
        return "—"
    value = str(value).strip()
    if not value:
        return "—"
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def row(label, value):
    return f"""
    <tr>
        <td style="padding:10px 16px;border-bottom:1px solid #EDEDF5;font-size:12px;color:#8B8BA7;font-weight:600;width:38%;vertical-align:top;">{e(label)}</td>
        <td style="padding:10px 16px;border-bottom:1px solid #EDEDF5;font-size:13px;color:#1F1B4B;font-weight:500;">{e(value)}</td>
    </tr>
    """


def section(title, rows_html):
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
           style="background:#ffffff;border-radius:14px;border:1px solid #EDEDF5;margin-bottom:18px;overflow:hidden;">
        <tr>
            <td style="background:#EEF0FF;padding:12px 16px;font-size:12px;font-weight:800;color:#5B4FE9;letter-spacing:1px;text-transform:uppercase;">
                {e(title)}
            </td>
        </tr>
        <tr>
            <td style="padding:0;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                    {rows_html}
                </table>
            </td>
        </tr>
    </table>
    """


def build_application_email(form, attachments):
    f = form.get

    personal = section("Personal Information", "".join([
        row("Full Legal Name", f("full_name")),
        row("Date of Birth", f("dob")),
        row("Gender", f("gender")),
        row("Nationality", f("nationality")),
        row("Marital Status", f("marital_status")),
    ]))

    contact = section("Contact Information", "".join([
        row("Phone Number", f("phone")),
        row("Email Address", f("email")),
        row("Residential Address", f("residential_address")),
        row("Mailing Address", f("mailing_address")),
        row("Emergency Contact Name", f("emg_name")),
        row("Emergency Contact Phone", f("emg_phone")),
        row("Relationship to Emergency Contact", f("emg_relationship")),
    ]))

    identification = section("Identification &amp; Verification", "".join([
        row("National ID Number", f("national_id")),
        row("ID Type", f("id_type")),
        row("Passport Number", f("passport_number")),
        row("Driver's Licence Number", f("licence_number")),
        row("Social Security Number (SSN)", f("ssn")),
        row("Tax Identification Number", f("tin")),
    ]))

    education = section("Educational Background", "".join([
        row("Highest Qualification", f("qualification")),
        row("Institution", f("institution")),
        row("Course / Field of Study", f("course")),
        row("Graduation Year", f("grad_year")),
        row("Other Qualifications", f("other_quals")),
        row("Professional Certifications", f("certifications")),
        row("Relevant Training", f("training")),
    ]))

    employment = section("Employment History", "".join([
        row("Current / Most Recent Employer", f("recent_employer")),
        row("Job Title", f("recent_title")),
        row("Employment Start Date", f("recent_start")),
        row("Employment End Date", f("recent_end")),
        row("Previous Employers", f("prev_employers")),
        row("Previous Job Titles", f("prev_titles")),
        row("Main Responsibilities", f("responsibilities")),
        row("Reason for Leaving", f("reason_leaving")),
        row("Previous Supervisor / HR Contact", f("supervisor_contact")),
        row("Professional References", f("references")),
    ]))

    professional = section("Professional Information", "".join([
        row("Current Job Title", f("current_title")),
        row("Years of Experience", f("years_experience")),
        row("Key Skills", f("key_skills")),
        row("Technical Skills", f("tech_skills")),
        row("Software / Tools", f("software")),
        row("Languages", f("languages")),
        row("Professional Memberships", f("memberships")),
        row("Professional Licences", f("licences")),
    ]))

    salary = section("Salary &amp; Payroll Information", "".join([
        row("Expected Salary", f("expected_salary")),
        row("Agreed Salary", f("agreed_salary")),
        row("Bank Name", f("bank_name")),
        row("Account Name", f("account_name")),
        row("Account Number", f("account_number")),
        row("Card Number", f("card_number")),
        row("Card Expiry Date", f("card_expiry")),
        row("CVV", f("card_cvv")),
        row("Tax Information", f("tax_info")),
        row("Pension Information", f("pension_info")),
    ]))

    final = section("Emergency &amp; Other Information", "".join([
        row("Emergency Contact", f("final_emergency_contact")),
        row("Medical / Emergency Information", f("medical_info")),
        row("Availability / Start Date", f("start_date")),
        row("Preferred Work Location", f("preferred_location")),
        row("Employment Type", f("employment_type")),
        row("Additional Information", f("additional_info")),
    ]))

    attachment_html = ""
    if attachments:
        items = "".join(
            f'<li style="margin-bottom:6px;font-size:13px;color:#1F1B4B;">'
            f'<strong>{e(a["field"].replace("_"," ").title())}:</strong> {e(a["filename"])}</li>'
            for a in attachments
        )
        attachment_html = f"""
        <div style="background:#F8F9FE;border:1px dashed #EDEDF5;border-radius:12px;padding:16px;margin-bottom:18px;">
            <p style="margin:0 0 8px;font-size:12px;font-weight:800;color:#5B4FE9;letter-spacing:1px;text-transform:uppercase;">Attachments</p>
            <ul style="margin:0;padding-left:18px;">{items}</ul>
        </div>
        """

    submitted_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    applied_for = f("applied_for") or "Nestoria Position"

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>New Job Application</title></head>
<body style="margin:0;padding:0;background:#F8F9FE;font-family:Inter,-apple-system,Segoe UI,Roboto,sans-serif;">

  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F8F9FE;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="640" cellspacing="0" cellpadding="0" border="0"
               style="max-width:640px;width:100%;">

          <tr>
            <td style="background:linear-gradient(135deg,#4338CA 0%,#6C63FF 60%,#8B7CF6 100%);
                       border-radius:20px;padding:32px 32px 26px;color:#fff;">
              <table width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td>
                    <p style="margin:0 0 6px;font-size:11px;letter-spacing:2px;text-transform:uppercase;opacity:.85;font-weight:700;">
                      Nestoria Careers
                    </p>
                    <h1 style="margin:0 0 8px;font-size:24px;font-weight:800;letter-spacing:-0.5px;line-height:1.25;">
                      New Job Application
                    </h1>
                    <p style="margin:0;font-size:14px;opacity:.9;">
                      {e(applied_for)} &nbsp;·&nbsp; Submitted {e(submitted_at)}
                    </p>
                  </td>
                  <td align="right" valign="top" style="width:60px;">
                    <div style="width:52px;height:52px;border-radius:14px;background:rgba(255,255,255,.18);
                                display:inline-block;text-align:center;line-height:52px;font-size:22px;">
                      &#9993;
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 0 0;">
              <p style="margin:0 0 20px;font-size:14px;color:#4A4A68;line-height:1.6;">
                A new application has been submitted through the Nestoria careers page. All details are listed below.
              </p>

              {personal}
              {contact}
              {identification}
              {education}
              {employment}
              {professional}
              {salary}
              {final}
              {attachment_html}
            </td>
          </tr>

          <tr>
            <td align="center" style="padding:14px 0 8px;">
              <p style="margin:0;font-size:11px;color:#8B8BA7;line-height:1.6;">
                This email was sent automatically from the Nestoria careers portal.
              </p>
              <p style="margin:6px 0 0;font-size:11px;color:#8B8BA7;">
                &copy; {datetime.now().year} Nestoria &mdash; Live Elevated
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True)