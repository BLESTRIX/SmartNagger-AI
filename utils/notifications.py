import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import streamlit as st


# ---------------------------------------------------------------------------
# Helper: safely read from st.secrets without raising KeyError
# ---------------------------------------------------------------------------
def _secret(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# NotificationService
#
# Send priority:
#   1. SendGrid HTTP API  -> works on Streamlit Cloud (HTTPS / port 443)
#   2. SMTP fallback      -> works locally when SENDGRID_API_KEY is absent
#
# Required secrets / env-vars:
#   SendGrid : SENDGRID_API_KEY  +  SENDER_EMAIL
#   SMTP     : SMTP_SERVER  SMTP_PORT  SENDER_EMAIL  SENDER_PASSWORD
# ---------------------------------------------------------------------------
class NotificationService:

    def __init__(self):
        # SendGrid
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY",
                                          _secret("SENDGRID_API_KEY"))

        # Shared sender address -- strip whitespace immediately on load
        # This is the most common cause of SendGrid 403 errors
        raw_sender = os.getenv("SENDER_EMAIL", _secret("SENDER_EMAIL"))
        self.sender_email = raw_sender.strip().lower() if raw_sender else ""

        # SMTP (fallback)
        self.smtp_server   = os.getenv("SMTP_SERVER",
                                       _secret("SMTP_SERVER", "smtp.gmail.com"))
        self.smtp_port     = int(os.getenv("SMTP_PORT",
                                           _secret("SMTP_PORT", "587")))
        self.smtp_password = os.getenv("SENDER_PASSWORD",
                                       _secret("SENDER_PASSWORD"))

        # Determine mode
        self._use_sendgrid = bool(self.sendgrid_api_key)

        # DEBUG: print exactly what was loaded so mismatches are visible in logs
        masked_key = "NOT SET"
        if self.sendgrid_api_key:
            k = self.sendgrid_api_key
            masked_key = k[:6] + "..." + k[-4:] if len(k) > 10 else "SET"

        print(f"[NotificationService DEBUG] SENDGRID_API_KEY : {masked_key}")
        print(f"[NotificationService DEBUG] SENDER_EMAIL repr: {repr(self.sender_email)}")

        if self._use_sendgrid:
            print("[NotificationService] Mode: SendGrid API")
        elif self.sender_email and self.smtp_password:
            print("[NotificationService] Mode: SMTP fallback")
        else:
            print("[NotificationService] WARNING: No email credentials configured.")

    # -----------------------------------------------------------------------
    # PUBLIC -- unified send entry-point
    # -----------------------------------------------------------------------
    def send_email(self, recipient_email: str, subject: str, body_html: str) -> bool:
        """
        Send an HTML email.

        Tries SendGrid first (if SENDGRID_API_KEY is present), then
        automatically falls back to SMTP.

        Returns True on success, False on failure.
        """
        if not self.sender_email:
            print("[NotificationService] SENDER_EMAIL not configured -- skipping.")
            return False

        if self._use_sendgrid:
            success = self._send_via_sendgrid(recipient_email, subject, body_html)
            if success:
                return True
            print("[NotificationService] SendGrid failed -- attempting SMTP fallback.")

        if self.smtp_password:
            return self._send_via_smtp(recipient_email, subject, body_html)

        print("[NotificationService] No working email method available.")
        return False

    # -----------------------------------------------------------------------
    # PRIVATE -- SendGrid (uses only stdlib urllib, no extra pip install)
    # -----------------------------------------------------------------------
    def _send_via_sendgrid(self, recipient_email: str,
                           subject: str, body_html: str) -> bool:
        import json
        import urllib.request
        import urllib.error

        clean_recipient = recipient_email.strip().lower()

        # DEBUG: log exactly what we are sending -- makes 403 mismatches obvious
        print(f"[SendGrid DEBUG] from    : {repr(self.sender_email)}")
        print(f"[SendGrid DEBUG] to      : {repr(clean_recipient)}")
        print(f"[SendGrid DEBUG] subject : {repr(subject)}")

        payload = {
            "personalizations": [
                {"to": [{"email": clean_recipient}]}
            ],
            "from":    {"email": self.sender_email},
            "subject": subject,
            "content": [{"type": "text/html", "value": body_html}]
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url     = "https://api.sendgrid.com/v3/mail/send",
            data    = data,
            method  = "POST",
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type":  "application/json",
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 202):
                    print(f"[SendGrid] Email sent to {clean_recipient} (HTTP {resp.status})")
                    return True
                print(f"[SendGrid] Unexpected status {resp.status}")
                return False

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"[SendGrid] HTTPError {e.code}: {body}")
            return False

        except Exception as e:
            print(f"[SendGrid] Error: {e}")
            return False

    # -----------------------------------------------------------------------
    # PRIVATE -- SMTP with STARTTLS (works locally)
    # -----------------------------------------------------------------------
    def _send_via_smtp(self, recipient_email: str,
                       subject: str, body_html: str) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"]    = self.sender_email
            message["To"]      = recipient_email
            message.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(self.sender_email, self.smtp_password)
                server.send_message(message)

            print(f"[SMTP] Email sent to {recipient_email}")
            return True

        except Exception as e:
            print(f"[SMTP] Error: {e}")
            return False

    # -----------------------------------------------------------------------
    # SMS (simulated -- replace with Twilio / MSG91 in production)
    # -----------------------------------------------------------------------
    def send_sms(self, phone_number: str, message: str) -> bool:
        print(f"[SMS SIMULATION] To: {phone_number}")
        print(f"[SMS SIMULATION] Message: {message}")
        return True

    # -----------------------------------------------------------------------
    # Pre-built email templates
    # -----------------------------------------------------------------------
    def send_complaint_confirmation(self, recipient_email: str,
                                    tracking_id: str,
                                    issue_type: str,
                                    location: str) -> bool:
        """Send complaint-submission confirmation email."""
        subject = f"Complaint Submitted - {tracking_id}"
        body_html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                               color: white; padding: 20px; text-align: center;
                               border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px;
                                border-radius: 0 0 10px 10px; }}
                    .tracking-id {{ background: #4CAF50; color: white; padding: 15px;
                                    text-align: center; font-size: 24px; font-weight: bold;
                                    border-radius: 5px; margin: 20px 0; }}
                    .details {{ background: white; padding: 20px; border-radius: 5px;
                                margin: 20px 0; }}
                    .detail-row {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
                    .label {{ font-weight: bold; color: #667eea; }}
                    .footer {{ text-align: center; color: #777; margin-top: 30px;
                               font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>SmartNaggar AI</h1>
                        <p>Complaint Submitted Successfully</p>
                    </div>
                    <div class="content">
                        <p>Dear Citizen,</p>
                        <p>Thank you for reporting a civic issue. Your complaint has been
                           successfully registered in our system.</p>
                        <div class="tracking-id">
                            Tracking ID: {tracking_id}
                        </div>
                        <div class="details">
                            <div class="detail-row">
                                <span class="label">Issue Type:</span> {issue_type}
                            </div>
                            <div class="detail-row">
                                <span class="label">Location:</span> {location}
                            </div>
                            <div class="detail-row">
                                <span class="label">Status:</span> Pending Review
                            </div>
                        </div>
                        <p><strong>What happens next?</strong></p>
                        <ul>
                            <li>Your complaint will be reviewed by our team</li>
                            <li>It will be assigned to the appropriate department</li>
                            <li>You will receive updates via email and SMS</li>
                            <li>Track your complaint status anytime using the tracking ID</li>
                        </ul>
                        <p><strong>Important:</strong> Please save your Tracking ID for
                           future reference.</p>
                        <div class="footer">
                            <p>SmartNaggar AI - Making Cities Better Together</p>
                            <p>Visit: www.smartnaggar.ai | Email: support@smartnaggar.ai</p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        return self.send_email(recipient_email, subject, body_html)

    def send_status_update(self, recipient_email: str,
                           tracking_id: str,
                           old_status: str,
                           new_status: str,
                           admin_notes: str = "") -> bool:
        """Send complaint status-update email."""
        subject = f"Status Update - {tracking_id}"
        status_colors = {
            "Pending":      "#FFA726",
            "Under Review": "#42A5F5",
            "Assigned":     "#66BB6A",
            "In Progress":  "#26C6DA",
            "Resolved":     "#4CAF50",
            "Rejected":     "#EF5350",
        }
        status_color = status_colors.get(new_status, "#999")
        notes_html   = (f"<p><strong>Admin Notes:</strong> {admin_notes}</p>"
                        if admin_notes else "")

        body_html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                               color: white; padding: 20px; text-align: center;
                               border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px;
                                border-radius: 0 0 10px 10px; }}
                    .status-update {{ background: {status_color}; color: white; padding: 20px;
                                      text-align: center; font-size: 20px; font-weight: bold;
                                      border-radius: 5px; margin: 20px 0; }}
                    .details {{ background: white; padding: 20px; border-radius: 5px;
                                margin: 20px 0; }}
                    .footer {{ text-align: center; color: #777; margin-top: 30px;
                               font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Status Update</h1>
                        <p>Tracking ID: {tracking_id}</p>
                    </div>
                    <div class="content">
                        <p>Dear Citizen,</p>
                        <p>Your complaint status has been updated.</p>
                        <div class="status-update">
                            {old_status} to {new_status}
                        </div>
                        <div class="details">
                            <p><strong>Tracking ID:</strong> {tracking_id}</p>
                            <p><strong>New Status:</strong> {new_status}</p>
                            {notes_html}
                        </div>
                        <p>You can track your complaint anytime using the tracking ID
                           on our platform.</p>
                        <div class="footer">
                            <p>SmartNaggar AI - Making Cities Better Together</p>
                            <p>Visit: www.smartnaggar.ai | Email: support@smartnaggar.ai</p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        return self.send_email(recipient_email, subject, body_html)

    def send_complaint_confirmation_sms(self, phone_number: str,
                                        tracking_id: str) -> bool:
        """Send SMS confirmation after complaint submission."""
        msg = (f"Your complaint has been registered. "
               f"Tracking ID: {tracking_id}. "
               f"Track status at smartnaggar.ai")
        return self.send_sms(phone_number, msg)

    def send_status_update_sms(self, phone_number: str,
                               tracking_id: str,
                               new_status: str) -> bool:
        """Send SMS when complaint status changes."""
        msg = (f"Complaint {tracking_id} status updated to: {new_status}. "
               f"Visit smartnaggar.ai for details.")
        return self.send_sms(phone_number, msg)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_notification_service() -> NotificationService:
    return NotificationService()