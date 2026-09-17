from contextlib import asynccontextmanager
from __future__  import annotations
from typing import Annotated
from fastapi import FastAPI , Request , status, Depends, HTTPException

from fastapi.exception_handlers import(
     http_exception_handler,
     request_validation_exception_handler
)
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

import model
from database import Base , engine , get_db 
from schemas import PostCreate , PostResponse ,PostUpdate, UserCreate, UserResponse, UserUpdate


@asynccontextmanager
async def lifespan(_app:lifespan):
     async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.create_all)

     yield
     await engine.dispose()

app = FastAPI()

app.mount("/static",StaticFiles(directory="static"), name="static")
app.mount("/media" , StaticFiles(directory= "media") , name = "media")

templates = Jinja2Templates(directory="templates")


#home route
@app.get("/",  name = "home")
@app.get("/posts",  name = "posts")
def home(request : Request , db : Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts" : posts , "title": "Home"}
    )




@app.get("/posts/{post_id}", name = "post_page")
def post_page(request : Request , post_id: int , db : Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first()

    if post:
        title = post.title[:50],
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
def user_post_page(request: Request , user_id : int , db: Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.User).where((model.User.id == user_id)))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "User not found"
        )

    result = db.execute(select(model.Post).where((model.Post.user_id == user_id)))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "user_post.html",
        {"posts":posts, "user":user ,"title":f"{user.username}'s posts"}
    )



@app.get("/api/posts/", response_model=list[PostResponse])
def get_posts(db : Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.Post))
    posts = result. scalars().all()
    return posts




# creating User 
@app.post("/api/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def  create_user(user: UserCreate , db : Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.User).where(model.User.username == user.username))
    existing_user = result.scalars().first()

    if existing_user:
          raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= "User is already created"
          )

    result = db.execute(select(model.User).where(model.User.email == user.email ))
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
              status_code = status.HTTP_400_BAD_REQUEST,
              detail= "Email is already created"
        )

    new_user = model.User(
        username = user.username,
        email = user.email,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user



@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(user_id:int , user_data: UserUpdate , db : Annotated[Session , Depends(get_db)]):
     result = db.execute(select(model.User).where(model.User.id == user_id))
     user = result.scalars().first()

     if not user:
          raise HTTPException(
               status_code = status.HTTP_404_NOT_FOUND,
               detail= "User does not exists"
          )

     if user.username is not None and user_data.username != user.username:
          result = db.execute(select(model.User).where(model.User.username == user_data.username))
          existing_user = result.scalars().first();

          if existing_user:
               raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail= "Username already exists"
               )

     if user_data.username is not None:
        user.username = user_data.username

     if user_data.email is not None:
        user.email = user_data.email

     if user_data.image_file is not None:
        user.image_file = user_data.image_file


     db.commit()
     db.refresh(user)
     return user



#delete user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id : int , db: Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
             status_code= status.HTTP_404_NOT_FOUND,
             detail= "user does not exists"
        )

    db.delete(user)
    db.commit()


# userPosts 
@app.get("/api/users/{user_id}/posts", response_model= list[PostResponse])
def get_user_posts(user_id : int , db: Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.User).where((model.User.id) == user_id))

    user = result.scalars().first()

    if not user:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not present"

        )


    result = db.execute(select(model.Post).where((model.Post.user_id) == user_id) )
    posts = result.scalars().all()
    return posts



@app.post("/api/posts", response_model=PostResponse , status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate , db : Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.User).where(model.User.id == post.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
             status_code = status.HTTP_404_NOT_FOUND,
             detail="User not present",
        )

    new_post = model.Post(
         title = post.title,
         content = post.content,
         user_id = post.user_id,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post




@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id : int , db : Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first()

    if not post:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "Post not found")

    return post



@app.put("api/posts/{post_id}" , response_model= PostResponse)
def update_post_full(post_id : int , post_data : PostCreate , db : Annotated[Session ,Depends(get_db)]):
    result = db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first();

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Post does not exists")

    if post_data.user_id != post.user_id:
        result = db.execute(select(model.Post).where(model.User.id == post_data.user_id))
        user = result.scalars().first();

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not present")


    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    db.commit()
    db.refresh(post)
    return post
         

@app.patch("/api/posts/{post_id}" , response_model=PostResponse)
def post_update_partial(post_id : int , post_data : PostUpdate , db : Annotated[Session , Depends(get_db)]):
     result = db.execute(select(model.Post).where(model.Post.id == post_id))
     post = result.scalars().first();

     if not post:
          raise HTTPException(
               status_code= status.HTTP_404_NOT_FOUND, 
               detail= "Post not found"
          )

     update_data = post_data.model_dump(exclude_unset=True)
     for field , value in update_data.items():
          setattr(post , field ,value)

     db.commit()
     db.refresh(post)
     return post

@app.delete("/api/posts/{post_id}" , status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int , db : Annotated[Session, Depends(get_db)]):
     result = db.execute(select(model.Post).where(model.Post.id == post_id))
     post = result.scalars().first()

     if not post:
          raise HTTPException(
               status_code= status.HTTP_404_NOT_FOUND,
               detail="Post not found"
          )

     db.delete(post)
     db.commit()



    
@app.get("/api/users/{user_id}" , response_model=UserResponse)
def get_user(user_id:int , db: Annotated[Session , Depends(get_db)]):
    result = db.execute(select(model.User).where(model.User.id == user_id))

    user = result.scalars().first()

    if user:
        return user

    raise HTTPException(
             status_code= status.HTTP_404_NOT_FOUND,
             detail="User not present "
        )




@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request , exception:StarletteHTTPException):
        message=(
            exception.detail
            if exception.detail
            else "An error occurred . Please try again"
      )

        if request.url.path.startswith("/api"):
           return http_exception_handler(request  , exception)

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