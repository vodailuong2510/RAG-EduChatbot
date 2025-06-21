import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

import uvicorn
import requests
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, BackgroundTasks, Depends, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse, RedirectResponse
from auth_routes import router as auth_router, get_current_user
from admin_routes import admin as admin_router

from chat.response import gpt_chat, generate_chat_title
from database.mongodb import (
    get_mongo_collection, save_message, 
    create_new_chat, get_user_chats, 
    get_messages, delete_chat as delete_chat_db,
    update_chat_title, get_chat_by_id
)

MONGO_URI = os.getenv("MONGO_URI")
CHAT_PATH = r"./templates/chat.html"
LOGIN_PATH = r"./templates/login.html"
TERMS_PATH = r"./templates/terms.html"
PRIVACY_PATH = r"./templates/privacy.html"
ADMIN_PATH = r"./templates/admin.html"
ACCOUNT_PATH = r"./templates/account.html"
mongo_collections = get_mongo_collection(MONGO_URI)

app = FastAPI()
app.include_router(auth_router)
app.include_router(admin_router)
app.mount("/static", StaticFiles(directory="./static"), name="static")

class MessageRequest(BaseModel):
    message: str
    chat_id: str | None = None
    user_id: str = None

class NewChatRequest(BaseModel):
    title: str | None = None

@app.get("/login")
async def login_page():
    return FileResponse(LOGIN_PATH, media_type="text/html", status_code=200)
@app.get("/chat")
async def chat_page(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return FileResponse(CHAT_PATH, media_type="text/html", status_code=200)
@app.get("/terms")
async def terms_page():
    return FileResponse(TERMS_PATH, media_type="text/html", status_code=200)
@app.get("/privacy")
async def privacy_page():
    return FileResponse(PRIVACY_PATH, media_type="text/html", status_code=200)
@app.get("/admin")
async def admin_page(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return FileResponse(ADMIN_PATH, media_type="text/html", status_code=200)
@app.get("/account")
async def account_page(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return FileResponse(ACCOUNT_PATH, media_type="text/html", status_code=200)

@app.get("/")
async def root_redirect(current_user: dict = Depends(get_current_user)):
    if current_user:
        return RedirectResponse(url="/chat")
    return RedirectResponse(url="/login")
@app.get("/login-redirect")
async def login_page(current_user: dict = Depends(get_current_user)):
    if current_user:
        return RedirectResponse(url="/chat")
    return RedirectResponse(url="/login")
@app.get("/chat-redirect")
async def chat_page(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/chat")
@app.get("/terms-redirect")
async def terms_page():
    return RedirectResponse(url="/terms")
@app.get("/privacy-redirect")
async def privacy_page():
    return RedirectResponse(url="/privacy")
@app.get("/admin-redirect")
async def admin_redirect(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/admin")
@app.get("/account-redirect")
async def account_redirect(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/account")

@app.post("/chats/new")
async def create_chat(
    request: NewChatRequest,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    chat_id = create_new_chat(mongo_collections, current_user, "Đoạn chat mới")
    return JSONResponse(content={"chat_id": chat_id})

@app.get("/chats")
async def get_chats(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    chats = get_user_chats(mongo_collections, current_user)
    return JSONResponse(content=chats)

@app.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    messages = get_messages(mongo_collections, current_user, chat_id, limit=10)
    return JSONResponse(content=messages)

@app.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    deleted_count = delete_chat_db(mongo_collections, current_user, chat_id)
    return JSONResponse(content={"message": f"Deleted {deleted_count} messages"})

async def generate_title_for_chat(chat_id, current_user, chat_history):
    current_chat = get_chat_by_id(mongo_collections, current_user, chat_id)
    
    if current_chat and current_chat.get("title") != "Đoạn chat mới" and "New Chat" not in current_chat.get("title", ""):
        return current_chat.get("title")
        
    if len(chat_history) >= 2:
        first_messages = chat_history[:2]
        title = await generate_chat_title(first_messages)
        update_chat_title(mongo_collections, current_user, chat_id, title)
        return title
    return None

@app.post("/chat")
async def chat(
    request: MessageRequest, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    prompt = request.message
    chat_id = request.chat_id
    
    if not chat_id:
        chat_id = create_new_chat(mongo_collections, current_user, "Đoạn chat mới")
    
    chat_history = get_messages(mongo_collections, current_user, chat_id, limit=10)
    
    response = []
    async def response_generator():
        async for chunk in gpt_chat(prompt, chat_history):
            response.append(chunk)
            yield chunk 
    
    async def save_response_and_generate_title():
        full_response = "".join(response)
        save_message(mongo_collections, current_user, chat_id, "user", prompt)
        save_message(mongo_collections, current_user, chat_id, "assistant", full_response)
        
        updated_history = get_messages(mongo_collections, current_user, chat_id, limit=10)
        
        current_chat = get_chat_by_id(mongo_collections, current_user, chat_id)
        if current_chat and (current_chat.get("title") == "Đoạn chat mới" or "New Chat" in current_chat.get("title", "")):
            if len(updated_history) == 4:
                await generate_title_for_chat(chat_id, current_user, updated_history)

    background_tasks.add_task(save_response_and_generate_title)

    # Tạo response với chat_id trong header
    response_stream = StreamingResponse(response_generator(), media_type="text/plain")
    response_stream.headers["X-Chat-ID"] = chat_id
    
    return response_stream

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    status_code = 500
    if isinstance(exc, requests.HTTPError) and hasattr(exc, 'response'):
        status_code = exc.response.status_code
    
    return JSONResponse(
        status_code=status_code,
        content={"message": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run('server:app', host="0.0.0.0", port=8000, reload=True, log_level="info") 