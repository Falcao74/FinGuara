# FinGuará

FinGuará é um sistema de controle de gastos pessoal construído em Flask, com autenticação segura, internacionalização e uma interface responsiva.

## Requisitos do Sistema
- Python 3.11+
- Pip e virtualenv (opcional)

## Como criar e inicializar o banco de dados
1. Crie e ative o ambiente virtual (opcional):
   - Windows PowerShell: `python -m venv env ; ./env/Scripts/Activate.ps1`
2. Instale dependências: `pip install -r requirements.txt`
3. Execute a aplicação (cria o banco SQLite automaticamente): `python run.py`
4. O banco SQLite será criado em `finance.db` na raiz do projeto.

## Configuração do .gitignore
Adicionamos regras para ignorar arquivos sensíveis e artefatos locais:
- `env/` (ambiente virtual)
- `finance.db` (banco local)
- `*.pyc`, `__pycache__/`
- `.env` (variáveis de ambiente)
- `.DS_Store`, `Thumbs.db`

## Testes aprovados
Todos os testes unitários e de integração passaram. Lista de casos:
- `tests/test_admin_flow.py::test_initial_banner_shows_on_login_and_signup`
- `tests/test_admin_flow.py::test_signup_removes_admin_and_hides_banner`
- `tests/test_admin_flow.py::test_block_admin_username`
- `tests/test_admin_flow.py::test_subsequent_users_banner_stays_hidden`
- `tests/test_banks_accounts.py::test_banks_requires_login`
- `tests/test_banks_accounts.py::test_accounts_requires_login`
- `tests/test_banks_accounts.py::test_create_bank_and_list`
- `tests/test_banks_accounts.py::test_create_account_with_bank_and_list`
- `tests/test_banks_accounts.py::test_account_validation_name_required`
- `tests/test_banks_accounts.py::test_accounts_are_user_scoped`
- `tests/test_transactions_flow.py::test_create_valid_expense_and_list_badges`
- `tests/test_transactions_flow.py::test_create_valid_income_and_list`
- `tests/test_transactions_flow.py::test_validation_invalid_value_and_description`
- `tests/test_transactions_flow.py::test_validation_invalid_dates`
- `tests/test_transactions_flow.py::test_dashboard_summary_and_upcoming`
- `tests/test_perf_security.py` (todos os checks)

---

# English Version

FinGuará is a personal expense tracker built with Flask, featuring secure authentication, internationalization, and a responsive UI.

## Database Setup
- Optional: create and activate a virtual environment.
- Install dependencies: `pip install -r requirements.txt`
- Run the app: `python run.py` (SQLite database `finance.db` is created automatically).

## .gitignore
- Ignore local environment (`env/`), `finance.db`, `__pycache__/`, `.env`, and common OS files.

## Approved Tests
All unit and integration tests passed. See the list above for exact test cases.

---

# Versión en Español

FinGuará es un sistema de control de gastos personal hecho con Flask, con autenticación segura, internacionalización y una interfaz responsiva.

## Creación de la base de datos
- Opcional: crea y activa un entorno virtual.
- Instala dependencias: `pip install -r requirements.txt`
- Ejecuta la aplicación: `python run.py` (se crea automáticamente la base SQLite `finance.db`).

## .gitignore
- Ignora `env/`, `finance.db`, `__pycache__/`, `.env` y archivos comunes del sistema operativo.

## Pruebas aprobadas
Todas las pruebas unitarias y de integración han pasado. Consulta la lista arriba para los casos exactos.