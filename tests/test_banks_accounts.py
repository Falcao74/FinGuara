from app.models import Bank, Account, User


def signup_and_login(client, username="tester", password="pw12345"):
    # Cadastra usuário real e faz login
    rv = client.post("/auth/signup", data={
        "username": username,
        "password": password,
        "confirm": password,
    }, follow_redirects=True)
    assert "Usuário criado com sucesso" in rv.get_data(as_text=True)
    rv = client.post("/auth/login", data={
        "username": username,
        "password": password,
    }, follow_redirects=True)
    assert "Login realizado com sucesso" in rv.get_data(as_text=True)


def test_banks_requires_login(client):
    # Sem login, deve redirecionar para login
    rv = client.get("/cadastros/bancos")
    assert rv.status_code in (302, 401)


def test_accounts_requires_login(client):
    rv = client.get("/cadastros/contas")
    assert rv.status_code in (302, 401)


def test_create_bank_and_list(client, app_ctx):
    signup_and_login(client)

    # Cria banco
    rv = client.post("/cadastros/bancos", data={
        "bank_name": "Banco do Brasil",
        "bank_code": "001",
        "notes": "Teste",
    }, follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert "Banco cadastrado" in html
    # Lista contém o banco
    assert "Banco do Brasil" in html
    assert "001" in html


def test_create_account_with_bank_and_list(client, app_ctx):
    signup_and_login(client, username="joao", password="pw12345")

    # Cria banco e depois conta vinculada
    rv = client.post("/cadastros/bancos", data={
        "bank_name": "Nubank",
        "bank_code": "260",
    }, follow_redirects=True)
    assert "Banco cadastrado" in rv.get_data(as_text=True)

    rv = client.post("/cadastros/contas", data={
        "account_name": "Conta salário",
        "account_bank": "Nubank",
        "account_type": "Corrente",
        "notes": "Principal",
    }, follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert "Conta cadastrada" in html

    # Listagem mostra conta e banco
    assert "Conta salário" in html
    assert "Nubank" in html
    assert "Corrente" in html


def test_account_validation_name_required(client, app_ctx):
    signup_and_login(client, username="maria", password="pw12345")
    rv = client.post("/cadastros/contas", data={
        "account_name": "",
        "account_type": "Carteira",
    }, follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert "Apelido da conta é obrigatório" in html


def test_accounts_are_user_scoped(client, app_ctx):
    # Usuário A cria conta
    signup_and_login(client, username="alice", password="pw12345")
    client.post("/cadastros/contas", data={
        "account_name": "Conta Alice",
        "account_type": "Poupança",
    }, follow_redirects=True)

    # Logout e login como B
    client.get("/auth/logout", follow_redirects=True)
    signup_and_login(client, username="bob", password="pw12345")
    rv = client.get("/cadastros/contas")
    html = rv.get_data(as_text=True)
    # Bob não deve ver a conta de Alice
    assert "Conta Alice" not in html