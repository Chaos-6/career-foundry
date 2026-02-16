"""
Email notification service.

Sends transactional emails via SMTP (configurable for SendGrid/SES later).
Uses BackgroundTasks to avoid blocking the request handler.

Email triggers:
1. Coaching invite sent → email to student
2. Coaching invite accepted → email to coach
3. Community question approved → email to submitter
4. Community question rejected → email to submitter (with reason)

Configuration:
- Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL
- If SMTP_HOST is empty, emails are logged but not sent (dev mode)
- Users can opt out via email_notifications = False on their profile
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email templates — inline HTML with minimal styling
# ---------------------------------------------------------------------------

def _base_template(title: str, body_html: str) -> str:
    """Wrap content in a simple, email-safe HTML template."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:20px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">
  <tr><td style="background:#1a365d;padding:24px 32px;">
    <h1 style="margin:0;color:#ffffff;font-size:20px;">{title}</h1>
  </td></tr>
  <tr><td style="padding:32px;">
    {body_html}
  </td></tr>
  <tr><td style="padding:16px 32px;background:#fafafa;border-top:1px solid #eee;">
    <p style="margin:0;font-size:12px;color:#999;">
      Career Foundry — AI Interview Coach<br>
      <a href="{settings.FRONTEND_URL}" style="color:#2b6cb0;">Open Career Foundry</a>
    </p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def coaching_invite_email(coach_name: str, coach_email: str) -> tuple[str, str]:
    """Email sent to student when a coach invites them."""
    subject = f"{coach_name or coach_email} invited you to coaching on Career Foundry"
    body = _base_template(
        "You've Been Invited!",
        f"""<p style="font-size:16px;color:#333;">
          <strong>{coach_name or coach_email}</strong> has invited you to join
          their coaching program on Career Foundry.
        </p>
        <p style="font-size:14px;color:#666;">
          As a coached student, your coach can view your evaluation scores and
          provide personalized feedback to help you improve.
        </p>
        <p style="text-align:center;margin:24px 0;">
          <a href="{settings.FRONTEND_URL}/coaching"
             style="display:inline-block;padding:12px 32px;background:#1a365d;color:#fff;
                    text-decoration:none;border-radius:6px;font-weight:600;">
            View Invite
          </a>
        </p>
        <p style="font-size:12px;color:#999;">
          Log in to accept or decline this invitation.
        </p>""",
    )
    return subject, body


def coaching_accepted_email(student_name: str, student_email: str) -> tuple[str, str]:
    """Email sent to coach when a student accepts the invite."""
    subject = f"{student_name or student_email} accepted your coaching invite"
    body = _base_template(
        "Invite Accepted!",
        f"""<p style="font-size:16px;color:#333;">
          <strong>{student_name or student_email}</strong> has accepted your
          coaching invitation.
        </p>
        <p style="font-size:14px;color:#666;">
          You can now view their evaluation history and add feedback from your
          Coach Dashboard.
        </p>
        <p style="text-align:center;margin:24px 0;">
          <a href="{settings.FRONTEND_URL}/coaching"
             style="display:inline-block;padding:12px 32px;background:#1a365d;color:#fff;
                    text-decoration:none;border-radius:6px;font-weight:600;">
            Open Coach Dashboard
          </a>
        </p>""",
    )
    return subject, body


def question_approved_email(question_text: str) -> tuple[str, str]:
    """Email sent to submitter when their community question is approved."""
    # Truncate long questions for the email
    preview = question_text[:120] + "..." if len(question_text) > 120 else question_text
    subject = "Your question was approved!"
    body = _base_template(
        "Question Approved",
        f"""<p style="font-size:16px;color:#333;">
          Your community question has been approved and is now live in the
          Career Foundry Question Bank.
        </p>
        <p style="font-size:14px;color:#666;background:#f0f7ff;padding:12px 16px;
                  border-left:4px solid #2b6cb0;border-radius:4px;">
          &ldquo;{preview}&rdquo;
        </p>
        <p style="font-size:14px;color:#666;">
          Other users can now practice with your question. Thank you for
          contributing to the community!
        </p>""",
    )
    return subject, body


def question_rejected_email(question_text: str, reason: str) -> tuple[str, str]:
    """Email sent to submitter when their community question is rejected."""
    preview = question_text[:120] + "..." if len(question_text) > 120 else question_text
    subject = "Update on your submitted question"
    body = _base_template(
        "Question Not Approved",
        f"""<p style="font-size:16px;color:#333;">
          Your community question was reviewed but could not be approved at
          this time.
        </p>
        <p style="font-size:14px;color:#666;background:#f0f7ff;padding:12px 16px;
                  border-left:4px solid #2b6cb0;border-radius:4px;">
          &ldquo;{preview}&rdquo;
        </p>
        <p style="font-size:14px;color:#333;"><strong>Reason:</strong></p>
        <p style="font-size:14px;color:#666;">{reason}</p>
        <p style="font-size:14px;color:#666;">
          Feel free to revise and resubmit. Good behavioral questions are
          specific, open-ended, and focus on past experiences.
        </p>""",
    )
    return subject, body


# ---------------------------------------------------------------------------
# Send function
# ---------------------------------------------------------------------------

def send_email(to_email: str, subject: str, html_body: str) -> None:
    """Send an email via SMTP.

    If SMTP_HOST is not configured, logs the email instead of sending.
    This makes development easy — no mail server needed.
    """
    if not settings.SMTP_HOST:
        logger.info(
            "Email (dev mode — not sent): to=%s subject=%s",
            to_email,
            subject,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        if settings.SMTP_PORT == 465:
            # SSL
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            # STARTTLS (port 587) or plain (port 25)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

        logger.info("Email sent: to=%s subject=%s", to_email, subject)

    except Exception:
        # Email failures should never break the app — log and continue
        logger.exception("Failed to send email to %s", to_email)
