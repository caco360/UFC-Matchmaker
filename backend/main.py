from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

try:
    from .db import get_fighter, get_matchups, refresh_database, search_fighters
except ImportError:
    from db import get_fighter, get_matchups, refresh_database, search_fighters


@asynccontextmanager
async def lifespan(app: FastAPI):
    refresh_database()
    yield


app = FastAPI(
    title="UFC Matchmaking API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/fighters/search")
def fighters_search(q: str = Query(default="", min_length=0, max_length=80)):
    return search_fighters(q)


@app.get("/fighters/{slug}")
def fighter_detail(slug: str):
    fighter = get_fighter(slug)
    if not fighter:
        raise HTTPException(status_code=404, detail="Fighter not found")
    return fighter


@app.get("/fighters/{slug}/matchups")
def fighter_matchups(slug: str):
    fighter = get_fighter(slug)
    if not fighter:
        raise HTTPException(status_code=404, detail="Fighter not found")
    return get_matchups(slug)
