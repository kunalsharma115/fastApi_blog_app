from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI();

posts: list[dict] = [
    {
        "id": 1,
        "author": "Kunal Sharma",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "sep 7 , 2026",
    },
    {
        "id": 2,
        "author": "shristi ",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better.",
        "date_posted": "sep 7 , 2026",
    },
]

@app.get("/", response_class=HTMLResponse)
def home():
    return f"{posts[0]}";


@app.get("/api/posts")
def get_posts():
    return posts;
