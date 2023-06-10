from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr, constr
from bson import ObjectId

router = APIRouter()

client = MongoClient("mongodb://localhost:27017/")
db = client["TODOList"]
todos = db["todos"]


class create_todo(BaseModel):
    title: str
    content: str

class update_todo(BaseModel):
    title: str 
    content: str 

@router.post("/todo_create")
async def create_todos(create:create_todo):
    todo = {
        "title": create.title,
        "content": create.content,
    }
    result = todos.insert_one(todo)
    return {
        "id": str(result.inserted_id),
        "title": todo["title"],
        "content": todo["content"],
    }

@router.get("/todo_read/{todo_id}")
async def read_todos(todo_id :str):
    todo = todos.find_one({"_id": ObjectId(todo_id)})
    if not todo:
        raise HTTPException(status_code=404, detail="TODO not found")
    return {
        "id": str(todo["_id"]),
        "title": todo["title"],
        "content": todo["content"],
    }


@router.put("/todo_update/{todo_id}")
async def update_todos(todo_id: str, update: update_todo):
    todo1 = todos.find_one({"_id": ObjectId(todo_id)})
    if not todo1:
        raise HTTPException(status_code=404, detail="TODO not found")
    todo = {
        "title": update.title,
        "content": update.content,
    }
    todos.replace_one({"_id": ObjectId(todo_id)}, todo)
    return {
        "id": str(todo1["_id"]),
        "title": todo["title"],
        "content": todo["content"],
    }

@router.delete("/todo_delete/{todo_id}")
async def delete_todos(todo_id : str):
    todo = todos.find_one({"_id": ObjectId(todo_id)})
    if not todo:
        raise HTTPException(status_code=404, detail="TODO not found")
    todos.delete_one({"_id": ObjectId(todo_id)})
    return {
        "id": str(todo["_id"]),
        "title": todo["title"],
        "content": todo["content"],
    }
