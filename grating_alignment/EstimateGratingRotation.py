import torch
from typing import NamedTuple
from torch.nn import Module, Linear
from torchvision.models import resnet18
from torchvision import transforms
from torchvision.transforms import functional as F
from torchvision.transforms import Compose, Normalize
from torchvision.models.resnet import ResNet

class GratingRotationPredictorWithFftResnet18(Module):

    def __init__(self):

        super().__init__()

        self.__resnet18_rgb_feature_extractor: ResNet = resnet18(weights = None)
        self.__resnet18_rgb_feature_extractor.fc = Linear(self.__resnet18_rgb_feature_extractor.fc.in_features, self.__resnet18_rgb_feature_extractor.fc.in_features / 2)

        # convert the image into grayscale image and perform fft
        # fft result is converted into a 3-channel tensor
        # the first channel is the magnitude, the second channel is the angle, the third channel is the real part
        self.__fft_transform: Compose = Compose([
            F.rgb_to_grayscale,
            Normalize(mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225]),
            transforms.Lambda(lambda x: torch.fft.rfft2(x, norm = "ortho")),
            transforms.Lambda(lambda x: torch.dstack((x.abs(), x.angle(), x.real()))) 
        ])

        self.__resnet18_fft_feature_extractor: ResNet = resnet18(weights = None)
        self.__resnet18_fft_feature_extractor.fc = Linear(self.__resnet18_fft_feature_extractor.fc.in_features, self.__resnet18_fft_feature_extractor.fc.in_features / 2)

        # after 
        self.__concat_transform: Compose = Compose([
            Linear(self.__resnet18_rgb_feature_extractor.fc.in_features + self.__resnet18_fft_feature_extractor.fc.in_features, 512),
            Linear(512, 256),
            Linear(256, 128),
            Linear(128, 1)
        ])

    def forward(self, x: torch.Tensor) -> torch.Tensor:

        rgb_feature:torch.Tensor = self.__resnet18_rgb_feature_extractor(x)
        fft_feature:torch.Tensor = self.__resnet18_fft_feature_extractor(self.__fft_transform(x))

        concat_feature:torch.Tensor = torch.hstack((rgb_feature, fft_feature))

        del rgb_feature, fft_feature

        return self.__concat_transform(concat_feature)