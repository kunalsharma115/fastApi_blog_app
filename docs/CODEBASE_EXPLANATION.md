# FastWeb — Complete Codebase Explanation

> This document explains every important part of the FastWeb project.
> It is based on the **actual code** in the repository, not generic theory.
> The `docs/` folder is **not served** to users — it only exists for developer reference.

---

## Table of Contents

1. [What This Project Is](#1-what-this-project-is)
2. [Architecture — The Big Picture](#2-architecture--the-big-picture)
3. [Folder & File Structure](#3-folder--file-structure)
4. [Prerequisites — Concepts You Need](#4-prerequisites--concepts-you-need)
5. [The `.env` File and `config.py` — Configuration Layer](#5-the-env-file-and-configpy--configuration-layer)
6. [The Database Layer — `database.py`](#6-the-database-layer--databasepy)
7. [The ORM Models — `model.py`](#7-the-orm-models--modelpy)
8. [Data Validation — `schemas.py`](#8-data-validation--schemaspy)
9. [Authentication — `auth.py`](#9-authentication--authpy)
10. [The Entry Point — `main.py`](#10-the-entry-point--mainpy)
11. [Post Endpoints — `routers/posts.py`](#11-post-endpoints--routerspostspy)
12. [User Endpoints — `routers/users.py`](#12-user-endpoints--routersuserspy)
13. [Image Processing — `image_utils.py`](#13-image-processing--image_utilspy)
14. [Email Sending — `email_utils.py`](#14-email-sending--email_utilspy)
15. [The Frontend — Templates & JavaScript](#15-the-frontend--templates--javascript)
16. [Complete Execution Flows (Dry Runs)](#16-complete-execution-flows-dry-runs)
17. [Commands](#17-commands)
18. [Common Mistakes](#18-common-mistakes)
19. [Industry Perspective](#19-industry-perspective)

---

## 1. What This Project Is

### What does it do?
FastWeb is a **full-stack blog application**. Users can register, log in, create/edit/delete blog posts, upload profile pictures, reset forgotten passwords via email, and browse all posts with "Load More" pagination.

### What problem does it solve?
It provides a complete blogging platform with user authentication, CRUD operations on posts, and profile management — all built as a single deployable application.

### Main features
- User registration and login (JWT-based)
- Create, read, update, delete blog posts
- Profile management (username, email, profile picture)
- Password reset via email link
- Change password while logged in
- Infinite-scroll pagination (Load More)
- Dark mode / light mode toggle
- Server-side rendered HTML pages (Jinja2)
- JSON REST API for all data operations

### Technologies used
| Layer | Technology |
|-------|-----------|
| **Backend framework** | FastAPI (Python) |
| **Server** | Uvicorn (ASGI) |
| **Database** | SQLite (via `aiosqlite` for async) |
| **ORM** | SQLAlchemy 2.0 (async mode) |
| **Data validation** | Pydantic v2 |
| **Templating** | Jinja2 |
| **Frontend CSS** | Bootstrap 5.3 + custom CSS |
| **Frontend JS** | Vanilla JavaScript (ES Modules) |
| **Auth** | JWT (PyJWT) + password hashing (pwdlib) |
| **Email** | aiosmtplib (via Mailtrap sandbox) |
| **Image processing** | Pillow (PIL) |

---

## 2. Architecture — The Big Picture

```
┌──────────────────────────────────────────────────────┐
│                    BROWSER                           │
│  (HTML pages + JavaScript)                           │
└──────────┬──────────────────────┬────────────────────┘
           │ Page request         │ API request
           │ GET /                │ GET /api/posts?skip=10
           ▼                      ▼
┌──────────────────────────────────────────────────────┐
│                   main.py                            │
│  FastAPI app instance                                │
│  ┌─────────────────┐  ┌────────────────────────────┐ │
│  │ Template Routes  │  │ API Routers                │ │
│  │ GET /            │  │ routers/posts.py           │ │
│  │ GET /login       │  │ routers/users.py           │ │
│  │ GET /account     │  │ (mounted at /api/...)      │ │
│  └────────┬────────┘  └──────────┬─────────────────┘ │
│           │                      │                    │
│           │   ┌──────────────────┘                    │
│           ▼   ▼                                       │
│  ┌─────────────────────────────────────────────┐      │
│  │     Dependencies (Dependency Injection)     │      │
│  │  get_db()  →  database session              │      │
│  │  get_current_user()  →  authenticated user  │      │
│  └──────────────────────┬──────────────────────┘      │
│                         │                             │
│                         ▼                             │
│  ┌──────────────────────────────┐                     │
│  │  model.py (SQLAlchemy ORM)  │                      │
│  │  User, Post, ResetToken     │                      │
│  └────────────┬─────────────────┘                     │
│               ▼                                       │
│  ┌──────────────────────┐                             │
│  │  database.py         │                             │
│  │  AsyncEngine → SQLite│                             │
│  │  blog.db             │                             │
│  └──────────────────────┘                             │
└──────────────────────────────────────────────────────┘
```

**Mental model**: The browser talks to `main.py`. Template routes return HTML. API routes (under `/api/`) return JSON. Both types of routes share the same database layer and authentication system.

---

## 3. Folder & File Structure

```
FastWeb/
├── .env                    # Secret config (NOT committed to git)
├── .gitignore              # Files git should ignore
├── main.py                 # THE ENTRY POINT — app creation + template routes
├── config.py               # Loads .env into a typed Settings object
├── database.py             # DB engine, session factory, get_db() dependency
├── model.py                # SQLAlchemy table definitions (User, Post, PasswordResetToken)
├── schemas.py              # Pydantic models for request/response validation
├── auth.py                 # Password hashing, JWT creation/verification, auth dependency
├── email_utils.py          # Sends password-reset emails via SMTP
├── image_utils.py          # Resizes/saves profile picture uploads
├── populate_db.py          # Script to seed the database with test data
├── test_app.py             # Automated test suite
│
├── routers/                # FastAPI router modules
│   ├── __init__.py         # Makes routers/ a Python package (empty file)
│   ├── posts.py            # CRUD endpoints for posts (/api/posts)
│   └── users.py            # User endpoints: register, login, profile, password (/api/users)
│
├── templates/              # Jinja2 HTML templates (server-rendered)
│   ├── layout.html         # Base template — navbar, footer, modals, shared scripts
│   ├── home.html           # Homepage — post list + Load More
│   ├── post.html           # Single post view + edit/delete
│   ├── user_post.html      # Posts by a specific user + Load More
│   ├── login.html          # Login form
│   ├── register.html       # Registration form
│   ├── account.html        # Account settings — profile, picture, password, delete
│   ├── forgot_password.html# Forgot password form
│   ├── reset_password.html # Reset password form (reached via email link)
│   ├── error.html          # Generic error page
│   └── email/
│       └── password_reset.html  # HTML email template for reset link
│
├── static/                 # Publicly served static files
│   ├── css/main.css        # All custom styles (variables, dark mode, components)
│   ├── js/
│   │   ├── auth.js         # Token storage, getCurrentUser(), logout()
│   │   └── utils.js        # Shared helpers: modals, error messages, XSS escape, date format
│   ├── icons/              # Favicon files
│   └── profile_pics/       # Default profile picture
│
├── media/                  # User-uploaded files (not in static/)
│   └── profile_pics/       # Uploaded profile pictures (generated filenames)
│
├── credentials/            # Reference file for seed user credentials
│   ├── users.json
│   └── README.md
│
├── populate_images/        # Source images for populate_db.py
├── blog.db                 # SQLite database file (not committed)
└── docs/                   # THIS FOLDER — developer documentation (not public)
```

### Why each important file exists

| File | Exists because | Depends on | Depended on by |
|------|---------------|------------|----------------|
| `main.py` | Creates the app, defines template routes, includes routers | `database.py`, `model.py`, `routers/*`, `config.py`, `schemas.py` | Uvicorn runs it |
| `config.py` | Centralizes all config — avoids hardcoded secrets | `.env`, `pydantic-settings` | Every module that needs settings |
| `database.py` | Isolates DB connection logic — single place to change DB | SQLAlchemy, `aiosqlite` | `model.py`, `auth.py`, both routers, `main.py` |
| `model.py` | Defines database schema as Python classes | `database.py` | Both routers, `auth.py`, `main.py` |
| `schemas.py` | Separates "what data looks like to the outside world" from "what's in the DB" | Pydantic | Both routers |
| `auth.py` | Centralizes all auth logic — hashing, JWT, user extraction | `config.py`, `model.py`, `database.py` | Both routers |
| `routers/posts.py` | Keeps post API logic separate from `main.py` | `model.py`, `schemas.py`, `auth.py`, `database.py` | `main.py` includes it |
| `routers/users.py` | Keeps user API logic separate from `main.py` | Everything | `main.py` includes it |

---

## 4. Prerequisites — Concepts You Need

### PREREQUISITE: Async/Await
Python's `async def` creates a coroutine — a function that can pause (at `await`) to let other tasks run. This matters because your server can handle multiple requests simultaneously without threads. When you see `await db.execute(...)`, the function pauses while the database works, and the server handles other requests in the meantime.

### PREREQUISITE: Dependency Injection
FastAPI's `Depends()` is a way to say "before running this endpoint, run *this other function* first, and give me its result." For example, `db: Annotated[AsyncSession, Depends(get_db)]` means "call `get_db()`, get a database session, and pass it to me as `db`." The framework handles creating and closing the session automatically.

### PREREQUISITE: ORM (Object-Relational Mapping)
Instead of writing raw SQL (`SELECT * FROM users WHERE id=5`), you write Python: `select(model.User).where(model.User.id == 5)`. SQLAlchemy translates this to SQL for you. Each Python class = one database table. Each class attribute = one column.

### PREREQUISITE: JWT (JSON Web Token)
A JWT is a signed string that contains data (like `{"sub": "5", "exp": 1699999999}`). The server creates it at login, the client stores it in `localStorage`, and sends it with every request. The server can verify the signature without a database lookup. If someone tampers with the token, the signature check fails.

---

## 5. The `.env` File and `config.py` — Configuration Layer

### What are we solving?
Secrets (like database passwords, JWT keys, email credentials) should never be hardcoded in source code. They change between development and production, and they must not be committed to git.

### Where is it in the project?
- [`.env`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/.env) — the raw key-value file
- [`config.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/config.py) — loads `.env` into a typed Python object

### How `.env` works
```
SECRET_KEY="fastweb-super-secret-development-key-1234567890"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
...
```
This is a plain text file. Each line is `KEY=VALUE`. `.gitignore` includes `.env`, so it is **never committed** to git.

### How `config.py` works — line by line

```python
from pydantic import SecretStr                           # (1)
from pydantic_settings import SettingsConfigDict, BaseSettings  # (2)

class Settings(BaseSettings):                            # (3)
    model_config = SettingsConfigDict(                    # (4)
        env_file=".env",
        env_file_encoding="utf-8"
    )

    secret_key: SecretStr = SecretStr("fastweb-super-secret...") # (5)
    algorithm: str = "HS256"                              # (6)
    access_token_expire_minutes: int = 30
    max_upload_size_bytes: int = 5 * 1024 * 1024          # (7)
    post_per_page: int = 10
    posts_per_page: int = 10
    reset_token_expire_minutes: int = 60
    mail_server: str = "localhost"
    mail_port: int = 587
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@example.com"
    mail_use_tls: bool = True
    frontend_url: str = "http://localhost:8000"

settings = Settings()                                     # (8)
```

1. **`SecretStr`** — a Pydantic type that masks the value in logs/repr. You must call `.get_secret_value()` to read it. This prevents accidentally logging your secret key.
2. **`pydantic-settings`** — a separate package (not built into Pydantic) that adds environment variable loading. *Third-party library. Install: `pip install pydantic-settings`.*
3. **`BaseSettings`** — when you create a `Settings()` instance, it automatically reads environment variables that match the field names (case-insensitive). So the field `secret_key` reads the env var `SECRET_KEY`.
4. **`model_config`** — tells pydantic-settings to also look in the `.env` file. Env vars take priority over `.env` file values, which take priority over defaults.
5. Each field has a **type annotation** (`str`, `int`, `bool`) and a **default value**. If `SECRET_KEY` is set in `.env`, it overrides the default. If not, the default is used.
6. **`"HS256"`** = HMAC-SHA256, the algorithm for signing JWTs.
7. **`5 * 1024 * 1024`** = 5 MB in bytes. This is the max profile picture upload size.
8. **`settings = Settings()`** — this singleton is imported everywhere. Creating the instance triggers `.env` loading.

### Why this approach?
- **Type safety**: If someone sets `ACCESS_TOKEN_EXPIRE_MINUTES=not_a_number` in `.env`, Pydantic raises an error at startup, not at runtime during a request.
- **Single source of truth**: Every module imports `from config import settings` instead of calling `os.environ.get()` scattered everywhere.
- **Alternative**: Using `python-dotenv` directly with `os.environ.get()` — works but no type checking, no defaults validation, easy to misspell env var names.

### What if we remove it?
Every file that imports `settings` would break. You'd need to hardcode values or use `os.environ.get()` everywhere.

---

## 6. The Database Layer — `database.py`

### What are we solving?
We need a way to connect to the SQLite database, create sessions for each request, and ensure sessions are properly closed.

### Where is it?
[`database.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/database.py) — 23 lines, one of the smallest but most critical files.

### Code explanation — line by line

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./blog.db"   # (1)

engine = create_async_engine(                                # (2)
   SQLALCHEMY_DATABASE_URL,
   connect_args={"check_same_thread": False}                 # (3)
)

AsyncSessionLocal = async_sessionmaker(                      # (4)
    autocommit=False,                                        # (5)
    autoflush=False,                                         # (6)
    bind=engine,                                             # (7)
    expire_on_commit=False,                                  # (8)
    class_=AsyncSession                                      # (9)
)

Base = declarative_base()                                    # (10)

async def get_db():                                          # (11)
    async with AsyncSessionLocal() as session:               # (12)
        yield session                                        # (13)
```

1. **`sqlite+aiosqlite:///./blog.db`** — The connection URL. `sqlite` = database type. `aiosqlite` = the async driver (regular `sqlite3` is synchronous and would block the event loop). `///./blog.db` = file path relative to where you run the server.
2. **`create_async_engine`** — creates the connection pool. The engine manages actual connections to the database. It's created **once** at import time, not per request.
3. **`check_same_thread: False`** — SQLite by default refuses connections from a different thread than the one that created them. Since FastAPI uses async (which may switch threads), this flag disables that check. **Only needed for SQLite**, not for PostgreSQL/MySQL.
4. **`async_sessionmaker`** — a factory. Calling `AsyncSessionLocal()` creates a new session. A session is like a "workspace" — you query through it, make changes, and then commit or rollback.
5. **`autocommit=False`** — you must explicitly call `await db.commit()`. This gives you control over transactions.
6. **`autoflush=False`** — SQLAlchemy won't automatically send pending changes to the DB before every query. You control when changes are flushed.
7. **`bind=engine`** — connects sessions to the engine (and thus to `blog.db`).
8. **`expire_on_commit=False`** — after `commit()`, objects stay usable. Without this, accessing `user.username` after commit would trigger a new DB query (which fails in async context).
9. **`class_=AsyncSession`** — sessions should be the async type.
10. **`Base = declarative_base()`** — the parent class for all ORM models. Every model (User, Post, etc.) inherits from `Base`. This is how SQLAlchemy knows which classes represent tables.
11. **`get_db()`** — an async generator function used as a **FastAPI dependency**.
12. **`async with`** — creates a session and guarantees it's closed when the request finishes (even if an exception occurs).
13. **`yield session`** — gives the session to the endpoint function. After the endpoint returns, execution resumes after `yield`, and the `async with` block closes the session.

### Internal working: What `yield` does here
This is a **dependency with cleanup**. FastAPI calls `get_db()`, gets the session from `yield`, passes it to your endpoint. After the endpoint returns its response, FastAPI resumes `get_db()` after the `yield` line. Since there's nothing after `yield`, the `async with` block exits and closes the session.

### What if you removed `expire_on_commit=False`?
After calling `await db.commit()`, any access to model attributes (like `user.username`) would try to lazily load from the database. In async SQLAlchemy, lazy loading raises an error because it requires a synchronous database call. You'd get `MissingGreenlet` errors.

---

## 7. The ORM Models — `model.py`

### What are we solving?
Defining the database schema (tables, columns, relationships) as Python classes so we never write raw SQL.

### Where is it?
[`model.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/model.py) — defines 3 tables: `users`, `posts`, `password_reset_tokens`.

### The `User` model

```python
from __future__ import annotations                          # (1)

class User(Base):
    __tablename__ = "users"                                 # (2)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)     # (3)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # (4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)    # (5)
    image_file: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)  # (6)

    posts: Mapped[list[Post]] = relationship(               # (7)
        back_populates="author",                            # (8)
        cascade="all, delete-orphan"                        # (9)
    )

    reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property                                               # (10)
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"
```

1. **`from __future__ import annotations`** — makes all type annotations strings by default. This solves a circular reference problem: `User` references `Post` in its `posts` relationship, but `Post` is defined below `User`. Without this import, Python would raise `NameError: name 'Post' is not defined`.
2. **`__tablename__`** — the actual SQL table name. SQLAlchemy uses this when generating SQL.
3. **`Mapped[int]`** — SQLAlchemy 2.0 style type annotation. `primary_key=True` makes it auto-increment. `index=True` creates a database index for faster lookups.
4. **`unique=True`** — no two users can have the same username. The database enforces this.
5. **`password_hash`** — stores the **hashed** password, never the plain text. This is critical for security.
6. **`str | None`** — this column is optional. New users start with `None` (no profile picture).
7. **`relationship`** — NOT a database column. This tells SQLAlchemy: "A User has many Posts. When I access `user.posts`, load them from the `posts` table." This is an **ORM-level convenience** — the actual link is the `user_id` foreign key in the `Post` table.
8. **`back_populates="author"`** — bidirectional link. `user.posts` gives you the user's posts. `post.author` gives you the post's user. Both sides need to reference each other.
9. **`cascade="all, delete-orphan"`** — when a User is deleted, all their Posts are automatically deleted too. "delete-orphan" means if a Post's `user_id` is set to `None`, the Post is also deleted.
10. **`@property`** — a computed attribute (not in the database). When templates or schemas access `user.image_path`, this method runs and returns the correct URL. If the user uploaded a picture, it points to `/media/...`. Otherwise, the default.

### The `Post` model

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(TEXT, nullable=False)            # (1)
    user_id: Mapped[int] = mapped_column(                                 # (2)
        ForeignKey("users.id"), index=True, nullable=False
    )
    date_posted: Mapped[datetime] = mapped_column(
        DATETIME(timezone=True),
        default=lambda: datetime.now(UTC),                                # (3)
    )

    author: Mapped[User] = relationship(back_populates="posts")           # (4)
```

1. **`TEXT`** — the SQL TEXT type. `String` has a length limit in some databases; `TEXT` is unlimited. Blog content can be long.
2. **`ForeignKey("users.id")`** — this is the actual database-level link. It says "the `user_id` column must contain a value that exists in `users.id`." This is what makes the User-Post relationship work at the SQL level. `index=True` makes queries like "get all posts by user 5" fast.
3. **`default=lambda: datetime.now(UTC)`** — a callable default. The `lambda` is important: without it, `datetime.now(UTC)` would be called **once** at import time, and every post would have the same timestamp. The lambda makes it call `datetime.now(UTC)` fresh each time a new Post is created.
4. **`author`** — the reverse side of `User.posts`. Given a post, `post.author` loads the User who wrote it.

### The `PasswordResetToken` model

```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # (1)
    expires_at: Mapped[datetime] = mapped_column(DATETIME(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(timezone=True), default=lambda: datetime.now(UTC),
    )

    user: Mapped[User] = relationship(back_populates="reset_tokens")
```

1. **`token_hash`** — stores a **SHA-256 hash** of the reset token, not the token itself. The plain token is sent in the email URL. If someone gets access to the database, they can't use the hashed tokens. The user submits the plain token, the server hashes it, and compares with the stored hash. This is the same principle as password hashing.

### Database diagram

```
┌──────────────────────┐       ┌──────────────────────────┐
│       users          │       │         posts            │
├──────────────────────┤       ├──────────────────────────┤
│ id (PK, auto)        │◄──┐   │ id (PK, auto)            │
│ username (unique)    │   │   │ title                    │
│ email (unique)       │   │   │ content (TEXT)            │
│ password_hash        │   └───│ user_id (FK → users.id)  │
│ image_file (nullable)│       │ date_posted              │
└──────────┬───────────┘       └──────────────────────────┘
           │
           │ 1:N
           ▼
┌──────────────────────────┐
│  password_reset_tokens   │
├──────────────────────────┤
│ id (PK, auto)            │
│ user_id (FK → users.id)  │
│ token_hash (unique)      │
│ expires_at               │
│ created_at               │
└──────────────────────────┘
```

---

## 8. Data Validation — `schemas.py`

### What are we solving?
The ORM models define what's in the **database**. Schemas define what data looks like in **HTTP requests and responses**. You never want to expose `password_hash` to the client, and you want to validate that a username is 1-20 characters before it hits the database.

### Where is it?
[`schemas.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/schemas.py)

### Key schemas explained

```python
class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=20)       # (1)
    email: EmailStr = Field(max_length=100)                  # (2)

class UserCreate(UserBase):                                  # (3)
    password: str = Field(min_length=8)

class UserPublic(BaseModel):                                 # (4)
    model_config = ConfigDict(from_attributes=True)          # (5)
    id: int
    username: str
    image_file: str | None
    image_path: str                                          # (6)

class UserPrivate(UserBase):                                 # (7)
    model_config = ConfigDict(from_attributes=True)
    id: int
    image_file: str | None = None
    image_path: str
```

1. **`Field(min_length=1, max_length=20)`** — Pydantic validates this automatically. If a client sends `{"username": ""}`, FastAPI returns a 422 error before your endpoint code even runs.
2. **`EmailStr`** — from `pydantic[email]`. Validates the string is a proper email format. *Requires: `pip install pydantic[email]` or `pip install email-validator`.*
3. **`UserCreate(UserBase)`** — inherits `username` and `email` from `UserBase`, adds `password`. This is what the registration endpoint expects.
4. **`UserPublic`** — what any user can see about another user. Notice: NO email, NO password_hash. Only safe fields.
5. **`ConfigDict(from_attributes=True)`** — tells Pydantic "you can create this schema from an ORM object." Without this, `PostResponse.model_validate(post)` would fail because `post` is a SQLAlchemy object, not a dictionary.
6. **`image_path: str`** — this maps to the `@property` in `model.py`. Pydantic reads it like any other attribute.
7. **`UserPrivate`** — what the logged-in user sees about themselves. Includes email (not in `UserPublic`).

### Schema hierarchy

```
UserBase (username, email)
├── UserCreate (+ password)         — for registration POST body
├── UserPrivate (+ id, image_path)  — for /api/users/me response
│
UserPublic (id, username, image)    — for public profile, embedded in PostResponse
│
PostBase (title, content)
├── PostCreate                      — for creating a post (no extra fields)
├── PostResponse (+ id, date, author: UserPublic)  — for API responses
│
PaginatedPostResponse (posts[], total, skip, limit, has_more)  — for paginated lists
│
Token (access_token, token_type)    — for login response
│
ForgotPasswordRequest (email)
ResetPasswordRequest (token, new_password)
ChangePasswordRequest (current_password, new_password)
```

### Why separate schemas from models?

| Concern | Model (model.py) | Schema (schemas.py) |
|---------|-----------------|---------------------|
| Purpose | Database structure | API data shape |
| Contains `password_hash`? | Yes | No (never exposed) |
| Contains `image_path` property? | Yes (computed) | Yes (serialized) |
| Validates input length? | No (just DB constraints) | Yes (before DB) |
| Used by | SQLAlchemy queries | FastAPI endpoints |

---

## 9. Authentication — `auth.py`

### What are we solving?
Users need to prove who they are. We need to:
1. Hash passwords so they're safe in the database
2. Create tokens at login so users don't send passwords with every request
3. Verify tokens on protected endpoints
4. Generate secure reset tokens for password recovery

### Where is it?
[`auth.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/auth.py)

### Password hashing

```python
from pwdlib import PasswordHash                              # (1)

password_hash = PasswordHash.recommended()                   # (2)

def hash_password(password: str) -> str:
    return password_hash.hash(password)                      # (3)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)  # (4)
```

1. **`pwdlib`** — third-party password hashing library. *Install: `pip install pwdlib[bcrypt]`.* An alternative to `passlib` which is no longer actively maintained.
2. **`.recommended()`** — uses the currently recommended algorithm (bcrypt). The hash includes the salt and algorithm info, so you don't need to store them separately.
3. A hash of `"mypassword123"` looks like `$2b$12$LJ3E...`. Even if two users have the same password, their hashes will be different (because of random salts).
4. `verify` re-hashes the plain password with the same salt and compares. It returns `True` or `False`. You **never** decrypt a hash — hashing is one-way.

### Why not store plain passwords?
If the database is stolen (SQL injection, backup leak, insider threat), all user passwords would be exposed. With hashing, the attacker gets useless hashes.

### JWT token creation

```python
import jwt                                                   # (1)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")  # (2)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()                                  # (3)

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(              # (4)
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})                        # (5)

    encoded_jwt = jwt.encode(                                # (6)
        to_encode,
        settings.secret_key.get_secret_value(),              # (7)
        algorithm=settings.algorithm,
    )

    return encoded_jwt
```

1. **`jwt`** — the PyJWT library. *Install: `pip install PyJWT`.* Encodes/decodes JSON Web Tokens.
2. **`OAuth2PasswordBearer`** — tells FastAPI "extract the token from the `Authorization: Bearer <token>` header." The `tokenUrl` tells Swagger UI where the login endpoint is.
3. **`.copy()`** — don't mutate the original dict. The `data` typically looks like `{"sub": "5"}` where "sub" (subject) is the user ID.
4. Default expiry: 30 minutes from now.
5. **`"exp"`** — a standard JWT claim. The token becomes invalid after this timestamp.
6. **`jwt.encode()`** — creates the token string. It takes the payload, the secret key, and the algorithm.
7. **`.get_secret_value()`** — because `secret_key` is a `SecretStr`, you must explicitly "unwrap" it.

### JWT token verification

```python
def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(                                # (1)
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["sub", "exp"]},             # (2)
        )
    except jwt.InvalidTokenError:                            # (3)
        return None
    else:
        return payload.get("sub")                            # (4)
```

1. **`jwt.decode()`** — verifies the signature and decodes the payload. If the token was created with a different secret key, or if it's been tampered with, this raises an error.
2. **`"require": ["sub", "exp"]`** — the token MUST contain both the subject (user ID) and expiration. Without this, a malicious token without `exp` would never expire.
3. **`jwt.InvalidTokenError`** — catches expired tokens, bad signatures, missing required claims, and malformed tokens. Returns `None` so the caller knows authentication failed.
4. Returns the user ID string (e.g., `"5"`) on success.

### The `get_current_user` dependency — the heart of auth

```python
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],           # (1)
    db: Annotated[AsyncSession, Depends(get_db)],            # (2)
) -> model.User:

    user_id = verify_access_token(token)                     # (3)

    if not user_id:                                          # (4)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or Expired Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)                           # (5)
    except (TypeError, ValueError):
        raise HTTPException(...)

    result = await db.execute(                               # (6)
        select(model.User).where(model.User.id == user_id_int)
    )
    user = result.scalars().first()

    if not user:                                             # (7)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, ...)

    return user                                              # (8)

CurrentUser = Annotated[model.User, Depends(get_current_user)]  # (9)
```

1. **`Depends(oauth2_scheme)`** — FastAPI extracts the Bearer token from the request header automatically.
2. It also needs a database session to look up the user.
3. Verify the token and get the user ID.
4. If verification fails (expired, tampered, etc.), return 401 Unauthorized.
5. The JWT stores the user ID as a string (JSON doesn't distinguish int from string in the "sub" claim). We convert it back to int.
6. Look up the actual user in the database — the user might have been deleted since the token was issued.
7. If the user was deleted but the token is still valid, return 404.
8. Return the full User ORM object.
9. **`CurrentUser`** — a type alias. Instead of writing `current_user: Annotated[model.User, Depends(get_current_user)]` in every endpoint, you write `current_user: CurrentUser`. This is a significant readability improvement.

### Execution flow when a protected endpoint is called

```
Browser sends: GET /api/users/me
Header: Authorization: Bearer eyJhbGci...

→ FastAPI sees the endpoint requires CurrentUser
→ Calls get_current_user()
  → oauth2_scheme extracts "eyJhbGci..." from the header
  → get_db() creates a database session
  → verify_access_token() decodes the JWT → returns "5"
  → SELECT * FROM users WHERE id = 5
  → Returns the User object
→ The endpoint receives the User object as current_user
→ Returns the user data as JSON
```

### Reset token functions

```python
import secrets, hashlib

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)                         # (1)

def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()         # (2)
```

1. **`secrets.token_urlsafe(32)`** — generates 32 random bytes, encoded as a URL-safe base64 string (~43 characters). This is cryptographically secure — unlike `random.random()` which is predictable.
2. **`hashlib.sha256`** — one-way hash. The plain token goes in the email URL. The hash goes in the database. When the user clicks the link, the server hashes the token from the URL and compares it with the database.

### Why hash the reset token?
Same reason as passwords. If the database leaks, an attacker can't use the hashed tokens to reset anyone's password. They need the original token (which only exists in the user's email).

---

## 10. The Entry Point — `main.py`

### What are we solving?
This is the file Uvicorn loads. It creates the FastAPI application, mounts static files, includes routers, defines template routes, and handles errors.

### Where is it?
[`main.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/main.py)

### Application lifecycle (lifespan)

```python
@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:                       # (1)
        await conn.run_sync(Base.metadata.create_all)        # (2)

    yield                                                    # (3)
    await engine.dispose()                                   # (4)

app = FastAPI(lifespan=lifespan)                             # (5)
```

1. **`engine.begin()`** — starts a database transaction.
2. **`Base.metadata.create_all`** — inspects all classes that inherit from `Base` (User, Post, PasswordResetToken) and creates their tables IF they don't already exist. It does NOT modify existing tables (no migrations). `run_sync` is needed because `create_all` is a synchronous function, but we're in an async context.
3. **`yield`** — the app is now running. Control returns to FastAPI. Everything before `yield` is "startup". Everything after is "shutdown".
4. **`engine.dispose()`** — cleanly closes all database connections when the server shuts down.
5. The `lifespan` is passed to `FastAPI()` — this replaces the older `@app.on_event("startup")` pattern.

### Static file mounting

```python
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")
```

- **`/static`** → serves files from the `static/` folder. URL `/static/css/main.css` maps to `static/css/main.css` on disk.
- **`/media`** → serves user-uploaded files. Profile pictures go to `media/profile_pics/`.
- **Why separate?** `static/` contains app code (CSS, JS, default images) that's committed to git. `media/` contains user data (uploaded pictures) that's generated at runtime and should be in `.gitignore` for production.

### Router inclusion

```python
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
```

- **`prefix="/api/users"`** — every route in `users.py` gets this prefix. So `@router.post("/")` becomes `/api/users/`. `@router.get("/me")` becomes `/api/users/me`.
- **`tags=["users"]`** — groups endpoints in Swagger UI (http://localhost:8000/docs).
- **Why routers?** Without them, all 20+ endpoints would be in `main.py` making it 600+ lines.

### Template routes

Template routes serve **HTML pages** (not JSON). They render Jinja2 templates with data from the database.

```python
@app.get("/", name="home")
@app.get("/posts", name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    count_result = await db.execute(select(func.count()).select_from(model.Post))   # (1)
    total = count_result.scalar() or 0                       # (2)
    result = await db.execute(
        select(model.Post)
        .options(selectinload(model.Post.author))            # (3)
        .order_by(model.Post.date_posted.desc())             # (4)
        .limit(settings.post_per_page)                       # (5)
    )
    posts = result.scalars().all()

    has_more = len(posts) < total                            # (6)
    return templates.TemplateResponse(
        request, "home.html",
        {"posts": posts, "title": "Home", "limit": settings.post_per_page, "has_more": has_more}
    )
```

1. **`func.count()`** — generates `SELECT COUNT(*) FROM posts`. This gets the total number of posts for pagination.
2. **`.scalar()`** — extracts the single value from the result (the count number). `or 0` handles the case where the table is empty.
3. **`selectinload(model.Post.author)`** — **this is critical**. Without it, accessing `post.author.username` in the template would trigger a separate DB query for each post (the "N+1 problem"). With 10 posts, that's 11 queries instead of 2. `selectinload` loads all authors in one additional query.
4. **`.desc()`** — newest posts first.
5. **`.limit(settings.post_per_page)`** — only load the first page (10 posts).
6. **`has_more`** — if we got fewer posts than the total, there are more to load. This tells the template whether to show the "Load More" button.

### Exception handlers

```python
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception):
    if request.url.path.startswith("/api"):                  # (1)
        return await http_exception_handler(request, exception)

    message = (exception.detail if exception.detail
               else "An error occurred. Please try again")

    return templates.TemplateResponse(                       # (2)
        request, "error.html",
        {"status_code": exception.status_code, "title": exception.status_code, "message": message},
        status_code=exception.status_code,
    )
```

1. **API requests** get standard JSON error responses (what Swagger expects).
2. **Browser requests** get a rendered HTML error page (friendly for users).

This is a dual-mode pattern: the same app serves both an API and a website. The exception handler checks the URL path to decide which format to use.

---

## 11. Post Endpoints — `routers/posts.py`

### Where is it?
[`routers/posts.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/routers/posts.py)

### GET /api/posts — Paginated list

```python
@router.get("/", response_model=PaginatedPostResponse)
@router.get("", response_model=PaginatedPostResponse, include_in_schema=False)  # (1)
async def get_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,                  # (2)
    limit: Annotated[int, Query(ge=1, le=100)] = settings.posts_per_page,
):
    count_result = await db.execute(select(func.count()).select_from(model.Post))
    total = count_result.scalar() or 0
    result = await db.execute(
        select(model.Post)
        .options(selectinload(model.Post.author))
        .order_by(model.Post.date_posted.desc())
        .offset(skip)                                        # (3)
        .limit(limit)
    )
    posts = result.scalars().all()
    has_more = skip + len(posts) < total                     # (4)
    return PaginatedPostResponse(
        posts=[PostResponse.model_validate(post) for post in posts],  # (5)
        total=total, skip=skip, limit=limit, has_more=has_more,
    )
```

1. **Two routes for the same function** — handles both `/api/posts/` (with trailing slash) and `/api/posts` (without). The second is hidden from docs (`include_in_schema=False`).
2. **`Query(ge=0)`** — `skip` must be ≥ 0 (you can't skip a negative number of posts). `limit` must be 1-100. These are query parameters: `/api/posts?skip=10&limit=5`.
3. **`.offset(skip)`** — skips the first `skip` rows. Combined with `.limit(limit)`, this implements pagination. First page: `skip=0, limit=10`. Second page: `skip=10, limit=10`.
4. **`has_more`** — if `skip + returned_posts < total`, there are more posts. The frontend uses this to show/hide the "Load More" button.
5. **`model_validate(post)`** — converts SQLAlchemy objects to Pydantic schemas. This is where `from_attributes=True` matters.

### POST /api/posts — Create (authenticated)

```python
@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, current_user: CurrentUser, db: ...):
    new_post = model.Post(
        title=post.title,
        content=post.content,
        user_id=current_user.id,                             # (1)
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])    # (2)
    return new_post
```

1. **`user_id=current_user.id`** — the post is automatically assigned to the logged-in user. The client doesn't specify who the author is — that's determined by the JWT token.
2. **`db.refresh(new_post, attribute_names=["author"])`** — after commit, `new_post` has an auto-generated `id` and `date_posted`, but the `author` relationship isn't loaded. `refresh` re-reads from the database, and `attribute_names=["author"]` specifically loads the relationship so the response includes author info.

### PUT vs PATCH — Full vs Partial update

```python
# PUT — requires ALL fields (title AND content)
@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(post_id: int, current_user: CurrentUser, post_data: PostCreate, ...):
    ...
    post.title = post_data.title
    post.content = post_data.content

# PATCH — only update provided fields
@router.patch("/{post_id}", response_model=PostResponse)
async def post_update_partial(post_id: int, current_user: CurrentUser, post_data: PostUpdate, ...):
    ...
    update_data = post_data.model_dump(exclude_unset=True)   # (1)
    for field, value in update_data.items():                 # (2)
        setattr(post, field, value)
```

1. **`exclude_unset=True`** — only includes fields the client actually sent. If they only sent `{"title": "New Title"}`, `update_data` is `{"title": "New Title"}` (content is excluded, not set to `None`).
2. **`setattr(post, field, value)`** — dynamically sets `post.title = "New Title"` without needing separate if-statements for each field.

### Authorization pattern

Every mutating endpoint (create, update, delete) checks:

```python
if post.user_id != current_user.id:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not Authorized")
```

This ensures User A can't edit/delete User B's posts.

---

## 12. User Endpoints — `routers/users.py`

### Where is it?
[`routers/users.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/routers/users.py) — the largest file (441 lines).

### POST /api/users — Registration

```python
async def create_user(user: UserCreate, db: ...):
    # Check username uniqueness (case-insensitive)
    result = await db.execute(
        select(model.User).where(func.lower(model.User.username) == user.username.lower())  # (1)
    )
    ...
    # Check email uniqueness (case-insensitive)
    ...
    new_user = model.User(
        username=user.username,
        email=user.email.lower(),                            # (2)
        password_hash=hash_password(user.password),          # (3)
    )
    db.add(new_user)
    await db.commit()
```

1. **Case-insensitive check** — `func.lower()` converts both sides to lowercase. Without this, "KunalSharma" and "kunalsharma" would be treated as different usernames.
2. **`user.email.lower()`** — emails are always stored lowercase. This prevents duplicate emails like "User@Gmail.com" and "user@gmail.com".
3. **`hash_password(user.password)`** — the plain password is hashed before storage. The plain text never touches the database.

### POST /api/users/token — Login

```python
async def login_for_access_token(
    formData: Annotated[OAuth2PasswordRequestForm, Depends()],  # (1)
    db: ...
):
    result = await db.execute(
        select(model.User).where(func.lower(model.User.email) == formData.username.lower())  # (2)
    )
    user = result.scalars().first()

    if not user or not verify_password(formData.password, user.password_hash):  # (3)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, ...)

    access_token = create_access_token(data={"sub": str(user.id)}, ...)  # (4)
    return Token(access_token=access_token, token_type="bearer")
```

1. **`OAuth2PasswordRequestForm`** — a built-in FastAPI class that expects `username` and `password` as **form data** (not JSON). This follows the OAuth2 spec. The login form on the frontend sends form data, not JSON.
2. The field is called `username` in the OAuth2 spec, but your app uses email to log in. So `formData.username` actually contains the email.
3. **One error for both cases** — "Incorrect username or Password" whether the user doesn't exist OR the password is wrong. This prevents attackers from discovering valid emails (a technique called "user enumeration").
4. **`str(user.id)`** — the JWT "sub" claim is stored as a string. The user ID `5` becomes `"5"` in the token.

### POST /api/users/forgot-password — Password Reset Request

```python
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,                       # (1)
    db: ...
):
    ...
    if user:
        # Delete any existing reset tokens for this user
        await db.execute(                                    # (2)
            sql_delete(model.PasswordResetToken).where(
                model.PasswordResetToken.user_id == user.id,
            ),
        )

        token = generate_reset_token()                       # (3)
        token_hash = hash_reset_token(token)                 # (4)
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.reset_token_expire_minutes)

        reset_token = model.PasswordResetToken(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at,
        )
        db.add(reset_token)
        await db.commit()

        background_tasks.add_task(                           # (5)
            send_password_reset_email,
            to_email=user.email, username=user.username, token=token,  # (6)
        )

    return {"message": "If an account exists..."}            # (7)
```

1. **`BackgroundTasks`** — FastAPI's built-in mechanism to run functions after the response is sent. Sending email is slow (network call); we don't want the user to wait for it.
2. **Delete old tokens** — each user should only have one active reset token. Old ones are removed.
3. The **plain token** is generated (e.g., `"dG9rZW4tZXhhbXBsZS0xMjM0NTY3OA"`).
4. The **hashed token** is stored in the database.
5. Email is sent in the background — the response is returned immediately.
6. The **plain token** (not the hash) is sent in the email URL.
7. **Always returns the same message** — even if the email doesn't exist. This prevents user enumeration attacks.

### POST /api/users/reset-password — Complete the Reset

```python
async def reset_password(request_data: ResetPasswordRequest, db: ...):
    token_hash = hash_reset_token(request_data.token)        # (1)

    result = await db.execute(
        select(model.PasswordResetToken).where(
            model.PasswordResetToken.token_hash == token_hash,
        ),
    )
    reset_token = result.scalars().first()

    if not reset_token:                                      # (2)
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if reset_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):  # (3)
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(...)

    # Look up the user and update password
    user.password_hash = hash_password(request_data.new_password)  # (4)

    # Delete ALL reset tokens for this user (invalidate any others)
    await db.execute(
        sql_delete(model.PasswordResetToken).where(
            model.PasswordResetToken.user_id == user.id,
        ),
    )
    await db.commit()
```

1. Hash the token from the URL to compare with the database.
2. Token not found → either invalid or already used.
3. **Expiry check** — the token is only valid for `reset_token_expire_minutes` (60 minutes).
4. Hash the new password before storing.

### Profile picture upload

```python
async def update_profile_pic(user_id: int, file: UploadFile, current_user: CurrentUser, db: ...):
    ...
    content = await file.read()                              # (1)

    if len(content) > settings.max_upload_size_bytes:        # (2)
        raise HTTPException(...)

    try:
        new_filename = await run_in_threadpool(process_file_image, content)  # (3)
    except UnidentifiedImageError:
        raise HTTPException(...)

    old_filename = current_user.image_file
    current_user.image_file = new_filename                   # (4)
    await db.commit()

    if old_filename:
        delete_profile_pic(old_filename)                     # (5)
```

1. **`file.read()`** — reads the uploaded file into memory.
2. Check file size after reading. `5 * 1024 * 1024` = 5 MB.
3. **`run_in_threadpool`** — `process_file_image` does CPU-intensive work (resizing). Running it on the event loop would block all other requests. `run_in_threadpool` runs it in a separate thread.
4. Update the database first.
5. Delete the old file **after** the database commit succeeds. If you deleted first and the commit failed, the user would lose their picture.

---

## 13. Image Processing — `image_utils.py`

### Where is it?
[`image_utils.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/image_utils.py)

```python
from PIL import Image, ImageOps
import uuid

PROFILE_PIC_DIR = Path("media/profile_pics")

def process_file_image(content: bytes) -> str:
    with Image.open(BytesIO(content)) as original:           # (1)
        img = ImageOps.exif_transpose(original)              # (2)
        img = ImageOps.fit(img, (300, 300), method=Image.Resampling.LANCZOS)  # (3)

        if img.mode in ("RGBA", "LA", "P"):                  # (4)
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg"                 # (5)
        filepath = PROFILE_PIC_DIR / filename
        PROFILE_PIC_DIR.mkdir(parents=True, exist_ok=True)
        img.save(filepath, "JPEG", quality=85, optimize=True) # (6)

    return filename
```

1. **`BytesIO(content)`** — wraps the raw bytes so Pillow can read them as a "file".
2. **`exif_transpose`** — phone photos have EXIF rotation metadata. Without this, a portrait photo might appear rotated 90° after upload.
3. **`ImageOps.fit(..., (300, 300))`** — crops and resizes to exactly 300×300 pixels. `LANCZOS` is the highest quality resampling algorithm.
4. **RGBA → RGB** — JPEG doesn't support transparency. If someone uploads a PNG with a transparent background, convert it to RGB first.
5. **`uuid4().hex`** — generates a random 32-character filename like `"a1b2c3d4e5f6...".jpg`. This prevents filename collisions and makes URLs unguessable.
6. **`quality=85`** — JPEG quality. 85 is a good balance between file size and visual quality.

---

## 14. Email Sending — `email_utils.py`

### Where is it?
[`email_utils.py`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/email_utils.py)

```python
import aiosmtplib                                            # (1)
from email.message import EmailMessage                       # (2)

async def send_email(to_email, subject, plain_text, html_content=None):
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(plain_text)                          # (3)

    if html_content:
        message.add_alternative(html_content, subtype="html") # (4)

    await aiosmtplib.send(                                   # (5)
        message,
        hostname=settings.mail_server,
        port=settings.mail_port,
        username=settings.mail_username if settings.mail_username else None,
        password=settings.mail_password.get_secret_value() or None,
        start_tls=settings.mail_use_tls,
    )
```

1. **`aiosmtplib`** — async SMTP client. *Install: `pip install aiosmtplib`.* The standard `smtplib` is synchronous and would block the event loop.
2. **`EmailMessage`** — Python's built-in email construction class. (Standard library, not third-party.)
3. **`set_content(plain_text)`** — the plain-text version (for email clients that don't render HTML).
4. **`add_alternative(html_content)`** — the HTML version. Email clients that support HTML will show this instead. The email has both versions (multipart/alternative).
5. The SMTP connection goes to Mailtrap (a testing service that captures emails without actually sending them).

### How `send_password_reset_email` builds the URL

```python
async def send_password_reset_email(to_email, username, token):
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"  # (1)
    template = templates.env.get_template("email/password_reset.html")
    html_content = template.render(reset_url=reset_url, username=username)  # (2)
    ...
```

1. Builds a URL like `http://localhost:8000/reset-password?token=dG9rZW4...`. This is what the user clicks in their email.
2. Renders the HTML email template with the URL and username.

---

## 15. The Frontend — Templates & JavaScript

### How the template system works

All templates inherit from [`layout.html`](file:///c:/Users/kunal/OneDrive/Desktop/FastWeb/templates/layout.html) using Jinja2's template inheritance:

```
layout.html (base)
├── {% block content %} — the page-specific HTML
├── {% block scripts %} — the page-specific JavaScript
├── Navbar (with auth state management)
├── Footer
├── Create Post Modal
├── Success Modal
├── Error Modal
├── Dark Mode Toggle script
└── Auth State Management script
```

Every page template starts with `{% extends "layout.html" %}` and fills in `{% block content %}` and `{% block scripts %}`.

### Auth state in the navbar (layout.html)

```html
<!-- Shown when logged in (hidden by default) -->
<div id="loggedInNav" class="d-none">
    <button data-bs-toggle="modal" data-bs-target="#createPostModal">New Post</button>
    <a href="/account" id="accountBtn">Account</a>
</div>
<!-- Shown when logged out -->
<div id="loggedOutNav">
    <a href="/login">Login</a>
    <a href="/register">Register</a>
</div>
```

```javascript
import { getCurrentUser } from '/static/js/auth.js';

async function updateAuthUI() {
    const user = await getCurrentUser();
    if (user) {
        loggedInNav.classList.remove('d-none');  // Show: New Post + Account
        loggedOutNav.classList.add('d-none');    // Hide: Login + Register
        accountBtn.textContent = user.username;  // "Account" → "KunalSharma"
    } else {
        // Reverse
    }
}
updateAuthUI();
```

**Why client-side?** The server doesn't know about the JWT token (it's in `localStorage`, not in cookies). So the navbar always renders both states, and JavaScript shows/hides the correct one based on the token.

### `auth.js` — Token management

```javascript
let currentUser = null;
let fetchPromise = null;                                     // (1)

export async function getCurrentUser() {
    if (currentUser) return currentUser;                      // (2)
    if (fetchPromise) return fetchPromise;                    // (3)

    const token = localStorage.getItem("access_token");
    if (!token) return null;

    fetchPromise = (async () => {                             // (4)
        const response = await fetch("/api/users/me", {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
            currentUser = await response.json();
            return currentUser;
        }
        localStorage.removeItem("access_token");             // (5)
        return null;
    })();

    return fetchPromise;
}
```

1. **`fetchPromise`** — prevents duplicate API calls. If two scripts both call `getCurrentUser()` before the first one finishes, the second one gets the same in-progress promise.
2. **In-memory cache** — if the user is already loaded, don't call the API again.
3. **Deduplication** — return the in-progress fetch instead of starting a new one.
4. **IIFE (Immediately Invoked Async Function)** — creates and immediately calls an async function, storing the promise.
5. **Token cleanup** — if the API returns non-200 (expired token, deleted user), remove the invalid token.

### `utils.js` — Shared helpers

```javascript
export function escapeHtml(text) {                           // (1)
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

export function formatDate(dateString) {                     // (2)
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
        year: "numeric", month: "long", day: "2-digit",
    });
}
```

1. **XSS prevention** — when inserting user-generated content (post titles, usernames) into HTML dynamically, this escapes `<script>` tags, `&`, `"`, etc. Without this, a malicious post title like `<img onerror=alert(1)>` would execute JavaScript in every visitor's browser.
2. **Date formatting** — converts `"2026-10-04T12:30:00"` to `"October 04, 2026"` to match the server-side `strftime("%B %d, %Y")` format.

### Pagination in `home.html`

```javascript
let currentOffset = {{ limit }};     // Server tells JS where to start (10)
const limit = {{ limit }};           // How many to load each time (10)
let hasMore = {{ 'true' if has_more else 'false' }};

async function loadMorePosts() {
    loadMoreBtn.disabled = true;
    loadMoreBtn.textContent = 'Loading...';

    const response = await fetch(`/api/posts?skip=${currentOffset}&limit=${limit}`);
    const data = await response.json();

    for (const post of data.posts) {
        postsContainer.insertAdjacentHTML('beforeend', createPostHTML(post));  // (1)
    }

    currentOffset += data.posts.length;
    hasMore = data.has_more;

    if (!hasMore) loadMoreBtn.classList.add('d-none');  // Hide button
}
```

1. **`insertAdjacentHTML('beforeend', ...)`** — appends HTML at the end of the container without destroying existing DOM nodes. Faster than `innerHTML +=` because the browser doesn't re-parse the entire container.

---

## 16. Complete Execution Flows (Dry Runs)

### Flow 1: User visits the homepage

```
1. Browser → GET http://localhost:8000/
2. Uvicorn receives the request → passes to FastAPI
3. FastAPI matches @app.get("/") → home()
4. Dependency injection: get_db() creates AsyncSession
5. Query 1: SELECT COUNT(*) FROM posts → total = 44
6. Query 2: SELECT posts.*, users.* FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY posts.date_posted DESC
            LIMIT 10
   → posts = [Post1, Post2, ..., Post10]
7. has_more = len(10) < 44 → True
8. Jinja2 renders home.html with posts data
9. Response: HTTP 200, body = full HTML page
10. Browser renders HTML, loads CSS/JS
11. layout.html JS: getCurrentUser() → checks localStorage for token
12. No token → shows Login/Register buttons
```

### Flow 2: User logs in

```
1. User fills email + password on /login page
2. JS intercepts form submit (event.preventDefault())
3. JS sends: POST /api/users/token
   Body (form data): username=kunal.sharma@example.com&password=Kunal@Example2026!
4. FastAPI matches @router.post("/token")
5. OAuth2PasswordRequestForm parses form data
6. Query: SELECT * FROM users WHERE lower(email) = 'kunal.sharma@example.com'
   → user = User(id=1, username="KunalSharma", password_hash="$2b$12$...")
7. verify_password("Kunal@Example2026!", "$2b$12$...") → True
8. create_access_token({"sub": "1"}, 30 min) → "eyJhbGciOiJIUzI1NiIs..."
9. Response: {"access_token": "eyJhbGci...", "token_type": "bearer"}
10. JS stores token: localStorage.setItem("access_token", "eyJhbGci...")
11. JS shows success modal → redirects to /
12. On homepage load: getCurrentUser() → finds token in localStorage
13. GET /api/users/me with Authorization: Bearer eyJhbGci...
14. get_current_user() → decodes JWT → sub="1" → SELECT * FROM users WHERE id=1
15. Returns user data → navbar shows "KunalSharma" + "New Post" button
```

### Flow 3: Creating a post

```
1. Logged-in user clicks "New Post" → Bootstrap modal opens
2. User types title and content, clicks "Post"
3. JS intercepts form submit
4. JS sends: POST /api/posts
   Headers: Content-Type: application/json, Authorization: Bearer eyJhbGci...
   Body: {"title": "My First Post", "content": "Hello World"}
5. FastAPI matches @router.post("/")
6. Pydantic validates PostCreate: title length 1-100 ✓, content min 1 ✓
7. get_current_user() → JWT decoded → user_id=1 → User loaded
8. model.Post(title="My First Post", content="Hello World", user_id=1) created
9. db.add(new_post)
10. await db.commit() → INSERT INTO posts (title, content, user_id, date_posted) VALUES (...)
11. await db.refresh(new_post, ["author"]) → loads the author relationship
12. Response: HTTP 201, body = {"id": 45, "title": "My First Post", "author": {...}, ...}
13. JS hides create modal, shows success modal
14. On modal close → window.location.reload() → fresh page with new post at top
```

### Flow 4: Password reset (complete end-to-end)

```
Step A — Request the reset:
1. User visits /forgot-password
2. Types email, clicks "Send Reset Link"
3. JS sends: POST /api/users/forgot-password
   Body: {"email": "kunal.sharma@example.com"}
4. Server finds user → deletes old tokens → generates new token
   token = "dG9rZW4..." (plain), hash = "a3b4c5..." (SHA-256)
5. Saves PasswordResetToken(user_id=1, token_hash="a3b4c5...", expires_at=+60min)
6. background_tasks.add_task(send_password_reset_email, ..., token="dG9rZW4...")
7. Response: HTTP 202, {"message": "If an account exists..."}
   (response sent immediately, email sends in background)

Step B — User receives email:
8. Email contains link: http://localhost:8000/reset-password?token=dG9rZW4...

Step C — Reset the password:
9. User clicks link → browser loads /reset-password?token=dG9rZW4...
10. JS extracts token from URL: urlParams.get('token')
11. User types new password, clicks "Reset Password"
12. JS sends: POST /api/users/reset-password
    Body: {"token": "dG9rZW4...", "new_password": "NewSecure@2026"}
13. Server hashes token: SHA-256("dG9rZW4...") = "a3b4c5..."
14. Query: SELECT * FROM password_reset_tokens WHERE token_hash = "a3b4c5..."
15. Found → check expiry → not expired ✓
16. Look up user → hash new password → update user.password_hash
17. Delete ALL reset tokens for this user
18. Response: HTTP 200, {"message": "Password reset successfully..."}
19. JS redirects to /login
```

---

## 17. Commands

### `uvicorn main:app --reload`
| Part | Meaning |
|------|---------|
| `uvicorn` | The ASGI server program. It listens for HTTP connections and passes requests to your app. |
| `main` | The Python module name (file `main.py`, without `.py`). |
| `:app` | The variable name inside `main.py` that holds the FastAPI instance (`app = FastAPI(...)`). |
| `--reload` | Watches files for changes and restarts the server automatically. **Only for development** — in production, this adds overhead. |

**What happens when you run this:**
1. Uvicorn imports `main.py`
2. `main.py` imports `config.py` → loads `.env`
3. `main.py` imports `database.py` → creates the engine (but doesn't connect yet)
4. `main.py` imports `model.py` → registers models with `Base`
5. `main.py` imports `routers/posts.py` and `routers/users.py`
6. The `lifespan` runs → `create_all` creates tables if needed
7. Uvicorn starts listening on `http://127.0.0.1:8000`

### `python populate_db.py`
Seeds the database with test users and posts. Reads `credentials/users.json` for user data and `populate_images/` for profile pictures. Clears existing posts and creates fresh ones.

### `pip install -r requirements.txt`
Installs all Python dependencies. The key packages:
- `fastapi`, `uvicorn[standard]` — web framework + server
- `sqlalchemy`, `aiosqlite` — ORM + async SQLite driver
- `pydantic[email]`, `pydantic-settings` — validation + config
- `PyJWT` — JWT creation/verification
- `pwdlib[bcrypt]` — password hashing
- `aiosmtplib` — async email sending
- `Pillow` — image processing
- `python-multipart` — required for file uploads and form data parsing

### `git add .` vs `git add.`
- `git add .` — stages ALL changes (new, modified, deleted files) in the current directory.
- `git add.` — **error** (git thinks "add." is a subcommand). Always include the space.

---

## 18. Common Mistakes

### Forgetting `await`
If you write `db.execute(...)` without `await`, you get a coroutine object instead of results. The query never actually runs. Python may not even give you an error — it just silently returns a coroutine.

### Lazy loading in async
If you forget `selectinload(model.Post.author)` and then access `post.author.username`, you get a `MissingGreenlet` error. SQLAlchemy tries to lazily load the relationship synchronously, which is forbidden in async mode.

### Forgetting `from_attributes=True`
Without `ConfigDict(from_attributes=True)` in your Pydantic schema, `PostResponse.model_validate(post)` raises an error because it can't read attributes from a SQLAlchemy object.

### Setting Content-Type for file uploads
When uploading files with `FormData`, do NOT set `Content-Type: multipart/form-data` manually. The browser sets it automatically and includes a boundary string. If you set it manually, the boundary is missing and the server can't parse the upload.

### Not handling `expire_on_commit`
Without `expire_on_commit=False`, accessing any model attribute after `db.commit()` triggers a lazy load, which fails in async.

---

## 19. Industry Perspective

### Security
- ✅ Passwords are hashed (bcrypt via pwdlib)
- ✅ Reset tokens are hashed (SHA-256)
- ✅ JWT tokens expire (30 min)
- ✅ User enumeration protection (forgot-password always returns the same message)
- ✅ XSS prevention in JavaScript (`escapeHtml`)
- ⚠️ CSRF protection is not implemented (less critical for JWT-based auth since tokens are in localStorage, not cookies)
- ⚠️ Rate limiting is not implemented (in production, use middleware or a reverse proxy)

### Performance
- ✅ Async database access (non-blocking I/O)
- ✅ `selectinload` prevents N+1 queries
- ✅ Image processing runs in a thread pool (doesn't block the event loop)
- ✅ Email sending is done in background tasks
- ⚠️ SQLite has a single-writer limitation. For high traffic, switch to PostgreSQL.

### Production considerations
- Replace `SECRET_KEY` with a strong random key
- Use PostgreSQL instead of SQLite
- Use a real email service (SendGrid, AWS SES) instead of Mailtrap
- Add rate limiting, CORS configuration, and a reverse proxy (Nginx)
- Run with `gunicorn -k uvicorn.workers.UvicornWorker` instead of `--reload`
- Store media files in cloud storage (S3) instead of the local filesystem

---

*This document covers every major component, execution flow, and design decision in the FastWeb codebase. It is meant to be read alongside the actual source code for maximum understanding.*
