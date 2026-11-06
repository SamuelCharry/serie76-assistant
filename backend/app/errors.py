"""Public failure vocabulary: never expose exception bodies or connection details."""

from fastapi import HTTPException
from fastapi.responses import JSONResponse


FAILURES = {
    'service_unavailable': (503, 'The assistant is temporarily unavailable. Please try again shortly.'),
    'not_configured': (503, 'The assistant is not configured yet. Please contact the service administrator.'),
    'budget_exhausted': (402, 'The assistant is temporarily out of provider credits. Please try again later.'),
    'timeout': (504, 'The assistant took too long to respond. Please try again.'),
    'turn_deadline': (504, 'The assistant took too long to respond. Please try again.'),
    'provider_error': (502, 'The assistant could not get a response. Please try again shortly.'),
    'provider_unreachable': (503, 'The assistant cannot connect right now. Please try again shortly.'),
    'rate_limited': (503, 'The assistant is busy. Please try again shortly.'),
    'rate_limited_local': (503, 'The assistant is busy. Please try again shortly.'),
    'database_unavailable': (503, 'The service cannot access your conversation right now. Please try again shortly.'),
    'service_busy': (503, 'The assistant is busy. Please try again shortly.'),
    'session_busy': (409, 'A response is already being prepared for this conversation. Please wait and retry.'),
}


def error_response(code):
    code = code if code in FAILURES else 'provider_error'
    status, message = FAILURES[code]
    return JSONResponse(status_code=status, content={'detail': message, 'error_code': code})


class DatabaseUnavailable(HTTPException):
    def __init__(self):
        status, message = FAILURES['database_unavailable']
        super().__init__(status, message)
