from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

router=APIRouter(prefix="/item",tags=["item"])

class Item(BaseModel):
    name:str
    desc:str=None

@router.get("/{item_id}")
def read_item(item_id:int):
    return {"item_id":item_id}

@router.post("/")
def create_item(item:Item):
    return item

