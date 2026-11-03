"""Database-backed, revocable authentication. No credentials are logged."""

import re
import secrets
from threading import BoundedSemaphore

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, SecretStr

from backend.catalog.db import connect
from .security import DUMMY_HASH, token_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["authentication"])
bearer = HTTPBearer(auto_error=False)
HASH_CAPACITY = BoundedSemaphore(2)


def unauthorized():
    return HTTPException(401, "Invalid or expired credentials", headers={"WWW-Authenticate": "Bearer"})


def require_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None or credentials.scheme.lower() != "bearer" or not re.fullmatch(r"[A-Za-z0-9_-]{43}", credentials.credentials):
        raise unauthorized()
    try:
        with connect() as connection:
            user = connection.execute("""SELECT u.id,u.email,u.name FROM series76.auth_sessions s
                JOIN series76.users u ON u.id=s.user_id WHERE s.token_hash=%s
                AND s.expires_at>clock_timestamp() AND u.active""", (token_hash(credentials.credentials),)).fetchone()
    except psycopg.Error:
        raise HTTPException(503, "Authentication service unavailable") from None
    if user is None:
        raise unauthorized()
    return user


def check_limit(connection, scope: str, maximum: int):
    row = connection.execute("""INSERT INTO series76.auth_login_limits(scope_hash,attempts)
        VALUES (%s,1) ON CONFLICT(scope_hash) DO UPDATE SET
        attempts=CASE WHEN auth_login_limits.window_start<clock_timestamp()-interval '5 minutes'
            THEN 1 ELSE auth_login_limits.attempts+1 END,
        window_start=CASE WHEN auth_login_limits.window_start<clock_timestamp()-interval '5 minutes'
            THEN clock_timestamp() ELSE auth_login_limits.window_start END RETURNING attempts""", (token_hash(scope),)).fetchone()
    return row["attempts"] <= maximum


class LoginRequest(BaseModel):
    email: str
    password: SecretStr


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    email = body.email.strip().lower()
    password = body.password.get_secret_value()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or not 1 <= len(password) <= 1024:
        raise unauthorized()
    if not HASH_CAPACITY.acquire(blocking=False):
        raise HTTPException(429, "Please wait before trying again", headers={"Retry-After": "5"})
    try:
        with connect() as connection:
            connection.execute("DELETE FROM series76.auth_login_limits WHERE window_start<clock_timestamp()-interval '10 minutes'")
            # Do not trust X-Forwarded-For from arbitrary clients.
            allowed_ip = check_limit(connection, "ip:" + (request.client.host if request.client else "unknown"), 30)
            # A blocked IP cannot grow an unbounded set of email-limit rows.
            allowed_email = check_limit(connection, "email:" + email, 10) if allowed_ip else False
        if not allowed_email or not allowed_ip:
            raise HTTPException(429, "Please wait before trying again", headers={"Retry-After": "300"})
        with connect() as connection:
            user = connection.execute("SELECT id,email,name,password_hash,active FROM series76.users WHERE email=%s", (email,)).fetchone()
            valid = verify_password(password, user["password_hash"] if user else DUMMY_HASH)
            if not valid or not user or not user["active"]:
                raise unauthorized()
            token = secrets.token_urlsafe(32)
            connection.execute("DELETE FROM series76.auth_sessions WHERE expires_at<=clock_timestamp()")
            expiry = connection.execute("""INSERT INTO series76.auth_sessions(token_hash,user_id,expires_at)
                VALUES (%s,%s,clock_timestamp()+interval '12 hours') RETURNING expires_at""", (token_hash(token), user["id"])).fetchone()
            return {"access_token": token, "token_type": "bearer", "expires_at": expiry["expires_at"],
                    "user": {key: user[key] for key in ("id", "email", "name")}}
    except psycopg.Error:
        raise HTTPException(503, "Authentication service unavailable") from None
    finally:
        HASH_CAPACITY.release()


@router.get("/me")
def me(response: Response, user=Depends(require_user)):
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout", status_code=204)
def logout(user=Depends(require_user), credentials=Depends(bearer)):
    try:
        with connect() as connection:
            connection.execute("DELETE FROM series76.auth_sessions WHERE token_hash=%s AND user_id=%s", (token_hash(credentials.credentials), user["id"]))
    except psycopg.Error:
        raise HTTPException(503, "Could not revoke session. Try again.") from None
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
