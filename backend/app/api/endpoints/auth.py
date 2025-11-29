"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from datetime import timedelta, datetime
import uuid

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


@router.get("/test")
async def test():
    """Test endpoint"""
    return {"message": "Auth routes working!", "timestamp": str(datetime.utcnow())}


@router.post("/register-simple")
async def register_simple(email: str, password: str, full_name: str):
    """Simple registration without complex schemas"""
    try:
        print(f"Simple register: {email}")
        # Just create a user and return success
        user_id = "simple-" + email.split("@")[0]
        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "message": "Registration would work here"
        }
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.post("/register-test")
async def register_test(user_data: UserCreate):
    """Test registration without DB"""
    try:
        print(f"📝 Received data: {user_data}")
        hashed_pw = get_password_hash(user_data.password)
        print(f"🔐 Hashed password: {hashed_pw[:20]}...")
        
        user_doc = UserModel.create(
            email=user_data.email,
            hashed_password=hashed_pw,
            full_name=user_data.full_name,
            is_admin=False,
        )
        print(f"📄 User doc created: {user_doc}")
        
        user_doc["_id"] = "test-id-123"
        user_doc.pop("hashed_password")
        
        print(f"✅ Final user doc: {user_doc}")
        return {"success": True, "user": user_doc}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    print(f"📝 Registration request received: {user_data.email}")
    
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    hashed_password = get_password_hash(user_data.password)
    user_doc = UserModel.create(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_admin=False,
    )
    
    # Insert into MongoDB
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    user_doc["_id"] = user_id
    
    print(f"✅ User registered: {user_data.email} with ID: {user_id}")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_id, "email": user_doc["email"]}
    )
    
    # Remove password from response
    user_doc.pop("hashed_password", None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "_id": user_id,
            "email": user_doc["email"],
            "full_name": user_doc.get("full_name"),
            "is_active": user_doc.get("is_active", True),
            "is_admin": user_doc.get("is_admin", False),
            "created_at": user_doc["created_at"].isoformat()
        }
    }


@router.post("/login", response_model=Token)
async def login(email: str = Form(...), password: str = Form(...)):
    """Login with email and password"""
    
    db = get_database()
    
    # Find user in MongoDB
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
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
    
    print(f"✅ User logged in: {user['email']}")
    
    # Create access token
    user_id = str(user["_id"])
    access_token = create_access_token(
        data={"sub": user_id, "email": user["email"]}
    )
    
    # Remove password from response
    user.pop("hashed_password", None)
    
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
