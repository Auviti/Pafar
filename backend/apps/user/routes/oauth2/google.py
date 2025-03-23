import os
import aiohttp
import json
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, HTTPException, status,Request
from fastapi.responses import RedirectResponse
from authlib.integrations.base_client import OAuthError
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import Settings
from core.database import get_db1
from authlib.integrations.starlette_client import OAuth
from apps.user.models.user import User, UUID
from core.utils.reponse import Response
from apps.user.services.oauth2 import create_user


settings = Settings()
router = APIRouter()
oauth = OAuth()

# Register Google OAuth client
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={"scope": "openid profile email"}
)


@router.get("/users/login/google")
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request,settings.GOOGLE_REDIRECT_URI)


@router.get("/users/login/google/callback")
async def auth_google(request: Request, db: AsyncSession = Depends(get_db1)):
    try:
        user_response: OAuth2Token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        return Response(message="Could not validate credentials", data=str(e),success=False,code=401)

    user = user_response.get("userinfo")
    user['role'] = "Buyer"
    if request.query_params.get("role"):
        user['role'] = request.query_params.get("role")

    try:
        result = await db.execute(select(User).filter(User.email == user['email']).options(selectinload(User.addresses)))
        if len(result.scalars().all())>0:
            return Response(message=f"User with email-'{user['email']}' Already Exists",success=False,code=400)
        
        created_user = await create_user(db, user)  # Refresh to get updated info (e.g., ID after commit)
        
        if created_user is None:
            return Response(message="User not Created",data=created_user.to_dict(),success=False,code=404)

        # Prepare the response in a dict format
        jsonuser = {
            'id': created_user.id,
            'firstname': created_user.firstname,
            'lastname': created_user.lastname,
            'email': created_user.email,
            'role': created_user.role.value,
            'picture': created_user.picture,
            'active': created_user.active
        }
        
        # Returning the response with the newly created user data
        return Response(data=jsonuser, message="User created successfully", code=201)
    except Exception as error:
        return Response(message=str(error), success=False,code=500)

