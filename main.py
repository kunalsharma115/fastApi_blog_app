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
from schemas import PostCreate , PostResponse ,PostUpdate, UserCreate, UserResponse, UserUpdate


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



@app.get("/api/posts/", response_model=list[PostResponse])
async def get_posts(db : Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.Post).options(selectinload(model.Post.author)))
    posts = result. scalars().all()
    return posts




# creating User 
@app.post("/api/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def  create_user(user: UserCreate , db : Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.username == user.username))
    existing_user = result.scalars().first()

    if existing_user:
          raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= "User is already created"
          )

    result = await db.execute(select(model.User).where(model.User.email == user.email ))
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
    await db.commit()
    await db.refresh(new_user)

    return new_user



@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id:int , user_update: UserUpdate , db : Annotated[AsyncSession , Depends(get_db)]):
     result = await db.execute(select(model.User).where(model.User.id == user_id))
     user = result.scalars().first()

     if not user:
          raise HTTPException(
               status_code = status.HTTP_404_NOT_FOUND,
               detail= "User does not exists"
          )

     if user_update.username is not None and user_update.username != user.username:
          result = await db.execute(select(model.User).where(model.User.username == user_update.username))
          existing_user = result.scalars().first();

          if existing_user:
               raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail= "Username already exists"
               )

     if user_update.email is not None and user_update.email != user.email:
        result = await db.execute(
            select(model.User).where(model.User.email == user_update.email),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

     if user_update.username is not None:
        user.username = user_update.username

     if user_update.email is not None:
        user.email = user_update.email

     if user_update.image_file is not None:
        user.image_file = user_update.image_file


     await db.commit()
     await db.refresh(user)
     return user



#delete user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id : int , db: Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
             status_code= status.HTTP_404_NOT_FOUND,
             detail= "user does not exists"
        )

    await db.delete(user)
    await db.commit()


# userPosts 
@app.get("/api/users/{user_id}/posts", response_model= list[PostResponse])
async def get_user_posts(user_id : int , db: Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.User).where((model.User.id) == user_id))

    user = result.scalars().first()

    if not user:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not present"

        )


    result = await db.execute(select(model.Post).options(selectinload(model.Post.author)).where((model.Post.user_id) == user_id) )
    posts = result.scalars().all()
    return posts



@app.post("/api/posts", response_model=PostResponse , status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate , db : Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.id == post.user_id))
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
    await db.commit()
    await db.refresh(new_post , attribute_names=["author"])

    return new_post




@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id : int , db : Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.Post).options(selectinload(model.Post.author)).where(model.Post.id == post_id))
    post = result.scalars().first()

    if not post:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "Post not found")

    return post



@app.put("/api/posts/{post_id}" , response_model= PostResponse)
async def update_post_full(post_id : int , post_data : PostCreate , db : Annotated[AsyncSession ,Depends(get_db)]):
    result = await db.execute(select(model.Post).where(model.Post.id == post_id))
    post = result.scalars().first();

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Post does not exists")

    if post_data.user_id != post.user_id:
        result = await db.execute(select(model.User).where(model.User.id == post_data.user_id))
        user = result.scalars().first();

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not present")


    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    await db.commit()
    await db.refresh(post , attribute_names=["author"])
    return post
         

@app.patch("/api/posts/{post_id}" , response_model=PostResponse)
async def post_update_partial(post_id : int , post_data : PostUpdate , db : Annotated[AsyncSession , Depends(get_db)]):
     result = await db.execute(select(model.Post).where(model.Post.id == post_id))
     post = result.scalars().first();

     if not post:
          raise HTTPException(
               status_code= status.HTTP_404_NOT_FOUND, 
               detail= "Post not found"
          )

     update_data = post_data.model_dump(exclude_unset=True)
     for field , value in update_data.items():
          setattr(post , field ,value)

     await db.commit()
     await db.refresh(post, attribute_names=["author"])
     return post

@app.delete("/api/posts/{post_id}" , status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int , db : Annotated[AsyncSession, Depends(get_db)]):
     result = await db.execute(select(model.Post).where(model.Post.id == post_id))
     post = result.scalars().first()

     if not post:
          raise HTTPException(
               status_code= status.HTTP_404_NOT_FOUND,
               detail="Post not found"
          )

     await db.delete(post)
     await db.commit()



    
@app.get("/api/users/{user_id}" , response_model=UserResponse)
async def get_user(user_id:int , db: Annotated[AsyncSession , Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.id == user_id))

    user = result.scalars().first()

    if user:
        return user

    raise HTTPException(
             status_code= status.HTTP_404_NOT_FOUND,
             detail="User not present "
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