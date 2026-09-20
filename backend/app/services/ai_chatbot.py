import os
import google.generativeai as genai
from app.core.config import settings

# Initialize Gemini if key is provided
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

STATIC_KNOWLEDGE = {
    "transparency": "NGO Transparency Scores are calculated out of 100 based on Document Completeness (60% weight, including audit reports and registration credentials), Active Donation Verification (40%), minus any penalties from active AI Fraud Detection flags.",
    "ledger": "Every donation and NGO verification event is appended to an immutable SHA-256 cryptographic hash-chain ledger. Each block contains a block hash and previous block hash. Anyone can verify chain integrity in real-time on our Blockchain Explorer page.",
    "fraud": "The AI Fraud Detection system continuously scans financial ratios, expense-to-beneficiary consistency, registration numbers, and transaction velocities. Anomalies generate real-time alerts (LOW, MEDIUM, HIGH, CRITICAL) for platform administrators.",
    "donate": "To donate safely: 1. Browse approved NGOs on the Public Transparency Portal. 2. Inspect their Transparency Score and verified document status. 3. Click 'Donate' to log a secure, cryptographically tracked contribution.",
    "verification": "NGOs must register with their official Registration Number, Tax ID, and upload compliance documents (Audit Reports, Tax Exempt Certificates, ID proofs). Platform Administrators review documents before approving an NGO for public donations."
}


class AIChatbotService:

    @classmethod
    def get_response(cls, query: str) -> str:
        q_lower = query.lower()

        # Try Gemini API if key exists
        if settings.GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    "You are the NGO Impact Data Commons AI Assistant. Answer the user's question clearly, concisely, "
                    "and professionally regarding NGO transparency, blockchain donations, fraud detection, and donation safety.\n\n"
                    f"User Query: {query}"
                )
                res = model.generate_content(prompt)
                if res and res.text:
                    return res.text
            except Exception:
                pass # Fallback to static KB

        # Fallback KB search logic
        if any(w in q_lower for w in ["score", "calculate", "rating", "transparency"]):
            return STATIC_KNOWLEDGE["transparency"]
        elif any(w in q_lower for w in ["ledger", "blockchain", "block", "hash", "immutable", "verify"]):
            return STATIC_KNOWLEDGE["ledger"]
        elif any(w in q_lower for w in ["fraud", "detect", "flag", "fake", "scam"]):
            return STATIC_KNOWLEDGE["fraud"]
        elif any(w in q_lower for w in ["donate", "how to donate", "payment", "give"]):
            return STATIC_KNOWLEDGE["donate"]
        elif any(w in q_lower for w in ["register", "approve", "verify", "document", "admin"]):
            return STATIC_KNOWLEDGE["verification"]

        return (
            "Welcome to NGO Impact Data Commons! I am your AI Transparency Assistant. "
            "You can ask me about how our Transparency Scores work, how our SHA-256 Blockchain Ledger secures donations, "
            "how our AI Fraud Detection works, or how to register an NGO."
        )
