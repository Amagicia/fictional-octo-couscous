
# app/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.models import Photo
from app.database import SessionLocal, engine, Base
from fastapi.responses import FileResponse
import shutil, os

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    with open("app/static/index.html") as f:
        return f.read()

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    path = f"app/static/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    db = SessionLocal()
    db_photo = Photo(path=path)
    db.add(db_photo)
    db.commit()
    db.close()
    return {"filename": file.filename}

@app.get("/gallery")
def gallery():
    db = SessionLocal()
    photos = db.query(Photo).all()
    db.close()
    html = "<h1>Gallery</h1>"
    for photo in photos:
        html += f'<img src="/{photo.path}" width="200" style="margin: 10px;" />'
    return HTMLResponse(content=html)
