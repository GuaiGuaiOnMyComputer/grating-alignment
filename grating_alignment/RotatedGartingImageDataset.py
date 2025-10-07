import torch
import pandas as pd
import logging
import torchvision.io as io
from pathlib import Path
from torch.utils.data import Dataset
from torchvision.transforms import Compose
from typing import NamedTuple, List, Tuple

class GratingPostureInfo(NamedTuple):
    """Named tuple representing a single row from the Excel file"""
    image_id: str
    gratering_side_x_cm: float
    gratering_side_y_cm: float
    gratering_side_angle_deg: float
    grating_side_rotation_deg: float

class RotatedGartingImageDataset(Dataset):

    def __init__(self, root_dir: str, excel_file_path: str | Path, transform: Compose | None = None, image_extension: str = "png", logger: logging.Logger | None = None):

        excel_file_path: Path = Path(excel_file_path)
        root_dir: Path = Path(root_dir)

        self.__logger: logging.Logger = logger if logger is not None else logging.getLogger(__name__)
        self.__logger.addHandler(logging.NullHandler())

        if not excel_file_path.exists():
            self.__logger.error(f"Excel file not found: {excel_file_path}")
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
        
        if not root_dir.is_dir():
            self.__logger.error(f"Root directory is not a directory: {root_dir}")
            raise NotADirectoryError(f"Root directory is not a directory: {root_dir}")

        self.__root_dir: Path = Path(root_dir)
        self.__excel_file_path: Path = excel_file_path
        self.__grating_posture_info: List[GratingPostureInfo] = self.__load_excel_file(excel_file_path, self.__logger)
        self.__image_paths: List[Path] = [self.__root_dir / f"{info.image_id}.{image_extension}" for info in self.__grating_posture_info]
        self.__transform: Compose | None = transform

    def __len__(self) -> int:
        return len(self.__grating_posture_info)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, GratingPostureInfo]:

        image_path: Path = self.__image_paths[index]
        image: torch.Tensor = io.read_image(image_path)
        if self.__transform:
            image = self.__transform(image)

        return image, self.__grating_posture_info[index]

    @property
    def grating_posture_info(self) -> List[GratingPostureInfo]:
        return self.__grating_posture_info

    @property
    def root_dir(self) -> Path:
        return self.__root_dir

    @property
    def transform(self) -> Compose | None:
        return self.__transform
    
    @transform.setter
    def transform(self, transform: Compose | None):
        self.__transform = transform

    @staticmethod
    def __load_excel_file(excel_file_path: Path, logger: logging.Logger | None = None) -> List[GratingPostureInfo]:
        """
        Load Excel file and parse each row into a GratingData NamedTuple.
        
        Returns:
            List[GratingData]: List of GratingData objects, one for each row in the Excel file
        """
        # read Excel file
        logger.debug(f"Loading excel file: {excel_file_path}")
        df: pd.DataFrame = pd.read_excel(excel_file_path)
        
        # Parse each row into GratingData NamedTuple
        grating_posture_info: List[GratingPostureInfo] = []
        
        for _, row in df.iterrows():
            grating_info = GratingPostureInfo(
                image_id = torch.as_tensor(row["image_id"], dtype = torch.int32),
                gratering_side_x_cm = torch.as_tensor(row["gratering_side_x_cm"], dtype = torch.float32),
                gratering_side_y_cm = torch.as_tensor(row["gratering_side_y_cm"], dtype = torch.float32),
                gratering_side_angle_deg = torch.as_tensor(row["gratering_side_angle_deg"], dtype = torch.float32),
                grating_side_rotation_deg = torch.as_tensor(row["grating_side_rotation_deg"], dtype = torch.float32)
            )

            logger.debug(f"Loaded grating posture info: {grating_info}")
            grating_posture_info.append(grating_info)
        
        return grating_posture_info