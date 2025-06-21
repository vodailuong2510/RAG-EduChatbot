import os
import jwt
import secrets
import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta
class Auth:
    def __init__(self):

        self.github_client_id = os.getenv("GITHUB_CLIENT_ID", "")
        self.github_client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
        self.facebook_client_id = os.getenv("FACEBOOK_CLIENT_ID", "")
        self.facebook_client_secret = os.getenv("FACEBOOK_CLIENT_SECRET", "")
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.jwt_secret = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = 24  # hours
    
    def github_login_url(self, redirect_uri):
        """Generate GitHub OAuth login URL"""
        params = {
            "client_id": self.github_client_id,
            "redirect_uri": redirect_uri,
            "scope": "user:email",
            "state": secrets.token_urlsafe(16)
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    async def github_callback(self, code, redirect_uri):
        """Handle GitHub OAuth callback"""
        # Exchange code for access token
        token_url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": self.github_client_id,
            "client_secret": self.github_client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        headers = {"Accept": "application/json"}
        
        response = requests.post(token_url, json=payload, headers=headers)
        response.raise_for_status()
        access_token = response.json().get("access_token")
        
        # Get user info
        user_url = "https://api.github.com/user"
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json"
        }
        response = requests.get(user_url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        
        # Get email if not public
        if not user_data.get("email"):
            email_url = "https://api.github.com/user/emails"
            response = requests.get(email_url, headers=headers)
            response.raise_for_status()
            emails = response.json()
            primary_email = next((e for e in emails if e.get("primary")), emails[0] if emails else {})
            user_data["email"] = primary_email.get("email", "")
        
        return {
            "id": user_data.get("id"),
            "name": user_data.get("name") or user_data.get("login"),
            "email": user_data.get("email"),
            "avatar": user_data.get("avatar_url"),
            "provider": "github"
        }
    
    def google_login_url(self, redirect_uri):
        """Generate Google OAuth login URL"""
        params = {
            "client_id": self.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
            "access_type": "offline",
            "state": secrets.token_urlsafe(16)
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    async def google_callback(self, code, redirect_uri):
        """Handle Google OAuth callback"""
        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": self.google_client_id,
            "client_secret": self.google_client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        tokens = response.json()
        access_token = tokens.get("access_token")
        
        # Get user info
        user_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(user_url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        
        return {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "avatar": user_data.get("picture"),
            "provider": "google"
        }
    
    def facebook_login_url(self, redirect_uri):
        """Generate Facebook OAuth login URL"""
        params = {
            "client_id": self.facebook_client_id,
            "redirect_uri": redirect_uri,
            "scope": "email",
            "state": secrets.token_urlsafe(16)
        }
        return f"https://www.facebook.com/v12.0/dialog/oauth?{urlencode(params)}"
    
    async def facebook_callback(self, code, redirect_uri):
        """Handle Facebook OAuth callback"""
        # Exchange code for access token
        token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
        params = {
            "client_id": self.facebook_client_id,
            "client_secret": self.facebook_client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        response = requests.get(token_url, params=params)
        response.raise_for_status()
        access_token = response.json().get("access_token")
        
        # Get user info
        user_url = "https://graph.facebook.com/me"
        params = {
            "fields": "id,name,email,picture.type(large)",
            "access_token": access_token
        }
        response = requests.get(user_url, params=params)
        response.raise_for_status()
        user_data = response.json()
        
        return {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "avatar": user_data.get("picture", {}).get("data", {}).get("url", ""),
            "provider": "facebook"
        }

    def create_token(self, user_data: dict) -> str:
        """Create a JWT token for the user"""
        expiration = datetime.now() + timedelta(hours=self.jwt_expiration)
        payload = {
            "id": str(user_data["id"]),
            "name": user_data["name"],
            "email": user_data["email"],
            "avatar": user_data["avatar"],
            "provider": user_data["provider"],
            "exp": expiration.timestamp()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            print("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Token verification failed: {str(e)}")
            return None
