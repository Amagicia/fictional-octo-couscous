import os
import uuid
import psycopg2
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_303_SEE_OTHER

app = FastAPI()

UPLOAD_FOLDER = "app/static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_CONFIG = {
    "dbname": "location_1698",
    "user": "location_1698_user",
    "password": "Scmgt1Keu8Y4SgFsoTM0OVG6PKAUg1Hu",
    "host": "dpg-d1fbfsfgi27c73ckorkg-a",
    "port": "5432"
}

# ========== DB Init ==========
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
from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/")
def stealth_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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

# ========== Delete All ==========
@app.post("/delete-all")
def delete_all_photos():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT path FROM photos;")
        paths = cur.fetchall()

        for (path,) in paths:
            if os.path.exists(path):
                os.remove(path)

        cur.execute("DELETE FROM photos;")
        conn.commit()
        cur.close()
        conn.close()

        return RedirectResponse(url="/gallery", status_code=HTTP_303_SEE_OTHER)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ========== Gallery ==========
@app.get("/gallery")
def gallery(password: str = ""):
    if password != "1234":  # 🔒 Change this to your secret
        return HTMLResponse("""
            <html><body style="font-family:sans-serif">
                <h2>Enter Password to View Gallery</h2>
                <form method="get" action="/gallery">
                    <input name="password" type="password" style="padding:10px;" />
                    <button type="submit" style="padding:10px 20px;">Enter</button>
                </form>
            </body></html>
        """)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT path FROM photos;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    images_html = "".join([f'<img src="/{path}" width="300" style="margin:10px;border-radius:10px;box-shadow:0 0 10px #aaa;">' for (path,) in rows])
    
    return HTMLResponse(f"""
    <html>
    <head>
        <title>Gallery</title>
        <style>
            body {{ font-family: Arial; background: #f4f4f4; text-align: center; }}
            .btn {{ padding: 12px 24px; margin: 20px 10px; font-size: 18px; border:none; border-radius:8px; cursor:pointer; }}
            .delete {{ background-color:#f44336; color:white; }}
            .upload {{ background-color:#4CAF50; color:white; }}
            img:hover {{ transform:scale(1.03); transition:0.3s; }}
        </style>
    </head>
    <body>
        <h1>📸 Photo Gallery</h1>
        <form action="/delete-all" method="post">
            <button class="btn delete" type="submit">🗑 Delete All</button>
        </form>
        <div>{images_html or "<p>No photos yet.</p>"}</div>
    </body>
    </html>
    """)

# ========== Static Files ==========
app.mount("/static", StaticFiles(directory="app/static"), name="static")
