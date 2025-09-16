import logging
import datetime
import pypylon.pylon
from os import path, makedirs
from pypylon import pylon
from typing import Tuple
from pypylon.pylon import TimeoutHandling_ThrowException, TimeoutException
from pypylon.pylon import InstantCamera, GrabResult
from pypylon.genicam import INodeMap, IEnumeration, IEnumEntry, INode, IFloat, IInteger, IBoolean
from shared.GrabbedImage import GrabbedImage
from shared.CameraEnum import CameraEnum
from shared.FrameProviderAbc import FrameProviderAbc
from shared.SettingPersistentCameraAbc import SettingPersistentCameraAbc

class PylonCameraWrapper(FrameProviderAbc, SettingPersistentCameraAbc):
    """
    Wrapper for the pypylon camera. Supports the most common camera settings.
    Implements the FrameProviderAbc interface.
    """

    def __init__(self, camera: InstantCamera, logger: logging.Logger | None = None):

        self.__camera: InstantCamera = InstantCamera(camera)
        self.__node_map: INodeMap | None = None
        self.__camera_name: str = ""
        if logger is not None:
            self.__logger: logging.Logger = logger
        else:
            self.__logger: logging.Logger = logging.getLogger(__name__)
            self.__logger.addHandler(logging.NullHandler())

    def start_camera_streaming(self):

        self.__camera.StartGrabbing()
        self.__logger.info("Camera started streaming")

    def stop_camera_streaming(self):

        self.__camera.StopGrabbing()
        self.__logger.info("Camera stopped streaming")

    def get_camera_info(self) -> dict:
        """Get camera information as a dictionary."""
        device_info: pypylon.pylon.DeviceInfo = self.__camera.GetDeviceInfo()
        return {
            "name": device_info.GetFriendlyName(),
            "model_name": device_info.GetModelName(),
            "vendor_name": device_info.GetVendorName(),
            "device_class": device_info.GetDeviceClass(),
            "serial_number": device_info.GetSerialNumber(),
            "device_version": device_info.GetDeviceVersion(),
        }

    def initialize_camera(self):
        self.__camera.Open()
        self.__node_map = self.__camera.GetNodeMap()
        self.__camera_name = self.__camera.GetDeviceInfo().GetFriendlyName()

    def log_camera_info(self):
        """Log camera information to the logger."""
        camera_info = self.get_camera_info()
        for key, value in camera_info.items():
            self.__logger.info(f"{key.replace('_', ' ').title()}: {value}")

    def get_frame(self) -> GrabbedImage | Exception:

        grab_image_result: GrabResult | None = None
        GRAB_TIMEOUT_MS = 5000
        try:
            grab_image_result = self.__camera.RetrieveResult(GRAB_TIMEOUT_MS, TimeoutHandling_ThrowException)
        except TimeoutException as te:
            return te

        if not grab_image_result.GrabSucceeded():
            return RuntimeError("Failed to grab image.")

        return GrabbedImage(
            image = grab_image_result.GetArray(),
            timestamp = datetime.datetime.now(),
            camera = CameraEnum.Pylon,
            additional_info = {
                "camera_name": self.__camera_name
            }
        )

    def save_camera_settings(self, file_path:str) -> Exception | None:
        """
        Saves the camera settings to a file.
        Returns an exception if an error occurs and returns None if successful.

        Parameter:
            file_path: the path to the .pfs file to save the camera settings to.
        """
        if not file_path.endswith(".pfs"):
            self.__logger.warning(f"File path does not end with .pfs: {file_path}")

        # Create the directory if it does not exist
        if not path.exists(path.dirname(file_path)):
            try:
                makedirs(path.dirname(file_path))
            except Exception as e:
                self.__logger.error(f"Error creating directory {path.dirname(file_path)}: {e}")
                return e

        try:
            pylon.FeaturePersistence.Save(file_path, self.__node_map)
        except Exception as e:
            self.__logger.error(f"Error saving camera settings to {file_path}: {e}")
            return e

        self.__logger.info(f"Camera settings saved to {file_path}")

    def load_camera_settings(self, file_path:str) -> Exception | None:
        """
        Loads the camera settings from a file.
        Returns an exception if an error occurs and returns None if successful.

        Parameter:
            file_path: the path to the .pfsfile to load the camera settings from.
        """
        try:
            pylon.FeaturePersistence.Load(file_path, self.__node_map)
        except Exception as e:
            self.__logger.error(f"Error loading camera settings from {file_path}: {e}")
            return e
        
        self.__logger.info(f"Camera settings loaded from {file_path}")

    @property
    def camera_name(self) -> str:
        return self.__camera_name

    @property
    def fps(self) -> float | Exception:
        """
        Returns the current frames per second.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("AcquisitionFrameRate")

    @fps.setter
    def fps(self, new_value: float) -> None:
        """
        Sets the new frames per second. Not valid when acquisition_frame_rate_enable is false.
        Raises an exception if an error occurs.
        """
        result = self.__write_float_node("AcquisitionFrameRate", new_value)
        if result is not None:
            raise result

    @property
    def acquisition_frame_rate_enable(self) -> bool | Exception:
        """
        Returns the current acquisition frame rate enable. Not valid when camera is streaming.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("AcquisitionFrameRateEnable")

    @acquisition_frame_rate_enable.setter
    def acquisition_frame_rate_enable(self, new_value: bool) -> None:
        """
        Sets the new acquisition frame rate enable. Not valid when camera is streaming.
        Raises an exception if an error occurs.
        """
        result = self.__write_bool_node("AcquisitionFrameRateEnable", new_value)
        if result is not None:
            raise result

    @property
    def acquisition_frame_rate(self) -> float | Exception:
        """
        Returns the current acquisition frame rate.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("AcquisitionFrameRate")

    @acquisition_frame_rate.setter
    def acquisition_frame_rate(self, new_value: float) -> None:
        """
        Sets the new acquisition frame rate. Not valid when acquisition_frame_rate_enable is disabled
        Raises an exception if an error occurs.
        """
        result = self.__write_float_node("AcquisitionFrameRate", new_value)
        if result is not None:
            raise result

    @property
    def acquisition_frame_rate_enable(self) -> bool | Exception:
        """
        Returns the current acquisition frame rate enable.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("AcquisitionFrameRateEnable")

    @acquisition_frame_rate_enable.setter
    def acquisition_frame_rate_enable(self, new_value: bool) -> None:
        """
        Sets the new acquisition frame rate enable.
        Raises an exception if an error occurs.
        """
        result = self.__write_bool_node("AcquisitionFrameRateEnable", new_value)
        if result is not None:
            raise result

    @property
    def gain_auto(self) -> str | Exception:
        """
        Returns the current gain auto.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("GainAuto")

    @gain_auto.setter
    def gain_auto(self, new_value: str) -> None:
        """
        Sets the new gain auto.
        Raises an exception if an error occurs.
        """
        result = self.__write_enum_node("GainAuto", new_value)
        if result is not None:
            raise result

    @property
    def pixel_format(self) -> str | Exception:
        """
        Returns the current pixel format. Not valid when camera is streaming.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("PixelFormat")

    @pixel_format.setter
    def pixel_format(self, new_value: str) -> None:
        """
        Sets the new pixel format. Not valid when camera is streaming.
        Raises an exception if an error occurs.
        """
        result = self.__write_enum_node("PixelFormat", new_value)
        if result is not None:
            raise result

    @property
    def image_width(self) -> int | Exception:
        """
        Returns the current image width.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("Width")

    @image_width.setter
    def image_width(self, new_value: int) -> None:
        """
        Sets the new image width.
        Raises an exception if an error occurs.
        """
        result = self.__write_int_node("Width", new_value)
        if result is not None:
            raise result

    @property
    def image_height(self) -> int | Exception:
        """
        Returns the current image height.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("Height")

    @image_height.setter
    def image_height(self, new_value: int) -> None:
        """
        Sets the new image height.
        Raises an exception if an error occurs.
        """
        result = self.__write_int_node("Height", new_value)
        if result is not None:
            raise result

    @property
    def gain(self) -> float | Exception:
        """
        Returns the current gain.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("Gain")

    @gain.setter
    def gain(self, new_value: float) -> None:
        """
        Sets the new gain.
        Raises an exception if an error occurs.
        """
        result = self.__write_float_node("Gain", new_value)
        if result is not None:
            raise result

    @property
    def gamma(self) -> float | Exception:
        """
        Returns the current gamma.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("Gamma")

    @gamma.setter
    def gamma(self, new_value: float) -> None:
        """
        Sets the new gamma.
        Raises an exception if an error occurs.
        """
        result = self.__write_float_node("Gamma", new_value)
        if result is not None:
            raise result

    @property
    def shutter_mode(self) -> str | Exception:
        """
        Returns the current shutter mode. Can be "Rolling" or "GlobalResetRelease"
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("ShutterMode")

    @shutter_mode.setter
    def shutter_mode(self, new_value: str) -> None:
        """
        Sets the new shutter mode. Can be "Rolling" or "GlobalResetRelease"
        Raises an exception if an error occurs.
        """
        result = self.__write_enum_node("ShutterMode", new_value)
        if result is not None:
            raise result

    @property
    def balance_ratio(self) -> float | Exception:
        """
        Returns the current balance ratio. Not valid if BalanceWhiteAuto is enabled.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("BalanceRatio")

    @balance_ratio.setter
    def balance_ratio(self, new_value: float) -> None:
        """
        Sets the new balance ratio. Not valid if BalanceWhiteAuto is enabled.
        Raises an exception if an error occurs.
        """
        result = self.__write_float_node("BalanceRatio", new_value)
        if result is not None:
            raise result

    @property
    def exposure_time(self) -> float | Exception:
        """
        Returns the current exposure time in microseconds. Not valid if ExposureAuto is enabled.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("ExposureTime")

    @exposure_time.setter
    def exposure_time(self, new_value: float) -> None:
        """
        Sets the new exposure time in microseconds. Not valid if ExposureAuto is enabled.
        Raises an exception if an error occurs.
        """
        result = self.__write_float_node("ExposureTime", new_value)
        if result is not None:
            raise result

    @property
    def exposure_auto(self) -> str | Exception:
        """
        Returns which state of auto exposure is currently set. Can be "On", "Off" or "Once"
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("ExposureAuto")

    @exposure_auto.setter
    def exposure_auto(self, new_value: str) -> None:
        """
        Sets the new state of auto exposure. Can be "On", "Off" or "Once"
        Raises an exception if an error occurs.
        """
        result = self.__write_enum_node("ExposureAuto", new_value)
        if result is not None:
            raise result

    @property
    def balance_white_auto(self) -> str | Exception:
        """
        Returns which state of auto white balance is currently set. Can be "On", "Off" or "Once"
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("BalanceWhiteAuto")

    @balance_white_auto.setter
    def balance_white_auto(self, new_value: str) -> None:
        """
        Sets the new state of auto white balance. Can be "On", "Off" or "Once"
        Raises an exception if an error occurs.
        """
        result = self.__write_enum_node("BalanceWhiteAuto", new_value)
        if result is not None:
            raise result

    @property
    def balance_ratio_selector(self) -> str | Exception:
        """
        Returns the current white balance ratio option.
        Returns the value if successful, or an exception if an error occurs.
        """
        return self.__read_node("BalanceRatioSelector")

    @balance_ratio_selector.setter
    def balance_ratio_selector(self, new_value: str) -> None:
        """
        Sets the new white balance ratio option. Causes error if BalanceWhiteAuto is enabled.
        Raises an exception if an error occurs.

        Parameter:
            new_value: new balance ratio option. Must be either "Red", "Green" or "Blue"
        """
        result = self.__write_enum_node("BalanceRatioSelector", new_value)
        if result is not None:
            raise result

    def __get_node(self, node_name:str) -> INode | Exception:
        """
        Acquires the node from node map using the node name.
        Returns the node if successful, or an exception if an error occurs.
        """
        try:
            if self.__node_map is None:
                return RuntimeError("Cannot access camera setting because node map is not initialized")
            node:INode = self.__node_map.GetNode(node_name)
            return node
        except Exception as e:
            return e

    def __read_node(self, node_name:str) -> float | Exception:
        """
        Returns the value of a float node.
        Returns the value if successful, or an exception if an error occurs.
        """
        try:
            node_result = self.__get_node(node_name)
            if isinstance(node_result, Exception):
                return node_result
            node: INode = node_result
            return node.Value

        except Exception as e:
            return e

    def __write_bool_node(self, node_name:str, new_value:bool) -> Exception | None:
        """
        Writes the value of the bool node.
        Returns None if successful, or an exception if an error occurs.
        """
        try:
            node_result = self.__get_node(node_name)
            if isinstance(node_result, Exception):
                return node_result
            node:IBoolean = node_result
            node.SetValue(new_value)
            return None
            
        except Exception as e:
            return e

    def __write_float_node(self, node_name:str, new_value:float) -> Exception | None:
        """
        Writes the value of the float node.
        Returns None if successful, or an exception if an error occurs.
        """
        try:
            node_result = self.__get_node(node_name)
            if isinstance(node_result, Exception):
                return node_result
            node:IFloat = node_result
            minimal_allowed_value:float = node.GetMin()
            maximal_allowed_value:float = node.GetMax()
            
            if not (minimal_allowed_value <= new_value <= maximal_allowed_value):
                return ValueError(f"Invalid value: {new_value}. Must be between {minimal_allowed_value} and {maximal_allowed_value}")
            
            node.SetValue(new_value)
            return None

        except Exception as e:
            return e

    def __write_int_node(self, node_name:str, new_value:int) -> Exception | None:
        """
        Writes the value of the int node.
        Returns None if successful, or an exception if an error occurs.
        """
        try:
            node_result = self.__get_node(node_name)
            if isinstance(node_result, Exception):
                return node_result
            node:IInteger = node_result
            node.SetValue(new_value)
            return None
            
        except Exception as e:
            return e

    def __write_enum_node(self, node_name:str, new_value:str) -> Exception | None:
        """
        Writes the value of the enum node.
        Returns None if successful, or an exception if an error occurs.
        """
        try:
            node_result = self.__get_node(node_name)
            if isinstance(node_result, Exception):
                return node_result
            node:IEnumeration = node_result
            valid_entries: Tuple[IEnumEntry] = node.GetEntries()
            
            if new_value not in (e.Symbolic for e in valid_entries):
                return ValueError(f"Invalid value: {new_value}. Can only be one of {[e.Symbolic for e in valid_entries]}")
            
            node.SetValue(new_value)
            return None
            
        except Exception as e:
            return e