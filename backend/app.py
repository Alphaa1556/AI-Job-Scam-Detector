from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import PyPDF2
from PIL import Image
import pytesseract
import cv2
import numpy as np

# ---------------- CONFIG ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../frontend/templates")
)
CORS(app)

# ---------------- HELPERS ----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- ROUTES ----------------
def detect_scam_rules(text):
    text = text.lower()

    rules = [
        # 🚨 URGENCY / PRESSURE
        ("limited time offer", 15, "Artificial urgency"),
        ("respond within 24 hours", 20, "Short deadline"),
        ("immediate joining", 15, "Immediate joining pressure"),
        ("final warning", 20, "Threat language"),
        ("last chance", 15, "Last chance pressure"),
        ("urgent requirement", 15, "Urgent hiring"),
        ("failure to respond will cancel", 25, "Threat of cancellation"),
        ("reply immediately", 15, "Forced reply"),
        ("confirm today", 15, "Forced confirmation"),

        # 💰 MONEY SCAMS
        ("earn ₹30,000", 25, "Unrealistic income"),
        ("₹50,000 per week", 30, "High weekly salary"),
        ("daily income", 25, "Daily income promise"),
        ("no experience required", 15, "No experience claim"),
        ("work only 1-2 hours", 25, "Low effort high pay"),
        ("guaranteed income", 30, "Guaranteed income"),
        ("100% job guarantee", 30, "Fake guarantee"),
        ("instant promotion", 20, "Instant promotion"),
        ("60 lpa", 35, "Unrealistic fresher salary"),
        ("easy money", 30, "Easy money"),

        # 🎁 TOO GOOD TO BE TRUE
        ("free international trip", 25, "Free international trip"),
        ("company pays all taxes", 20, "Pays personal taxes"),
        ("no bond", 10, "No bond highlight"),
        ("no risk", 20, "Zero risk"),
        ("joining bonus without joining", 35, "Fake joining bonus"),
        ("work anytime", 15, "Unlimited freedom"),
        ("unlimited earnings", 30, "Unlimited earnings"),

        # ❌ NO INTERVIEW
        ("selected without interview", 40, "No interview"),
        ("based on resume only", 30, "Resume-only selection"),
        ("no interview required", 40, "Interview skipped"),
        ("auto-selected", 35, "Auto selection"),
        ("direct offer letter", 25, "Direct offer"),
        ("hr round skipped", 30, "HR skipped"),
        ("final selection done", 25, "No hiring process"),

        # 🏢 FAKE COMPANY
        ("leading company", 15, "Vague company"),
        ("reputed client", 15, "Unknown client"),
        ("international company", 20, "Foreign claim"),
        ("based in usa", 20, "USA claim"),
        ("based in uk", 20, "UK claim"),
        ("company confidential", 25, "Company hidden"),
        ("due to privacy reasons", 25, "Privacy excuse"),
        ("our hr team", 15, "No HR names"),
    ]

    score = 0
    reasons = []

    for keyword, weight, reason in rules:
        if keyword in text:
            score += weight
            reasons.append(reason)

    score = min(score, 100)

    if score >= 70:
        verdict = "🚨 HIGH RISK JOB SCAM"
    elif score >= 40:
        verdict = "⚠️ SUSPICIOUS"
    else:
        verdict = "✅ LIKELY SAFE"

    return score, verdict, reasons
def detect_contact_risk(text):
    text = text.lower()

    score = 0
    reasons = []

    free_email_domains = [
        "gmail.com", "yahoo.com", "outlook.com",
        "hotmail.com", "rediffmail.com", "icloud.com"
    ]

    suspicious_keywords = [
        "contact on whatsapp",
        "whatsapp number",
        "telegram",
        "dm us",
        "text us",
        "reach us on whatsapp",
        "hr whatsapp",
        "only whatsapp",
        "no calls"
    ]

    # Free email domain detection
    for domain in free_email_domains:
        if domain in text:
            score += 25
            reasons.append("Uses free email domain instead of company email")
            break

    # WhatsApp / Telegram hiring
    for word in suspicious_keywords:
        if word in text:
            score += 20
            reasons.append("Hiring via WhatsApp / Telegram")
            break

    # Generic HR wording without company domain
    if "hr@" in text and not any(domain in text for domain in free_email_domains):
        score += 10
        reasons.append("Generic HR email without verified company domain")

    score = min(score, 100)

    return score, reasons
