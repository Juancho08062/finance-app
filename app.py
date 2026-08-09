import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    income = db.Column(db.Numeric(10, 2), nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'
    

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)       # 'income' or 'expense'
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=True)     # e.g. 'Groceries', 'Paycheck'
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(20), default='manual')    # 'manual' or 'plaid' (future)

    def __repr__(self):
        return f'<Transaction {self.type} ${self.amount}>'

class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    remaining_balance = db.Column(db.Numeric(10, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=True)
    minimum_payment = db.Column(db.Numeric(10, 2), nullable=True)

    def __repr__(self):
        return f'<Debt {self.name} ${self.remaining_balance}>'

class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    current_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    target_date = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<SavingsGoal {self.name} ${self.current_amount}/{self.target_amount}>'

class BudgetAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    percentage = db.Column(db.Numeric(5, 2), nullable=False)

def __repr__(self):
        return f'<BudgetAllocation {self.category} {self.percentage}%>'



@app.route('/')
def home():
    if current_user.is_authenticated:
        return f"Hello, {current_user.email}! You are logged in. <a href='/transactions'>View Transactions</a> | <a href='/add_transaction'>Add Transaction</a> | <a href='/debts'>View Debts</a> | <a href='/add_debt'>Add Debt</a> | <a href='/goals'>View Goals</a> | <a href='/add_goal'>Add Goal</a> | <a href='/add_allocation'>Add Allocation</a> | <a href='/summary'>Financial Summary</a> | <a href='/logout'>Logout</a>"
    return "Hello! You are not logged in..."
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "An account with that email already exists."

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            return "Invalid email or password."

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        type_ = request.form.get('type')
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        date_str = request.form.get('date')
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        new_transaction = Transaction(
            user_id=current_user.id,
            type=type_,
            amount=amount,
            category=category,
            description=description,
            date=date
        )
        db.session.add(new_transaction)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('add_transaction.html')

@app.route('/transactions')
@login_required
def transactions():
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=user_transactions)

@app.route('/add_debt', methods=['GET', 'POST'])
@login_required
def add_debt():
    if request.method == 'POST':
        name = request.form.get('name')
        total_amount = request.form.get('total_amount')
        remaining_balance = request.form.get('remaining_balance')
        interest_rate = request.form.get('interest_rate') or None
        minimum_payment = request.form.get('minimum_payment') or None

        new_debt = Debt(
            user_id=current_user.id,
            name=name,
            total_amount=total_amount,
            remaining_balance=remaining_balance,
            interest_rate=interest_rate,
            minimum_payment=minimum_payment
        )
        db.session.add(new_debt)
        db.session.commit()

        return redirect(url_for('debts'))

    return render_template('add_debt.html')


@app.route('/debts')
@login_required
def debts():
    user_debts = Debt.query.filter_by(user_id=current_user.id).all()
    return render_template('debts.html', debts=user_debts)

@app.route('/add_allocation', methods=['GET', 'POST'])
@login_required
def add_allocation():
    if request.method == 'POST':
        category = request.form.get('category')
        percentage = request.form.get('percentage')

        new_allocation = BudgetAllocation(
            user_id=current_user.id,
            category=category,
            percentage=percentage
        )
        db.session.add(new_allocation)
        db.session.commit()

        return redirect(url_for('summary'))

    return render_template('add_allocation.html')


@app.route('/add_goal', methods=['GET', 'POST'])
@login_required
def add_goal():
    if request.method == 'POST':
        name = request.form.get('name')
        target_amount = request.form.get('target_amount')
        current_amount = request.form.get('current_amount') or 0
        target_date_str = request.form.get('target_date')
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date() if target_date_str else None

        new_goal = SavingsGoal(
            user_id=current_user.id,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target_date
        )
        db.session.add(new_goal)
        db.session.commit()

        return redirect(url_for('goals'))

    return render_template('add_goal.html')


@app.route('/goals')
@login_required
def goals():
    user_goals = SavingsGoal.query.filter_by(user_id=current_user.id).all()
    return render_template('goals.html', goals=user_goals)


@app.route('/summary')
@login_required
def summary():
    income_transactions = Transaction.query.filter_by(user_id=current_user.id, type='income').all()
    total_income = sum(t.amount for t in income_transactions) or 0

    user_debts = Debt.query.filter_by(user_id=current_user.id).all()
    total_debt_payments = sum(d.minimum_payment or 0 for d in user_debts) or 0

    available = total_income - total_debt_payments

    user_allocations = BudgetAllocation.query.filter_by(user_id=current_user.id).all()
    total_percentage = sum(a.percentage for a in user_allocations) or 0

    allocations = []
    for a in user_allocations:
        amount = available * (a.percentage / 100)
        allocations.append({'category': a.category, 'percentage': a.percentage, 'amount': round(amount, 2)})

    return render_template(
        'summary.html',
        total_income=total_income,
        total_debt_payments=total_debt_payments,
        available=available,
        allocations=allocations,
        total_percentage=total_percentage
    )
if __name__ == '__main__':
    app.run(debug=True)