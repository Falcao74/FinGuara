from datetime import datetime
try:
    from datetime import UTC as _UTC
except Exception:
    # Python < 3.11 fallback
    import datetime as _dt
    _UTC = getattr(_dt, 'timezone', _dt.timezone.utc)
from decimal import Decimal
from typing import Optional
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(_UTC))

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kind = db.Column(db.String(10), nullable=False)  # 'despesa' ou 'receita'
    description = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Numeric(12, 2), nullable=False)

    # Despesa
    due_date = db.Column(db.Date)
    payment_date = db.Column(db.Date)
    status = db.Column(db.String(20))  # Pago/Pendente/Vencido
    expense_type = db.Column(db.String(30))  # Cartão/Dívida/Conta de consumo/Outros
    category = db.Column(db.String(50))  # Luz, Água, Aluguel, Internet, Celular, etc
    payment_method = db.Column(db.String(20))  # PIX, Boleto, Débito, Crédito, Dinheiro
    notes = db.Column(db.Text)

    # Receita
    received_date = db.Column(db.Date)
    source = db.Column(db.String(80))  # Empresa, Cliente, Plataforma
    income_category = db.Column(db.String(30))  # Renda fixa, Variável, Extra

    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(_UTC))

    def __repr__(self):
        return f"<Transaction {self.id} {self.kind} {self.value}>"


class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(10))
    notes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(_UTC))

    def __repr__(self):
        return f"<Bank {self.name}>"


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'))
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(40))  # Corrente, Poupança, Crédito, Carteira
    notes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(_UTC))

    bank = db.relationship('Bank')

    def __repr__(self):
        return f"<Account {self.name} user={self.user_id}>"