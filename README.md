# 📚 Library AI System

An AI-powered Library Management System that combines traditional library operations (inventory, borrowing) with modern AI features (RAG-based chat, semantic search, Q&A, and book summarization).

## ✨ Features

- **📖 Book Management** — Upload PDFs, auto-extract metadata, manage inventory
- **🔄 Borrow/Return System** — Track borrows, due dates, overdue detection
- **🤖 AI Librarian Chat** — Conversational assistant grounded in library content
- **🔍 Semantic Search** — Meaning-based search across all book content
- **❓ Q&A Engine (RAG)** — Ask questions per book with source citations
- **📋 Book Summarization** — AI-generated summaries with key ideas
- **📊 Dashboard & Analytics** — Admin analytics and activity tracking
- **🔐 JWT Authentication** — Role-based access (Admin / User)

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python) |
| Database | SQLite + SQLAlchemy |
| Vector Store | FAISS |
| Embeddings | HuggingFace (all-MiniLM-L6-v2) |
| LLM | OpenAI GPT |
| PDF Parsing | PyMuPDF |
| Auth | JWT (python-jose) |

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Seed Admin User

```bash
cd ..
python scripts/utils.py
```

### 4. Run the Server

```bash
cd backend
uvicorn app.main:app --reload
```

### 5. Access the API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login → JWT token |
| GET | `/api/auth/me` | Get profile |

### Books
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/books/upload` | Upload PDF (Admin) |
| GET | `/api/books/` | List books (paginated) |
| GET | `/api/books/{id}` | Book details |
| PUT | `/api/books/{id}` | Update book (Admin) |
| DELETE | `/api/books/{id}` | Delete book (Admin) |

### Borrow / Return
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/borrow/` | Borrow a book |
| POST | `/api/borrow/return` | Return a book |
| GET | `/api/borrow/history` | Borrow history |

### AI Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/chat/` | Chat with AI Librarian |
| GET | `/api/search/` | Semantic search |
| POST | `/api/ai/qa` | Ask question (RAG) |
| POST | `/api/ai/summary` | Book summary |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/` | Analytics (Admin) |

## 🐳 Docker

```bash
docker-compose up --build
```

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── api/routes/          # API endpoints
│   │   ├── core/ai/             # LLM, prompts, librarian
│   │   ├── core/embeddings/     # FAISS, embedder
│   │   ├── core/ingestion/      # PDF → chunks → vectors
│   │   ├── db/                  # Models, schemas, CRUD
│   │   ├── services/            # Business logic
│   │   ├── workers/             # Background tasks
│   │   └── middleware/          # Auth, rate limit, logging
│   ├── alembic/                 # DB migrations
│   └── requirements.txt
├── data/                        # PDFs, embeddings, DB
├── scripts/                     # CLI tools
└── docker-compose.yml
```

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Model name | gpt-3.5-turbo |
| `SECRET_KEY` | JWT signing key | Change in prod |
| `DATABASE_URL` | SQLite path | sqlite:///./data/library.db |
| `EMBEDDING_MODEL` | HuggingFace model | all-MiniLM-L6-v2 |

## 📄 License

Apache License 2.0
