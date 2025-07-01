import os
import uuid
import psycopg2
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# ======================== Config ========================
UPLOAD_FOLDER = "app/static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_CONFIG = {
    "dbname": "location_1698",
    "user": "location_1698_user",
    "password": "Scmgt1Keu8Y4SgFsoTM0OVG6PKAUg1Hu",
    "host": "dpg-d1fbfsfgi27c73ckorkg-a",  # or Render DB host
    "port": "5432"
}

# ======================== DB Setup ========================
def create_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id SERIAL PRIMARY KEY,
            path TEXT UNIQUE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

create_table()

# ======================== Upload Route ========================


from fastapi.responses import FileResponse

@app.get("/")
def index():
    return FileResponse("app/templates/index.html")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("INSERT INTO photos (path) VALUES (%s);", (file_path,))
        conn.commit()
        cur.close()
        conn.close()

        return JSONResponse(content={"message": "Uploaded", "path": f"/static/{unique_filename}"}, status_code=201)

    except psycopg2.errors.UniqueViolation:
        return JSONResponse(content={"error": "Duplicate path"}, status_code=400)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ======================== Gallery Route ========================
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")  # change as needed
    correct_password = secrets.compare_digest(credentials.password, "supersecret")  # change as needed

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.get("/gallery")
def gallery(credentials: HTTPBasicCredentials = Depends(verify_user)):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT path FROM photos;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        images_html = "".join([
            f'<img src="/static/{os.path.basename(path)}" width="300" style="margin:10px;">'
            for (path,) in rows
        ])
        return HTMLResponse(content=f"<html><body>{images_html}</body></html>")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ======================== Static Mount ========================
app.mount("/static", StaticFiles(directory="app/static"), name="static")
