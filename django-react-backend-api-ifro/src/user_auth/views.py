from django.shortcuts import render
from ninja_extra import Router
from django.contrib.auth import authenticate
from ninja_jwt.tokens import RefreshToken
from ninja.errors import HttpError
from user_auth.schemas import RegisterSchema, LoginSchema, UserResponseSchema, UserUpdateSchema, PasswordChangeSchema
from user_auth.models import User, AdminCode
from ninja_jwt.authentication import JWTAuth
import os
from python_encrypter import EncryptionManager
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

router = Router()

@router.post("/register", response=UserResponseSchema)
def register(request, data: RegisterSchema):
    RegisterSchema.validate_username(data.username)
    RegisterSchema.validate_password(data.password)
    RegisterSchema.validate_email(data.email)
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, _("This username is already taken."))
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, _("This email is already registered."))
    role = 'operator'
    admin_code_used = None
    if data.admin_code:
        # 모든 관리자 코드에서 검색
        try:
            admin_code = AdminCode.objects.get(code=data.admin_code)
            if admin_code.is_valid:
                admin_code.use_code()
                role = 'admin'
                admin_code_used = data.admin_code
            else:
                raise HttpError(400, _("Invalid or expired admin code."))
        except AdminCode.DoesNotExist:
            raise HttpError(400, _("Invalid admin code."))
    salt = os.urandom(16).hex()
    hashed_password = EncryptionManager.hash_string(data.password, salt=salt)
    user = User.objects.create(
        username=data.username,
        password=hashed_password,
        password_salt=salt,
        email=data.email,
        name=data.name,
        role=role,
        admin_code_used=admin_code_used,
        is_active=True,
    )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }

@router.post("/login")
def login(request, data: LoginSchema):
    try:
        user = User.objects.get(username=data.username)
    except User.DoesNotExist:
        raise HttpError(401, _("Invalid username or password."))
    hashed_input = EncryptionManager.hash_string(data.password, salt=user.password_salt)
    if hashed_input != user.password:
        raise HttpError(401, _("Invalid username or password."))
    refresh = RefreshToken.for_user(user)
    # 커스텀 claim 추가
    refresh['username'] = user.username
    refresh['name'] = user.name
    refresh['email'] = user.email
    refresh['role'] = user.role
    access = refresh.access_token
    access['username'] = user.username
    access['name'] = user.name
    access['email'] = user.email
    access['role'] = user.role
    return {
        "refresh": str(refresh),
        "access": str(access),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }

@router.patch("/user/me", auth=JWTAuth(), response=UserResponseSchema)
def update_me(request, data: UserUpdateSchema):
    user = request.auth
    user.name = data.name
    user.email = data.email
    user.save()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }

@router.patch("/user/me/password", auth=JWTAuth())
def change_password(request, data: PasswordChangeSchema):
    user = request.auth
    hashed_current = EncryptionManager.hash_string(data.current_password, salt=user.password_salt)
    if hashed_current != user.password:
        raise HttpError(400, _("Current password is incorrect."))
    new_salt = os.urandom(16).hex()
    new_hashed = EncryptionManager.hash_string(data.new_password, salt=new_salt)
    user.password = new_hashed
    user.password_salt = new_salt
    user.save()
    return {"msg": _("Password changed successfully.")}

@router.delete("/user/me", auth=JWTAuth())
def delete_me(request):
    user = request.auth
    user.delete()
    return {"msg": _("Account deleted successfully.")}
