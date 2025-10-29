import logging
from app.models import User


def test_initial_banner_shows_on_login_and_signup(client, app_ctx):
    # Admin é seedado automaticamente; sem usuários reais
    assert User.query.count() == 1
    admin = User.query.filter_by(username="admin", is_admin=True).first()
    assert admin is not None

    # Login exibe banner
    rv = client.get("/auth/login")
    html = rv.get_data(as_text=True)
    assert "Usuário inicial:" in html and "Senha:" in html

    # Signup exibe banner
    rv = client.get("/auth/signup")
    html = rv.get_data(as_text=True)
    assert "Usuário inicial:" in html and "Senha:" in html


def test_signup_removes_admin_and_hides_banner(client, app_ctx, caplog):
    with caplog.at_level(logging.INFO):
        rv = client.post("/auth/signup", data={
            "username": "user1",
            "password": "secret123",
            "confirm": "secret123",
        }, follow_redirects=True)
        # Redireciona para login com sucesso
        html = rv.get_data(as_text=True)
        assert "Usuário criado com sucesso" in html

        # Logs de transição (soft delete/inativação)
        assert any("Primeiro usuário real criado: user1" in rec.message for rec in caplog.records)
        assert any("Usuário admin inativado imediatamente" in rec.message for rec in caplog.records)

    # Admin inativado (não ativo)
    admin_active = User.query.filter_by(username="admin", is_admin=True, ativo=True).first()
    assert admin_active is None

    # Banner some
    rv = client.get("/auth/login")
    html = rv.get_data(as_text=True)
    assert "Usuário inicial: admin | Senha: admin" not in html

    # Login com admin falha (inativo)
    rv = client.post("/auth/login", data={"username": "admin", "password": "admin"}, follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert "Usuário ou senha inválidos" in html

    # Login com novo usuário funciona
    rv = client.post("/auth/login", data={"username": "user1", "password": "secret123"}, follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert "Login realizado com sucesso" in html
    assert "Olá, user1" in html  # navbar autenticada


def test_block_admin_username(client, app_ctx):
    # Tentar cadastrar admin deve ser bloqueado
    rv = client.post("/auth/signup", data={
        "username": "admin",
        "password": "abcd1234",
        "confirm": "abcd1234",
    })
    html = rv.get_data(as_text=True)
    # Jinja escapa aspas simples; validamos trecho significativo
    assert "não pode ser utilizado" in html


def test_subsequent_users_banner_stays_hidden(client, app_ctx):
    # Primeiro usuário
    rv = client.post("/auth/signup", data={
        "username": "user2",
        "password": "pw12345",
        "confirm": "pw12345",
    }, follow_redirects=True)
    assert "Usuário criado com sucesso" in rv.get_data(as_text=True)

    # Banner não deve aparecer mais
    rv = client.get("/auth/login")
    assert "Usuário inicial: admin | Senha: admin" not in rv.get_data(as_text=True)

    # Segundo usuário
    rv = client.post("/auth/signup", data={
        "username": "user3",
        "password": "pw12345",
        "confirm": "pw12345",
    }, follow_redirects=True)
    assert "Usuário criado com sucesso" in rv.get_data(as_text=True)

    # Confirma que admin permanece inativo
    admin_active = User.query.filter_by(username="admin", is_admin=True, ativo=True).first()
    assert admin_active is None