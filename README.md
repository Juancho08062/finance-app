# Anchorpoint

A personal finance tracker built with Flask and PostgreSQL for the day-to-day individual. Enter your age, income, expenses, debts and goals, and it gives you age-aware budgeting guidance, tracks your progress, and projects where your savings could be in the future. The interface is available in English and Spanish.

## Features

- Sign up / log in, with a profile that includes your age and income
- Track income and expenses, debts (with payments), and savings goals
- Age-based quick setup for budget allocations, auto-balanced to always total 100%
- Summary dashboard and long-term savings projection (5, 10, 20 and 30 years)
- Welcome and 7-day check-in emails (optional, via Resend)

## Run it locally

Requires Python 3.9 or newer (Flask 3.1's minimum; tested on Python 3.14).

```bash
git clone https://github.com/Juancho08062/finance-app.git
cd finance-app

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

flask --app app db upgrade        # creates the database
flask --app app run
```

Then open http://127.0.0.1:5000 and create an account.

- **No `.env` file or database server is needed to try it.** With no `DATABASE_URL` set, the app uses a local SQLite file (`finance.db`) automatically.
- On macOS, port 5000 is often taken by AirPlay Receiver. Use `flask --app app run --port 5001` instead.
- **PostgreSQL:** copy `.env.example` to `.env` and set `DATABASE_URL` to your Postgres URL. If you copy `.env.example` but don't have Postgres, delete or comment out the `DATABASE_URL` line, otherwise the app will try to connect to a server that isn't there.
- **Emails:** the app works without email configured. To enable the welcome/check-in emails, set `RESEND_API_KEY` (free at https://resend.com) in `.env`.
- In production, set a real `SECRET_KEY` (see `.env.example`).

## Deploying

See [DEPLOY.md](DEPLOY.md) for a step-by-step guide to hosting it free on PythonAnywhere.
