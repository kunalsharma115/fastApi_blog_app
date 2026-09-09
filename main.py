from fastapi import FastAPI , Request , status
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException,RequestValidationError
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
app = FastAPI()

app.mount("/static",StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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

@app.get("/posts")
def home(request: Request):
                return templates.TemplateResponse(
                    request,
                    "home.html",
                    {"posts":posts, "title":"Home"}
                )
    
@app.get("/posts/{post_id}") 
def get_post(request: Request,post_id : int):
    for post in posts:
        if post.get("id") == post_id :
            title = post["title"][:50]
            return templates.TemplateResponse(
                  request,
                  "home.html",
                  {
                    "posts":[post],
                    "title":title,
                  }
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page Not found")

@app.get("/api/posts/{post_id}") 
def get_post(post_id : int):
    for post in posts:
        if post.get("id") == post_id :
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page Not found")

@app.get("/api/posts/")
def get_posts():
    return posts 


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request , exception:StarletteHTTPException):
        message=(
            exception.detail
            if exception.detail
            else "An error occurred . Please try again"
      )

        if request.url.path.startswith("/api"):
           return JSONResponse(
                status_code = exception.status_code,
                content={"detail":message},
           )

        return templates.TemplateResponse(
              request,
              "error.html",
              {
                    "status_code": exception.status_code,
                    "title": exception.status_code,
                    "message":message,

              },
              status_code= exception.status_code,
        )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request:Request , exception:RequestValidationError):
            if request.url.path.startswith("/api"):
                return JSONResponse(
                status_code = status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={"detail":exception.errors()},
           )

            return templates.TemplateResponse(
                  request,
                  "error.html",{
                  "status_code":status.HTTP_422_UNPROCESSABLE_CONTENT,
                  "title":status.HTTP_422_UNPROCESSABLE_CONTENT,
                  "message":"An error occurred . Please try again"
                  },
                  status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
            )