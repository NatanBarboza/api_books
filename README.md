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
idna==3.11
pydantic==2.13.3
pydantic_core==2.46.3
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
SECRET_KEY=seu-valor-gerado-com-openssl-rand-hex-32
DATABASE_URL=sqlite:///./books.db
DEBUG=false
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Para gerar uma `SECRET_KEY` segura:

```bash
openssl rand -hex 32
```

### 5. Executar a aplicação

```bash
python run.py
```

### 6. Acessar a API

Após subir a aplicação, acesse:

* Swagger UI: http://localhost:8000/docs
* ReDoc: http://localhost:8000/redoc

---

## 📌 Funcionalidades

### Livros

* 📖 Listar livros
* 🔍 Buscar livro por ID
* ➕ Criar livro
* ✏️ Atualizar livro
* ❌ Deletar livro

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

* `user` — acesso a rotas de leitura e operações básicas
* `admin` — acesso total, incluindo operações destrutivas

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
├── .env.example                      # modelo de variáveis de ambiente
├── .gitignore
├── main.py
├── run.py
├── requirements.txt
└── app/
    ├── core/
    │   ├── config.py                 # configurações centralizadas
    │   └── security.py              # hashing e JWT
    ├── models/
    │   ├── user_model.py
    │   └── revoked_token.py         # model da blocklist
    ├── schema/
    │   └── auth_schema.py
    ├── repository/
    │   ├── user_repository.py
    │   └── revoked_token_repository.py
    ├── services/
    │   └── auth_service.py
    ├── routes/
    │   ├── auth_routes.py
    │   └── book_routes.py
    └── dependencies/
        └── auth.py
```

---

## 🗺️ Próximos passos

* Proteção das rotas de livros por escopo
* Limpeza periódica de tokens expirados da blocklist
* Testes automatizados de autenticação
* Rate limiting nos endpoints de login e registro

---

## 📄 Licença

Este projeto é de uso livre para fins de estudo e aprendizado.