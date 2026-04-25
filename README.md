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
* **APScheduler** – agendamento de tarefas em background
* **pytest** – testes automatizados

---

## 📦 Dependências

As dependências do projeto estão definidas no arquivo `requirements.txt`:

```
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.13.0
apscheduler>=3.10.0
bcrypt>=4.0.0
click==8.3.2
dotenv==0.9.9
fastapi==0.136.0
greenlet==3.4.0
h11==0.16.0
httpx>=0.27.0
idna==3.11
limits==5.8.0
pydantic==2.13.3
pydantic_core==2.46.3
pytest>=8.0.0
python-dotenv==1.2.2
python-jose[cryptography]>=3.3.0
slowapi==0.1.9
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

# Rate limit
RATE_LIMIT_LOGIN="5/minute"
RATE_LIMIT_REGISTER="3/minute"

# Tests config
TEST_DATABASE_URL="sqlite:///./test-env.db"
```

Para gerar um `APP_SECRET_KEY` seguro:

```bash
openssl rand -hex 32
```

### 5. Executar a aplicação

```bash
python run.py
```

### 6. Acessar a API

* Swagger UI: http://localhost:8080/docs
* ReDoc: http://localhost:8080/redoc

---

## 📌 Funcionalidades

### Livros

| Método | Rota | Descrição | Escopo |
|---|---|---|---|
| `GET` | `/books/` | Listar todos os livros | `user` |
| `GET` | `/books/{id}` | Buscar livro por ID | `user` |
| `POST` | `/books/create` | Criar livro | `admin` |
| `PUT` | `/books/edit/{id}` | Atualizar livro | `admin` |
| `DELETE` | `/books/delete/{id}` | Deletar livro | `admin` |

### Autenticação

* 📝 Registro de usuário com validação de senha
* 🔑 Login com emissão de access token e refresh token
* 🔄 Renovação de access token via refresh token com rotação
* 🚪 Logout com revogação imediata dos tokens
* 👤 Consulta do usuário autenticado (`/auth/me`)
* 🛡️ Proteção de rotas por escopos (`user` e `admin`)
* 🔼 Promoção de usuário para admin
* 🔽 Rebaixamento de admin para usuário

---

## 🔐 Autenticação

A API utiliza autenticação baseada em **JWT (JSON Web Tokens)** com dois tokens distintos:

| Token | Validade | Finalidade |
|---|---|---|
| Access Token | 30 minutos | Autenticar requisições |
| Refresh Token | 7 dias | Emitir novos access tokens |

### Endpoints de autenticação

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| `POST` | `/auth/register` | Cadastro de novo usuário | Não |
| `POST` | `/auth/login` | Login e emissão de tokens | Não |
| `POST` | `/auth/refresh` | Renovação do access token | Refresh token |
| `POST` | `/auth/logout` | Logout e revogação dos tokens | Access token |
| `GET` | `/auth/me` | Dados do usuário logado | Access token |
| `PATCH` | `/auth/users/{id}/promote` | Promover usuário para admin | `admin` |
| `PATCH` | `/auth/users/{id}/demote` | Rebaixar admin para usuário | `admin` |

### Como autenticar uma requisição

Após o login, utilize o `access_token` retornado no header `Authorization`:

```
Authorization: Bearer <access_token>
```

### Escopos de acesso

* `user` — acesso às rotas de leitura (`GET`)
* `admin` — acesso total, incluindo criação, edição, exclusão e gestão de papéis

Usuários comuns recebem o escopo `user` automaticamente no login. A promoção e o rebaixamento são feitos via API por um admin:

```
PATCH /auth/users/{id}/promote   → promove para admin
PATCH /auth/users/{id}/demote    → rebaixa para usuário
```

Regras de gestão de papéis:
* Somente admins podem promover ou rebaixar outros usuários
* Um admin não pode alterar o próprio papel
* Promover quem já é admin retorna `400`
* Rebaixar quem já é usuário retorna `400`
* O novo papel só é refletido no token após um novo login

### Revogação de tokens

A API mantém uma blocklist de tokens revogados na base de dados. Cada token carrega um identificador único (`jti`) e sua data de expiração (`expires_at`) no payload, registrados na tabela `revoked_tokens` nas seguintes situações:

* **Logout** — revoga imediatamente o access token e, se enviado, o refresh token
* **Refresh** — o refresh token utilizado é revogado antes de emitir o novo par (rotação de token)

Toda requisição autenticada consulta a blocklist pelo `jti` do token. Um token revogado é rejeitado com `401` mesmo que ainda esteja dentro do prazo de expiração.

### Segurança

