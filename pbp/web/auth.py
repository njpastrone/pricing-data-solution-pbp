"""
Staff login: the shared APP_PASSWORD, remembered per browser in a signed cookie.

Same password as the Streamlit app (parity), checked once at /login; the
cookie carries a random session id that keys the working order in memory.
"""

import uuid

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, TimestampSigner

from pbp import settings

COOKIE = "pbp_staff"
_signer = TimestampSigner(settings.SECRET_KEY)


def session_id(request: Request):
    """The staff session id from the cookie, or None when not logged in (or expired)."""
    raw = request.cookies.get(COOKIE)
    if not raw:
        return None
    try:
        return _signer.unsign(raw, max_age=settings.SESSION_DAYS * 86400).decode()
    except BadSignature:
        return None


def require_staff(request: Request) -> str:
    """FastAPI dependency: the session id, or a redirect to /login."""
    sid = session_id(request)
    if sid is None:
        raise HTTPException(status_code=303, headers={"Location": f"/login?next={request.url.path}"})
    return sid


def login(password, next_url="/orders"):
    """A redirect carrying a fresh session cookie, or None if the password is wrong."""
    if password != settings.APP_PASSWORD:
        return None
    response = RedirectResponse(next_url if next_url.startswith("/") else "/orders", status_code=303)
    response.set_cookie(COOKIE, _signer.sign(uuid.uuid4().hex).decode(), max_age=settings.SESSION_DAYS * 86400,
                        httponly=True, samesite="lax")
    return response


def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE)
    return response