import re

def detect_online_presence_risk(text):
    text = text.lower()
    score = 0
    reasons = []

    # Website detection
    website_regex = r"(https?://[^\s]+|www\.[^\s]+)"
    websites = re.findall(website_regex, text)

    suspicious_domains = [".xyz", ".site", ".blogspot", ".free", ".online"]
    shorteners = ["bit.ly", "tinyurl", "t.co", "rb.gy"]

    if not websites:
        score += 20
        reasons.append("No official company website mentioned")
    else:
        for site in websites:
            if any(sd in site for sd in suspicious_domains):
                score += 15
                reasons.append("Uses suspicious website domain")
            if any(short in site for short in shorteners):
                score += 15
                reasons.append("Uses URL shortener instead of official website")
            if not site.startswith("https"):
                score += 10
                reasons.append("Website not using HTTPS")

    # LinkedIn detection
    has_linkedin = "linkedin.com" in text
    has_company_linkedin = "linkedin.com/company" in text

    if not has_linkedin:
        score += 20
        reasons.append("No LinkedIn presence found")
    elif not has_company_linkedin:
        score += 10
        reasons.append("Only personal LinkedIn found, no company page")

    score = min(score, 100)
    return score, reasons
def detect_logo_authenticity(image_path, extracted_text):
    score = 0
    reasons = []

    try:
        image = cv2.imread(image_path)

        if image is None:
            score += 20
            reasons.append("No identifiable company logo found")
            return score, reasons

        height, width, _ = image.shape

        # 1️⃣ Low resolution check
        if width < 200 or height < 200:
            score += 15
            reasons.append("Low-resolution logo image")

        # 2️⃣ Blur detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < 100:
            score += 15
            reasons.append("Blurry or unclear company logo")

        # 3️⃣ Aspect ratio distortion
        aspect_ratio = width / height
        if aspect_ratio < 0.3 or aspect_ratio > 4:
            score += 10
            reasons.append("Logo appears distorted or improperly cropped")

        # 4️⃣ Generic logo detection (low color variance)
        color_variance = np.var(image)
        if color_variance < 500:
            score += 15
            reasons.append("Generic or stock-style logo detected")

        # 5️⃣ Logo but no online presence
        if ("http" not in extracted_text.lower()
            and "linkedin" not in extracted_text.lower()):
            score += 20
            reasons.append("Logo present but no verifiable company online presence")

    except Exception:
        score += 20
        reasons.append("Error while analyzing logo authenticity")

    score = min(score, 40)  # cap logo risk
    return score, reasons



# ---------------- HOME ROUTE ----------------
@app.route("/")
def home():
    return render_template("upload.html")


# ---------------- ANALYZE ROUTE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # 1. Validate file
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file type"}), 400

        # 2. Save file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        extracted_text = ""
        ext = file.filename.rsplit(".", 1)[1].lower()

        # 3. Extract text
        if ext == "pdf":
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted_text += page.extract_text() or ""
        else:
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image)

        # ---------------- PHASE 2 + 3 ANALYSIS ----------------

        # Rule-based scam detection
        rule_score, _, rule_reasons = detect_scam_rules(extracted_text)

        # Contact / email / phone risk
        contact_score, contact_reasons = detect_contact_risk(extracted_text)

        # Website + LinkedIn presence risk
        presence_score, presence_reasons = detect_online_presence_risk(extracted_text)

        # Logo authenticity (images only)
        logo_score = 0
        logo_reasons = []
        if ext in ["png", "jpg", "jpeg"]:
            logo_score, logo_reasons = detect_logo_authenticity(
                file_path, extracted_text
            )

        # Final scoring
        final_score = min(
            rule_score + contact_score + presence_score + logo_score,
            100
        )

        final_reasons = (
            rule_reasons
            + contact_reasons
            + presence_reasons
            + logo_reasons
        )

        # Final verdict
        if final_score >= 70:
            final_verdict = "🚨 HIGH RISK JOB SCAM"
        elif final_score >= 40:
            final_verdict = "⚠️ SUSPICIOUS"
        else:
            final_verdict = "✅ LIKELY SAFE"

        # 4. Response
        return jsonify({
            "status": "success",
            "filename": file.filename,
            "file_type": ext,
            "text_length": len(extracted_text),
            "scam_score": final_score,
            "verdict": final_verdict,
            "reasons": final_reasons,
            "text_preview": extracted_text[:1000]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)








