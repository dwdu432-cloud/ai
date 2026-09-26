import os
import shutil
import sqlite3
from fastapi import FastAPI, Depends, UploadFile, File, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import models, database

# إنشاء جداول SQLAlchemy تلقائياً عند التشغيل
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# ربط مجلد الواجهات والمستندات
templates = Jinja2Templates(directory="templates")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --- إعداد قاعدة بيانات SQLite للأنشطة والورش ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        )
    ''')
    
    # إضافة ورشات افتراضية إذا كانت قاعدة البيانات فارغة
    cursor.execute("SELECT COUNT(*) FROM activities")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO activities (title) VALUES ('ورشة الذكاء الاصطناعي')")
        cursor.execute("INSERT INTO activities (title) VALUES ('دورة برمجة C++')")
        cursor.execute("INSERT INTO activities (title) VALUES ('ورشة الأجهزة الذكية والـ IoT')")
        conn.commit()
        
    conn.close()

# تشغيل التهيئة تلقائياً
init_db()


# 1. واجهة الطالب (جلب الورش مباشرة من قاعدة البيانات)
@app.get("/student")
def get_student_ui(request: Request):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM activities")
    rows = cursor.fetchall()
    conn.close()
    
    # تحويل البيانات إلى قائمة يفهمها قالب Jinja2
    activities = [{"id": row[0], "title": row[1]} for row in rows]
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "activities": activities
    })


# 2. استقبال الشهادة المرفوعة من الطالب
@app.post("/api/submit")
async def submit_certificate(
    student_id: int = Form(...),
    activity_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    # حفظ صورة الشهادة في مجلد uploads
    file_location = f"uploads/{student_id}_{activity_id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # حفظ طلب الشهادة في قاعدة البيانات
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


# 5. API لجلب الأنشطة كـ JSON
@app.get("/api/activities")
def get_activities():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM activities")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1]} for row in rows]


# 6. API لإضافة نشاط جديد إلى قاعدة البيانات
@app.post("/api/activities")
def add_activity(title: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO activities (title) VALUES (?)", (title,))
    conn.commit()
    conn.close()
    return {"message": "تم حفظ النشاط بنجاح في قاعدة البيانات!"}
