import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import delete, select, update

import model as models
from database import AsyncSessionLocal, engine
from image_utils import PROFILE_PIC_DIR as PROFILE_PICS_DIR

from main import app

POPULATE_IMAGES_DIR = Path("populate_images")

USERS = [
    {
        "username": "KunalSharma",
        "email": "kunal.sharma@fastweb.dev",
        "password": "Kunal@FastWeb2026!",
        "image": "corey.png",
    },
    {
        "username": "DefaultDude",
        "email": "alex.dude@fastweb.dev",
        "password": "DefaultDude#2026Pass",
        # No image - uses default
    },
    {
        "username": "WillowTheCat",
        "email": "willow.feline@fastweb.dev",
        "password": "WillowPaws$2026Cat",
        "image": "willow.png",
    },
    {
        "username": "FarmDogs",
        "email": "farm.pack@fastweb.dev",
        "password": "RanchDogs%2026Bark",
        "image": "farmdogs.png",
    },
    {
        "username": "PoppyTheCoder",
        "email": "poppy.dev@fastweb.dev",
        "password": "PoppyCode^2026Dev",
        "image": "poppy.png",
    },
    {
        "username": "GoodBoyBronx",
        "email": "bronx.pup@fastweb.dev",
        "password": "GoodBoyBronx&2026",
        "image": "bronx.png",
    },
]

