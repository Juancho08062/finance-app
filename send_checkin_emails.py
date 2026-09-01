"""
Sends the 7-day check-in email to users who signed up a week ago and haven't
gotten one yet. Meant to run once a day via a scheduled task (cron on your own
server, or PythonAnywhere's "Tasks" tab).

Usage: python3 send_checkin_emails.py
"""
from datetime import datetime, timedelta

from app import app, db, User
from emails import send_checkin_email

CHECKIN_AFTER_DAYS = 7


def run():
    cutoff = datetime.utcnow() - timedelta(days=CHECKIN_AFTER_DAYS)

    with app.app_context():
        due = User.query.filter(
            User.checkin_email_sent.is_(False),
            User.created_at <= cutoff,
        ).all()

        if not due:
            print('[send_checkin_emails] No users due for a check-in email today.')
            return

        sent, failed = 0, 0
        for user in due:
            if send_checkin_email(user):
                user.checkin_email_sent = True
                sent += 1
            else:
                failed += 1

        db.session.commit()
        print(f'[send_checkin_emails] Sent {sent}, failed {failed}, out of {len(due)} due.')


if __name__ == '__main__':
    run()
