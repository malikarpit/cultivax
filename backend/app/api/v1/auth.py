"""
Auth API

User registration and login endpoints.
POST /api/v1/auth/register
POST /api/v1/auth/login
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.security.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return JWT token."""

    # Check if phone already exists
    existing = db.query(User).filter(User.phone == user_data.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered",
        )

    # Check email uniqueness if provided
    if user_data.email:
        email_exists = db.query(User).filter(User.email == user_data.email).first()
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    # Validate role
    valid_roles = ["farmer", "provider", "admin"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role. Must be one of: {valid_roles}",
        )

    # Create user
    user = User(
        full_name=user_data.full_name,
        phone=user_data.phone,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        region=user_data.region,
        preferred_language=user_data.preferred_language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""

    user = db.query(User).filter(
        User.phone == credentials.phone,
        User.is_deleted == False,
    ).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact admin.",
        )

    token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )
