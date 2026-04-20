"""
🚀 Library AI System — Interactive Launcher

Run:  python run.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = ROOT_DIR / "data"
VENV_DIR = BACKEND_DIR / "venv"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
ENV_FILE = BACKEND_DIR / ".env"
ENV_EXAMPLE = BACKEND_DIR / ".env.example"


# ─── Helpers ─────────────────────────────────────────────

def clear_screen():
    os.system("cls" if sys.platform == "win32" else "clear")


def pause():
    input("\n  Press Enter to continue...")


def get_python():
    """Get the Python executable (prefer venv if exists)."""
    if sys.platform == "win32":
        venv_python = VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def print_banner():
    clear_screen()
    print("""
╔══════════════════════════════════════════════════════╗
║            📚 Library AI System v1.0.0               ║
║       AI-Powered Library Management System           ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║   [1]  🚀 Full Setup + Start Server                  ║
║   [2]  📦 Install Dependencies Only                  ║
║   [3]  🗄️  Initialize Database Only                   ║
║   [4]  👤 Seed Admin User                             ║
║   [5]  ▶️  Start Server Only                           ║
║   [6]  🔧 Setup .env File                             ║
║   [7]  📊 Check System Status                         ║
║   [8]  🗑️  Reset Database                              ║
║   [9]  📖 View API Endpoints                          ║
║   [0]  ❌ Exit                                        ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
    """)


def print_status(label: str, ok: bool, detail: str = ""):
    icon = "✅" if ok else "❌"
    detail_str = f" — {detail}" if detail else ""
    print(f"  {icon} {label}{detail_str}")


# ─── Actions ─────────────────────────────────────────────

def action_full_setup():
    """Full setup: dirs → deps → env → db → admin → start."""
    clear_screen()
    print("\n  🚀 Full Setup + Start Server")
    print("  " + "═" * 45)

    action_create_dirs()
    action_setup_env()
    action_install_deps()
    action_init_db()
    action_seed_admin()

    print(f"\n  {'═'*45}")
    print("  ✅ Setup complete! Starting server...\n")
    _start_server()


def action_create_dirs():
    """Create all required data directories."""
    print("\n  📁 Creating directories...")
    dirs = [
        DATA_DIR / "books",
        DATA_DIR / "processed",
        DATA_DIR / "embeddings",
        ROOT_DIR / "logs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"    ✓ {d.relative_to(ROOT_DIR)}")


def action_setup_env():
    """Copy .env.example → .env if needed."""
    print("\n  🔧 Setting up .env file...")
    if not ENV_FILE.exists() and ENV_EXAMPLE.exists():
        shutil.copy(str(ENV_EXAMPLE), str(ENV_FILE))
        print("    ✓ Created .env from .env.example")
        print("    ⚠️  Update OPENAI_API_KEY in backend/.env!")
    elif ENV_FILE.exists():
        print("    ✓ .env already exists")
    else:
        print("    ❌ .env.example not found!")


def action_install_deps():
    """Create venv and install requirements."""
    clear_screen()
    print("\n  📦 Installing Dependencies")
    print("  " + "═" * 45)

    python = sys.executable

    # Create venv
    if not VENV_DIR.exists():
        print("\n  → Creating virtual environment...")
        subprocess.run([python, "-m", "venv", str(VENV_DIR)], check=True)
        print("  ✓ Virtual environment created")
    else:
        print("\n  ✓ Virtual environment already exists")

    venv_python = get_python()

    # Upgrade pip
    print("  → Upgrading pip...")
    subprocess.run(
        [venv_python, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        check=True,
    )

    # Install requirements
    print("  → Installing packages (this may take a few minutes)...")
    print()
    result = subprocess.run(
        [venv_python, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        cwd=str(BACKEND_DIR),
    )

    if result.returncode == 0:
        print("\n  ✅ All dependencies installed successfully!")
    else:
        print("\n  ❌ Some dependencies failed to install.")
        print("    Try running: pip install -r backend/requirements.txt")

    pause()


def action_init_db():
    """Initialize the database tables."""
    clear_screen()
    print("\n  🗄️  Initializing Database")
    print("  " + "═" * 45)

    venv_python = get_python()

    script = """
import sys, os
sys.path.insert(0, r'{backend_dir}')
os.chdir(r'{backend_dir}')

from app.db.database import engine, Base
from app.db.models import *

