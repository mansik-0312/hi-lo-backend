#controller/user_auth.py

import asyncio
from datetime import datetime
import math
import json
from api.controller.user.files_controller import *
from bson import ObjectId
from core.utils.auth_utils import *
from fastapi import Request
from jose import jwt,JWTError
from core.utils.helper import serialize_datetime_fields,convert_objectid_to_str
from schemas.user_schemas import *
from config.db_config import *
from core.utils.redis_helper import redis_client 
from core.utils.pagination import StandardResultsSetPagination   
from services.translation import translate_message
from core.templates.email_templates import *
from core.utils.core_enums import *
from bson import ObjectId
from config.models.user_models import *
from core.utils.helper import *
from bson.errors import InvalidId

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES =int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

response = CustomResponseMixin()

async def refresh_token(
    request: RefreshTokenRequest,
    lang: str = "en",
):
    """
    Refresh access token using a valid refresh token.
    """

    # =====================================================
    # FIND REFRESH TOKEN
    # =====================================================

    existing_token = (
        await token_collection.find_one(
            {
                "refresh_token": (
                    request.refresh_token
                )
            }
        )
    )

    if not existing_token:

        return response.error_message(
            translate_message(
                "REFRESH_TOKEN_NOT_FOUND",
                lang=lang,
            ),
            status_code=400,
        )

    # =====================================================
    # CHECK BLACKLIST
    # =====================================================

    if existing_token.get(
        "is_blacklisted",
        False,
    ):

        return response.error_message(
            translate_message(
                "REFRESH_TOKEN_BLACKLISTED",
                lang=lang,
            ),
            status_code=401,
        )

    # =====================================================
    # VERIFY REFRESH TOKEN
    # =====================================================

    try:

        token_data = verify_refresh_token(
            request.refresh_token
        )

    except Exception:

        return response.error_message(
            translate_message(
                "INVALID_REFRESH_TOKEN",
                lang=lang,
            ),
            status_code=401,
        )

    # =====================================================
    # FIND USER
    # =====================================================

    user = await user_collection.find_one(
        {
            "email": token_data.get(
                "sub"
            )
        }
    )

    if not user:

        return response.error_message(
            "USER_NOT_FOUND",
            status_code=404,
        )

    # =====================================================
    # GET PLAYER / OPERATOR
    # =====================================================

    player_id = user.get(
        "player_id"
    )

    operator_id = user.get(
        "operator_id"
    )

    if not player_id:

        return response.error_message(
            "Player ID is not configured.",
            status_code=400,
        )

    if not operator_id:

        return response.error_message(
            "Operator ID is not configured.",
            status_code=400,
        )

    # =====================================================
    # BLACKLIST OLD TOKEN
    # TOKEN ROTATION
    # =====================================================

    await token_collection.update_one(
        {
            "_id": existing_token["_id"]
        },
        {
            "$set": {
                "is_blacklisted": True,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # =====================================================
    # GENERATE NEW TOKENS
    # =====================================================

    new_access_token, new_refresh_token = (
        generate_login_tokens(
            user=user,
            player_id=player_id,
            operator_id=operator_id,
        )
    )

    # =====================================================
    # STORE NEW REFRESH TOKEN
    # =====================================================

    await token_collection.insert_one(
        {
            "user_id": str(
                user["_id"]
            ),

            "email": user[
                "email"
            ],

            "access_token": (
                new_access_token
            ),

            "refresh_token": (
                new_refresh_token
            ),

            "is_blacklisted": False,

            "created_at": (
                datetime.utcnow()
            ),

            "updated_at": None,
        }
    )

    return response.success_message(
        "TOKEN_REFRESHED_SUCCESSFULLY",

        data=[
            {
                "access_token": (
                    new_access_token
                ),

                "refresh_token": (
                    new_refresh_token
                ),
            }
        ],

        status_code=200,
    )

async def logout(
    request: LogoutRequest,
    lang: str = "en",
):
    """
    Logout a user by blacklisting
    all active refresh tokens.
    """

    try:

        token_data = verify_refresh_token(
            request.refresh_token
        )

    except Exception:

        return response.error_message(
            translate_message(
                "INVALID_REFRESH_TOKEN",
                lang=lang,
            ),
            status_code=400,
        )

    existing_token = (
        await token_collection.find_one(
            {
                "refresh_token": (
                    request.refresh_token
                )
            }
        )
    )

    if not existing_token:

        return response.error_message(
            translate_message(
                "REFRESH_TOKEN_NOT_FOUND",
                lang=lang,
            ),
            status_code=400,
        )

    if existing_token.get(
        "is_blacklisted",
        False,
    ):

        return response.error_message(
            "REFRESH_TOKEN_ALREADY_INVALID",
            status_code=401,
        )

    user_id = existing_token.get(
        "user_id"
    )

    if not user_id:

        return response.error_message(
            translate_message(
                "USER_ID_NOT_FOUND",
                lang=lang,
            ),
            status_code=400,
        )

    # =====================================================
    # BLACKLIST ACTIVE TOKENS
    # =====================================================

    await token_collection.update_many(
        {
            "user_id": user_id,
            "is_blacklisted": False,
        },
        {
            "$set": {
                "is_blacklisted": True,

                "updated_at": (
                    datetime.utcnow()
                ),
            }
        },
    )

    # =====================================================
    # UPDATE LOGIN STATUS
    # =====================================================

    await user_collection.update_one(
        {
            "_id": ObjectId(
                user_id
            )
        },
        {
            "$set": {
                "login_status": (
                    LoginStatus.INACTIVE
                ),

                "last_logout_at": (
                    datetime.utcnow()
                ),
            }
        },
    )

    return response.success_message(
        translate_message(
            "LOGOUT_SUCCESSFUL",
            lang=lang,
        ),

        data={},

        status_code=200,
    )

# helper function -Dependency to extract user email from token
def get_current_user_email(request: Request):
    """
    Dependency to extract the email of the current user from the Authorization header in /change-password api.
    """
    # Extract token from Authorization header
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise response.raise_exception( message="INVALID_OR_MISSING_TOKEN", data=[], status_code=401)
    token = authorization.split(" ")[1]
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_ACCESS_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise response.raise_exception(message="INVALID_TOKEN_EMAIL_NOT_FOUND",data=[],status_code=401)
        return email
    except JWTError:
        raise response.raise_exception( message="INVALID_OR_EXPIRED_TOKEN",status_code=401)



#controller for get_user_profile_details 
async def get_user_profile_details(request: Request, current_user: dict, lang: str = "en"):
    """
    Get complete user profile info including profile photo URL (S3 presigned URL or LOCAL path).
    Uses Files model and helper to generate fetchable URL.
    """
    try:
        user_id = str(current_user["_id"])

        # Fetch all user fields
        user_data = await user_collection.find_one({"_id": ObjectId(user_id)})

        if not user_data:
            return response.success_message(
                translate_message("USER_NOT_FOUND", lang=lang),
                data=None
            )
        # Remove sensitive info
        user_data.pop("password", None)

        # Get profile photo URL
        profile_url = await get_profile_photo_url(current_user=user_data)
        user_data["profile_photo_url"] = profile_url if profile_url else None


        user_data = serialize_datetime_fields(user_data)
        # Convert ObjectId to str for all relevant fields
        user_data = convert_objectid_to_str(user_data)

        return response.success_message(
            translate_message("USER_PROFILE_FETCHED", lang=lang),
            data=user_data
        )

    except Exception as e:
        return response.raise_exception(
            translate_message("ERROR_FETCHING_PROFILE", lang=lang),
            data=str(e),
            status_code=500
        )
async def send_reset_password_otp_controller(payload: ForgotPasswordRequest, lang):
    email = payload.email

    # Step 1: Check user exists
    user = await user_collection.find_one({"email": email})
    if not user:
        return response.error_message(translate_message("NO_ACCOUNT_FOUND_WITH_EMAIL", lang=lang), status_code=404)

    # Step 2: Generate OTP
    otp = generate_verification_code()

    # Save OTP for 5 minutes
    await redis_client.setex(f"reset:{email}:otp", 300, otp)

    # Email Template
    subject, body = reset_password_otp_template(user["username"], otp, lang)

    await send_email(email, subject, body, is_html=True)

    return response.success_message(translate_message("NEW_OTP_SENT_TO_EMAIL", lang=lang), data=[], status_code=200)

async def verify_reset_password_otp_controller(payload, lang):
    email = payload.email
    otp = payload.otp

    stored_otp = await redis_client.get(f"reset:{email}:otp")

    if not stored_otp:
        return response.error_message(translate_message("OTP_EXPIRED_OR_NOT_FOUND", lang=lang), status_code=400)

    stored_otp = stored_otp.decode() if isinstance(stored_otp, bytes) else stored_otp

    if otp != stored_otp:
        return response.error_message(translate_message("INVALID_OTP", lang=lang), status_code=400)

    # Mark OTP as verified (valid for 10 minutes)
    await redis_client.setex(f"reset:{email}:verified", 600, "true")

    return response.success_message(translate_message("OTP_VERIFIED_SUCCESSFULLY", lang=lang), status_code=200)

async def reset_password_controller(payload, lang):
    email = payload.email
    new_password = payload.new_password

    # Ensure user completed OTP verification
    is_verified = await redis_client.get(f"reset:{email}:verified")
    if not is_verified:
        return response.error_message(translate_message("OTP_VERIFICATION_REQUIRED", lang=lang), status_code=400)

    # Hash new password
    hashed_password = get_hashed_password(new_password)

    # Update DB
    await user_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}}
    )

    # Remove reset session data
    await redis_client.delete(f"reset:{email}:otp")
    await redis_client.delete(f"reset:{email}:verified")

    return response.success_message(translate_message("PASSWORD_RESET_SUCCESSFULLY", lang=lang), status_code=200)

