import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
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
    
@app.route('/')
def home():
    return "Hello! My finance app is working."


if __name__ == '__main__':
    app.run(debug=True)