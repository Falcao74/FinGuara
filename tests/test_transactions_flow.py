from decimal import Decimal


def signup_and_login(client, username="user_tx", password="pw12345"):
    rv = client.post("/auth/signup", data={
        "username": username,
        "password": password,
        "confirm": password,
    }, follow_redirects=True)
    assert "Usuário criado com sucesso" in rv.get_data(as_text=True)
    rv = client.post("/auth/login", data={"username": username, "password": password}, follow_redirects=True)
    assert "Login realizado com sucesso" in rv.get_data(as_text=True)


def test_create_valid_expense_and_list_badges(client):
    signup_and_login(client)
    rv = client.post("/transacoes", data={
        "kind": "despesa",
        "description": "Conta de luz",
        "value": "123,45",
        "due_date": "10/10/2025",
        "status": "Pendente",
        "expense_type": "Conta de consumo",
        "category": "Luz",
        "payment_method": "PIX",
    }, follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert "Transação registrada" in html
    assert "Conta de luz" in html
    assert "R$ 123.45" in html
    # Badge de tipo despesa
    assert "badge" in html and "despesa" in html
    # Badge de status pendente
    assert "Pendente" in html


def test_create_valid_income_and_list(client):
    signup_and_login(client, username="income_user")
    rv = client.post("/transacoes", data={
        "kind": "receita",
        "description": "Salário",
        "value": "2500",
        "received_date": "05/10/2025",
        "source": "Empresa",
        "income_category": "Renda fixa",
    }, follow_redirects=True)
    html = rv.get_data(as_text=True)
    assert "Transação registrada" in html
    assert "Salário" in html
    assert "R$ 2500.00" in html
    assert "receita" in html


def test_validation_invalid_value_and_description(client):
    signup_and_login(client, username="val_user")
    # Valor inválido
    rv = client.post("/transacoes", data={
        "kind": "despesa",
        "description": "Teste",
        "value": "-10",
    }, follow_redirects=True)
    assert "Valor deve ser positivo" in rv.get_data(as_text=True)

    # Descrição curta
    rv = client.post("/transacoes", data={
        "kind": "receita",
        "description": "abc",
        "value": "10",
    }, follow_redirects=True)
    assert "Descrição deve ter ao menos 5 caracteres" in rv.get_data(as_text=True)


def test_validation_invalid_dates(client):
    signup_and_login(client, username="date_user")
    rv = client.post("/transacoes", data={
        "kind": "despesa",
        "description": "Conta água",
        "value": "100",
        "due_date": "31/02/2025",
        "status": "Pendente",
        "expense_type": "Conta de consumo",
        "category": "Água",
        "payment_method": "Boleto",
    }, follow_redirects=True)
    assert "Data de vencimento inválida" in rv.get_data(as_text=True)

    rv = client.post("/transacoes", data={
        "kind": "receita",
        "description": "Freelancer",
        "value": "500",
        "received_date": "32/10/2025",
        "source": "Cliente",
        "income_category": "Variável",
    }, follow_redirects=True)
    assert "Data de recebimento inválida" in rv.get_data(as_text=True)


def test_dashboard_summary_and_upcoming(client):
    signup_and_login(client, username="dash_user")
    # Cria despesa pendente para aparecer em Próximas contas
    client.post("/transacoes", data={
        "kind": "despesa",
        "description": "Internet",
        "value": "200",
        "due_date": "10/10/2025",
        "status": "Pendente",
        "expense_type": "Conta de consumo",
        "category": "Internet",
        "payment_method": "Boleto",
    }, follow_redirects=True)
    # Cria receita
    client.post("/transacoes", data={
        "kind": "receita",
        "description": "Autônomo",
        "value": "1000",
        "received_date": "05/10/2025",
        "source": "Cliente",
        "income_category": "Variável",
    }, follow_redirects=True)

    rv = client.get("/")
    html = rv.get_data(as_text=True)
    assert "Receitas (mês)" in html
    assert "Despesas (mês)" in html
    assert "Saldo (mês)" in html
    # Próximas contas contém Internet
    assert "Próximas contas" in html
    assert "Internet" in html