Base.metadata.create_all(bind=engine)
print("  ✅ Database tables created successfully!")
print()
print("  Tables: users, books, book_copies, borrow_records,")
print("          interactions, reading_stats")
""".format(backend_dir=str(BACKEND_DIR))

    result = subprocess.run([venv_python, "-c", script], cwd=str(BACKEND_DIR))

    if result.returncode != 0:
        print("  ❌ Database initialization failed.")
        print("    Make sure dependencies are installed first (Option 2).")

    pause()


def action_seed_admin():
    """Create default admin user."""
    clear_screen()
    print("\n  👤 Seeding Admin User")
    print("  " + "═" * 45)

    venv_python = get_python()

    script = """
import sys, os
sys.path.insert(0, r'{backend_dir}')
os.chdir(r'{backend_dir}')

from app.db.database import SessionLocal
from app.db.crud.user_crud import get_user_by_email, create_user
from app.db.models.user import UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

try:
    existing = get_user_by_email(db, "admin@library.ai")
    if existing:
        print("  ✓ Admin user already exists!")
        print()
        print("    Email:    admin@library.ai")
    else:
        hashed = pwd_context.hash("admin123")
        user = create_user(
            db=db,
            email="admin@library.ai",
            username="admin",
            hashed_password=hashed,
            full_name="System Administrator",
            role=UserRole.ADMIN,
        )
        print("  ✅ Admin user created!")
        print()
        print("  ┌──────────────────────────────────┐")
        print("  │  📧 Email:    admin@library.ai    │")
        print("  │  🔑 Password: admin123            │")
        print("  └──────────────────────────────────┘")
        print()
        print("  ⚠️  Change the password after first login!")
finally:
    db.close()
