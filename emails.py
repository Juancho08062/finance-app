"""Transactional emails for Anchorpoint, sent via Resend's HTTP API."""
import os
import requests

RESEND_API_URL = 'https://api.resend.com/emails'

FOOTER = """
<p style="margin-top:32px; padding-top:16px; border-top:1px solid #e3e7ec; color:#6b7280; font-size:12px;">
  You're receiving this because you signed up for Anchorpoint at {app_url}.
</p>
""".strip()


def send_email(to, subject, html_body):
    """Send one email via Resend. Returns True on success, False on any failure — never raises."""
    # Read env vars lazily (not at module import time) so this works regardless of
    # whether load_dotenv() has already run when this module is first imported.
    api_key = os.environ.get('RESEND_API_KEY')
    email_from = os.environ.get('EMAIL_FROM', 'Anchorpoint <onboarding@resend.dev>')
    app_url = os.environ.get('APP_URL', 'http://localhost:5000')

    if not api_key:
        print(f"[emails] RESEND_API_KEY not set — skipping email to {to} ({subject!r})")
        return False

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={'Authorization': f'Bearer {api_key}'},
            json={
                'from': email_from,
                'to': [to],
                'subject': subject,
                'html': html_body + FOOTER.format(app_url=app_url),
            },
            timeout=10,
        )
        if response.status_code >= 400:
            print(f"[emails] Resend API error {response.status_code} sending to {to}: {response.text}")
            return False
        return True
    except requests.RequestException as e:
        print(f"[emails] Failed to send email to {to}: {e}")
        return False


def send_welcome_email(user):
    name = user.first_name or 'there'
    app_url = os.environ.get('APP_URL', 'http://localhost:5000')
    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; max-width:480px; margin:0 auto; color:#101418;">
      <h1 style="font-size:22px; margin-bottom:8px;">Welcome to Anchorpoint, {name}.</h1>
      <p style="font-size:15px; line-height:1.6; color:#3c4450;">
        Your account is set up. Anchorpoint gives you one place to track income and expenses,
        pay down debt, hit savings goals, and see a personalized budget split — plus a projection
        of where your money could be years from now if you stick with it.
      </p>
      <p style="font-size:15px; line-height:1.6; color:#3c4450;">
        A good first step: log a few recent transactions, then try
        <strong>Quick Setup</strong> on the Summary page for a recommended budget split based on
        your age.
      </p>
      <p style="margin-top:24px;">
        <a href="{app_url}" style="background:#0f62d6; color:#fff; padding:10px 20px; border-radius:999px; text-decoration:none; font-weight:600; font-size:14px;">
          Open Anchorpoint
        </a>
      </p>
    </div>
    """
    return send_email(user.email, 'Welcome to Anchorpoint', html)


def send_checkin_email(user):
    name = user.first_name or 'there'
    app_url = os.environ.get('APP_URL', 'http://localhost:5000')
    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; max-width:480px; margin:0 auto; color:#101418;">
      <h1 style="font-size:22px; margin-bottom:8px;">How's it going, {name}?</h1>
      <p style="font-size:15px; line-height:1.6; color:#3c4450;">
        You signed up for Anchorpoint about a week ago. We'd love to know how it's working for you —
        what's useful, what's confusing, and what you wish it did.
      </p>
      <p style="font-size:15px; line-height:1.6; color:#3c4450;">
        Just reply to this email — a real person reads it.
      </p>
      <p style="margin-top:24px;">
        <a href="{app_url}" style="background:#0f62d6; color:#fff; padding:10px 20px; border-radius:999px; text-decoration:none; font-weight:600; font-size:14px;">
          Open Anchorpoint
        </a>
      </p>
    </div>
    """
    return send_email(user.email, "How's Anchorpoint working for you?", html)
