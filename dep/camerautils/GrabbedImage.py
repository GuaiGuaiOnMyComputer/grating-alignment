import numpy as np
import datetime
from dataclasses import dataclass
from .CameraEnum import CameraEnum
from .PixelFormatEnum import PixelFormatEnum

@dataclass(slots = True)
class GrabbedImage:
    image: np.ndarray
    timestamp: datetime.datetime
    camera: CameraEnum
    pixel_format: PixelFormatEnum
    additional_info: dict[str, any]