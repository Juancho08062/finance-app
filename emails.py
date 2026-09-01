"""Transactional emails for Anchorpoint, sent via Resend's HTTP API."""
import os
import requests

RESEND_API_URL = 'https://api.resend.com/emails'


# Email-client-safe layout: a table-based shell (not flexbox/grid, which many
# clients strip), inline styles only, and a plain solid blue instead of a
# gradient for the button/badge — gradients are unreliable across clients,
# a flat brand blue reads consistently everywhere. Mirrors the app's own
# card/anchor-mark/blue-accent look from static/css/style.css.
FOOTER_TEXT = {
    'en': "You're receiving this because you signed up for Anchorpoint at {app_url}.",
    'es': 'Recibes esto porque te registraste en Anchorpoint en {app_url}.',
}


def _wrap_email(app_url, body_html, lang='en'):
    footer = FOOTER_TEXT.get(lang, FOOTER_TEXT['en']).format(app_url=app_url)
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
        {footer}
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


WELCOME_COPY = {
    'en': {
        'subject': 'Welcome to Anchorpoint',
        'heading': 'Welcome to Anchorpoint, {name}.',
        'p1': (
            "Your account is set up. Anchorpoint gives you one place to track income and expenses, "
            "pay down debt, hit savings goals, and see a personalized budget split — plus a projection "
            "of where your money could be years from now if you stick with it."
        ),
        'p2': (
            'A good first step: log a few recent transactions, then try '
            '<strong>Quick Setup</strong> on the Summary page for a recommended budget split based on '
            'your age.'
        ),
        'button': 'Open Anchorpoint',
    },
    'es': {
        'subject': 'Bienvenido a Anchorpoint',
        'heading': 'Bienvenido a Anchorpoint, {name}.',
        'p1': (
            'Tu cuenta ya está lista. Anchorpoint te da un solo lugar para llevar tus ingresos y gastos, '
            'pagar tus deudas, alcanzar tus metas de ahorro y ver un plan de presupuesto personalizado — '
            'además de una proyección de cómo podría verse tu dinero en el futuro si sigues el plan.'
        ),
        'p2': (
            'Un buen primer paso: registra algunas transacciones recientes, y luego prueba '
            '<strong>Configuración Rápida</strong> en la página de Resumen para obtener un plan de '
            'presupuesto recomendado según tu edad.'
        ),
        'button': 'Abrir Anchorpoint',
    },
}

CHECKIN_COPY = {
    'en': {
        'subject': "How's Anchorpoint working for you?",
        'heading': "How's it going, {name}?",
        'p1': (
            "You signed up for Anchorpoint about a week ago. We'd love to know how it's working for you — "
            "what's useful, what's confusing, and what you wish it did."
        ),
        'p2': "Just reply to this email — a real person reads it.",
        'button': 'Open Anchorpoint',
    },
    'es': {
        'subject': '¿Cómo te está funcionando Anchorpoint?',
        'heading': '¿Cómo va todo, {name}?',
        'p1': (
            'Te registraste en Anchorpoint hace como una semana. Nos encantaría saber cómo te está '
            'funcionando — qué te sirve, qué te confunde, y qué te gustaría que hiciera.'
        ),
        'p2': 'Solo responde a este correo — una persona real lo lee.',
        'button': 'Abrir Anchorpoint',
    },
}


def _render_body(copy, name):
    return f"""
    <h1 style="font-size:21px; font-weight:700; letter-spacing:-0.01em; color:#1C1C1E; margin:0 0 12px;">
      {copy['heading'].format(name=name)}
    </h1>
    <p style="font-size:15px; line-height:1.6; color:#3A3A3C; margin:0 0 16px;">
      {copy['p1']}
    </p>
    <p style="font-size:15px; line-height:1.6; color:#3A3A3C; margin:0 0 22px;">
      {copy['p2']}
    </p>
    """


FALLBACK_NAME = {'en': 'there', 'es': 'amigo'}


def send_welcome_email(user):
    lang = getattr(user, 'language', None) or 'en'
    name = user.first_name or FALLBACK_NAME.get(lang, 'there')
    app_url = os.environ.get('APP_URL', 'http://localhost:5000')
    copy = WELCOME_COPY.get(lang, WELCOME_COPY['en'])

    body = _render_body(copy, name) + _button(app_url, copy['button'])
    html = _wrap_email(app_url, body, lang)
    return send_email(user.email, copy['subject'], html)


def send_checkin_email(user):
    lang = getattr(user, 'language', None) or 'en'
    name = user.first_name or FALLBACK_NAME.get(lang, 'there')
    app_url = os.environ.get('APP_URL', 'http://localhost:5000')
    copy = CHECKIN_COPY.get(lang, CHECKIN_COPY['en'])

    body = _render_body(copy, name) + _button(app_url, copy['button'])
    html = _wrap_email(app_url, body, lang)
    return send_email(user.email, copy['subject'], html)
