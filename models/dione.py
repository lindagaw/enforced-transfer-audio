"""Dione, the 4th concatenation, for ADDA."""

import torch.nn.functional as F
from torch import nn


class DioneEncoder(nn.Module):
    """Dione encoder model for ADDA."""

    def __init__(self):
        """Init LeNet encoder."""
        super(DioneEncoder, self).__init__()

        self.restored = False

        self.encoder = nn.Sequential(
            # 1st conv layer
            # input [48 x 272]
            # output [46 x 3072]
            #nn.Conv1d(in_channels=272, out_channels=3072, kernel_size=3),
            #nn.ReLU(),
            #nn.MaxPool1d(kernel_size=2, stride=2, padding=0),
            #nn.Dropout(),

            # 2nd conv layer
            # input [23, 3072]
            # output [21, 6144]
            #nn.Conv1d(in_channels=3072, out_channels=6144, kernel_size=3, stride=2),
            #nn.ReLU(),
            #nn.MaxPool1d(kernel_size=2, stride=2, padding=0),
            #nn.Dropout(),

            # 3rd conv layer
            # input [10, 6144]
            # output [8, 6144]
            #nn.Conv1d(in_channels=6144, out_channels=6144, kernel_size=3, stride=2),
            #nn.ReLU(),
            #nn.MaxPool1d(kernel_size=2, stride=2, padding=0),
            #nn.Dropout(),

            # 4th conv layer
            # input [4, 6144]
            # output [2, 3072]
            #nn.Conv1d(in_channels=6144, out_channels=3072, kernel_size=1, stride=1),
            #nn.ReLU(),
            #nn.MaxPool1d(kernel_size=1, stride=1, padding=0),
            #nn.Dropout(),
            nn.Flatten(),
            nn.Linear(3072, 4096),
        )

        self.fc1 = nn.Sequential(
            #nn.Flatten(),
            #nn.Linear(3072, 4096),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.Dropout()
            #nn.Linear(4096, 5)
        )

    def forward(self, input):
        """Forward the LeNet."""
        conv_out = self.encoder(input)
        #feat = self.fc1(conv_out.view(-1, 3072 * 1))
        feat = self.fc1(conv_out)
        return feat


class DioneClassifier(nn.Module):
    """LeNet classifier model for ADDA."""
    def __init__(self):
        """Init LeNet encoder."""
        super(DioneClassifier, self).__init__()
        #self.fc2 = nn.Linear(4096, 2)
        self.fc2 = nn.Linear(4096, 2)

    def forward(self, feat):
        """Forward the LeNet classifier."""
        out = F.dropout(F.relu(feat), training=self.training)
        out = self.fc2(out)
        return out
