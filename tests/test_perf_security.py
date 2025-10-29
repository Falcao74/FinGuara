import time
import statistics
from app import create_app, db
from app.models import User


def _setup_user(client):
    # Cadastra usuário básico
    rv = client.post("/auth/signup", data={
        "username": "perfuser",
        "password": "perfpass",
        "confirm": "perfpass",
    }, follow_redirects=True)
    assert "Usuário criado com sucesso" in rv.get_data(as_text=True)


def test_login_page_perf_and_security(app_ctx):
    app = create_app()
    with app.test_client() as client:
        _setup_user(client)

        # Performance: medir GET /auth/login em alta repetição
        samples = []
        for _ in range(200):
            t0 = time.perf_counter()
            rv = client.get("/auth/login")
            t1 = time.perf_counter()
            assert rv.status_code == 200
            samples.append((t1 - t0) * 1000.0)  # ms

        avg_ms = statistics.mean(samples)
        p95_ms = statistics.quantiles(samples, n=100)[94]
        # Limites leves para ambiente de teste/dev
        assert avg_ms < 50, f"Login GET médio lento: {avg_ms:.2f}ms"
        assert p95_ms < 100, f"Login GET p95 lento: {p95_ms:.2f}ms"

        # Segurança básica: SQL injection não deve autenticar
        rv = client.post("/auth/login", data={
            "username": "perfuser' OR '1'='1",
            "password": "whatever",
        }, follow_redirects=True)
        html = rv.get_data(as_text=True)
        assert "Usuário ou senha inválidos" in html

        # Segurança: usuário inativo não autentica
        user = User.query.filter_by(username="perfuser").first()
        user.ativo = False
        db.session.commit()
        rv = client.post("/auth/login", data={
            "username": "perfuser",
            "password": "perfpass",
        }, follow_redirects=True)
        html = rv.get_data(as_text=True)
        assert "Usuário ou senha inválidos" in html