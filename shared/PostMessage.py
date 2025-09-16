import json
from StatusCode import StatusCode
from typing import NamedTuple
from io import BytesIO

class PostMessage(NamedTuple):
    status_code: StatusCode
    message: str
    latest_frame: BytesIO
    displacement: float

class PostMessageFactory:
    def create(self, status_code: StatusCode, message: str, data: BytesIO, displacement: float | None = None) -> PostMessage:
        return PostMessage(status_code, message, data)