from flask import Flask, request, jsonify

app = Flask(__name__)

# ==============================
# SCAM KEYWORDS WITH WEIGHTAGE
# ==============================
SCAM_KEYWORDS = {
    # Urgency & pressure
    "limited time offer": 15,
    "respond within 24 hours": 20,
    "immediate joining": 20,
    "final warning": 20,
    "last chance": 15,
    "urgent requirement": 15,
    "failure to respond will cancel offer": 25,
    "reply immediately": 15,
    "confirm today": 15,
    "no further extensions": 15,

    # Unrealistic income promises
    "earn ₹30,000": 30,
    "₹50,000 per week": 30,
    "daily income": 25,
    "freshers earn ₹60 lpa": 40,
    "guaranteed income": 30,
    "100% job guarantee": 35,
    "easy money": 30,
    "instant promotion": 25,

    # Too-good-to-be-true benefits
    "free international trip": 30,
    "company pays all taxes": 25,
    "no bond": 20,
    "joining bonus without joining": 40,
    "work anytime anywhere": 20,
    "unlimited earnings": 25,

    # No selection process
    "selected without interview": 35,
    "based on resume only": 25,
    "no interview required": 35,
    "auto-selected": 30,
    "direct offer letter": 25,
    "hr round skipped": 30,
    "final selection done": 20,

    # Fake company identity
    "leading company": 20,
    "reputed client": 15,
    "international company": 20,
    "company confidential": 25,
    "privacy reasons": 20,
    "our hr team": 15
}

# ==============================
# HOME ROUTE
# ==============================
@app.route("/")
def home():
    return "AI Job Scam Detector Backend Running"

# ==============================
# ANALYZE ROUTE
# ==============================
@app.route("/analyze", methods=["POST"])
def analyze_offer():
    data = request.json
    text = data.get("text", "").lower()

    # Normalize special characters
    text = text.replace("–", "-")

    score = 0
    reasons = []

    for keyword, weight in SCAM_KEYWORDS.items():
        if keyword in text:
            score += weight
            reasons.append(f"Detected suspicious phrase: '{keyword}'")

    # Risk classification
    if score >= 80:
        risk_level = "High Risk"
    elif score >= 40:
        risk_level = "Suspicious"
    else:
        risk_level = "Safe"

    return jsonify({
        "risk_score": score,
        "risk_level": risk_level,
        "reasons": reasons
    })

# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
