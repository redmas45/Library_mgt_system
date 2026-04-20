<div align="center">
  <h1>📚 Library AI System</h1>
  <p><strong>An Intelligent, Modern Library Management System powered by AI & RAG</strong></p>
</div>

<br />

The **Library AI System** is a next-generation library management application. It bridges the gap between traditional inventory management (borrowing, returning, tracking copies) and cutting-edge artificial intelligence. By using advanced **Retrieval-Augmented Generation (RAG)**, users can chat with their books, search by meaning instead of keywords, and generate intelligent summaries instantly.

## ✨ Key Features

### 📖 Traditional Library Management
- **PDF Uploads**: Admins can securely upload books in PDF format.
- **Auto-Metadata**: Automatically extracts book titles and authors.
- **Inventory Tracking**: Manage total copies and available copies.
- **Borrow & Return System**: Users can borrow available books, track due dates, and admins can forcefully manage returns.
- **Analytics Dashboard**: Real-time KPI tracking for total users, books, active borrows, and overdue items.

### 🤖 AI-Powered Capabilities (RAG)
- **Semantic Search**: Stop guessing keywords. Search across the entire library based on the *meaning* of your query.
- **AI Librarian Chat**: Talk to a conversational assistant that grounds its answers purely in your library's content.
- **Q&A Engine**: Have a specific question about a specific book? The AI provides precise answers with exact source citations.
- **Instant Summarization**: Generate concise, AI-driven summaries and extract key ideas from any book.

---

## 🏗️ Architecture & Tech Stack

This project is built using modern, fast, and scalable technologies:

- **Backend**: FastAPI (Python 3.10+)
- **Database**: SQLite with SQLAlchemy ORM
- **Vector Database**: FAISS (for high-speed similarity search)
- **Embeddings**: HuggingFace (`all-MiniLM-L6-v2`)
- **LLM Engine**: OpenAI GPT models (`gpt-3.5-turbo` / `gpt-4o`)
- **PDF Processing**: PyMuPDF (`fitz`)
- **Frontend**: Vanilla JS, HTML5, CSS3 (No build step required!)
- **Security**: JWT-based Authentication & Role-Based Access Control (Admin vs. User)

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** installed on your machine.
- An **OpenAI API Key**.

### 1. Clone & Setup Environment

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env
```
Open `.env` in your text editor and add your OpenAI API Key:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Initialize the Database & Seed Admin

We provide a utility script to create your first Admin user so you can start uploading books immediately.

```bash
# Go back to the root directory
cd ..

# Run the utility script
python scripts/utils.py
```
*This will create an admin user with email `admin@library.ai` and password `admin`.*

### 4. Start the Application

```bash
# Go back to the backend directory
cd backend

# Start the FastAPI server
uvicorn app.main:app --reload
```
The application is now running! 
- **Frontend UI**: Open your browser and go to `http://localhost:8000/`
- **Interactive API Docs**: `http://localhost:8000/docs`

---

## 🐳 Running with Docker

Prefer Docker? You can spin up the entire application with a single command:

```bash
docker-compose up --build
```
The app will be available at `http://localhost:8000/`.

---

## 📡 API Overview

The API is fully documented via Swagger UI at `/docs`. Here is a quick summary:

### 🔐 Authentication
- `POST /api/auth/register`: Create a new user account.
- `POST /api/auth/login`: Authenticate and receive a JWT.
- `GET /api/auth/me`: Get the current user's profile.

### 📚 Book Management
- `POST /api/books/upload`: Upload a PDF book (Admin Only).
- `GET /api/books/`: List all books (paginated).
- `GET /api/books/{id}`: Get detailed info about a specific book.

### 🔄 Borrowing System
- `POST /api/borrow/`: Borrow a book.
- `POST /api/borrow/return`: Return a borrowed book.
- `GET /api/borrow/history`: View current user's borrowing history.
- `GET /api/borrow/admin/history`: View all users' borrowing history (Admin Only).

### 🧠 AI & RAG Endpoints
- `POST /api/ai/chat/`: Converse with the AI Librarian.
- `GET /api/search/`: Perform a semantic search.
- `POST /api/ai/qa`: Ask a question about a specific book.
- `POST /api/ai/summary`: Generate a summary for a book.

---

## 📁 Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI Route handlers
│   │   ├── core/         # Core AI, Embedding, and Ingestion logic
│   │   ├── db/           # SQLAlchemy Models, Schemas, and CRUD ops
│   │   ├── services/     # Business logic (borrowing, returning)
│   │   ├── workers/      # Background tasks (async embedding)
│   │   └── main.py       # Application entry point
│   └── static/           # Vanilla JS Frontend (HTML/CSS/JS)
├── data/                 # Local database storage & uploaded PDFs
├── scripts/              # Helper scripts (Admin creation, DB seeding)
└── docker-compose.yml    # Docker orchestration
```

---

## 🤝 Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue. If you'd like to contribute code:
1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/my-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Open a Pull Request.

## 📄 License

This project is licensed under the Apache License 2.0.
