from fastapi import FastAPI, Query, Path, Depends
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import Float, create_engine, text, Column, Integer, String, Boolean, DateTime
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime
from typing import Optional
app=FastAPI()

# 세션 -> 작업을 묶어서 처리(트랜잭션)
# 변경사항(dml)모아둬서 commit할 때 한번에 실행 -> DB부하 少
# DB연결관리도 세션이 커넥션 가져오고, 끝나면 반환함 -> 직접 관리 안해도 됨
DATABASE_CONN = "mysql+mysqlconnector://root:1234@127.0.0.1:3306/board"

engine=create_engine(DATABASE_CONN, poolclass=QueuePool)

#sqlalchemy에서 모델 정의할 때 상속받는 기본 클래스
Base=declarative_base()

#테이블 생성 시 sqlalchemy가 정보 사용가능
class Items(Base):
    __tablename__="items"
    #정수, 기본키, auto increate
    id=Column(Integer,primary_key=True, autoincrement=True)
    #최대 50자,unique, nullable=False
    name=Column(String(50), nullable=False)
    #실수,  nullable=false
    price=Column(Float, nullable=False)
    #정수
    quantity=Column(Integer, nullable=False)

#pydantic 모델링
#클라이언트가 보내는 JSON검증
class ItemCreate(BaseModel):
    name:str=Field(..., min_length=3, max_length=50, pattern='^[a-zA-Z0-9]+$')
    price:float=Field(..., gt=0)
    quantity:int=Field(..., ge=0, le=100)


#DB 세션 관리
def get_con():
    db=Session(bind=engine) #db 세션 생성
    try:
        yield db #db내보낸
    finally:
        db.close()

Base.metadata.create_all(bind=engine)


# item 추가작업(C)
@app.post("/items")
def create_item(item:ItemCreate, db:Session=Depends(get_con)):
    #db에 추가
    add_item=Items(name=item.name, price=item.price, quantity=item.quantity)
    db.add(add_item) #세션에 객체 추가
    db.commit() #실제 반영
    db.refresh(add_item) #생성된 정보를 갱신

    return {"id":add_item.id, "name":add_item.name, "price":add_item.price, "quantity":add_item.quantity}

#학생 조회(R)
@app.get("/items/{item_id}")
def read_item(item_id:int, db:Session=Depends(get_con)):
    #student테이블에서 데이터 조회
    db_item=db.query(Items).filter(Items.id == item_id).first()
    if db_item is None:
        return {"error":"Student Not Found"}
    return {"id": db_item.id, "name":db_item.name, "price":db_item.price, "quantity":db_item.quantity}

#학생 수정(U)
# @app.put("/items")
# def update_stu(item_id:int, itemUpdate:ItemUpdate, db:Session=Depends(get_con)):

#     db_stu=db.query(Item).filter(Item.id == item_id).first()
#     if db_stu is None:
#         return {"error":"Student Not Found"}
    
#     #stu_name이 있으면 수정한 stu_name을 db에 넣기
#     if stuUpdate.stu_name is not None:
#         db_stu.stu_name=stuUpdate.stu_name

#     if stuUpdate.email is not None:
#         db_stu.email=stuUpdate.email

#     db.commit()
#     db.refresh(db_stu) #객체의 최신상태 반영
#     return {"id": db_stu.id, "stu_name":db_stu.stu_name, "email":db_stu.email}

# #학생 삭제(D)
# @app.delete("/students/{stu_id}")
# def delete_stu(stu_id:int, db:Session=Depends(get_con)):
#     db_stu=db.query(Student).filter(Student.id == stu_id).first()
#     if db_stu is None:
#         return {"error":"Student Not Found"}
    
#     db.delete(db_stu)
#     db.commit()
#     return {"ok":True}