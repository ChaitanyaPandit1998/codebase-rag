"""Error handling utilities for API endpoints."""
import logging
from functools import wraps
from typing import Callable, Any


logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(APIError):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        """Initialize validation error with 400 status code."""
        super().__init__(message, status_code=400)


class NotFoundError(APIError):
    """Raised when a resource is not found."""

    def __init__(self, message: str):
        """Initialize not found error with 404 status code."""
        super().__init__(message, status_code=404)


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    def __init__(self, message: str):
        """Initialize authentication error with 401 status code."""
        super().__init__(message, status_code=401)


def handle_errors(func: Callable) -> Callable:
    """
    Decorator for handling errors in API endpoints.

    This decorator catches exceptions and converts them to appropriate
    API responses with proper status codes and error messages.

    Usage:
        @handle_errors
        def my_endpoint():
            # Your endpoint code here
            pass

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return {
                "error": e.message,
                "status": e.status_code
            }
        except NotFoundError as e:
            logger.warning(f"Not found: {e.message}")
            return {
                "error": e.message,
                "status": e.status_code
            }
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e.message}")
            return {
                "error": e.message,
                "status": e.status_code
            }
        except APIError as e:
            logger.error(f"API error: {e.message}")
            return {
                "error": e.message,
                "status": e.status_code
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {
                "error": "Internal server error",
                "status": 500
            }

    return wrapper


def validate_input(data: dict, required_fields: list) -> None:
    """
    Validate that all required fields are present in the input data.

    Args:
        data: Input data dictionary
        required_fields: List of required field names

    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )
