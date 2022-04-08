#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 16 16:39:44 2022

@author: lferiani
"""
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor



class CNNFromTierpsyBase(nn.Module):

    def __init__(self):
        super().__init__()
        self.conv_layers = nn.Sequential()
        self.fc_layers_with_dropout = nn.Sequential()

    def GlobalMaxPool2d(self, input_tensor):
        # this was missing from the pytorch adaptation of avelino's cnn
        # it's tensorflow's GlobalMaxPooling2D
        # makes the network robust against roi size change,
        # since it removes x,y dimensions
        out = F.max_pool2d(
            input_tensor, kernel_size=input_tensor.size()[-2:])
        return out

    def forward(self, x):
        x = self.conv_layers(x)  # convolutional layers
        x = self.GlobalMaxPool2d(x)  # maximum of each feature map
        x = x.view(x.shape[0], -1)  # 4d -> 2d tensor, x.shape[0] is batch_size
        x = self.fc_layers_with_dropout(x)  # fully connected layers
        x = x.squeeze()  # BCEwithlogitsloss wants same size as labels (1d)
        return x


class CNNFromTierpsy(CNNFromTierpsyBase):

    def __init__(self):
        super().__init__()

        # convolutional layers
        self.conv_layers = nn.Sequential(
            # conv 0
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/2 height, width, (160)
            # conv 1
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/4 height, width  (80)
            # conv2
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/8 height, width (40)
            # conv3
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            )

        # fully connected layers
        self.fc_layers_with_dropout = nn.Sequential(
            nn.Linear(256, 512),
            nn.Dropout(p=0.5),
            nn.Linear(512, 64),
            nn.Dropout(p=0.5),
            nn.Linear(64, 1),
            )



class CNNFromTierpsyShallower(CNNFromTierpsyBase):

    def __init__(self):
        super().__init__()

        # convolutional layers
        self.conv_layers = nn.Sequential(
            # conv 0
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/2 height, width, (160)
            # conv 1
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/4 height, width  (80)
            # conv2
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/8 height, width (40)
            # conv3
            # nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            # nn.BatchNorm2d(256),
            # nn.ReLU(),
            # nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            # nn.BatchNorm2d(256),
            # nn.ReLU(),
            )

        # fully connected layers
        self.fc_layers_with_dropout = nn.Sequential(
            nn.Linear(128, 256),
            nn.Dropout(p=0.5),
            nn.Linear(256, 32),
            nn.Dropout(p=0.5),
            nn.Linear(32, 1),
            )



class CNNFromTierpsyDeeper(CNNFromTierpsyBase):

    def __init__(self):
        super().__init__()

        # convolutional layers
        self.conv_layers = nn.Sequential(
            # conv 0
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/2 height, width, (160)
            # conv 1
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/4 height, width  (80)
            # conv2
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/8 height, width (40)
            # conv3
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/8 height, width (20)
            # conv4
            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            )

        # fully connected layers
        self.fc_layers_with_dropout = nn.Sequential(
            nn.Linear(512, 1024),
            nn.Dropout(p=0.5),
            nn.Linear(1024, 128),
            nn.Dropout(p=0.5),
            nn.Linear(128, 1),
            )


class CNNFromTierpsyEvenShallower(CNNFromTierpsyBase):

    def __init__(self):
        super().__init__()

        # convolutional layers
        self.conv_layers = nn.Sequential(
            # conv 0
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/2 height, width, (160)
            # conv 1
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/4 height, width  (80)
            # conv2
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            # nn.MaxPool2d(kernel_size=2, stride=2),  # 1/8 height, width (40)
            # conv3
            # nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            # nn.BatchNorm2d(256),
            # nn.ReLU(),
            # nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            # nn.BatchNorm2d(256),
            # nn.ReLU(),
            )

        # fully connected layers
        self.fc_layers_with_dropout = nn.Sequential(
            nn.Linear(128, 128),
            nn.Dropout(p=0.5),
            nn.Linear(128, 32),
            nn.Dropout(p=0.5),
            nn.Linear(32, 1),
            )


class CNNFromTierpsyShallowest(CNNFromTierpsyBase):

    def __init__(self):
        super().__init__()

        # convolutional layers
        self.conv_layers = nn.Sequential(
            # conv 0
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/2 height, width, (160)
            # conv 1
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 1/4 height, width  (80)
            # conv 2
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            # conv2
            # nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            # nn.BatchNorm2d(128),
            # nn.ReLU(),
            # nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            # nn.BatchNorm2d(128),
            # nn.ReLU(),
            # nn.MaxPool2d(kernel_size=2, stride=2),  # 1/8 height, width (40)
            # conv3
            # nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            # nn.BatchNorm2d(256),
            # nn.ReLU(),
            # nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            # nn.BatchNorm2d(256),
            # nn.ReLU(),
            )

        # fully connected layers
        self.fc_layers_with_dropout = nn.Sequential(
            nn.Linear(128, 128),
            nn.Dropout(p=0.5),
            nn.Linear(128, 32),
            nn.Dropout(p=0.5),
            nn.Linear(32, 1),
            )