POSTS = [
    {
        "title": "Building Scalable Modern Web Apps with FastAPI",
        "content": "FastAPI has fundamentally revolutionized asynchronous backend development in Python. Combining intuitive type annotations, automatic OpenAPI documentation generation, and blazing-fast Starlette ASGI foundations, it provides developer productivity without sacrificing throughput.",
    },
    {
        "title": "Asynchronous Python: From Coroutines to High-Performance APIs",
        "content": "Understanding the event loop, task scheduling, and cooperative multitasking unlocks the full potential of Python 3.12+. Non-blocking I/O ensures your web services can comfortably handle thousands of concurrent client requests.",
    },
    {
        "title": "Mastering Pydantic V2: Rust-Powered Serialization",
        "content": "With its core rewritten in Rust, Pydantic V2 delivers a 5x to 20x speedup for data parsing and validation. Learning ConfigDict, computed fields, and custom validators makes request schemas both bulletproof and incredibly fast.",
    },
    {
        "title": "Database Migration Strategies with Alembic",
        "content": "Schema evolution should always be reproducible and version-controlled. Alembic allows teams to track changes cleanly, test rollbacks safely, and automate migrations in continuous deployment pipelines.",
    },
    {
        "title": "REST vs GraphQL vs gRPC: Choosing the Right API Style",
        "content": "Every communication protocol serves distinct system requirements. REST excels in caching and simplicity, GraphQL solves over-fetching for complex frontends, and gRPC dominates microservice internal communication.",
    },
    {
        "title": "JWT Authentication Best Practices in Production",
        "content": "Stateless JWT tokens are powerful, but security requires strict implementation: always sign with asymmetric RS256 or strong HS256 secrets, keep lifespans short, enforce HTTPS, and implement secure token revocation mechanisms.",
    },
    {
        "title": "Designing Clean Microservices with Domain-Driven Design",
        "content": "Decoupling business logic from infrastructure frameworks ensures long-term maintainability. Bounded contexts, aggregates, and domain events provide clarity when scaling engineering teams.",
    },
    {
        "title": "Docker Multi-Stage Builds for Minimalist Python Containers",
        "content": "Multi-stage Docker builds dramatically shrink container images and eliminate build tools from runtime environments. Smaller images mean faster deployments, reduced attack surface, and lower cloud storage costs.",
    },
    {
        "title": "SQLAlchemy 2.0 Async Session Patterns and Gotchas",
        "content": "Transitioning to 2.0-style select() and mapped_column() syntax creates clear, type-safe queries. Managing session scopes properly prevents dreaded 'Session is closed' errors during async execution.",
    },
    {
        "title": "Effective Multi-Layer Caching with Redis",
        "content": "Strategic caching turns heavy database bottlenecks into sub-millisecond responses. Implementing cache invalidation patterns like Cache-Aside and Write-Through maintains consistency across distributed nodes.",
    },
    {
        "title": "Securing Web Applications with Essential HTTP Security Headers",
        "content": "Deploying Content-Security-Policy (CSP), Strict-Transport-Security (HSTS), X-Frame-Options, and X-Content-Type-Options blocks the vast majority of cross-site scripting (XSS) and clickjacking attacks out of the box.",
    },
    {
        "title": "Zero-Downtime Rolling Deployments Explained",
        "content": "Users shouldn't experience 502 bad gateway errors while you deploy new features. Rolling deployments with health checks ensure traffic only shifts to new pods once they are verified ready.",
    },
    {
        "title": "Real-Time WebSockets in Modern Asynchronous Backends",
        "content": "Bidirectional real-time communication enables chat rooms, live financial tickers, and collaborative documents. FastAPI's native WebSocket support makes connection lifecycles clean and intuitive.",
    },
    {
        "title": "Background Tasks: Native FastAPI vs Celery and Redis",
        "content": "For lightweight operations like sending welcome emails or logging analytics, FastAPI's BackgroundTasks requires zero extra infrastructure. For heavy compute jobs or scheduled tasks, Celery remains the gold standard.",
    },
    {
        "title": "SQL Query Optimization: Indexes, EXPLAIN Plans, and Joins",
        "content": "Writing fast SQL starts with understanding query execution plans. Composite indexes, covering indexes, and eliminating N+1 query patterns yield order-of-magnitude performance enhancements.",
    },
    {
        "title": "Clean Architecture and Repository Patterns in Python",
        "content": "Separating domain rules from persistence databases allows you to swap SQLite for PostgreSQL without touching core application logic. Dependency injection makes testing with mocks seamless.",
    },
    {
        "title": "The Comprehensive Guide to Unit and Integration Testing with Pytest",
        "content": "Confidence in shipping code stems from comprehensive test suites. Async HTTP test clients, isolated transactional fixtures, and mocking external services guarantee resilient software releases.",
    },
    {
        "title": "API Rate Limiting and DoS Protection Strategies",
        "content": "Protecting endpoints from abusive clients or runaway scrapers is essential. Leaky-bucket and sliding-window algorithms backed by Redis ensure fair API quota distribution across all consumers.",
    },
    {
        "title": "Understanding Cross-Origin Resource Sharing (CORS) Properly",
        "content": "CORS errors are among the most common web issues. Understanding preflight OPTIONS requests, allowed origins, and credential flags helps configure access securely without using wildcard asterisks.",
    },
    {
        "title": "Structured JSON Logging and Distributed Observability",
        "content": "Plain text log files don't scale in distributed clusters. Emitting structured JSON logs with correlation IDs enables centralized aggregation in Elasticsearch, Datadog, or Grafana Loki.",
    },
    {
        "title": "Crafting Beautiful and Developer-Friendly OpenAPI Documentation",
        "content": "Interactive documentation via Swagger UI and ReDoc is one of FastAPI's killer features. Adding descriptions, status code schemas, and request examples elevates your developer experience.",
    },
    {
        "title": "Monoliths vs Microservices: Choosing Pragmatism Over Hype",
        "content": "Starting with a well-architected modular monolith is almost always the right choice for early-stage products. Break out microservices only when organizational or throughput boundaries strictly demand it.",
    },
    {
        "title": "Type Safety in Python: How Mypy and Ruff Transform Codebases",
        "content": "Static typing catches bugs long before code hits production. Modern type hints with TypedDict, Generics, and Union types make refactoring large codebases fast and fearless.",
    },
    {
        "title": "Secrets Management and Zero-Trust Configuration",
        "content": "Never commit credentials or tokens to version control. Using environment variables, 12-factor principles, and secret managers like Vault ensures your deployment pipeline remains uncompromised.",
    },
    {
        "title": "Profiling Asyncio: Detecting Event Loop Blockers",
        "content": "Running synchronous CPU-heavy work on the event loop starves all other requests. Using run_in_threadpool or ProcessPoolExecutor keeps your server responsive and latency ultra-low.",
    },
    {
        "title": "Modern CSS Layouts: Practical CSS Grid and Flexbox",
        "content": "Gone are the days of float hacks and complex clearance divs. Modern CSS Grid and Flexbox allow for fully responsive, content-adaptive layouts with clean and minimal stylesheets.",
    },
    {
        "title": "Server-Sent Events (SSE) vs WebSockets: What Fits Best?",
        "content": "When your application only requires one-way real-time server-to-client updates—like AI streaming tokens or notification badges—Server-Sent Events offer a simpler HTTP-compliant alternative to WebSockets.",
    },
    {
        "title": "Writing Reusable and Modular Jinja2 Templates",
        "content": "Template inheritance, macro components, and scoped blocks turn Jinja2 into a powerful templating engine for server-side rendered web applications.",
    },
    {
        "title": "Secure File Uploads and Streaming Validation",
        "content": "Validating file sizes, MIME types, and scanning magic bytes prevents malicious uploads. Processing incoming streams in chunks guarantees memory usage remains capped even under large payloads.",
    },
    {
        "title": "Nginx Reverse Proxy Optimization for Python Web Apps",
        "content": "Placing Nginx ahead of Uvicorn provides static file caching, SSL termination, Gzip compression, and connection buffering, freeing Python worker threads to focus solely on dynamic requests.",
    },
    {
        "title": "Automating Code Quality with Pre-commit, Ruff, and Black",
        "content": "Automated linting and formatting eliminate style debates during code reviews. Running checks on git commit hooks keeps the codebase uniformly clean across the entire engineering team.",
    },
    {
        "title": "Graceful Shutdown and Lifecycle Management in FastAPI",
        "content": "Using async lifespan context managers ensures database connection pools, background workers, and external connections drain cleanly without terminating in-flight client requests.",
    },
    {
        "title": "Building Resilient Circuit Breakers in Distributed Systems",
        "content": "When downstream microservices fail, cascading failures can bring down your whole cluster. Circuit breakers detect failing dependencies and fail fast, preserving system health.",
    },
    {
        "title": "Webhook Architecture: Delivery Guarantees and HMAC Signatures",
        "content": "Designing reliable webhooks requires exponential backoff retries, idempotency keys, and HMAC SHA-256 signatures so recipients can verify authenticity and replay safety.",
    },
    {
        "title": "Database Connection Pooling: Balancing Latency and Concurrency",
        "content": "Creating new database connections per request is expensive. Proper pool sizing with SQLAlchemy ensures optimal connection reuse without overwhelming database process limits.",
    },
    {
        "title": "Consistent API Error Handling: Standardized JSON Responses",
        "content": "Uniform error structures with clear status codes, machine-readable error codes, and descriptive messages make frontend integration seamless and predictable.",
    },
    {
        "title": "Kubernetes 101 for Python Backend Developers",
        "content": "Pods, Deployments, Services, and Ingress controllers form the foundation of cloud-native infrastructure. Understanding readiness probes ensures traffic only routes to healthy instances.",
    },
    {
        "title": "Modern Client-Side State Management Without Heavy Frameworks",
        "content": "You don't always need massive single-page application frameworks. Combining server-rendered HTML with lightweight ES6 modules and Fetch APIs yields incredible performance and simplicity.",
    },
    {
        "title": "SQLite in Development to PostgreSQL in Production",
        "content": "SQLite offers instant zero-config setups for local prototyping and testing, while PostgreSQL delivers enterprise concurrency, robust JSONB querying, and rich full-text indexing in production.",
    },
    {
        "title": "Writing Self-Documenting and Maintainable Code",
        "content": "Code is read far more often than it is written. Meaningful variable names, focused single-responsibility functions, and strategic comments create software that teammates love maintaining.",
    },
    {
        "title": "Observability with Prometheus Metrics and Grafana Dashboards",
        "content": "Exposing request latency histograms, error counters, and memory utilization metrics turns abstract cloud operations into real-time visual insights.",
    },
    {
        "title": "Demystifying OAuth2: Grant Types, PKCE, and Scopes",
        "content": "Understanding Authorization Code flow with PKCE, Client Credentials, and refresh tokens enables secure third-party integrations and delegated authorization.",
    },
    {
        "title": "The Evolution of FastWeb: From Concept to Production",
        "content": "FastWeb showcases how modern Python web applications should be built: clean architectural separation, robust authentication, asynchronous scalability, and elegant user experiences.",
    },
]

