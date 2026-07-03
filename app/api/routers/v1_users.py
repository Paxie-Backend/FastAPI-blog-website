from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.database import get_db
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PostResponse
    )


router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.posts))
        .where(models.User.id == user_id)
        ) 
    
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can't find user with id {user_id}"
        )
        
    return user

@router.get(
    "/{user_id}/posts",
    response_model=list[PostResponse])
async def get_user_posts(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
        )
    
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
        )
    
    posts = result.scalars().all()
    return posts

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(
            (models.User.username == user.username) 
            | (models.User.username == user.username)
            )
        )
    
    exists = result.scalars().first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "User already exists",
        )
    
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK)
async def update_user_partial(
    user_id: int,
    user_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
        )
    
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
        )
    
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()