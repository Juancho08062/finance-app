# Deploying Anchorpoint to PythonAnywhere (Free Tier)

Steps 1-2 are yours to do manually (account creation) — everything after that is copy/paste.

This app already falls back to SQLite automatically when `DATABASE_URL` isn't set (see the top
of `app.py`), which is exactly what makes it deployable on PythonAnywhere's free tier without
needing a separate Postgres server.

---

## Step 1 — Create a free PythonAnywhere account

Go to https://www.pythonanywhere.com/, click "Pricing & signup", and create a **Beginner (free)**
account. This is a manual step — just sign up with your email/password like any other site.

## Step 2 — Open a Bash console

From the PythonAnywhere dashboard, go to the **Consoles** tab → click **Bash** to start a new
console. All the commands in Steps 3–5 and 9 below run in this console.

## Step 3 — Clone the repo

The code needs to be pushed to GitHub first (it already has an `origin` remote pointed at
`https://github.com/Juancho08062/finance-app.git` — make sure your latest commits are pushed
there before doing this step).

```bash
git clone https://github.com/Juancho08062/finance-app.git
cd finance-app
```

## Step 4 — Create a virtualenv and install dependencies

PythonAnywhere's documented, standard pattern uses `virtualenvwrapper`'s `mkvirtualenv` helper —
it's what the Web tab's "Virtualenv" field expects, and it's the pattern PythonAnywhere supports
directly. As of now, free-tier accounts created after March 2025 have Python 3.11, 3.12, and
3.13 available (Ubuntu 22.04). Use whichever matches your local dev version — the commands below
use 3.13:

```bash
mkvirtualenv anchorpoint-venv --python=/usr/bin/python3.13
pip install -r ~/finance-app/requirements.txt
```

`mkvirtualenv` both creates and activates the virtualenv, and it will be created at
`/home/<your-username>/.virtualenvs/anchorpoint-venv` — you'll need that exact path in Step 7.

## Step 5 — Set a real SECRET_KEY via a `.env` file

The app loads a `.env` file (via `python-dotenv`) from its own project directory at import time.
Create one in the cloned repo on PythonAnywhere:

```bash
cd ~/finance-app
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the printed value, then create the `.env` file (also see `.env.example` in the repo):

```bash
cat > .env << 'EOF'
SECRET_KEY=<paste-the-generated-value-here>
RESEND_API_KEY=<your-resend-api-key>
EMAIL_FROM=Anchorpoint <onboarding@resend.dev>
APP_URL=https://<your-username>.pythonanywhere.com
EOF
```

**Do NOT add a `DATABASE_URL` line.** Leaving it unset is what makes `app.py` fall back to
SQLite automatically (`sqlite:///.../finance.db` next to `app.py`).

**Getting `RESEND_API_KEY`:** sign up free at https://resend.com (no domain verification needed
to start — `onboarding@resend.dev` works immediately as the sender). Create an API key from
their dashboard and paste it in above. Confirmed: `api.resend.com` is on PythonAnywhere's
free-tier outbound whitelist, so this works without needing a paid PythonAnywhere account.

## Step 6 — Create the web app (Manual configuration) and edit the WSGI file

1. Go to the **Web** tab → **Add a new web app**.
2. Choose **Manual configuration** (not the guided "Flask" wizard — this is an existing app with
   its own structure, not a fresh scaffold).
3. Choose the Python version that matches the virtualenv you created in Step 4 (e.g. 3.13).
4. PythonAnywhere generates a WSGI configuration file and links it on the Web tab (something like
   `/var/www/<your_username>_pythonanywhere_com_wsgi.py`). Click it to edit, **delete everything**,
   and replace it with:

```python
import sys
import os

project_home = '/home/<your-username>/finance-app'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
```

Replace `<your-username>` with your actual PythonAnywhere username.

Note: `app.py` was updated to load `.env` using an explicit path relative to its own file
location (`load_dotenv(os.path.join(basedir, '.env'))`) rather than relying on the process's
current working directory. WSGI processes are often started with an unpredictable cwd, so this
was a real risk before the fix — now `.env` will be found reliably regardless of how the WSGI
process is launched, and you do **not** need to hardcode the SECRET_KEY into the WSGI file as a
workaround.

## Step 7 — Set the Virtualenv path

Back on the **Web** tab, find the **Virtualenv** section and enter:

```
/home/<your-username>/.virtualenvs/anchorpoint-venv
```

(Replace `<your-username>` with your actual username.) Click the checkmark to confirm.

## Step 8 — Map static files

Still on the **Web** tab, scroll to **Static files** and add an entry:

| URL | Directory |
|---|---|
| `/static/` | `/home/<your-username>/finance-app/static` |

This is what lets `style.css` and any JS in `static/` actually load.

## Step 9 — Create the database tables

Back in a Bash console:

```bash
workon anchorpoint-venv
cd ~/finance-app
flask db upgrade
```

This runs the existing Alembic migrations against a fresh SQLite file, creating `finance.db`
(and all tables) in the project directory — nothing to configure, since `DATABASE_URL` is unset.

## Step 10 — Reload and verify

Go back to the **Web** tab and click the green **Reload** button. Then visit:

```
https://<your-username>.pythonanywhere.com
```

You should see the Anchorpoint landing page.

## Step 11 — Schedule the 7-day check-in email

New signups get a welcome email immediately (built into the `/register` route — nothing to
configure). The 7-day "how's it going" follow-up needs a daily scheduled task, since it has to
run on its own regardless of whether anyone visits the site that day.

1. Go to the **Tasks** tab.
2. Add a **Daily** task (free accounts get one). Pick any time — early morning is typical.
3. Set the command to:

```bash
/home/<your-username>/.virtualenvs/anchorpoint-venv/bin/python /home/<your-username>/finance-app/send_checkin_emails.py
```

(Use the full path to the virtualenv's Python interpreter, not just `python3` — scheduled tasks
don't activate your virtualenv the way a Bash console does.)

This runs `send_checkin_emails.py`, which finds every user who signed up 7+ days ago and hasn't
been checked in on yet, sends them one email, and marks them so they're never emailed twice. You
can test it manually anytime from a Bash console with the same command.

## Step 12 — If something's wrong

If you get a 500 error or the site won't load, the Web tab has an **Error log** link near the
top (next to Server log and Access log) — click it to see the actual Python traceback. Common
causes: a typo in the WSGI file's `project_home` path or username, the virtualenv path not
matching Step 4 exactly, or `flask db upgrade` not having been run yet (Step 9).
