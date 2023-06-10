from fastapi import APIRouter, WebSocket, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from typing import List
from pydantic import BaseModel, EmailStr, constr
import uuid

router = APIRouter()

client = MongoClient("mongodb://localhost:27017/")
db = client["TODOList"]
users = db["users"]
todos = db["todos"]


class ShareTodo(BaseModel):
    todo_id: str
    shared_with: List[str]


class User(BaseModel):
    token: str


async def get_current_user(token: str):
    user = users.find_one({"access_token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user["username"]


@router.post("/todo_share/{todo_id}")
async def share_todo(todo_id: str, share: ShareTodo, token: User):
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    current_user = await get_current_user(token)
    todo = todos.find_one({"_id": ObjectId(todo_id)})
    if not todo:
        raise HTTPException(status_code=404, detail="TODO not found")
    if todo["token"] != "":
        raise HTTPException(status_code=403, detail="TODO is already shared")
    shared_with = share.shared_with
    if not shared_with:
        raise HTTPException(status_code=400, detail="Shared with list can't be empty")
    shared_by = current_user
    todos.update_one({"_id": ObjectId(todo_id)}, {"$set": {"token": str(uuid.uuid4())}})
    for shared_user in shared_with:
        share_user = users.find_one({"username": shared_user})
        if not share_user:
            raise HTTPException(status_code=404, detail="User not found")
        shared_todo = {
            "todo_id": todo_id,
            "shared_by": shared_by,
        }
        shared_todos = share_user.get("shared_todos", [])
        shared_todos.append(shared_todo)
        users.update_one({"_id": share_user["_id"]}, {"$set": {"shared_todos": shared_todos}})
        await send_shared_todo_notification(share_user["access_token"], shared_todo)
    return {"detail": "TODO shared successfully"}


async def send_shared_todo_notification(token: str, shared_todo: dict):
    async with WebSocket(url=f"ws://{token}") as ws:
        await ws.send_json(shared_todo)
        await ws.close()
