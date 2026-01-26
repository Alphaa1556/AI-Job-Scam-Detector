
import os
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

import PyPDF2
import pdfplumber
from PIL import Image
import pytesseract
import cv2
import numpy as np

# ======================
# TESSERACT PATH (WINDOWS)
# ======================
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Janhavi\tesseract.exe"

# ======================
# BASIC CONFIG
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
CORS(app)

# ======================
# HELPERS
# ======================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ======================
# TEXT EXTRACTION (PDF + OCR)
# ======================
def extract_text_from_file(file_path, ext):
    text = ""

    if ext == "pdf":
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""

    else:
        # ✅ OCR FIX (padding avoids missing first letters)
        image = cv2.imread(file_path)
        image = cv2.copyMakeBorder(
            image, 30, 30, 50, 30,
            cv2.BORDER_CONSTANT,
            value=[255, 255, 255]
        )
        text = pytesseract.image_to_string(image, config="--psm 6")

    return text.strip()

# ======================
# LOGO AUTHENTICITY CHECK
# ======================
def logo_authenticity_check(file_path):
    score = 0
    reasons = []

    image = cv2.imread(file_path)
    if image is None:
        return 20, ["No identifiable company logo found"]

    h, w, _ = image.shape

    if w < 200 or h < 200:
        score += 15
        reasons.append("Low-resolution company logo")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur < 100:
        score += 15
        reasons.append("Blurry or unclear company logo")

    color_variance = np.var(image)
    if color_variance < 500:
        score += 15
        reasons.append("Generic or stock-style logo detected")

    return score, reasons

# ======================
# ONLINE PRESENCE CHECK
# ======================
def online_presence_check(text):
    score = 0
    reasons = []

    websites = re.findall(r"(https?://[^\s]+|www\.[^\s]+)", text)
    if not websites:
        score += 20
        reasons.append("No official company website mentioned")

    if "linkedin.com" not in text:
        score += 20
        reasons.append("No LinkedIn presence found")

    return score, reasons

# ======================
# SCAM ANALYSIS RULES
# ======================
def analyze_text(text):
    text = text.lower()

    rules = [
        ("immediate joining", 15, "Immediate joining pressure"),
        ("respond within", 20, "Short response deadline"),
        ("no interview", 35, "No interview process"),
        ("registration fee", 40, "Mentions registration fee"),
        ("processing fee", 40, "Asks for processing fee"),
        ("whatsapp", 20, "Hiring via WhatsApp"),
        ("telegram", 20, "Hiring via Telegram"),
        ("guaranteed job", 30, "Guarantees job"),
        ("no experience required", 15, "No experience claim"),
        ("earn ₹", 25, "Unrealistic salary promise"),
        ("limited time", 15, "Artificial urgency"),
    ]

    score = 0
    reasons = []

    for keyword, weight, reason in rules:
        if keyword in text:
            score += weight
            reasons.append(reason)

    return score, reasons

# ======================
# AI SUMMARY GENERATOR
# ======================
def generate_summary(score, verdict, reasons):
    if score >= 70:
        level = "highly risky"
    elif score >= 40:
        level = "potentially suspicious"
    else:
        level = "likely safe"

    if reasons:
        key_reasons = ", ".join(reasons[:3])
        return (
            f"This offer letter appears {level}. "
            f"The analysis detected concerns such as {key_reasons}. "
            f"It is recommended to verify the company through official sources "
            f"before taking any action."
        )
    else:
        return (
            "No major scam indicators were detected in this offer letter. "
            "However, users are advised to independently verify the company "
            "before accepting the offer."
        )

# ======================
# ROUTES
# ======================
@app.route("/")
def home():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
def analyze_offer():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file type"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        ext = filename.rsplit(".", 1)[1].lower()
        extracted_text = extract_text_from_file(file_path, ext)

        rule_score, rule_reasons = analyze_text(extracted_text)
        presence_score, presence_reasons = online_presence_check(extracted_text)

        logo_score, logo_reasons = (0, [])
        if ext in ["png", "jpg", "jpeg"]:
            logo_score, logo_reasons = logo_authenticity_check(file_path)

        final_score = min(rule_score + presence_score + logo_score, 100)
        reasons = rule_reasons + presence_reasons + logo_reasons

        if final_score >= 70:
            verdict = "🚨 HIGH RISK JOB SCAM"
        elif final_score >= 40:
            verdict = "⚠️ SUSPICIOUS"
        else:
            verdict = "✅ LIKELY SAFE"

        summary = generate_summary(final_score, verdict, reasons)

        return jsonify({
            "status": "success",
            "filename": filename,
            "file_type": ext,
            "scam_score": final_score,
            "verdict": verdict,
            "summary": summary,
            "reasons": reasons
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ======================
# RUN SERVER
# ======================
if __name__ == "__main__":
   if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
