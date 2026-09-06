import os
import random
from jose import JWTError, jwt  # Change from regular jwt to jose.jwt
from redis import Redis
from dotenv import load_dotenv
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Dict, Optional, Any
from config.basic_config import settings
from .response_mixin import CustomResponseMixin
from schemas.tokens_schema import TokenData
from core.utils.redis_helper import store_in_redis, get_from_redis, delete_from_redis
from config.models.user_models import store_token
from config.basic_config import settings

load_dotenv()
response = CustomResponseMixin()

#Secret key for JWT access token and refresh token encoding and decoding
SECRET_ACCESS_KEY = settings.SECRET_ACCESS_KEY
SECRET_REFRESH_KEY = settings.SECRET_REFRESH_KEY
ALGORITHM = settings.ALGORITHM
# ACCESS_TOKEN_EXPIRE_MINUTES = 120 # 2hr time
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES

if not (SECRET_ACCESS_KEY or SECRET_REFRESH_KEY):
    raise response.error_message("Cannot load JWT Secret key or Refresh key")

# Password hash context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Function Password hashing
def get_hashed_password(password: str) -> str:
    return pwd_context.hash(password)


# Function to Verify password
def verify_password(plain_pwd, hashed_pwd) -> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)


# Function to Genrating access token
def create_access_token(
    data: Dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + (
            expires_delta
            or timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    to_encode.update(
        {
            "exp": expire,
            "token_type": "access",
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_ACCESS_KEY,
        algorithm=settings.ALGORITHM,
    )


# Function to create_refresh_token
def create_refresh_token(
    data: Dict[str, Any],
) -> str:

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode.update(
        {
            "exp": expire,
            "token_type": "refresh",
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_REFRESH_KEY,
        algorithm=settings.ALGORITHM,
    )

# Function to verify a token and extract user info
def verify_refresh_token(
    refresh_token: str,
):
    payload = jwt.decode(
        refresh_token,
        settings.SECRET_REFRESH_KEY,
        algorithms=[
            settings.ALGORITHM
        ],
    )

    if payload.get(
        "token_type"
    ) != "refresh":

        raise ValueError(
            "Invalid refresh token."
        )

    return payload

# Function to generate_verification_code
def generate_verification_code(length: int =4) -> str:
    """
    Generate random 6 digit number
    """
    return ''.join(random.choices('0123456789', k=length))


# Function to send_email
async def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    from tasks import send_email_task

    send_email_task.delay(to_email, subject, body, is_html)


# Function to verify_refresh_token
def verify_refresh_token(refresh_token: str):
    payload = jwt.decode(refresh_token, SECRET_REFRESH_KEY, algorithms=[ALGORITHM])
    return payload  # This should include the token data

from core.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
)


def generate_login_tokens(
    user: dict,
    player_id: str,
    operator_id: str,
):
    """
    Generate JWT access and refresh tokens
    for an authenticated player.
    """

    user_id = str(
        user["_id"]
    )

    email = user[
        "email"
    ]

    token_data = {
        "sub": email,
        "user_id": user_id,

        "player_id": player_id,

        "operator_id": operator_id,

        "role": user.get(
            "role",
            "user",
        ),
    }

    access_token = create_access_token(
        token_data
    )

    refresh_token = create_refresh_token(
        token_data
    )

    return (
        access_token,
        refresh_token,
    )