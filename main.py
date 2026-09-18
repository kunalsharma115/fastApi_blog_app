from __future__  import annotations
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI , Request , status, Depends, HTTPException

from fastapi.exception_handlers import(
     http_exception_handler,
     request_validation_exception_handler
)
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession 

import model
from database import Base , engine , get_db 
from routers import posts , users


@asynccontextmanager
async def lifespan(_app:FastAPI):
     async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.create_all)

     yield
     await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount("/static",StaticFiles(directory="static"), name="static")
app.mount("/media" , StaticFiles(directory= "media") , name = "media")

templates = Jinja2Templates(directory="templates")

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])


#home route
@app.get("/",  name = "home")
@app.get("/posts",  name = "posts")
async def home(request : Request , db : Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.Post).options(selectinload(model.Post.author)),)
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts" : posts , "title": "Home"}
    )




@app.get("/posts/{post_id}", name = "post_page")
async def post_page(request : Request , post_id: int , db : Annotated[AsyncSession , Depends(get_db)]):
    result = await  db.execute(select(model.Post).options(selectinload(model.Post.author)).where(model.Post.id == post_id))
    post = result.scalars().first()

    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post":post, "title":title}
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail= "Post not found"
    )




@app.get("/users/{user_id}/posts", name="user_posts")
async def user_post_page(request: Request , user_id : int , db: Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.User).where((model.User.id == user_id)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "User not found"
        )

    result = await db.execute(select(model.Post).options(selectinload(model.Post.author)).where((model.Post.user_id == user_id)))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "user_post.html",
        {"posts":posts, "user":user ,"title":f"{user.username}'s posts"}
    )




@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request , exception:StarletteHTTPException):

        if request.url.path.startswith("/api"):
           return  await http_exception_handler(request  , exception)

        message=(
            exception.detail
            if exception.detail
            else "An error occurred . Please try again"
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
async def validation_exception_handler(request:Request , exception:RequestValidationError):
            if request.url.path.startswith("/api"):
                return await request_validation_exception_handler(request , exception)

            return templates.TemplateResponse(
                  request,
                  "error.html",{
                  "status_code":status.HTTP_422_UNPROCESSABLE_CONTENT,
                  "title":status.HTTP_422_UNPROCESSABLE_CONTENT,
                  "message":"An error occurred . Please try again"
                  },
                  status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
            )