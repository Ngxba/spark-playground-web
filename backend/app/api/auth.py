"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models.user import User
from ..models.auth_schemas import (
    UserSignUpRequest,
    UserSignInRequest,
    TokenResponse,
    UserResponse,
    ErrorResponse
)
from ..utils.security import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Email or username already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def sign_up(user_data: UserSignUpRequest, db: Session = Depends(get_db)):
    """
    Register a new user

    Creates a new user account with hashed password (using bcrypt with automatic salt).

    - **username**: Unique username (3-50 characters, alphanumeric with _ and -)
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 6 characters)

    Returns JWT token and user information
    """
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Hash password with bcrypt (automatic salt generation)
    hashed_password = get_password_hash(user_data.password)

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,
        last_login=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create JWT token
    access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})

    # Return token and user data
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post(
    "/signin",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    }
)
async def sign_in(credentials: UserSignInRequest, db: Session = Depends(get_db)):
    """
    Sign in an existing user

    Authenticates user with email and password, returns JWT token.

    - **email**: User's email address
    - **password**: User's password

    Password is securely verified against bcrypt hash stored in database.
    Returns JWT token and user information on successful authentication.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Return token and user data
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    }
)
async def get_current_user(token: str, db: Session = Depends(get_db)):
    """
    Get current authenticated user

    Requires valid JWT token in Authorization header or query parameter.
    Returns user information for the authenticated user.
    """
    from ..utils.security import decode_access_token

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return UserResponse.model_validate(user)
