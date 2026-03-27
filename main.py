from fastapi import FastAPI, Query, Path, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import create_engine, ForeignKey, text, Column, Integer, String, Boolean, DateTime
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
import datetime

app=FastAPI()

#DB연결
DATABASE_CONN = "mysql+mysqlconnector://root:1234@127.0.0.1:3306/board"
engine=create_engine(DATABASE_CONN, poolclass=QueuePool)
Base=declarative_base()



#DB모델링
class Student(Base):
    __tablename__="student"
    id=Column(Integer,primary_key=True, autoincrement=True)
    name=Column(String(20), nullable=False)
    age=Column(Integer, nullable=False)

class Course(Base):
    __tablename__="course"
    id=Column(Integer,primary_key=True, autoincrement=True)
    title=Column(String(30), nullable=False)
    student_id=Column(ForeignKey("student.id"), nullable=False)

#pydantic 모델링
#클라이언트가 보내는 JSON검증
class StudentCreate(BaseModel):
    name:str=Field(..., min_length=2, max_length=20)
    age:int=Field(..., ge=10, le=100)

class CourseCreate(BaseModel):
    title:str=Field(..., min_length=2, max_length=30)
    student_id:int=Field(..., gt=0)

#DB 세션 관리
def get_con():
    db=Session(bind=engine) 
    try:
        yield db 
    finally:
        db.close()

Base.metadata.create_all(bind=engine)


# 학생 추가작업(C)
@app.post("/students")
def create_stu(stu: StudentCreate, db: Session = Depends(get_con)):
    add_stu=Student(name=stu.name, age=stu.age)
    db.add(add_stu)
    db.commit()
    db.refresh(add_stu)

    return {"id": add_stu.id, "name": add_stu.name, "age": add_stu.age}

# 학생 전체 조회(R)
@app.get("/students")
def read_stus(age: int = Query(..., ge=0), db:Session=Depends(get_con)):
    #해당나이 이상 학생만 조회
    db_stus=db.query(Student).filter(Student.age >= age).all()
    return [{"id":stu.id, "name":stu.name, "age":stu.age} for stu in db_stus]


#특정 학생 조회(R)
@app.get("/student/{stu_id}")
def read_stu(stu_id:int, db:Session=Depends(get_con)):
    #student테이블에서 데이터 조회
    db_stu=db.query(Student).filter(Student.id == stu_id).first()
    if db_stu is None:
        return HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    return {"id": db_stu.id, "name":db_stu.name, "age":db_stu.age}


#학생 삭제(D)
@app.delete("/students/{stu_id}")
def delete_stu(stu_id:int, db:Session=Depends(get_con)):
    #학생데이터와 연관된 과목데이터도 삭제
    db_courses=db.query(Course).filter(Course.student_id == stu_id).all()
    for course in db_courses:
        db.delete(course)
    db_stu=db.query(Student).filter(Student.id == stu_id).first()
    if db_stu is None:
        return HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    db.delete(db_stu)
    db.commit()
    return {"msg":"삭제완료"}

#과목 생성(C)
@app.post("/courses")
def create_course(course: CourseCreate, db: Session = Depends(get_con)):
    #student_id가 존재하는지 확인
    db_stu=db.query(Student).filter(Student.id == course.student_id).first()
    if db_stu is None:
        return HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    add_course=Course(title=course.title, student_id=course.student_id)
    db.add(add_course)
    db.commit()
    db.refresh(add_course)

    return {"id": add_course.id, "title": add_course.title, "student_id": add_course.student_id}

#전체과목조회(R)
@app.get("/courses")
def read_courses(title: str = Query(None), db:Session=Depends(get_con)):
    if title:
        db_courses=db.query(Course).filter(Course.title.contains(title)).all()
    else:
        db_courses=db.query(Course).all()
    return [{"id":course.id, "title":course.title, "student_id":course.student_id} for course in db_courses]

#특정 학생의 과목 조회
@app.get("/students/{id}/courses")
def read_stu_courses(id:int, db:Session=Depends(get_con)):
    db_stu=db.query(Student).filter(Student.id == id).first()
    if db_stu is None:
        return HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    db_courses=db.query(Course).filter(Course.student_id == id).all()
    return [{"student_name": db_stu.name,"courses":[{"id": course.id, "title": course.title,"student_id": course.student_id} for course in db_courses]}]

#과목 삭제
@app.delete("/courses/{course_id}")
def delete_course(course_id:int, db:Session=Depends(get_con)):
    db_course=db.query(Course).filter(Course.id == course_id).first()
    if db_course is None:
        return HTTPException(status_code=404, detail="과목을 찾을 수 없습니다.")
    db.delete(db_course)
    db.commit()
    return {"msg":"삭제완료"}

#특정 학생 과목 개수 조회
@app.get("/students/{id}/count")
def count_stu_courses(id:int, db:Session=Depends(get_con)):
    db_stu=db.query(Student).filter(Student.id == id).first()
    if db_stu is None:
        return HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")
    course_count=db.query(Course).filter(Course.student_id == id).count()
    return {"student_id": id, "course_count": course_count}