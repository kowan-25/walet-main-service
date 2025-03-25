from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None and isinstance(exc, (InvalidToken, TokenError)):
        if "Token is expired" in str(exc):
            response.data = {"error": "Token expired"}
        else:
            response.data = {"error": "Invalid token"}
    
    return response