async def resend_forgot_password_otp_controller(payload, lang):
    email = payload.email

    # Step 1: Check user exists
    user = await user_collection.find_one({"email": email})
    if not user:
        return response.error_message(
            translate_message("NO_ACCOUNT_FOUND_WITH_EMAIL", lang=lang),
            status_code=404
        )

    otp_key = f"reset:{email}:otp"
    resend_key = f"reset:{email}:resend"

    # Step 2: Optional rate limit (1 resend per 60 seconds)
    resend_block = await redis_client.get(resend_key)
    if resend_block:
        return response.error_message(
            translate_message("OTP_RESEND_TOO_SOON", lang=lang),
            status_code=429
        )

    # Step 3: Generate new OTP
    otp = generate_verification_code()

    # Step 4: Store OTP again (5 minutes)
    await redis_client.setex(otp_key, 300, otp)

    # Step 5: Set resend lock (60 seconds)
    await redis_client.setex(resend_key, 60, "1")

    # Step 6: Send email
    subject, body = reset_password_otp_template(user["username"], otp, lang)
    await send_email(email, subject, body, is_html=True)

    return response.success_message(
        translate_message("OTP_RESENT_SUCCESSFULLY", lang=lang),
        data=[],
        status_code=200
    )

async def get_user_by_id_controller(user_id: str, lang: str):
    if not ObjectId.is_valid(user_id):
        return response.error_message(translate_message("INVALID_USER_ID", lang=lang), status_code=400)

    user = await get_user_details(
        condition={"_id": ObjectId(user_id), "is_deleted": {"$ne": True}},
        fields=[
            "_id",
            "username",
            "email",
            "role",
            "two_factor_enabled",
            "login_status",
            "last_login_at",
            "created_at",
            "updated_at",
            "membership_type",
            "is_verified",
            "tokens",
        ]
    )

    if not user:
        return response.error_message(translate_message("USER_NOT_FOUND", lang=lang), status_code=404)

    # Normalize ID
    user["id"] = user.pop("_id")

    user = convert_objectid_to_str(user)
    user = serialize_datetime_fields(user)

    return response.success_message(
        translate_message("USER_PROFILE_FETCHED", lang=lang),
        data=[user],
        status_code=200
    )

