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
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    income = db.Column(db.Numeric(10, 2), nullable=True)
    employment_status = db.Column(db.String(20), nullable=True)

    @property
    def display_name(self):
        full_name = ' '.join(part for part in [self.first_name, self.last_name] if part)
        return full_name or self.email.split('@')[0]

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
    debt_id = db.Column(db.Integer, db.ForeignKey('debt.id'), nullable=True)

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
    priority = db.Column(db.Integer, nullable=False, default=5)  # 1-10, how important this category is to the user

    def __repr__(self):
        return f'<BudgetAllocation {self.category} {self.percentage}%>'

def classify_category(category_name):
    name = category_name.lower()

    if any(word in name for word in ['rent', 'mortgage', 'debt', 'loan', 'minimum payment', 'needs', 'bills', 'insurance']):
        return 'essential', 1
    elif any(word in name for word in ['emergency', 'safety net', 'rainy day']):
        return 'emergency_fund', 2
    elif 'roth' in name or '401k' in name or '401(k)' in name or 'ira' in name:
        return 'retirement', 3
    elif 'etf' in name or 'index fund' in name or 'stock' in name or 'brokerage' in name:
        return 'investing', 4
    elif 'savings' in name or 'cash' in name:
            return 'cash_savings', 6
    elif 'crypto' in name or 'bitcoin' in name:
        return 'crypto', 5
    elif any(word in name for word in ['fun', 'travel', 'vacation', 'entertainment', 'shopping', 'hobby']):
        return 'discretionary', 7
    else:
        return 'other', 8


def get_financial_picture(user):
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    total_income = sum(t.amount for t in transactions if t.type == 'income') or 0
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense') or 0

    debts = Debt.query.filter_by(user_id=user.id).all()
    total_debt_remaining = sum(d.remaining_balance for d in debts) or 0

    available_cash = total_income - total_expenses

    allocations = BudgetAllocation.query.filter_by(user_id=user.id).all()
    invested_by_type = {}
    for a in allocations:
        tier, _ = classify_category(a.category)
        amount = float(available_cash) * (float(a.percentage) / 100) if available_cash > 0 else 0
        invested_by_type[tier] = invested_by_type.get(tier, 0) + amount

    goals = SavingsGoal.query.filter_by(user_id=user.id).all()
    total_in_goals = sum(g.current_amount for g in goals) or 0

    return {
        'available_cash': available_cash,
        'total_debt_remaining': total_debt_remaining,
        'invested_by_type': invested_by_type,
        'total_in_goals': total_in_goals,
        'total_income': total_income,
    }
def get_recommended_split(age, financial_picture=None):
    if age is None:
        base = [('Needs', 50), ('Fun Money', 30), ('Roth IRA', 12), ('Stock Market', 8)]
    elif age < 30:
        base = [('Needs', 50), ('Fun Money', 20), ('Roth IRA', 18), ('Stock Market', 12)]
    elif age < 45:
        base = [('Needs', 55), ('Fun Money', 20), ('Roth IRA', 15), ('Stock Market', 10)]
    elif age < 60:
        base = [('Needs', 55), ('Fun Money', 15), ('Roth IRA', 18), ('Stock Market', 12)]
    else:
        base = [('Needs', 60), ('Fun Money', 15), ('Roth IRA', 15), ('Stock Market', 10)]

    if financial_picture and financial_picture['invested_by_type'].get('emergency_fund', 0) == 0:
        base = [('Emergency Fund', 15)] + [(cat, round(pct * 0.85)) for cat, pct in base]

    return base

    
