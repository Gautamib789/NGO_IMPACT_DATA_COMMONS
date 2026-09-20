import smtplib
import socket
import logging
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def _send_email(to_email: str, subject: str, html_body: str) -> dict:
        """
        Sends email via SMTP if SMTP_HOST is configured in backend/.env.
        If SMTP_HOST is missing, operates in Development Mock Mode by writing to mock_email.txt and server console.
        Raises HTTPException(503) if SMTP is configured but delivery fails.
        """
        if not settings.SMTP_HOST or not settings.SMTP_HOST.strip():
            # No SMTP configured — Development / Mock Fallback Mode
            match = re.search(r'<h1[^>]*>(\d+)</h1>', html_body)
            otp_code = match.group(1) if match else "N/A"
            
            print(f"\n{'='*60}")
            print(f"  📧 EMAIL (MOCK FALLBACK - SMTP_HOST not set in .env)")
            print(f"  To      : {to_email}")
            print(f"  Subject : {subject}")
            print(f"  OTP CODE: {otp_code}  ← USE THIS CODE")
            print(f"{'='*60}\n")
            
            try:
                with open("mock_email.txt", "w") as f:
                    f.write(f"To: {to_email}\nSubject: {subject}\nOTP: {otp_code}\n\n{html_body}")
            except Exception as e:
                logger.warning(f"Could not write mock_email.txt: {e}")
                
            return {
                "delivered": False,
                "dev_mode": True,
                "message": "Development mode: SMTP host is not configured in backend/.env. Code logged to mock_email.txt and server console."
            }

        # Real SMTP Delivery Mode
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email

        part = MIMEText(html_body, "html")
        msg.attach(part)

        try:
            timeout_sec = 4
            if settings.SMTP_PORT == 465 or settings.SMTP_USE_SSL:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout_sec) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout_sec) as server:
                    if settings.SMTP_USE_TLS:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully via SMTP to {to_email}")
            return {
                "delivered": True,
                "dev_mode": False,
                "message": f"Verification code sent to {to_email} via SMTP."
            }
            
        except Exception as e:
            err_msg = f"SMTP error ({type(e).__name__}): {str(e)}"
            logger.warning(f"Failed to send email to {to_email}: {err_msg}")
            
            match = re.search(r'<h1[^>]*>(\d+)</h1>', html_body)
            otp_code = match.group(1) if match else "N/A"
            
            print(f"\n{'='*60}")
            print(f"  ⚠️ SMTP DELIVERY FALLBACK ({type(e).__name__})")
            print(f"  To      : {to_email}")
            print(f"  Subject : {subject}")
            print(f"  OTP CODE: {otp_code}  ← USE THIS CODE (FALLBACK LOGGED TO MOCK_EMAIL.TXT)")
            print(f"{'='*60}\n")
            
            try:
                with open("mock_email.txt", "w") as f:
                    f.write(f"To: {to_email}\nSubject: {subject}\nOTP: {otp_code}\n\n{html_body}")
            except Exception:
                pass
                
            return {
                "delivered": False,
                "dev_mode": True,
                "message": f"Development fallback mode active: SMTP delivery failed ({type(e).__name__}). Code logged to mock_email.txt and server console."
            }


    @staticmethod
    def send_login_otp(email: str, otp: str) -> dict:
        subject = "Your NGO Impact Data Commons Login Code"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; text-align: center; color: #333;">
                <h2>Login Authentication</h2>
                <p>You are attempting to log in to the NGO Impact Data Commons platform.</p>
                <p>Your one-time password (OTP) is:</p>
                <h1 style="font-size: 36px; letter-spacing: 4px; color: #1E3A8A; background-color: #F3F4F6; padding: 20px; display: inline-block; border-radius: 8px;">{otp}</h1>
                <p>This code will expire in 5 minutes.</p>
                <p style="color: #666; font-size: 12px; margin-top: 40px;">If you did not request this, please ignore this email.</p>
            </body>
        </html>
        """
        return EmailService._send_email(email, subject, body)

    @staticmethod
    def send_password_reset_otp(email: str, otp: str) -> dict:
        subject = "NGO Impact Data Commons Password Reset"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; text-align: center; color: #333;">
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password.</p>
                <p>Your one-time verification code is:</p>
                <h1 style="font-size: 36px; letter-spacing: 4px; color: #DC2626; background-color: #FEF2F2; padding: 20px; display: inline-block; border-radius: 8px;">{otp}</h1>
                <p>This code will expire in 5 minutes.</p>
                <p style="color: #666; font-size: 12px; margin-top: 40px;">If you did not request a password reset, please secure your account immediately.</p>
            </body>
        </html>
        """
        return EmailService._send_email(email, subject, body)

