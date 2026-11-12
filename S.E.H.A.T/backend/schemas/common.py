from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """
    Standard envelope format for all SEHAT API responses.
    Ensures every response consists of success status, typed/nested data, a message, and potential errors.
    """
    success: bool
    data: Optional[T] = None
    message: str = ""
    error: Optional[str] = None
