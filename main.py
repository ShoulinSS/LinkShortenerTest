import random
import string
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "secret")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

DB_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    short_id = Column(String(10), unique=True, index=True)
    original_url = Column(String, nullable=False, unique=True)
    usage_count = Column(BigInteger, default=0)

Base.metadata.create_all(bind=engine)

class UrlRequest(BaseModel):
    url: HttpUrl

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_id(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

app = FastAPI()

@app.post("/shorten")
def shorten_link(request: UrlRequest, db: Session = Depends(get_db)):
    existing = db.query(Link).filter(Link.original_url == str(request.url)).first()
    if existing:
        return {"short_id": existing.short_id}

    while True:
        id = generate_id()
        if not db.query(Link).filter(Link.short_id == id).first():
            break

    new_link = Link(short_id=id, original_url=str(request.url))
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return {"short_id": id}

@app.get("/{short_id}")
def redirect_link(short_id: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_id == short_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Not found")
    
    link.usage_count += 1
    db.commit()
    return RedirectResponse(url=link.original_url, status_code=302)

@app.get("/stats/{short_id}")
def get_stats(short_id: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_id == short_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {"short_id": link.short_id, "usage_count": link.usage_count}