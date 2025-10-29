from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import Transaction, Bank, Account

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    # Resumo simples do mês atual
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month, 28)

    expenses = db.session.query(db.func.sum(Transaction.value)).filter(
        Transaction.user_id == current_user.id,
        Transaction.kind == "despesa",
        Transaction.ativo.is_(True),
        Transaction.due_date >= month_start,
        Transaction.due_date <= month_end,
    ).scalar() or Decimal(0)

    incomes = db.session.query(db.func.sum(Transaction.value)).filter(
        Transaction.user_id == current_user.id,
        Transaction.kind == "receita",
        Transaction.ativo.is_(True),
        Transaction.received_date >= month_start,
        Transaction.received_date <= month_end,
    ).scalar() or Decimal(0)

    balance = incomes - expenses

    # Próximas contas a pagar (pendentes)
    upcoming = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.kind == "despesa",
        Transaction.ativo.is_(True),
        Transaction.status.in_(["Pendente", "Vencido"]),
    ).order_by(Transaction.due_date.asc()).limit(10).all()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        incomes=incomes,
        balance=balance,
        upcoming=upcoming,
    )


@bp.route("/transacoes", methods=["GET", "POST"])
@login_required
def transactions():
    if request.method == "POST":
        kind = request.form.get("kind")  # despesa/receita
        description = request.form.get("description", "").strip()
        value_str = request.form.get("value", "0").replace(",", ".")
        try:
            value = Decimal(value_str)
        except Exception:
            flash("Valor inválido", "warning")
            return redirect(url_for("main.transactions"))
        if value <= 0:
            flash("Valor deve ser positivo", "warning")
            return redirect(url_for("main.transactions"))
        if len(description) < 5:
            flash("Descrição deve ter ao menos 5 caracteres", "warning")
            return redirect(url_for("main.transactions"))

        tx = Transaction(user_id=current_user.id, kind=kind, description=description, value=value)
        if kind == "despesa":
            from datetime import datetime as dt
            due_date = request.form.get("due_date")
            payment_date = request.form.get("payment_date")
            tx.status = request.form.get("status")
            tx.expense_type = request.form.get("expense_type")
            tx.category = request.form.get("category")
            tx.payment_method = request.form.get("payment_method")
            tx.notes = request.form.get("notes")
            if due_date:
                try:
                    tx.due_date = dt.strptime(due_date, "%d/%m/%Y").date()
                except Exception:
                    flash("Data de vencimento inválida", "warning")
                    return redirect(url_for("main.transactions"))
            if payment_date:
                try:
                    tx.payment_date = dt.strptime(payment_date, "%d/%m/%Y").date()
                except Exception:
                    flash("Data de pagamento inválida", "warning")
                    return redirect(url_for("main.transactions"))
        else:
            from datetime import datetime as dt
            received_date = request.form.get("received_date")
            tx.source = request.form.get("source")
            tx.income_category = request.form.get("income_category")
            if received_date:
                try:
                    tx.received_date = dt.strptime(received_date, "%d/%m/%Y").date()
                except Exception:
                    flash("Data de recebimento inválida", "warning")
                    return redirect(url_for("main.transactions"))

        db.session.add(tx)
        db.session.commit()
        flash("Transação registrada", "success")
        return redirect(url_for("main.transactions"))

    # Listagem
    txs = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.ativo.is_(True),
    ).order_by(Transaction.created_at.desc()).limit(50).all()
    return render_template("transactions.html", transactions=txs)


@bp.route("/cadastros/bancos", methods=["GET", "POST"])
@login_required
def banks():
    if request.method == "POST":
        name = request.form.get("bank_name", "").strip()
        code = request.form.get("bank_code", "").strip()
        notes = request.form.get("notes", "").strip()
        if len(name) < 2:
            flash("Nome do banco é obrigatório", "warning")
            return redirect(url_for("main.banks"))
        bank = Bank(name=name, code=code or None, notes=notes or None)
        db.session.add(bank)
        db.session.commit()
        flash("Banco cadastrado", "success")
        return redirect(url_for("main.banks"))

    banks_list = Bank.query.filter(Bank.ativo.is_(True)).order_by(Bank.created_at.desc()).limit(20).all()
    return render_template("banks.html", banks=banks_list)


@bp.route("/cadastros/contas", methods=["GET", "POST"])
@login_required
def accounts():
    if request.method == "POST":
        name = request.form.get("account_name", "").strip()
        type_ = request.form.get("account_type", "").strip()
        bank_name = request.form.get("account_bank", "").strip()
        notes = request.form.get("notes", "").strip()
        if len(name) < 2:
            flash("Apelido da conta é obrigatório", "warning")
            return redirect(url_for("main.accounts"))
        bank = None
        if bank_name:
            bank = Bank.query.filter(Bank.name.ilike(bank_name)).first()
            if not bank:
                bank = Bank(name=bank_name)
                db.session.add(bank)
                db.session.flush()  # obtém id sem commit imediato
        acc = Account(user_id=current_user.id, name=name, type=type_ or None, notes=notes or None,
                      bank_id=bank.id if bank else None)
        db.session.add(acc)
        db.session.commit()
        flash("Conta cadastrada", "success")
        return redirect(url_for("main.accounts"))

    accounts_list = Account.query.filter(
        Account.user_id == current_user.id,
        Account.ativo.is_(True),
    ).order_by(Account.created_at.desc()).limit(20).all()
    return render_template("accounts.html", accounts=accounts_list)