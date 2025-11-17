"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from backend.app.core.config import settings
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from backend.app.core.database import get_database
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from backend.app.models.user import UserModel

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_doc = UserModel.create(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_admin=user_data.is_admin,
    )
    
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_doc["_id"], "email": user_doc["email"]}
    )
    
    # Remove password from response
    user_doc.pop("hashed_password", None)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**UserModel.serialize(user_doc))
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password"""
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"email": form_data.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "email": user["email"]}
    )
    
    # Remove password from response
    user.pop("hashed_password", None)
    user["_id"] = str(user["_id"])
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**UserModel.serialize(user))
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    db = get_database()
    from bson import ObjectId
    
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.pop("hashed_password", None)
    return UserResponse(**UserModel.serialize(user))