async def get_all_users_controller(
    pagination: StandardResultsSetPagination,
    lang: str
):
    users, total = await get_users_list(
        condition={"is_deleted": {"$ne": True}},
        fields=[
            "_id",
            "username",
            "email",
            "role",
            "two_factor_enabled",
            "login_status",
            "last_login_at",
            "created_at",
            "updated_at",
            "membership_type",
            "is_verified",
            "tokens",
        ],
        skip=pagination.skip,
        limit=pagination.limit
    )

    for user in users:
        user["id"] = user.pop("_id")

    users = convert_objectid_to_str(users)
    users = serialize_datetime_fields(users)

    return response.success_message(
        translate_message("USER_PROFILE_FETCHED", lang=lang),
        data=[{
            "results": users,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total
        }],
        status_code=200
    )

async def signup_controller(
    payload: Signup,
    lang: str,
):
    existing = await user_collection.find_one(
        {
            "email": payload.email,
        }
    )

    if existing:
        return response.error_message(
            translate_message(
                "EMAIL_ALREADY_REGISTERED",
                lang=lang,
            ),
            status_code=400,
        )

    existing_username = (
        await user_collection.find_one(
            {
                "username": payload.username,
            }
        )
    )

    if existing_username:
        return response.error_message(
            translate_message(
                "USERNAME_ALREADY_TAKEN",
                lang=lang,
            ),
            status_code=400,
        )

    # Temporary default operator
    operator_id = (
        "6a95200b5c314c48d5f42cf1"
    )

    player_id = str(
        ObjectId()
    )

    user_data = {
        "username": payload.username,
        "email": payload.email,
        "password": get_hashed_password(
            payload.password
        ),

        "membership_type": "free",
        "is_verified": True,
        "two_factor_enabled": False,

        "language": lang,
        "bonus_tokens": 0,
        "tokens": 0,

        "player_id": player_id,
        "operator_id": operator_id,

        "role": "user",

        "login_status": "inactive",
        "is_deleted": False,

        "created_at": datetime.utcnow(),
        "updated_at": None,
    }

    result = await user_collection.insert_one(
        user_data
    )

    return response.success_message(
        "User registered successfully.",
        data=[
            {
                "user_id": str(
                    result.inserted_id
                ),
                "username": payload.username,
                "email": payload.email,
                "player_id": player_id,
                "operator_id": operator_id,
            }
        ],
        status_code=201,
    )

async def login_controller(
    payload: LoginRequest,
    lang: str,
):

    email = payload.email

    password = payload.password

    # =====================================================
    # GET USER
    # =====================================================

    user = await get_user_details(
        condition={
            "email": email,
        },
        fields=[
            "_id",
            "email",
            "username",
            "password",
            "two_factor_enabled",
            "membership_type",
            "is_verified",
            "is_deleted",
            "player_id",
            "operator_id",
            "role",
        ],
    )

    if not user:
        return response.error_message(
            translate_message(
                "USER_NOT_REGISTERED",
                lang=lang,
            ),
            status_code=400,
        )

    player_id = user.get(
        "player_id"
    )

    operator_id = user.get(
        "operator_id"
    )

    if not player_id:
        return response.error_message(
            "Player ID is not configured for this user.",
            status_code=400,
        )

    if not operator_id:
        return response.error_message(
            "Operator ID is not configured for this user.",
            status_code=400,
        )
    # =====================================================
    # GENERATE TOKENS
    # =====================================================

    return await finalize_login_response(
        user=user,
        player_id=player_id,
        operator_id=operator_id,
        lang=lang,
    )