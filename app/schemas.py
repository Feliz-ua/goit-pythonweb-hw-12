"""Pydantic schemas used by the Contacts REST API."""

from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload used to register a new user."""
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Public representation of a user."""
    id: int
    username: str
    email: EmailStr
    avatar: str | None = None
    confirmed: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ContactBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(min_length=1, max_length=30)
    birthday: date
    additional_data: str | None = Field(default=None, max_length=500)
    is_favorite: bool = False

    """Base class for contact schemas."""

class ContactCreate(ContactBase):
    """Payload used to create a contact."""
    pass


class ContactUpdate(ContactBase):
    """Payload used to update a contact."""
    pass


class ContactResponse(ContactBase):
    """Public representation of a contact."""
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
    
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str | None = None
    confirmed: bool
    role: str

    model_config = ConfigDict(from_attributes=True)
