from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.constants import TEMPLATES_DIR, STATIC_DIR
from starlette.exceptions import HTTPException as StarletteHTTPException


app: FastAPI = FastAPI()

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

posts: list[dict] = [
    {"id": 1,
    "author": "Muhammad Nabawi",
    "title": "Saya Ingin Menjadi Fullstack Engineer/Software Engineer Yang Mahir",
    "content": "Proses nya tidak akan mudah, InsyaAllah saya bisa lalui dengan belajar.",
    "date_posted": "June 28, 2026"
    },
    {"id": 2,
    "author": "Corey Schafer",
    "title": "FastAPI is Awesome",
    "content": "This framework is really easy to use and super fast.",
    "date_posted": "June 28, 2026"
    },
    
]

@app.get("/v1", include_in_schema=False, name="home")
@app.get("/v1/posts", include_in_schema=False, name="posts")
async def home(request: Request):
    return templates.TemplateResponse(
        request, "home.html",
        status_code=200,
        context={
            "posts": posts,
            "title": "Home"
            }
        )


@app.get("/v1/posts/{post_id}", include_in_schema=False)
async def user_post(request: Request, post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return templates.TemplateResponse(
                request, "post.html",
                status_code=200,
                context={"post": post, "title": "Post"}
                )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Post not found"
        )

@app.get("/api/v1/posts")
async def get_posts():
    return posts


@app.get("/api/v1/posts/{post_id}")
async def get_post(post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return post
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Post not found"
        )


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