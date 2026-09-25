from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

import cloudinary.uploader

from app import cloudinary_config
from app.dependencies import CurrentUser, DbSession
from app.limiter import limiter
from app.schemas import UserResponse


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me", response_model=UserResponse)
@limiter.limit("10/minute")
def read_current_user(
    request: Request,
    current_user: CurrentUser,
):
    return current_user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
):
    allowed_types = {"image/jpeg", "image/png", "image/webp"}

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG and WEBP images are allowed",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty",
        )

    result = cloudinary.uploader.upload(
        contents,
        folder="contacts/avatars",
        resource_type="image",
    )

    current_user.avatar = result["secure_url"]
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user