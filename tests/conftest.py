import os
import logging
import pytest

from app import create_app, db


@pytest.fixture()
def app(tmp_path):
    # Usa SQLite temporário por teste
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    # Evita REDIS em testes
    os.environ.pop("REDIS_URL", None)

    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    # Garante nível de log adequado para captura
    app.logger.setLevel(logging.INFO)
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        yield