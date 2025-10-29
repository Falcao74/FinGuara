from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response
from flask_login import login_user, logout_user, login_required, current_user
from flask import session
from .. import db
from ..models import User, Account, Transaction

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember_flag = request.form.get("remember_username") == "on"
        # Apenas usuários ativos podem autenticar
        user = User.query.filter_by(username=username, ativo=True).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Login realizado com sucesso", "success")
            resp = make_response(redirect(url_for("main.dashboard")))
            # Configura ou remove cookie de "lembrar meu usuário"
            if remember_flag:
                # 30 dias
                max_age = 30 * 24 * 60 * 60
                resp.set_cookie(
                    "remember_username",
                    username,
                    max_age=max_age,
                    httponly=True,
                    secure=True,
                    samesite="Lax",
                    path="/"
                )
            else:
                resp.delete_cookie("remember_username", path="/")
            return resp
        flash("Usuário ou senha inválidos", "danger")
    # Pré-preenche usuário a partir de cookie HttpOnly (servidor-side)
    remembered_username = request.cookies.get("remember_username", "")
    return render_template("login.html", remembered_username=remembered_username)


@bp.route("/logout")
@login_required
def logout():
    # Encerra sessão do Flask-Login e limpa dados de sessão
    logout_user()
    session.clear()

    # Redireciona para login com cabeçalhos para evitar cache e navegação para páginas anteriores
    resp = make_response(redirect(url_for("auth.login")))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    flash("Sessão encerrada", "info")
    return resp


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    # Permite acesso ao cadastro tanto autenticado quanto anônimo
    # (continua bloqueando username 'admin' e validações usuais)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        # Validações simples
        if len(username) < 3:
            flash("Usuário deve ter ao menos 3 caracteres", "warning")
            return render_template("signup.html")
        if password != confirm or len(password) < 4:
            flash("Senha inválida ou não confere", "warning")
            return render_template("signup.html")
        if username.lower() == "admin":
            flash("Usuário 'admin' não pode ser utilizado", "warning")
            return render_template("signup.html")
        if User.query.filter_by(username=username).first():
            flash("Usuário já existe", "warning")
            return render_template("signup.html")

        user = User(username=username, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f"Primeiro usuário real criado: {username}. Iniciando inativação do admin.")

        # Inativa admin padrão, se existir (soft delete), após verificar integridade
        admin = User.query.filter_by(username="admin", is_admin=True).first()
        if admin:
            # Valida integridade: não pode inativar se houver registros ativos vinculados
            has_active_accounts = Account.query.filter(
                Account.user_id == admin.id,
                Account.ativo.is_(True),
            ).count() > 0
            has_active_transactions = Transaction.query.filter(
                Transaction.user_id == admin.id,
                Transaction.ativo.is_(True),
            ).count() > 0
            if has_active_accounts or has_active_transactions:
                current_app.logger.warning(
                    "Falha ao inativar admin: possui contas ou transações ativas"
                )
            else:
                admin.ativo = False
                db.session.commit()
                current_app.logger.info("Usuário admin inativado imediatamente após o primeiro cadastro.")
                current_app.logger.info(
                    f"AUDIT: status ativo alterado em User id={admin.id}, ativo=False, actor={username}"
                )

        flash("Usuário criado com sucesso. Faça login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")