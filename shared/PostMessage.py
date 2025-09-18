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

    @staticmethod
    def create(status_code: StatusCode, message: str, data: BytesIO, displacement: float | None = None) -> PostMessage:

        displacement = displacement if displacement is not None else float("nan")
        return PostMessage(status_code, message, data)