import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

# ربط مجلد الواجهات
templates = Jinja2Templates(directory="templates")

# مجلد الرفع المؤقت
os.makedirs("/tmp/uploads", exist_ok=True)

# قائمة الأنشطة الثابتة والمباشرة
ACTIVITIES_LIST = [
    {"id": 1, "title": "ورشة الذكاء الاصطناعي"},
    {"id": 2, "title": "دورة برمجة C++"},
    {"id": 3, "title": "ورشة الأجهزة الذكية والـ IoT"},
    {"id": 4, "title": "ورشة شبكات الحاسوب"}
]

@app.get("/")
def home():
    return {"status": "Server is running successfully"}

@app.get("/student")
def get_student_ui(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "activities": ACTIVITIES_LIST
    })

@app.get("/api/activities")
def get_activities():
    return ACTIVITIES_LIST

@app.post("/api/submit")
async def submit_certificate(
    student_id: int = Form(...),
    activity_id: int = Form(...),
    file: UploadFile = File(...)
):
    file_location = f"/tmp/uploads/{student_id}_{activity_id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"message": "تم رفع الشهادة بنجاح!"}
