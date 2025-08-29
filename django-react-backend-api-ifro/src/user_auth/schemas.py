from ninja import Schema, Field
from ninja.errors import HttpError
import re

class RegisterSchema(Schema):
    username: str = Field(..., min_length=4, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(..., description="email address")
    name: str = Field(..., min_length=2, max_length=100, description="name")
    admin_code: str = Field("", description="admin code(Optional)")

    @classmethod
    def validate_username(cls, value: str):
        if not re.match(r'^[a-zA-Z0-9]+$', value):
            raise HttpError(422, "Username must contain only letters and numbers.")
        return value

    @classmethod
    def validate_password(cls, value: str):
        if len(value) < 8:
            raise HttpError(422, "Password must be at least 8 characters long.")
        return value

    @classmethod
    def validate_email(cls, value: str):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise HttpError(422, "Invalid email format.")
        return value

class LoginSchema(Schema):
    username: str
    password: str

class UserResponseSchema(Schema):
    id: int
    username: str
    email: str
    name: str
    role: str
    created_at: str

class AdminCodeSchema(Schema):
    code: str
    description: str
    is_active: bool
    max_uses: int
    current_uses: int
    expires_at: str = None

class UserUpdateSchema(Schema):
    name: str = Field(..., min_length=2, max_length=100, description="name")
    email: str = Field(..., description="email address")

class PasswordChangeSchema(Schema):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128) 