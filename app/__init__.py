import os
from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_login import current_user
import os
from sqlalchemy import event, inspect as sa_inspect

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
# Remove mensagem padrão em inglês do Flask-Login
login_manager.login_message = None


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static")
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', 'finance.db')}",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    login_manager.init_app(app)
    
    # Inicializa sistema de internacionalização
    from .i18n import init_i18n
    init_i18n(app)

    # Regras de integridade e auditoria para alterações de status ativo/inativo
    from .models import User as _UserModel, Bank as _BankModel, Account as _AccountModel, Transaction as _TransactionModel

    def _log_actor():
        try:
            from flask_login import current_user as _cu
            return getattr(_cu, "username", "system") or "system"
        except Exception:
            return "system"

    @event.listens_for(_BankModel, "before_update")
    def _bank_integrity_check(mapper, connection, target):
        hist = sa_inspect(target).attrs.ativo.history
        changed_to_inactive = bool(hist.has_changes()) and (target.ativo is False)
        if changed_to_inactive:
            # Impede inativar banco com contas ativas vinculadas
            from .models import Account as _Account
            q = db.session.query(_Account).filter(
                _Account.bank_id == target.id,
                _Account.ativo.is_(True),
            )
            if q.count() > 0:
                raise ValueError("Integridade referencial: não é possível inativar banco com contas ativas")

    @event.listens_for(_UserModel, "before_update")
    def _user_integrity_check(mapper, connection, target):
        hist = sa_inspect(target).attrs.ativo.history
        changed_to_inactive = bool(hist.has_changes()) and (target.ativo is False)
        if changed_to_inactive:
            # Impede inativar usuário com contas ou transações ativas
            from .models import Account as _Account, Transaction as _Tx
            q_acc = db.session.query(_Account).filter(_Account.user_id == target.id, _Account.ativo.is_(True))
            q_tx = db.session.query(_Tx).filter(_Tx.user_id == target.id, _Tx.ativo.is_(True))
            if q_acc.count() > 0 or q_tx.count() > 0:
                raise ValueError("Integridade referencial: não é possível inativar usuário com dados ativos")

    @event.listens_for(_AccountModel, "before_update")
    def _account_integrity_check(mapper, connection, target):
        hist = sa_inspect(target).attrs.ativo.history
        changed_to_inactive = bool(hist.has_changes()) and (target.ativo is False)
        if changed_to_inactive and target.bank_id:
            # Se conta vai ser inativada, ok; não há vínculos de transação neste schema
            pass

    @event.listens_for(_TransactionModel, "before_update")
    def _transaction_integrity_check(mapper, connection, target):
        # Sem vínculo de conta, apenas permite inativar
        return

    @event.listens_for(db.session, "before_flush")
    def _audit_status_change(session, flush_context, instances):
        # Registra alterações de ativo/inativo para modelos principais
        actor = _log_actor()
        for obj in list(session.dirty):
            try:
                insp = sa_inspect(obj)
                if "ativo" in insp.attrs:
                    hist = insp.attrs.ativo.history
                    if hist.has_changes():
                        old = hist.deleted[0] if hist.deleted else None
                        new = hist.added[0] if hist.added else None
                        if old is not None and new is not None and old != new:
                            app.logger.info(
                                f"AUDIT: ativo change model={obj.__class__.__name__} id={getattr(obj, 'id', '-')}: {old} -> {new} by {actor}"
                            )
            except Exception:
                # Não interrompe o flush por falha de auditoria
                continue

    # Opção de sessões em Redis para maior disponibilidade
    try:
        from flask_session import Session
        import redis as _redis
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            app.config.update({
                "SESSION_TYPE": "redis",
                "SESSION_REDIS": _redis.from_url(redis_url),
            })
            Session(app)
    except Exception:
        # Mantém sessões padrão em cookies se falhar
        pass

    from .models import User  # noqa: F401

    with app.app_context():
        db.create_all()
        # Migração leve: garante coluna 'ativo' nas tabelas existentes (SQLite)
        try:
            from sqlalchemy import text, inspect as _inspect
            engine = db.engine
            insp = _inspect(engine)
            def _has_col(table, col):
                return any(c['name'] == col for c in insp.get_columns(table))
            with engine.begin() as conn:
                for table in ("user", "bank", "account", "transaction"):
                    if not _has_col(table, "ativo"):
                        conn.execute(text(f"ALTER TABLE \"{table}\" ADD COLUMN ativo BOOLEAN NOT NULL DEFAULT 1"))
                        app.logger.info(f"Migração: coluna 'ativo' adicionada à tabela {table}")
        except Exception as e:
            app.logger.warning(f"Migração automática da coluna 'ativo' falhou: {e}")
        # Seed admin if no users exist
        if User.query.count() == 0:
            admin = User(username="admin", is_admin=True)
            admin.set_password("admin")
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Seed inicial: criado usuário admin/admin para primeiro acesso")

    # Blueprints
    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    from .routes.i18n import bp as i18n_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(i18n_bp)

    # Swagger basic config
    try:
        from flasgger import Swagger

        Swagger(app, template={
            "swagger": "2.0",
            "info": {
                "title": "Finance API",
                "version": "1.0.0",
            },
        })
    except Exception:
        pass

    # Error handlers amigáveis
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error_404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("error_500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error_403.html"), 403

    # Segurança: evita cache de páginas autenticadas para impedir retorno pós-logout
    @app.after_request
    def add_cache_headers(response):
        try:
            if current_user.is_authenticated:
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
        except Exception:
            pass
        return response

    # Contexto para exibir banner inicial de credenciais admin enquanto for primeira execução
    @app.context_processor
    def initial_admin_banner():
        try:
            from .models import User as _User
            # Exibe banner se existe admin e nenhum usuário real foi criado ainda
            has_admin = _User.query.filter(
                _User.username == "admin",
                _User.is_admin.is_(True),
                _User.ativo.is_(True),
            ).first() is not None
            non_admin_count = _User.query.filter(
                _User.username != "admin",
                _User.ativo.is_(True),
            ).count()
            return {"show_initial_admin_banner": bool(has_admin and non_admin_count == 0)}
        except Exception:
            # Em caso de erro de DB, não exibe o banner
            return {"show_initial_admin_banner": False}

    return app