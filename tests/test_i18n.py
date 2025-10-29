import pytest


def test_footer_translations_default_pt_br(client, app_ctx):
    """Verifica strings do rodapé em pt-BR por padrão."""
    rv = client.get('/auth/login')
    html = rv.get_data(as_text=True)
    assert '© 2025 FinGuará' in html
    assert 'Acompanhe suas finanças com facilidade.' in html


def test_language_switch_en_us_updates_texts(client, app_ctx):
    """Troca para en-US e valida strings traduzidas no rodapé e título."""
    # Ajusta idioma via JSON
    rv = client.post('/i18n/set-language', json={'language': 'en-US'})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['success'] is True
    assert data['language'] == 'en-US'

    # Verifica renderização em inglês
    rv = client.get('/auth/login')
    html = rv.get_data(as_text=True)
    assert '© 2025 FinGuara. All rights reserved.' in html
    assert 'Track your finances with ease.' in html
    # Como navbar não aparece no login, validar apenas rodapé em en-US


def test_language_switch_persists_session_es_es(client, app_ctx):
    """Troca para es-ES e confirma persistência em requisições subsequentes."""
    rv = client.post('/i18n/set-language', json={'language': 'es-ES'})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['success'] is True
    assert data['language'] == 'es-ES'

    # Primeira renderização em espanhol
    rv = client.get('/auth/login')
    html = rv.get_data(as_text=True)
    assert '© 2025 FinGuara. Todos los derechos reservados.' in html
    assert 'Administra tus finanzas con facilidad.' in html

    # Segunda renderização deve manter espanhol (sessão)
    rv = client.get('/auth/login')
    html = rv.get_data(as_text=True)
    assert '© 2025 FinGuara. Todos los derechos reservados.' in html


def test_language_switch_invalid_returns_400(client, app_ctx):
    """Idioma inválido deve retornar 400 com erro apropriado."""
    rv = client.post('/i18n/set-language', json={'language': 'fr-FR'})
    assert rv.status_code == 400
    data = rv.get_json()
    assert data['success'] is False
    assert 'Idioma' in data.get('error', '') or 'Language' in data.get('error', '')


def test_nav_translations_authenticated_en_us(client, app_ctx):
    """Autentica usuário, troca para en-US e valida rótulos do menu."""
    # Cria usuário
    rv = client.post('/auth/signup', data={
        'username': 'user1',
        'password': 'abcd1234',
        'confirm': 'abcd1234',
    })
    assert rv.status_code in (200, 302)

    # Faz login
    rv = client.post('/auth/login', data={
        'username': 'user1',
        'password': 'abcd1234',
    }, follow_redirects=True)
    assert rv.status_code == 200

    # Troca idioma
    rv = client.post('/i18n/set-language', json={'language': 'en-US'})
    assert rv.status_code == 200

    # Abre dashboard autenticado e verifica labels
    rv = client.get('/dashboard')
    html = rv.get_data(as_text=True)
    assert 'Dashboard' in html
    assert 'Transactions' in html
    assert 'Registrations' in html or 'Users' in html  # menu cadastro
    assert 'Logout' in html