# The 44th post - oldest post (anchor post for pagination)
POST_44 = {
    "title": "Welcome to FastWeb: The Architecture and Vision",
    "content": "FastWeb was built to demonstrate the elegance and speed of modern Python web development. Designed with FastAPI, SQLAlchemy 2.0, asynchronous database interactions, and responsive UI components, it stands as an open and scalable blueprint for production-grade web applications.",
}


async def clear_existing_data() -> None:
    # Delete profile pictures from local storage
    if PROFILE_PICS_DIR.exists():
        for file in PROFILE_PICS_DIR.iterdir():
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()
        print(f"Deleted profile pictures from {PROFILE_PICS_DIR}")

    # Clear database tables (order respects foreign keys)
    async with AsyncSessionLocal() as db:
        await db.execute(delete(models.PasswordResetToken))
        await db.execute(delete(models.Post))
        await db.execute(delete(models.User))
        await db.commit()
    print("Cleared existing data")


async def update_post_dates() -> None:
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Post).order_by(models.Post.id))
        posts = result.scalars().all()

        if not posts:
            return

        # First post (POST_44) is the oldest - ~90 days ago
        await db.execute(
            update(models.Post)
            .where(models.Post.id == posts[0].id)
            .values(date_posted=now - timedelta(days=90)),
        )

        # Remaining posts: each ~1.5 days newer than previous
        for i, post in enumerate(posts[1:], start=1):
            days_ago = (len(posts) - i) * 1.5
            hours_offset = (i * 7) % 24
            post_date = now - timedelta(days=days_ago, hours=hours_offset)
            await db.execute(
                update(models.Post)
                .where(models.Post.id == post.id)
                .values(date_posted=post_date),
            )

        await db.commit()
    print("Updated post dates")


