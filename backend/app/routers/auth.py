from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from app import database, models, schemas, auth_utils, config
from app.dependencies import get_db

router = APIRouter()

# ========== 注册接口 ==========

@router.post("/register/student", response_model=schemas.Student)
def register_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    """学生注册"""
    db_student = db.query(models.Student).filter(models.Student.student_id == student.student_id).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Student ID already registered")
    hashed_password = auth_utils.get_password_hash(student.password)
    db_student = models.Student(
        student_id=student.student_id,
        name=student.name,
        password=hashed_password,
        class_name=student.class_name
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@router.post("/register/teacher", response_model=schemas.Teacher)
def register_teacher(teacher: schemas.TeacherCreate, db: Session = Depends(get_db)):
    """教师注册，如果班级和学生班级相同则自动绑定关系"""
    db_teacher = db.query(models.Teacher).filter(models.Teacher.email == teacher.email).first()
    if db_teacher:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth_utils.get_password_hash(teacher.password)
    db_teacher = models.Teacher(
        email=teacher.email,
        password=hashed_password,
        class_name=teacher.class_name
    )
    db.add(db_teacher)
    db.flush()  # 获取teacher.id
    
    # 如果指定了班级，查找相同班级的学生并建立关系
    if teacher.class_name:
        students = db.query(models.Student).filter(models.Student.class_name == teacher.class_name).all()
        for student in students:
            student_teacher = models.StudentTeacher(
                student_id=student.student_id,
                teacher_id=db_teacher.id
            )
            db.add(student_teacher)
    
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

@router.post("/register/parent", response_model=schemas.Parent)
def register_parent(parent: schemas.ParentCreate, db: Session = Depends(get_db)):
    """家长注册，需要指定关联的学生学号"""
    db_parent = db.query(models.Parent).filter(models.Parent.phone == parent.phone).first()
    if db_parent:
        raise HTTPException(status_code=400, detail="Phone already registered")
    
    # 检查学生是否存在
    student = db.query(models.Student).filter(models.Student.student_id == parent.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    hashed_password = auth_utils.get_password_hash(parent.password)
    db_parent = models.Parent(
        phone=parent.phone,
        password=hashed_password
    )
    db.add(db_parent)
    db.flush()  # 获取parent.id
    
    # 建立学生-家长关系
    student_parent = models.StudentParent(
        student_id=parent.student_id,
        parent_id=db_parent.id
    )
    db.add(student_parent)
    
    db.commit()
    db.refresh(db_parent)
    return db_parent

@router.post("/register/admin", response_model=schemas.Admin)
def register_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    """管理员注册"""
    db_admin = db.query(models.Admin).filter(models.Admin.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth_utils.get_password_hash(admin.password)
    db_admin = models.Admin(
        username=admin.username,
        password=hashed_password,
        name=admin.name
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

# ========== 登录接口 ==========

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db),
    user_type: Optional[str] = Query(None, description="用户类型：student, teacher, parent, admin")
):
    """统一登录接口，支持学生、教师、家长、管理员四种身份
    如果指定了user_type，只验证对应的身份；否则依次尝试所有身份"""
    username = form_data.username
    password = form_data.password
    
    # 验证输入不为空
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 如果指定了user_type，只验证对应的身份；否则依次尝试所有身份（向后兼容）
    if user_type == "student":
        # 只验证学生身份
        student = db.query(models.Student).filter(models.Student.student_id == username).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Student not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            if auth_utils.verify_password(password, student.password):
                access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = auth_utils.create_access_token(
                    data={"sub": student.student_id, "user_type": "student"}, 
                    expires_delta=access_token_expires
                )
                return {"access_token": access_token, "token_type": "bearer"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error verifying student password: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect student ID or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    elif user_type == "teacher":
        # 只验证教师身份
        teacher = db.query(models.Teacher).filter(models.Teacher.email == username).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Teacher not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            if auth_utils.verify_password(password, teacher.password):
                access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = auth_utils.create_access_token(
                    data={"sub": str(teacher.id), "user_type": "teacher"}, 
                    expires_delta=access_token_expires
                )
                return {"access_token": access_token, "token_type": "bearer"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error verifying teacher password: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    elif user_type == "parent":
        # 只验证家长身份
        parent = db.query(models.Parent).filter(models.Parent.phone == username).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Parent not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            if auth_utils.verify_password(password, parent.password):
                access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = auth_utils.create_access_token(
                    data={"sub": str(parent.id), "user_type": "parent"}, 
                    expires_delta=access_token_expires
                )
                return {"access_token": access_token, "token_type": "bearer"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error verifying parent password: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect phone or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    elif user_type == "admin":
        # 只验证管理员身份
        admin = db.query(models.Admin).filter(models.Admin.username == username).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            if auth_utils.verify_password(password, admin.password):
                access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = auth_utils.create_access_token(
                    data={"sub": str(admin.id), "user_type": "admin"}, 
                    expires_delta=access_token_expires
                )
                return {"access_token": access_token, "token_type": "bearer"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error verifying admin password: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    else:
        # 没有指定user_type，依次尝试所有身份（向后兼容）
        # 尝试学生登录（username是student_id）
        student = db.query(models.Student).filter(models.Student.student_id == username).first()
        if student:
            try:
                if auth_utils.verify_password(password, student.password):
                    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                    access_token = auth_utils.create_access_token(
                        data={"sub": student.student_id, "user_type": "student"}, 
                        expires_delta=access_token_expires
                    )
                    return {"access_token": access_token, "token_type": "bearer"}
            except Exception as e:
                print(f"Error verifying student password: {e}")
        
        # 尝试教师登录（username是email）
        teacher = db.query(models.Teacher).filter(models.Teacher.email == username).first()
        if teacher:
            try:
                if auth_utils.verify_password(password, teacher.password):
                    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                    access_token = auth_utils.create_access_token(
                        data={"sub": str(teacher.id), "user_type": "teacher"}, 
                        expires_delta=access_token_expires
                    )
                    return {"access_token": access_token, "token_type": "bearer"}
            except Exception as e:
                print(f"Error verifying teacher password: {e}")
        
        # 尝试家长登录（username是phone）
        parent = db.query(models.Parent).filter(models.Parent.phone == username).first()
        if parent:
            try:
                if auth_utils.verify_password(password, parent.password):
                    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                    access_token = auth_utils.create_access_token(
                        data={"sub": str(parent.id), "user_type": "parent"}, 
                        expires_delta=access_token_expires
                    )
                    return {"access_token": access_token, "token_type": "bearer"}
            except Exception as e:
                print(f"Error verifying parent password: {e}")
        
        # 尝试管理员登录（username是admin username）
        admin = db.query(models.Admin).filter(models.Admin.username == username).first()
        if admin:
            try:
                if auth_utils.verify_password(password, admin.password):
                    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                    access_token = auth_utils.create_access_token(
                        data={"sub": str(admin.id), "user_type": "admin"}, 
                        expires_delta=access_token_expires
                    )
                    return {"access_token": access_token, "token_type": "bearer"}
            except Exception as e:
                print(f"Error verifying admin password: {e}")
        
        # 所有尝试都失败
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
