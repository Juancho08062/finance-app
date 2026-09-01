"""Transactional emails for Anchorpoint, sent via Resend's HTTP API."""
import os
import requests

RESEND_API_URL = 'https://api.resend.com/emails'


# Email-client-safe layout: a table-based shell (not flexbox/grid, which many
# clients strip), inline styles only, and a plain solid blue instead of a
# gradient for the button/badge — gradients are unreliable across clients,
# a flat brand blue reads consistently everywhere. Mirrors the app's own
# card/anchor-mark/blue-accent look from static/css/style.css.
def _wrap_email(app_url, body_html):
    return f"""
<div style="background:#F2F2F7; padding:32px 16px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px; margin:0 auto;">
    <tr>
      <td style="padding-bottom:24px; text-align:center;">
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
          <tr>
            <td style="width:28px; height:28px; background-color:#0A3D91; border-radius:8px; text-align:center; vertical-align:middle; font-size:15px; line-height:28px;">
              <span style="color:#ffffff;">&#9875;</span>
            </td>
            <td style="padding-left:8px; font-size:17px; font-weight:700; color:#1C1C1E; vertical-align:middle;">Anchorpoint</td>
          </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td style="background-color:#ffffff; border:1px solid rgba(60,60,67,0.12); border-radius:16px; padding:32px 28px;">
        {body_html}
      </td>
    </tr>
    <tr>
      <td style="padding-top:20px; text-align:center; color:#6b6b70; font-size:12px; line-height:1.5;">
        You're receiving this because you signed up for Anchorpoint at {app_url}.
      </td>
    </tr>
  </table>
</div>
""".strip()


def _button(app_url, label):
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:8px;">
      <tr>
        <td style="background-color:#007AFF; border-radius:999px;">
          <a href="{app_url}" style="display:inline-block; padding:11px 22px; color:#ffffff; text-decoration:none; font-weight:600; font-size:14px;">
            {label}
          </a>
        </td>
      </tr>
    </table>
    """.strip()


def send_email(to, subject, html_body):
    """Send one email via Resend. Returns True on success, False on any failure — never raises."""
    # Read env vars lazily (not at module import time) so this works regardless of
    # whether load_dotenv() has already run when this module is first imported.
    api_key = os.environ.get('RESEND_API_KEY')
    email_from = os.environ.get('EMAIL_FROM', 'Anchorpoint <onboarding@resend.dev>')

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
                'html': html_body,
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

    body = f"""
    <h1 style="font-size:21px; font-weight:700; letter-spacing:-0.01em; color:#1C1C1E; margin:0 0 12px;">
      Welcome to Anchorpoint, {name}.
    </h1>
    <p style="font-size:15px; line-height:1.6; color:#3A3A3C; margin:0 0 16px;">
      Your account is set up. Anchorpoint gives you one place to track income and expenses,
      pay down debt, hit savings goals, and see a personalized budget split — plus a projection
      of where your money could be years from now if you stick with it.
    </p>
    <p style="font-size:15px; line-height:1.6; color:#3A3A3C; margin:0 0 22px;">
      A good first step: log a few recent transactions, then try
      <strong>Quick Setup</strong> on the Summary page for a recommended budget split based on
      your age.
    </p>
    {_button(app_url, 'Open Anchorpoint')}
    """
    html = _wrap_email(app_url, body)
    return send_email(user.email, 'Welcome to Anchorpoint', html)


def send_checkin_email(user):
    name = user.first_name or 'there'
    app_url = os.environ.get('APP_URL', 'http://localhost:5000')

    body = f"""
    <h1 style="font-size:21px; font-weight:700; letter-spacing:-0.01em; color:#1C1C1E; margin:0 0 12px;">
      How's it going, {name}?
    </h1>
    <p style="font-size:15px; line-height:1.6; color:#3A3A3C; margin:0 0 16px;">
      You signed up for Anchorpoint about a week ago. We'd love to know how it's working for you —
      what's useful, what's confusing, and what you wish it did.
    </p>
    <p style="font-size:15px; line-height:1.6; color:#3A3A3C; margin:0 0 22px;">
      Just reply to this email — a real person reads it.
    </p>
    {_button(app_url, 'Open Anchorpoint')}
    """
    html = _wrap_email(app_url, body)
    return send_email(user.email, "How's Anchorpoint working for you?", html)