async def populate() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://localhost",
    ) as client:
        # Clear existing data (local images first, then database)
        await clear_existing_data()

        users: list[dict] = []

        print(f"\nCreating {len(USERS)} users...")
        for user_data in USERS:
            response = await client.post(
                "/api/users",
                json={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            user = response.json()
            print(f"  Created: {user['username']}")

            response = await client.post(
                "/api/users/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            token = response.json()["access_token"]

            if image_name := user_data.get("image"):
                image_path = POPULATE_IMAGES_DIR / image_name
                if image_path.exists():
                    response = await client.patch(
                        f"/api/users/{user['id']}/picture",
                        files={
                            "file": (
                                image_name,
                                image_path.read_bytes(),
                                "image/png",
                            ),
                        },
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    response.raise_for_status()
                    print(f"    Uploaded: {image_name}")

            users.append(
                {"id": user["id"], "username": user["username"], "token": token},
            )

        print(f"\nCreating {len(POSTS) + 1} posts...")

        # First create POST_44 (will become oldest after date update)
        response = await client.post(
            "/api/posts",
            json={"title": POST_44["title"], "content": POST_44["content"]},
            headers={"Authorization": f"Bearer {users[0]['token']}"},
        )
        response.raise_for_status()
        print(f"  Created: '{POST_44['title']}'")

        # Create remaining posts in reverse (last in list = oldest, first = newest)
        for i, post_data in enumerate(reversed(POSTS)):
            await asyncio.sleep(0.05)  # brief delay to prevent SQLite file locking contention
            user = users[i % len(users)]
            response = await client.post(
                "/api/posts",
                json={
                    "title": post_data["title"],
                    "content": post_data["content"],
                },
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            response.raise_for_status()
            title = post_data["title"]
            print(
                f"  Created: '{title[:50]}...'"
                if len(title) > 50
                else f"  Created: '{title}'",
            )

        print("\nUpdating post dates...")
        await update_post_dates()

    await engine.dispose()

    print("\nDone!")
    print(f"  {len(USERS)} users")
    print(f"  {len(POSTS) + 1} posts")
    print("  Profile pictures saved locally")


if __name__ == "__main__":
    asyncio.run(populate())