@app.route('/')
def home():
    if not current_user.is_authenticated:
        return render_template('landing.html')

    income_transactions = Transaction.query.filter_by(user_id=current_user.id, type='income').all()
    total_income = sum(t.amount for t in income_transactions) or 0

    expense_transactions = Transaction.query.filter_by(user_id=current_user.id, type='expense').all()
    total_expenses = sum(t.amount for t in expense_transactions) or 0

    user_debts = Debt.query.filter_by(user_id=current_user.id).all()
    total_debt_remaining = sum(d.remaining_balance for d in user_debts) or 0

    available = total_income - total_expenses

    user_goals = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.id.desc()).all()

    user_allocations = BudgetAllocation.query.filter_by(user_id=current_user.id).all()
    allocations = []
    for a in user_allocations:
        amount = available * (a.percentage / 100) if available > 0 else 0
        allocations.append({'category': a.category, 'percentage': a.percentage, 'amount': round(amount, 2)})

    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_income=total_income,
        total_expenses=total_expenses,
        total_debt_remaining=total_debt_remaining,
        available=available,
        allocations=allocations,
        goals=user_goals,
        recent_transactions=recent_transactions
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name') or None
        last_name = request.form.get('last_name') or None
        age = request.form.get('age') or None
        income = request.form.get('income') or None

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with that email already exists.', 'error')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            age=age,
            income=income
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created — log in to get started.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        new_email = request.form.get('email')
        first_name = request.form.get('first_name') or None
        last_name = request.form.get('last_name') or None
        age = request.form.get('age') or None
        income = request.form.get('income') or None
        employment_status = request.form.get('employment_status') or None

        if new_email != current_user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing:
                flash('That email is already taken by another account.', 'error')
                return render_template('edit_profile.html')

        current_user.email = new_email
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.age = age
        current_user.income = income
        current_user.employment_status = employment_status
        db.session.commit()

        flash('Profile updated.', 'success')
        return redirect(url_for('home'))

    return render_template('edit_profile.html')

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
            flash('Invalid email or password.', 'error')
            return render_template('login.html')

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
        debt_id = request.form.get('debt_id') or None

        new_transaction = Transaction(
            user_id=current_user.id,
            type=type_,
            amount=amount,
            category=category,
            description=description,
            date=date,
            debt_id=debt_id
        )
        db.session.add(new_transaction)
        db.session.commit()

        flash('Transaction added.', 'success')
        return redirect(url_for('home'))

    user_debts = Debt.query.filter_by(user_id=current_user.id).all()
    return render_template('add_transaction.html', debts=user_debts)

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

        flash('Debt added.', 'success')
        return redirect(url_for('debts'))

    return render_template('add_debt.html')

@app.route('/delete_transaction/<int:id>')
@login_required
def delete_transaction(id):
    t = Transaction.query.get_or_404(id)
    if t.user_id != current_user.id:
        return "Not authorized.", 403
    db.session.delete(t)
    db.session.commit()
    flash('Transaction deleted.', 'success')
    return redirect(url_for('transactions'))


@app.route('/delete_debt/<int:id>')
@login_required
def delete_debt(id):
    d = Debt.query.get_or_404(id)
    if d.user_id != current_user.id:
        return "Not authorized.", 403
    db.session.delete(d)
    db.session.commit()
    flash('Debt deleted.', 'success')
    return redirect(url_for('debts'))


@app.route('/delete_goal/<int:id>')
@login_required
def delete_goal(id):
    g = SavingsGoal.query.get_or_404(id)
    if g.user_id != current_user.id:
        return "Not authorized.", 403
    db.session.delete(g)
    db.session.commit()
    flash('Goal deleted.', 'success')
    return redirect(url_for('goals'))


def recompute_allocation_percentages(user_id):
    """Derive each allocation's percentage from its priority (1-10) relative to the others, always summing to 100."""
    allocations = BudgetAllocation.query.filter_by(user_id=user_id).all()
    total_priority = sum(a.priority for a in allocations)
    if not allocations or total_priority <= 0:
        return

    running = 0
    for a in allocations[:-1]:
        pct = round(a.priority / total_priority * 100, 2)
        running += pct
        a.percentage = pct
    allocations[-1].percentage = round(100 - running, 2)


@app.route('/delete_allocation/<int:id>')
@login_required
def delete_allocation(id):
    a = BudgetAllocation.query.get_or_404(id)
    if a.user_id != current_user.id:
        return "Not authorized.", 403
    db.session.delete(a)
    db.session.flush()

    if BudgetAllocation.query.filter_by(user_id=current_user.id).first():
        recompute_allocation_percentages(current_user.id)
        flash('Allocation deleted — the rest were rebalanced to total 100%.', 'success')
    else:
        flash('Allocation deleted.', 'success')

    db.session.commit()
    return redirect(url_for('summary'))

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
        priority = int(request.form.get('priority') or 5)
        priority = min(10, max(1, priority))

        new_allocation = BudgetAllocation(
            user_id=current_user.id,
            category=category,
            percentage=0,
            priority=priority
        )
        db.session.add(new_allocation)
        db.session.flush()

        recompute_allocation_percentages(current_user.id)
        db.session.commit()

        flash('Allocation added — percentages recalculated based on importance.', 'success')
        return redirect(url_for('summary'))

    return render_template('add_allocation.html')

