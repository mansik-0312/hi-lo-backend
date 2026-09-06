import time
from fastapi import HTTPException, UploadFile, File
from bson import ObjectId
import re
from .response_mixin import CustomResponseMixin
import os, ssl, asyncio
from uuid import uuid4
from datetime import datetime, timezone, date, time, timedelta
from fastapi import Depends, Request
from jose import jwt,JWTError
# from core.utils.auth_utils import SECRET_ACCESS_KEY,ALGORITHM
response = CustomResponseMixin()
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from config.db_config import user_collection, file_collection, fcm_device_tokens_collection
import base64
import aiohttp
import uuid
from dotenv import load_dotenv
import os
from bson import ObjectId
from config.basic_config import settings
from config.models.user_models import *
from dateutil.relativedelta import relativedelta
from typing import Optional, Tuple
from services.translation import translate_message
from core.utils.core_enums import *
from core.utils.auth_utils import *
from enum import Enum
from typing import List
from decimal import Decimal, ROUND_HALF_UP
from config.basic_config import settings
import firebase_admin
from firebase_admin import messaging
from core.utils.logging_config import logging

logger = logging.getLogger(__name__)
TOKEN_TO_USDT_RATE = Decimal("0.05")

load_dotenv()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_REGION = os.getenv("AWS_S3_REGION")


# Helper function for validate_pwd
def validate_pwd(password):
    # Validate password strength
    if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,16}$", password):
        # Password must be 8-16 characters, include one uppercase, one lowercase, one digit, and one special character
        return response.raise_exception(message="Password must be 8-16 characters long, include one uppercase letter, one lowercase letter, one number, and one special character.",status_code=400)


# Helper function for validate_new_pwd
def validate_new_pwd(new_password):
    # Validate password strength
    if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,16}$", new_password):
        # Password must be 8-16 characters, include one uppercase, one lowercase, one digit, and one special character
        return response.raise_exception(message="new_password must be 8-16 characters long, include one uppercase letter, one lowercase letter, one number, and one special character.",status_code=400)


# Helper function for validate_confirm_new_password
def validate_confirm_new_password(confirm_new_password):
    # Validate password strength
    if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,16}$", confirm_new_password):
        # Password must be 8-16 characters, include one uppercase, one lowercase, one digit, and one special character
        return response.raise_exception(message="confirm_new_password must be 8-16 characters long, include one uppercase letter, one lowercase letter, one number, and one special character.",status_code=400)


#helper function for serialize_datetime_fields
def serialize_datetime_fields(data):
    """
    Recursively serialize datetime fields in a dictionary to ISO format strings.
    This function handles nested dictionaries and lists.
    """
    if isinstance(data, dict):
        serialized = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                serialized[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, (dict, list)):
                serialized[key] = serialize_datetime_fields(value)
            else:
                serialized[key] = value
        return serialized
    elif isinstance(data, list):
        return [serialize_datetime_fields(item) for item in data]
    else:
        return data


#helper function for convert_objectid_to_str
def convert_objectid_to_str(obj):
    """
    Recursively convert ObjectId fields to strings in a dict or list.
    """
    if isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

async def finalize_login_response(
    user: dict,
    player_id: str,
    operator_id: str,
    lang: str,
):
    """
    Finalize user login and generate JWT tokens.
    """

    access_token, refresh_token = (
        generate_login_tokens(
            user=user,
            player_id=player_id,
            operator_id=operator_id,
        )
    )

    # Store refresh token in database
    await token_collection.insert_one(
        {
            "user_id": str(
                user["_id"]
            ),

            "refresh_token": refresh_token,

            "is_blacklisted": False,

            "created_at": datetime.utcnow(),

            "updated_at": None,
        }
    )

    # Update user login status
    await user_collection.update_one(
        {
            "_id": user["_id"],
        },
        {
            "$set": {
                "login_status": (
                    LoginStatus.ACTIVE
                ),

                "last_login_at": (
                    datetime.utcnow()
                ),
            }
        },
    )

    return response.success_message(
        translate_message(
            "LOGIN_SUCCESSFUL",
            lang=lang,
        ),
        data=[
            {
                "access_token": (
                    access_token
                ),

                "refresh_token": (
                    refresh_token
                ),

                "user_id": str(
                    user["_id"]
                ),

                "player_id": (
                    player_id
                ),

                "operator_id": (
                    operator_id
                ),

                "username": (
                    user.get(
                        "username"
                    )
                ),

                "role": (
                    user.get(
                        "role",
                        "user",
                    )
                ),
            }
        ],
        status_code=200,
    )

def convert_datetime_to_date(obj, date_format="%Y-%m-%d"):
    """
     Recursively convert datetime objects to formatted date string.
    """
    if isinstance(obj, datetime):
        return obj.strftime(date_format)
    elif isinstance(obj, dict):
        return {k: convert_datetime_to_date(v, date_format) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_date(item, date_format) for item in obj]
    else:
        return obj

def parse_date_format(value: str | None):
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%d-%m-%Y")
    except ValueError:
        return None

async def subscribe_user_to_topic(user_id: str, topic: str):

    devices = await fcm_device_tokens_collection.find(
        {
            "user_id": user_id,
            "status": "active"
        }
    ).to_list(length=100)

    if not devices:
        return

    tokens = [d["device_token"] for d in devices]

    try:
        messaging.subscribe_to_topic(tokens, topic)
    except Exception as e:
        logger.error(f"[Topic Subscribe Failed] {e}")

async def unsubscribe_user_from_topic(user_id: str, topic: str):

    devices = await fcm_device_tokens_collection.find(
        {
            "user_id": user_id,
            "status": "active"
        }
    ).to_list(length=100)

    if not devices:
        return

    tokens = [d["device_token"] for d in devices]

    try:
        messaging.unsubscribe_from_topic(tokens, topic)
    except Exception as e:
        logger.error(f"[Topic Unsubscribe Failed] {e}")
