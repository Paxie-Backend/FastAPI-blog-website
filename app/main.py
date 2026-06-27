from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.constants import TEMPLATES_DIR, STATIC_DIR


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



@app.get("/v1/api/posts")
async def get_posts():
    return posts


@app.get("/v1/api/posts/{post_id}")
async def get_post(post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return post
    
    return False