@app.route('/quick_setup_allocations')
@login_required
def quick_setup_allocations():
    if current_user.age is None:
        flash('Add your age in Edit Profile first so we can tailor a recommended budget split for you.', 'warning')
        return redirect(url_for('edit_profile'))

    try:
        existing = BudgetAllocation.query.filter_by(user_id=current_user.id).all()
        for a in existing:
            db.session.delete(a)

        picture = get_financial_picture(current_user)
        recommended_split = get_recommended_split(current_user.age, picture)

        for category, percentage in recommended_split:
            db.session.add(BudgetAllocation(
                user_id=current_user.id,
                category=category,
                percentage=percentage,
                priority=max(1, round(percentage))
            ))

        db.session.commit()
        flash('Recommended budget split applied.', 'success')
        return redirect(url_for('summary'))

    except Exception as e:
        db.session.rollback()
        flash(f'Quick Setup failed: {str(e)}', 'error')
        return redirect(url_for('home'))


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

@app.route('/add_to_goal/<int:id>', methods=['GET', 'POST'])
@login_required
def add_to_goal(id):
    goal = SavingsGoal.query.get_or_404(id)
    if goal.user_id != current_user.id:
        return "Not authorized.", 403

    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        goal.current_amount = float(goal.current_amount) + amount

        db.session.add(Transaction(
            user_id=current_user.id,
            type='expense',
            amount=amount,
            category=f'Goal: {goal.name}',
            description=f'Contribution to savings goal "{goal.name}"',
            date=datetime.now().date()
        ))
        db.session.commit()

        if goal.current_amount >= goal.target_amount:
            flash(f'🎉 Goal reached! "{goal.name}" is fully funded.', 'success')
        else:
            flash('Funds added to your goal — this amount has been deducted from your available balance.', 'success')

        return redirect(url_for('goals'))

    return render_template('add_to_goal.html', goal=goal)


@app.route('/add_debt_payment/<int:id>', methods=['GET', 'POST'])
@login_required
def add_debt_payment(id):
    debt = Debt.query.get_or_404(id)
    if debt.user_id != current_user.id:
        return "Not authorized.", 403

    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        debt.remaining_balance = max(0, float(debt.remaining_balance) - amount)

        db.session.add(Transaction(
            user_id=current_user.id,
            type='expense',
            amount=amount,
            category=f'Debt Payment: {debt.name}',
            description=f'Payment toward "{debt.name}"',
            date=datetime.now().date(),
            debt_id=debt.id
        ))
        db.session.commit()

        if debt.remaining_balance <= 0:
            flash(f'🎉 "{debt.name}" is paid off!', 'success')
        else:
            flash('Payment recorded — this amount has been deducted from your available balance.', 'success')

        return redirect(url_for('debts'))

    return render_template('add_debt_payment.html', debt=debt)


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

    expense_transactions = Transaction.query.filter_by(user_id=current_user.id, type='expense').all()
    total_expenses = sum(t.amount for t in expense_transactions) or 0

    user_debts = Debt.query.filter_by(user_id=current_user.id).all()
    total_debt_remaining = sum(d.remaining_balance for d in user_debts) or 0
    debt_payment_transactions = Transaction.query.filter_by(user_id=current_user.id, type='expense').filter(Transaction.debt_id.isnot(None)).all()
    total_debt_payments = sum(t.amount for t in debt_payment_transactions) or 0

    available = total_income - total_expenses

    user_goals = SavingsGoal.query.filter_by(user_id=current_user.id).all()

    user_allocations = BudgetAllocation.query.filter_by(user_id=current_user.id).all()
    total_percentage = sum(a.percentage for a in user_allocations) or 0

    allocations = []
    for a in user_allocations:
        amount = available * (a.percentage / 100) if available > 0 else 0
        allocations.append({'id': a.id, 'category': a.category, 'percentage': a.percentage, 'amount': round(amount, 2)})

    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()

    return render_template(
        'summary.html',
        total_income=total_income,
        total_expenses=total_expenses,
        total_debt_remaining=total_debt_remaining,
        total_debt_payments=total_debt_payments,
        available=available,
        allocations=allocations,
        total_percentage=total_percentage,
        goals=user_goals,
        recent_transactions=recent_transactions
    )
if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))