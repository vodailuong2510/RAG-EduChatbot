import os
from fastapi import APIRouter, Depends, Cookie
from fastapi.responses import RedirectResponse, JSONResponse

from auth import Auth
from database.mongodb import get_mongo_collection, create_new_user

MONGO_URI = os.getenv("MONGO_URI")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

mongo_collections = get_mongo_collection(MONGO_URI)

auth = Auth()
router = APIRouter(prefix="/auth", tags=["Authentication"])

async def get_current_user(token: str = Cookie(None)):
    if not token:
        return None
    
    user_data = auth.verify_token(token)
    if not user_data:
        return None
    
    return user_data

@router.get("/me")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/github")
async def github_login():
    redirect_uri = f"{BASE_URL}/auth/github/callback"
    return RedirectResponse(url=auth.github_login_url(redirect_uri))

@router.get("/github/callback")
async def github_callback(code: str):
    redirect_uri = f"{BASE_URL}/auth/github/callback"
    try:
        user_data = await auth.github_callback(code, redirect_uri)
        user_data["provider"] = "github"
        create_new_user(mongo_collections, user_data)
        token = auth.create_token(user_data)
        response = RedirectResponse(url="/chat")
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            secure=True,
            max_age=86400,
            path="/",
            samesite="lax"
        )
        return response
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@router.get("/google")
async def google_login():
    redirect_uri = f"{BASE_URL}/auth/google/callback"
    return RedirectResponse(url=auth.google_login_url(redirect_uri))

@router.get("/google/callback")
async def google_callback(code: str):
    redirect_uri = f"{BASE_URL}/auth/google/callback"
    try:
        user_data = await auth.google_callback(code, redirect_uri)
        user_data["provider"] = "google"
        create_new_user(mongo_collections, user_data)
        token = auth.create_token(user_data)
        response = RedirectResponse(url="/chat")
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            secure=True,
            max_age=86400,
            path="/",
            samesite="lax"
        )
        return response
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@router.get("/facebook")
async def facebook_login():
    redirect_uri = f"{BASE_URL}/auth/facebook/callback"
    return RedirectResponse(url=auth.facebook_login_url(redirect_uri))

@router.get("/facebook/callback")
async def facebook_callback(code: str):
    redirect_uri = f"{BASE_URL}/auth/facebook/callback"
    try:
        user_data = await auth.facebook_callback(code, redirect_uri)
        user_data["provider"] = "facebook"
        create_new_user(mongo_collections, user_data)
        token = auth.create_token(user_data)
        response = RedirectResponse(url="/chat")
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            secure=True,
            max_age=86400,
            path="/",
            samesite="lax"
        )
        return response
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="token")
    return response 