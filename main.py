from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import weaviate
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Weaviate client setup
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
client = weaviate.Client(WEAVIATE_URL)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password hashing utility
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Signup endpoint
@app.post("/signup")
def signup(user: UserCreate):
    # Check if user already exists
    existing_user = client.query.get("User", ["username"]).where("username", "==", user.username).do()
    if existing_user.get("data", {}).get("Get", {}).get("User"):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash password
    hashed_password = hash_password(user.password)

    # Save user to Weaviate
    user_data = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password
    }
    client.data_object.create(user_data, "User")

    return {"message": "User created successfully"}

# Login endpoint
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Fetch user from Weaviate
    user_data = client.query.get("User", ["username", "hashed_password"]).where("username", "==", form_data.username).do()
    user = user_data.get("data", {}).get("Get", {}).get("User", [{}])[0]

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create JWT token
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Create post endpoint
@app.post("/posts")
def create_post(post: PostCreate, token: str = Depends(oauth2_scheme)):
    # Verify token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Save post to Weaviate
    post_data = {
        "title": post.title,
        "content": post.content,
        "author": payload["sub"]
    }
    client.data_object.create(post_data, "Post")

    return {"message": "Post created successfully"}

# Get posts endpoint
@app.get("/posts")
def get_posts():
    posts = client.query.get("Post", ["title", "content", "author"]).do()
    return posts.get("data", {}).get("Get", {}).get("Post", [])
