import jwt
import bcrypt
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from typing import Optional, Type

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import (
    SECRET_KEY,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_TOKEN_PREFIX,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.token import JWTMeta, JWTCreds, JWTPayload
from app.models.user import UserPasswordUpdate, UserInDB, UserBase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthException(BaseException):
    """
    Custom auth exception that can be modified later on.
    """

    pass


class AuthService:
    def create_salt_and_hashed_password(
        self, *, plaintext_password: str
    ) -> UserPasswordUpdate:
        salt = self.generate_salt()
        hashed_password = self.hash_password(password=plaintext_password, salt=salt)

        return UserPasswordUpdate(salt=salt, password=hashed_password)

    def generate_salt(self) -> str:
        return bcrypt.gensalt().decode()

    def hash_password(self, *, password: str, salt: str) -> str:
        return pwd_context.hash(password + salt)

    def verify_password(self, *, password: str, salt: str, hashed_pw: str) -> bool:
        return pwd_context.verify(password + salt, hashed_pw)

    def create_access_token_for_user(
        self,
        *,
        user: Type[UserBase],
        secret_key: str = str(SECRET_KEY),
        audience: str = JWT_AUDIENCE,
        expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES,
    ) -> str:
        if not user or not isinstance(user, UserBase):
            return None

        jwt_meta = JWTMeta(
            aud=audience,
            iat=datetime.timestamp(datetime.now(timezone.utc)),
            exp=datetime.timestamp(
                datetime.now(timezone.utc) + timedelta(minutes=expires_in)
            ),
        )
        jwt_creds = JWTCreds(sub=user.email, username=user.username)
        token_payload = JWTPayload(
            **jwt_meta.dict(),
            **jwt_creds.dict(),
        )
        # NOTE - previous versions of pyjwt ("<2.0") returned the token as bytes insted of a string.
        # That is no longer the case and the `.decode("utf-8")` has been removed.
        access_token = jwt.encode(
            token_payload.dict(), secret_key, algorithm=JWT_ALGORITHM
        )

        return access_token

    def get_username_from_token(self, *, token: str, secret_key: str) -> Optional[str]:
        try:
            decoded_token = jwt.decode(
                token,
                str(secret_key),
                audience=JWT_AUDIENCE,
                algorithms=[JWT_ALGORITHM],
            )
            payload = JWTPayload(**decoded_token)
        except (jwt.PyJWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload.username