""".format(backend_dir=str(BACKEND_DIR))

    result = subprocess.run([venv_python, "-c", script], cwd=str(BACKEND_DIR))

    if result.returncode != 0:
        print("  ❌ Failed to seed admin. Make sure DB is initialized (Option 3).")

    pause()


def action_start_server():
    """Start the FastAPI server."""
    clear_screen()
    print("\n  ▶️  Starting Server")
    print("  " + "═" * 45)
    _start_server()


def _start_server():
    """Internal: start uvicorn server."""
    venv_python = get_python()

    print(f"""
  ┌──────────────────────────────────────────┐
  │  🌐 API:     http://127.0.0.1:8000      │
  │  📖 Docs:    http://127.0.0.1:8000/docs │
  │  💚 Health:  http://127.0.0.1:8000/health│
  └──────────────────────────────────────────┘

  Press Ctrl+C to stop the server.
  {'─'*45}
    """)

    try:
        subprocess.run(
            [
                venv_python, "-m", "uvicorn",
                "app.main:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload",
            ],
            cwd=str(BACKEND_DIR),
        )
    except KeyboardInterrupt:
        print("\n\n  🛑 Server stopped.")
        pause()


def action_setup_env_interactive():
    """Setup or edit the .env file."""
    clear_screen()
    print("\n  🔧 Environment Configuration")
    print("  " + "═" * 45)

    action_setup_env()

    if ENV_FILE.exists():
        print(f"\n  📄 Current .env location: {ENV_FILE}")
        print("\n  Key settings to configure:")
        print("  ┌───────────────────────────────────────────────────┐")
        print("  │  OPENAI_API_KEY  → Your OpenAI API key           │")
        print("  │  OPENAI_MODEL    → gpt-3.5-turbo (default)       │")
        print("  │  SECRET_KEY      → Change for production!        │")
        print("  └───────────────────────────────────────────────────┘")

        edit = input("\n  Would you like to set your OpenAI API key now? (y/n): ").strip().lower()
        if edit == "y":
            api_key = input("  Enter your OpenAI API key: ").strip()
            if api_key:
                # Read, replace, write
                content = ENV_FILE.read_text()
                content = content.replace(
                    "OPENAI_API_KEY=sk-your-openai-api-key-here",
                    f"OPENAI_API_KEY={api_key}",
                )
                ENV_FILE.write_text(content)
                print("  ✅ API key saved to .env!")
            else:
                print("  ⚠️  No key entered, skipping.")

    pause()


def action_check_status():
    """Check system status — what's installed, what's ready."""
    clear_screen()
    print("\n  📊 System Status")
    print("  " + "═" * 45)
    print()

    # Check venv
    venv_exists = VENV_DIR.exists()
    print_status("Virtual environment", venv_exists,
                 str(VENV_DIR.relative_to(ROOT_DIR)) if venv_exists else "Not created")

    # Check .env
    env_exists = ENV_FILE.exists()
    api_key_set = False
    if env_exists:
        content = ENV_FILE.read_text()
        api_key_set = "OPENAI_API_KEY=" in content and "sk-your-openai-api-key-here" not in content
    print_status(".env file", env_exists)
    print_status("OpenAI API key configured", api_key_set)

    # Check database
    db_path = DATA_DIR / "library.db"
    db_exists = db_path.exists()
    print_status("Database", db_exists,
                 f"{db_path.stat().st_size // 1024}KB" if db_exists else "Not created")

    # Check data dirs
    books_dir = DATA_DIR / "books"
    pdf_count = len(list(books_dir.glob("*.pdf"))) if books_dir.exists() else 0
    print_status("Books storage", books_dir.exists(), f"{pdf_count} PDFs")

    embeddings_dir = DATA_DIR / "embeddings"
    index_exists = any(embeddings_dir.glob("*.index")) if embeddings_dir.exists() else False
    print_status("Vector store index", index_exists)

    # Check key packages
    venv_python = get_python()
    if venv_exists:
        print("\n  📦 Key packages:")
        for pkg in ["fastapi", "sqlalchemy", "openai", "sentence_transformers", "faiss"]:
            result = subprocess.run(
                [venv_python, "-c", f"import {pkg}; print({pkg}.__version__ if hasattr({pkg}, '__version__') else 'installed')"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                ver = result.stdout.strip()
                print(f"    ✅ {pkg} ({ver})")
            else:
                print(f"    ❌ {pkg} — not installed")

    pause()


def action_reset_db():
    """Reset (delete) the database."""
    clear_screen()
    print("\n  🗑️  Reset Database")
    print("  " + "═" * 45)
    print()
    print("  ⚠️  This will DELETE the database and all data!")
    print("  You will lose all users, books, borrow records, etc.")
    print()

    confirm = input("  Type 'RESET' to confirm: ").strip()
    if confirm == "RESET":
        db_path = DATA_DIR / "library.db"
        if db_path.exists():
            os.remove(db_path)
            print("  ✓ Database deleted")
        
        # Also remove vector index
        embeddings_dir = DATA_DIR / "embeddings"
        if embeddings_dir.exists():
            for f in embeddings_dir.glob("*"):
                if f.name != ".gitkeep":
                    os.remove(f)
            print("  ✓ Vector store cleared")

        print("\n  ✅ Database reset complete.")
        print("  Run Option 3 (Initialize DB) and Option 4 (Seed Admin) to start fresh.")
    else:
        print("  ❌ Reset cancelled.")

    pause()


def action_view_endpoints():
    """Display all API endpoints."""
    clear_screen()
    print("""
  📖 API Endpoints
  ════════════════════════════════════════════════════════

  🔐 AUTH
  ──────────────────────────────────────────────────────
  POST   /api/auth/register       Register new user
  POST   /api/auth/register/admin Register admin (admin only)
  POST   /api/auth/login          Login → JWT token
  GET    /api/auth/me             Get your profile

  📚 BOOKS
  ──────────────────────────────────────────────────────
  POST   /api/books/upload        Upload PDF book (admin)
  GET    /api/books/              List all books
  GET    /api/books/{id}          Get book details
  PUT    /api/books/{id}          Update book (admin)
  DELETE /api/books/{id}          Delete book (admin)

  🔄 BORROW / RETURN
  ──────────────────────────────────────────────────────
  POST   /api/borrow/             Borrow a book
  POST   /api/borrow/return       Return a book
  GET    /api/borrow/history      Your borrow history

  🤖 AI FEATURES
  ──────────────────────────────────────────────────────
  POST   /api/ai/chat/            Chat with AI Librarian
  GET    /api/search/?q=...       Semantic search
  POST   /api/ai/qa               Ask question (RAG)
  POST   /api/ai/summary          Book summary

  📊 DASHBOARD
  ──────────────────────────────────────────────────────
  GET    /api/dashboard/           Analytics (admin)

  💚 SYSTEM
  ──────────────────────────────────────────────────────
  GET    /health                   Health check
  GET    /docs                     Swagger UI
  GET    /redoc                    ReDoc
    """)
    pause()


# ─── Main Loop ───────────────────────────────────────────

def main():
    while True:
        print_banner()
        choice = input("  Enter your choice [0-9]: ").strip()

        if choice == "1":
            action_full_setup()
        elif choice == "2":
            action_install_deps()
        elif choice == "3":
            action_init_db()
        elif choice == "4":
            action_seed_admin()
        elif choice == "5":
            action_start_server()
        elif choice == "6":
            action_setup_env_interactive()
        elif choice == "7":
            action_check_status()
        elif choice == "8":
            action_reset_db()
        elif choice == "9":
            action_view_endpoints()
        elif choice == "0":
            clear_screen()
            print("\n  👋 Goodbye!\n")
            sys.exit(0)
        else:
            print("\n  ⚠️  Invalid choice. Please enter 0-9.")
            pause()


if __name__ == "__main__":
    main()
