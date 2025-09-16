import numpy as np
import datetime
from dataclasses import dataclass
from .CameraEnum import CameraEnum

@dataclass(slots = True)
class GrabbedImage:
    image: np.ndarray
    timestamp: datetime.datetime
    camera: CameraEnum
    additional_info: dict[str, any]