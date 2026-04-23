# 📚 Books API

API REST desenvolvida com foco em demonstrar conceitos de **CRUD (Create, Read, Update, Delete)**, **autenticação segura** e **proteção contra abuso com rate limiting**, utilizando Python e o framework FastAPI.

---

## 🚀 Tecnologias utilizadas

* **Python** – linguagem principal
* **FastAPI** – framework web moderno e performático
* **SQLAlchemy** – ORM para manipulação do banco de dados
* **Pydantic** – validação de dados e definição de schemas
* **Uvicorn** – servidor ASGI para execução da aplicação
* **bcrypt** – hashing seguro de senhas
* **python-jose** – geração e validação de tokens JWT
* **SlowAPI** – proteção contra abuso de requisições
* **pytest** – testes automatizados

---

## 📦 Dependências

As dependências do projeto estão definidas no arquivo `requirements.txt`:

```
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.13.0
bcrypt>=4.0.0
click==8.3.2
dotenv==0.9.9
fastapi==0.136.0
greenlet==3.4.0
h11==0.16.0
httpx>=0.27.0
idna==3.11
pydantic==2.13.3
pydantic_core==2.46.3
pytest>=8.0.0
python-dotenv==1.2.2
python-jose[cryptography]>=3.3.0
SQLAlchemy==2.0.49
starlette==1.0.0
typing-inspection==0.4.2
typing_extensions==4.15.0
uvicorn==0.44.0
```

---

## ⚙️ Como executar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/NatanBarboza/api_books
cd api_books
```

### 2. Criar e ativar ambiente virtual

#### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha com os valores reais:

```bash
cp .env.example .env
```

Edite o `.env` com suas configurações:

```env
# App config
DEBUG="True"
APP_NAME="API_V1-BOOKS"
APP_SECRET_KEY="seu-valor-gerado-com-openssl-rand-hex-32"
APP_DATABASE_URL="sqlite:///./books.db"

# Rate limit (exemplos)
RATE_LIMIT_LOGIN="5/minute"
RATE_LIMIT_REGISTER="3/minute"

# Tests config
TEST_DATABASE_URL="sqlite:///./test-env.db"
```

Gerar chave segura:

```bash
openssl rand -hex 32
```

---

### 5. Executar a aplicação

```bash
python run.py
```

---

### 6. Acessar a API

* Swagger UI: [http://localhost:8080/docs](http://localhost:8080/docs)
* ReDoc: [http://localhost:8080/redoc](http://localhost:8080/redoc)

---

## 📌 Funcionalidades

### Livros

| Método   | Rota                 | Descrição              | Escopo  |
| -------- | -------------------- | ---------------------- | ------- |
| `GET`    | `/books/`            | Listar todos os livros | `user`  |
| `GET`    | `/books/{id}`        | Buscar livro por ID    | `user`  |
| `POST`   | `/books/create`      | Criar livro            | `admin` |
| `PUT`    | `/books/edit/{id}`   | Atualizar livro        | `admin` |
| `DELETE` | `/books/delete/{id}` | Deletar livro          | `admin` |

---

### Autenticação

* 📝 Registro de usuário com validação de senha
* 🔑 Login com emissão de access token e refresh token
* 🔄 Refresh token com rotação
* 🚪 Logout com revogação de tokens
* 👤 Endpoint `/auth/me`
* 🛡️ Controle de acesso por escopos

---

## 🔐 Rate Limiting

A API implementa proteção contra abuso utilizando SlowAPI.

### Limites configurados

| Endpoint         | Limite                   |
| ---------------- | ------------------------ |
| `/auth/login`    | 5 requisições por minuto |
| `/auth/register` | 3 requisições por minuto |
| `/auth/refresh`  | Sem limite               |

### Características

* Limitação baseada em identificador do cliente (IP ou header customizado)
* Respostas com status `429 Too Many Requests`
* Corpo da resposta contém campo `error`
* Tentativas inválidas também contam para o limite
* Implementação centralizada (singleton) para evitar inconsistências

## 🔐 Autenticação

A API utiliza JWT com:

| Token         | Validade   | Finalidade   |
| ------------- | ---------- | ------------ |
| Access Token  | 30 minutos | Autenticação |
| Refresh Token | 7 dias     | Renovação    |

### Uso

```
Authorization: Bearer <access_token>
```

---

## 🧪 Testes

O projeto possui **54 testes automatizados**, incluindo cenários de segurança e rate limiting.

### Executar

```bash
pytest tests/ -v
```

### Cobertura

| Módulo                | Testes | Cenários                        |
| --------------------- | ------ | ------------------------------- |
| `test_book_routes.py` | 17     | CRUD + autenticação             |
| `test_auth_routes.py` | 26     | Auth + segurança                |
| `test_rate_limit.py`  | 11     | Limites, edge cases, isolamento |

### Destaques

* Testes de limite exato (edge cases)
* Validação de bloqueio correto (429)
* Banco de teste isolado por execução

---

## 🗄️ Banco de dados

SQLite utilizado para ambiente local.

### Tabelas

* `books`
* `users`
* `revoked_tokens`

As tabelas são criadas automaticamente na inicialização da aplicação.

---

## 🗂️ Estrutura do projeto

```
books-api/
├── .env.example
├── conftest.py
├── main.py
├── run.py
├── requirements.txt
├── tests/
│   ├── __init__.py
│   ├── test_auth_routes.py
│   ├── test_book_routes.py
│   └── test_rate_limit.py
└── app/
    ├── core/
    │   ├── config.py
    │   ├── security.py
    │   └── limiter.py          # limiter centralizado
    ├── models/
    │   ├── user_model.py
    │   └── revoked_token_model.py      # model da blocklist
    ├── schema/
    │   └── auth_schema.py
    ├── repository/
    │   ├── user_repository.py
    │   └── revoked_token_repository.py
    ├── service/
    │   ├── auth_service.py
    │   └── book_service.py
    ├── routes/
    │   ├── auth_routes.py
    │   └── book_routes.py
    └── dependecies/
        └── auth.py
```

---

## 🗺️ Próximos passos

* Rate limiting por usuário autenticado
* Limpeza automática de tokens expirados
* Painel de auditoria de autenticação
* Endpoint para promover usuário a admin sem precisar acessar o banco diretamente

---

## 📄 Licença

Projeto voltado para estudo, prática e portfólio.
