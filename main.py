import os
import shutil
from fastapi import FastAPI, Depends, UploadFile, File, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import models, database

# إنشاء جداول SQLAlchemy تلقائياً
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# ربط مجلد الواجهات والمستندات
templates = Jinja2Templates(directory="templates")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ==========================================
# 📌 قائمة الأنشطة المباشرة من الكود
# تقدر تضيف أو تعدل أو تمسح أي ورشة من هنا مباشرة!
# ==========================================
ACTIVITIES_LIST = [
    {"id": 1, "title": "ورشة الذكاء الاصطناعي"},
    {"id": 2, "title": "دورة برمجة C++"},
    {"id": 3, "title": "ورشة الأجهزة الذكية والـ IoT"},
    {"id": 4, "title": "ورشة شبكات الحاسوب"}
]


# 1. واجهة الطالب (تقرأ القائمة المباشرة من الكود فوراً)
@app.get("/student")
def get_student_ui(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "activities": ACTIVITIES_LIST
    })


# 2. استقبال الشهادة المرفوعة من الطالب
@app.post("/api/submit")
async def submit_certificate(
    student_id: int = Form(...),
    activity_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    file_location = f"uploads/{student_id}_{activity_id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    new_submission = models.Submission(
        student_id=student_id,
        activity_id=activity_id,
        certificate_path=file_location,
        status="pending"
    )
    db.add(new_submission)
    db.commit()
    
    return {"message": "تم رفع الشهادة بنجاح، وهي قيد المراجعة من رئيسة القسم!"}


# 3. واجهة رئيسة القسم/الأدمن لمراجعة الطلبات والاعتماد
@app.get("/admin", response_class=HTMLResponse)
async def get_admin_ui(request: Request, db: Session = Depends(database.get_db)):
    submissions = db.query(models.Submission).all()
    return templates.TemplateResponse("admin.html", {"request": request, "submissions": submissions})


# 4. زر موافقة الأدمن مع منح الدرجة للطالب
@app.post("/api/approve")
async def approve_submission(
    submission_id: int = Form(...),
    points: int = Form(...),
    db: Session = Depends(database.get_db)
):
    sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if sub:
        sub.status = "approved"
        sub.points = points
        db.commit()
        return {"message": f"تمت الموافقة وإضافة {points} درجات بنجاح!"}
    return JSONResponse(status_code=404, content={"message": "الطلب غير موجود"})


# 5. API لجلب قائمة الأنشطة كـ JSON
@app.get("/api/activities")
def get_activities():
    return ACTIVITIES_LIST
