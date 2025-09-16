from dep.camerautils.GrabbedImage import GrabbedImage
from abc import ABC, abstractmethod

class FrameProviderAbc(ABC):

    @abstractmethod
    def get_frame(self) -> GrabbedImage | Exception:
        """
        Returns the next frame from the camera. If successfull, returns an instance of GrabbedImage. 
        Otherwise, returns an exception.
        """

    @abstractmethod
    def start_camera_streaming(self) -> None:
        """
        Start streaming frames from the camera. The camera will become ready to provide frames.
        But much of the configuration options will be disabled.
        """

    @abstractmethod
    def stop_camera_streaming(self) -> None:
        """
        Stop streaming frames from the camera. This might enable some of the configuration options that were not available
        when the camera was streaming.
        """