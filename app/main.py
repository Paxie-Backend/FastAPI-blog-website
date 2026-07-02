from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Annotated
from app import models
from app.schemas import PostCreate, PostUpdate, PostResponse, UserCreate, UserUpdate, UserResponse  
from app.constants import TEMPLATES_DIR, STATIC_DIR, MEDIA_DIR
from app.database import get_db



app: FastAPI = FastAPI()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")



@app.get("/v1", include_in_schema=False, name="home")
@app.get("/v1/posts", include_in_schema=False, name="posts")
async def home(
    request: Request,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request, "home.html",
        status_code=200,
        context={
            "posts": posts, "title": "Home"}
        )


@app.get("/v1/posts/{post_id}", include_in_schema=False)
async def post_page(
    request: Request,
    post_id: int,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
            )
    
    return templates.TemplateResponse(
        request,
        "post.html",
        status_code=200,
        context={
            "post": post
        }
    )    


@app.get("/v1/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )






@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(
        models.User.id == user_id
        )
    ) 
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can't find user with id {user_id}"
        )
        
    return user


@app.get(
    "/api/v1/users/{user_id}/posts",
    response_model=list[PostResponse])
def get_user_posts(
    user_id: int,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(
            models.User.id == user_id
            )
        )
    
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    result = db.execute(
        select(models.Post).where(
            models.Post.user_id == user_id
            )
        )
    
    posts = result.scalars().all()
    return posts


@app.post(
    "/api/v1/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(
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
    
    new_user = models.User(
        username=user.username,
        email=user.email
        )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.patch(
    "/api/v1/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK)
def update_user_partial(
    user_id: int,
    user_data: UserUpdate,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(
            models.User.id == user_id
            )
        )
    
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@app.delete(
    "/api/v1/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(
            models.User.id == user_id
            )
        )
    
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()





@app.get("/api/v1/posts", response_model=list[PostResponse])
async def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


@app.post(
    "/api/v1/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED)
def create_post(
    post: PostCreate,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(
            models.User.id == post.user_id
            )
        )
    
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id
        )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return new_post

@app.get(
    "/api/v1/posts/{post_id}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK)
async def get_post(
    post_id: int,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
            )
    return post


@app.put("/api/v1/posts/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int,
    post_data: PostCreate,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
            )
    
    if post_data.user_id != post.user_id:
        result = db.execute(
            select(models.User).where(models.User.id == post_data.user_id))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This post is not yours!!!"
        )
    
    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id
    
    db.commit()
    db.refresh(post)
    return post


@app.patch("/api/v1/posts/{post_id}", response_model=PostResponse)
def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.Post).where(
            models.Post.id == post_id
            )
        )
    
    post = result.scalars().first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
        
    
    db.commit()
    db.refresh(post)
    return post


@app.delete(
    "/api/v1/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
            )
    
    db.delete(post)
    db.commit()





@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
        
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'details': exception.errors()}
        )
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again"
        }
    )