* Senhas passam por pré-hash SHA-256 + base64 antes do bcrypt, evitando o limite de 72 bytes
* bcrypt com custo 12 para hashing de senhas
* Mensagens de erro genéricas para evitar enumeração de usuários
* Escopos embutidos no payload do JWT, sem consulta ao banco por requisição
* Cada token possui um `jti` (JWT ID) único para rastreamento e revogação individual
* Rotação de refresh token: cada refresh token só pode ser usado uma única vez

---

## 🚦 Rate Limiting

A API implementa proteção contra abuso utilizando SlowAPI.

### Limites configurados

| Endpoint | Limite |
|---|---|
| `POST /auth/login` | 5 requisições por minuto |
| `POST /auth/register` | 3 requisições por minuto |
| `POST /auth/refresh` | Sem limite |

### Características

* Limitação baseada no IP do cliente (via `X-Forwarded-For` ou IP remoto)
* Respostas bloqueadas retornam status `429 Too Many Requests`
* Corpo da resposta contém campo `error` com descrição do limite
* Tentativas com credenciais inválidas também contam para o limite
* Limites configuráveis via variáveis de ambiente (`.env`)

---

## 🧹 Limpeza automática de tokens

A aplicação executa uma tarefa em background a cada hora que remove da tabela `revoked_tokens` todos os registros cujo `expires_at` já passou.

Tokens expirados são rejeitados pela validação de `exp` do JWT de qualquer forma — a limpeza garante que a tabela não cresça indefinidamente.

O agendador é iniciado automaticamente junto com a aplicação e encerrado de forma limpa ao desligar, sem deixar threads órfãs.

---

## 📋 Logging

A aplicação utiliza um logger centralizado disponível em `app/core/logging.py`. Qualquer módulo pode importá-lo com:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
```

O formato padrão dos logs é:

```
2026-04-23 20:00:00 | INFO | app.core.scheduler | Agendador iniciado — limpeza de tokens a cada 1 hora.
```

---

## 🧪 Testes

O projeto possui **84 testes automatizados** cobrindo todos os endpoints, rate limiting, limpeza de tokens e gestão de papéis.

### Executar todos os testes

```bash
pytest tests/ -v
```

### Executar por módulo

```bash
pytest tests/test_book_routes.py -v
pytest tests/test_auth_routes.py -v
pytest tests/test_rate_limit.py -v
pytest tests/test_scheduler.py -v
pytest tests/test_promote_demote.py -v
```

### Cobertura dos testes

| Módulo | Testes | Cenários cobertos |
|---|---|---|
| `test_book_routes.py` | 17 | CRUD, autenticação e escopos |
| `test_auth_routes.py` | 26 | registro, login, refresh, logout, tokens revogados |
| `test_rate_limit.py` | 11 | limites exatos, edge cases, bloqueio e isolamento por IP |
| `test_scheduler.py` | 13 | limpeza de tokens expirados, agendador e logging |
| `test_promote_demote.py` | 17 | promoção, rebaixamento, regras de negócio e ciclo completo |

### Estrutura dos testes

```
books-api/
├── conftest.py       # fixtures: banco de teste, client, tokens e dados de exemplo
└── tests/
    ├── __init__.py
    ├── test_book_routes.py
    ├── test_auth_routes.py
    ├── test_rate_limit.py
    ├── test_scheduler.py
    └── test_promote_demote.py
```

Os testes utilizam um banco SQLite isolado definido em `TEST_DATABASE_URL` no `.env`, criado e destruído a cada teste para garantir isolamento total. Testes de rate limiting utilizam `X-Forwarded-For` com UUID único por teste para isolar contadores.

---

## 🗄️ Banco de dados

O projeto utiliza **SQLite** como banco de dados padrão para facilitar a execução local. As tabelas são criadas automaticamente na inicialização da aplicação.

### Tabelas

* `books` — dados dos livros
* `users` — dados dos usuários
* `revoked_tokens` — blocklist de tokens revogados (`jti` e `expires_at`)

---

## 🗂️ Estrutura do projeto

```
books-api/
├── .env.example                        # modelo de variáveis de ambiente
├── .gitignore
├── conftest.py                         # fixtures compartilhadas dos testes
├── run.py
├── requirements.txt
├── tests/
│   ├── __init__.py
│   ├── test_auth_routes.py
│   ├── test_book_routes.py
│   ├── test_promote_demote.py
│   ├── test_rate_limit.py
│   └── test_scheduler.py
└── app/
    ├── core/
    │   ├── config.py                   # configurações centralizadas
    │   ├── logging.py                  # logger centralizado
    │   ├── scheduler.py                # limpeza automática de tokens
    │   └── security.py                 # hashing e JWT
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

* Painel de auditoria de autenticação
* Rate limiting por usuário autenticado

---

## 📄 Licença

Projeto voltado para estudo, prática e portfólio.