from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from app.services.user_service import UserService
from app.auth.security import create_access_token
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(tags=["Authentication & Authorization"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Patient self-registration endpoint.
    Creates a new PATIENT account and returns an access token.
    """
    existing_user = await UserService.get_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists.",
        )

    user = await UserService.create_user(
        db=db,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role=UserRole.PATIENT,
        phone=payload.phone,
    )

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    User login endpoint.
    Verifies credentials and returns a signed JWT access token.
    """
    user = await UserService.authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get profile information of currently authenticated user.
    """
    return UserResponse.model_validate(current_user)


@router.get("/patient-only", response_model=UserResponse)
async def patient_only_endpoint(
    current_user: User = Depends(require_roles(UserRole.PATIENT)),
):
    """Endpoint restricted exclusively to PATIENT role."""
    return UserResponse.model_validate(current_user)


@router.get("/doctor-only", response_model=UserResponse)
async def doctor_only_endpoint(
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
):
    """Endpoint restricted exclusively to DOCTOR role."""
    return UserResponse.model_validate(current_user)


@router.get("/admin-only", response_model=UserResponse)
async def admin_only_endpoint(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Endpoint restricted exclusively to ADMIN role."""
    return UserResponse.model_validate(current_user)
