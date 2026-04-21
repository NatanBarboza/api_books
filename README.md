# 📚 Books API

API REST desenvolvida com foco em demonstrar conceitos de **CRUD (Create, Read, Update, Delete)** utilizando Python e o framework FastAPI.

O principal objetivo deste projeto é servir como base para evolução futura, especialmente na implementação de **autenticação e autorização de APIs**.

---

## 🚀 Tecnologias utilizadas

O projeto foi construído com as seguintes tecnologias:

* **Python** – linguagem principal
* **FastAPI** – framework web moderno e performático
* **SQLAlchemy** – ORM para manipulação do banco de dados
* **Pydantic** – validação de dados e definição de schemas
* **Uvicorn** – servidor ASGI para execução da aplicação

---

## 📦 Dependências

As dependências do projeto estão definidas no arquivo `requirements.txt`:

```
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.13.0
click==8.3.2
dotenv==0.9.9
fastapi==0.136.0
greenlet==3.4.0
h11==0.16.0
idna==3.11
pydantic==2.13.3
pydantic_core==2.46.3
python-dotenv==1.2.2
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

---

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

---

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

---

### 4. Executar a aplicação

```bash
python run.py
```

---

### 5. Acessar a API

Após subir a aplicação, acesse:

* Swagger UI:
  http://localhost:8000/docs

* ReDoc:
  http://localhost:8000/redoc

---

## 📌 Funcionalidades

A API atualmente disponibiliza operações básicas de gerenciamento de livros:

* 📖 Listar livros
* 🔍 Buscar livro por ID
* ➕ Criar livro
* ✏️ Atualizar livro
* ❌ Deletar livro

---

## 🗄️ Banco de dados

O projeto utiliza **SQLite** como banco de dados padrão para facilitar a execução local.

As tabelas são criadas automaticamente na inicialização da aplicação.

---

## 🔐 Próximos passos

Este projeto foi estruturado para evoluir com foco em:

* Autenticação com JWT
* Controle de acesso por usuário
* Proteção de rotas
* Boas práticas de segurança em APIs

---

## 📄 Licença

Este projeto é de uso livre para fins de estudo e aprendizado.
