# Project Overview

This document provides a comprehensive explanation of the **FastWeb** FastAPI blog application. It covers the entry point, core libraries, project structure, key commands, and a brief description of major components. The folder is kept inside the repository but is **not served publicly** by the web server.

---

## 📂 Repository Structure (relevant parts)
```
FastWeb/
├─ .env                 # Environment variables (DB URL, secret keys, etc.)
├─ main.py               # **Entry point** – creates the FastAPI app and includes routers
├─ populate_db.py        # Script to seed or refresh the SQLite database
├─ credentials/          # JSON file with user credentials used by `populate_db.py`
├─ templates/            # Jinja2 HTML templates (home, login, account, etc.)
│   ├─ account.html
│   ├─ login.html
│   ├─ forgot_password.html
│   └─ reset_password.html
├─ static/               # Static assets (CSS, JS, images)
├─ routers/              # FastAPI router modules (posts, users, etc.)
├─ models.py             # SQLAlchemy models (User, Post, PasswordResetToken)
├─ schemas.py            # Pydantic schemas for request/response validation
├─ email_utils.py        # Helper for sending password‑reset e‑mails
└─ docs/                 # **Non‑public documentation folder** (this file lives here)
```

---

## 🚀 Entry Point – `main.py`
```python
# main.py (excerpt)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import posts, users

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(posts.router)
app.include_router(users.router)
```
*Creates the FastAPI `app` instance, mounts static assets, registers Jinja2 templates, and includes the router modules that contain the actual endpoint logic.*

---

## 📦 Core Libraries Used
| Library | Purpose |
|--------|---------|
| **fastapi** | Web framework – routing, dependency injection, automatic docs. |
| **uvicorn** | ASGI server used to run the app (`uvicorn main:app --reload`). |
| **jinja2** | Templating engine for HTML pages. |
| **sqlalchemy** | ORM for interacting with the SQLite database (`blog.db`). |
| **pydantic** | Data validation & serialization (schemas). |
| **python‑dotenv** | Loads environment variables from `.env`. |
| **passlib** (bcrypt) | Password hashing for user authentication. |
| **email‑utils** (custom) | Helper functions to send password‑reset e‑mails. |
| **python‑jwt** | (if used) to create JWT tokens for auth (depends on your auth implementation). |

---

## 🛠️ Common Commands
| Command | Description |
|---------|-------------|
| `python -m venv .venv` | Create a virtual environment (if not already present). |
| `source .venv/bin/activate` (Linux/macOS) or `.venv\\Scripts\\activate` (Windows) | Activate the virtual environment. |
| `pip install -r requirements.txt` | Install all project dependencies. |
| `uvicorn main:app --reload` | Run the development server (auto‑reload on code changes). |
| `python populate_db.py` | Populate or refresh the SQLite `blog.db` with seed data and user credentials. |
| `git add .`<br>`git commit -m "<msg>"`<br>`git push` | Standard Git workflow to stage, commit, and push changes. |
| `pytest` or `python -m unittest` | Run the test suite (if tests are present). |

---

## 📚 Component Summaries
### 1. **Authentication & Password Reset**
- **`models.py`** defines `User` and `PasswordResetToken` tables.
- **`email_utils.py`** contains `send_password_reset_email()` which builds a reset link and sends it via SMTP (configured in `.env`).
- **`routers/users.py`** implements:
  - `POST /forgot-password` – generates a token and emails the user.
  - `POST /reset-password` – validates the token and updates the password.
  - `PUT /me/password` – authenticated users can change their password.
- **Templates**: `forgot_password.html` and `reset_password.html` provide the UI.

### 2. **Database Seeding (`populate_db.py`)**
- Reads `credentials/users.json` for a list of user email/password pairs.
- Clears existing posts and creates a fresh set of 44 technical posts.
- Updates `blog.db` accordingly.

### 3. **Posts & Pagination**
- **`routers/posts.py`** contains CRUD routes for blog posts and pagination logic.
- Front‑end pagination is driven by `static/js/utils.js` and the Jinja2 loops in `templates/home.html`.

### 4. **Static & Template Assets**
- CSS lives in `static/css/`, JavaScript in `static/js/`.
- Templates are pure Jinja2; they pull data from the FastAPI responses.

---

## 📖 How to Extend the Documentation
- Add new markdown files under `docs/` for additional modules (e.g., `docs/EMAIL.md`, `docs/DB_SCHEMA.md`).
- Keep the folder out of the public static path – it is **not** referenced by `app.mount('/static', ...)`, so it never gets served.
- Commit documentation changes alongside code updates.

---

*This documentation is meant to be a quick reference for developers onboarding the FastWeb project. Feel free to modify or expand it as the codebase evolves.*
