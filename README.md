# 📚 Books API

API REST desenvolvida com foco em demonstrar conceitos de **CRUD (Create, Read, Update, Delete)** e **autenticação segura** utilizando Python e o framework FastAPI.

---

## 🚀 Tecnologias utilizadas

* **Python** – linguagem principal
* **FastAPI** – framework web moderno e performático
* **SQLAlchemy** – ORM para manipulação do banco de dados
* **Pydantic** – validação de dados e definição de schemas
* **Uvicorn** – servidor ASGI para execução da aplicação
* **bcrypt** – hashing seguro de senhas
* **python-jose** – geração e validação de tokens JWT
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

Após subir a aplicação, acesse:

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

### Como autenticar uma requisição

Após o login, utilize o `access_token` retornado no header `Authorization`:

```
Authorization: Bearer <access_token>
```

### Escopos de acesso

* `user` — acesso às rotas de leitura (`GET`)
* `admin` — acesso total, incluindo criação, edição e exclusão

Usuários comuns recebem o escopo `user` automaticamente no login. Para obter o escopo `admin`, o campo `is_superuser` do usuário deve ser `true` no banco de dados:

```sql
UPDATE users SET is_superuser = 1 WHERE username = 'seu_username';
```

### Revogação de tokens

A API mantém uma blocklist de tokens revogados na base de dados. Cada token carrega um identificador único (`jti`) no payload, que é registrado na tabela `revoked_tokens` nas seguintes situações:

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

## 🧪 Testes

O projeto possui uma suíte de **43 testes automatizados** cobrindo todos os endpoints.

### Executar todos os testes

```bash
pytest tests/ -v
```

### Executar por módulo

```bash
pytest tests/test_book_routes.py -v
pytest tests/test_auth_routes.py -v
```

### Cobertura dos testes

| Módulo | Testes | Cenários cobertos |
|---|---|---|
| `test_book_routes.py` | 17 | listagem, busca por ID, criação, edição, exclusão — fluxos felizes, 404, sem auth e escopos insuficientes |
| `test_auth_routes.py` | 26 | registro, login, `/me`, refresh com rotação, logout com revogação — fluxos felizes, credenciais inválidas, tokens revogados e usuário inativo |

### Estrutura dos testes

```
books-api/
├── conftest.py       # fixtures: banco de teste, client, tokens e dados de exemplo
└── tests/
    ├── __init__.py
    ├── test_book_routes.py
    └── test_auth_routes.py
```

Os testes utilizam um banco SQLite isolado definido em `TEST_DATABASE_URL` no `.env`, criado e destruído a cada teste para garantir isolamento total entre os casos.

---

## 🗄️ Banco de dados

O projeto utiliza **SQLite** como banco de dados padrão para facilitar a execução local. As tabelas são criadas automaticamente na inicialização da aplicação.

### Tabelas

* `books` — dados dos livros
* `users` — dados dos usuários
* `revoked_tokens` — blocklist de tokens revogados (identificados pelo `jti`)

---

## 🗂️ Estrutura do projeto

```
books-api/
├── .env.example                        # modelo de variáveis de ambiente
├── .gitignore
├── conftest.py                         # fixtures compartilhadas dos testes
├── main.py
├── run.py
├── requirements.txt
├── tests/
│   ├── __init__.py
│   ├── test_auth_routes.py
│   └── test_book_routes.py
└── app/
    ├── core/
    │   ├── config.py                   # configurações centralizadas
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

* Limpeza periódica de tokens expirados da blocklist
* Rate limiting nos endpoints de login e registro
* Endpoint para promover usuário a admin sem precisar acessar o banco diretamente

---

## 📄 Licença

Este projeto é de uso livre para fins de estudo e aprendizado.