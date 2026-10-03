from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy import func,  select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool


from database import get_db
import model
from schemas import PostResponse, UserCreate, UserPrivate, UserPublic, UserUpdate, Token
from image_utils import delete_profile_pic , process_file_image


from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from PIL import UnidentifiedImageError
from auth import CurrentUser , create_access_token, hash_password, verify_password
from config import settings


router = APIRouter()


@router.post("/", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).where(func.lower(model.User.username) == user.username.lower()))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already created",
        )

    result = await db.execute(select(model.User).where(func.lower(model.User.email) == user.email.lower()))
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already created",
        )

    new_user = model.User(
        username=user.username,
        email=user.email.lower(),
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user



@router.post("/token", response_model=Token)
async def login_for_access_token(
    formData: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(model.User).where(func.lower(model.User.email) == formData.username.lower())
    )
    user = result.scalars().first()

    if not user or not verify_password(
        formData.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or Password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expire = timedelta(minutes=settings.access_token_expire_minutes)

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expire,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPrivate)
async def get_current_user(
    current_user : CurrentUser
):
    return current_user


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()

    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not present ",
    )


@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(user_id: int, current_user : CurrentUser, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):

    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to update User"
        )
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exists",
        )

    if user_update.username is not None and user_update.username.lower() != user.username.lower():
        result = await db.execute(select(model.User).where(func.lower(model.User.username) == user_update.username.lower()))
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        result = await db.execute(
            select(model.User).where(func.lower(model.User.email) == user_update.email.lower()),
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
        user.email = user_update.email.lower()


    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user : CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):

    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to delete User"
        )
    result = await db.execute(select(model.User).where(model.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user does not exists",
        )

    old_filename = current_user.image_file
    await db.delete(user)
    await db.commit()

    if old_filename:
        delete_profile_pic(old_filename)


@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(model.User).where((model.User.id) == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not present",
        )

    result = await db.execute(
        select(model.Post).options(selectinload(model.Post.author)).where((model.Post.user_id) == user_id)
        .order_by(model.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return posts


@router.patch("/{user_id}/profile", response_model=UserPrivate)
@router.patch("/{user_id}/picture", response_model=UserPrivate, include_in_schema=False)
async def update_profile_pic(user_id: int, file: UploadFile, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to update User Profile Picture"
        )

    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is too large. Size limit is 5MB"
        )

    try:
        new_filename = await run_in_threadpool(process_file_image, content)

    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF)"
        ) from err

    old_filename = current_user.image_file
    current_user.image_file = new_filename

    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_pic(old_filename)

    return current_user


@router.delete("/{user_id}/profile", response_model=UserPrivate)
@router.delete("/{user_id}/picture", response_model=UserPrivate, include_in_schema=False)
async def delete_user_profile(
    user_id: int,
    current_user: CurrentUser, 
    db: Annotated[AsyncSession, Depends(get_db)]
):

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to delete User Profile"
        )

    old_filename = current_user.image_file

    if not old_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture found"
        )

    current_user.image_file = None

    await db.commit()
    await db.refresh(current_user)

    delete_profile_pic(old_filename)
    return current_user
