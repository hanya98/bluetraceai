"""
models/model1_arch.py
=====================
AttentionUNet architecture — copied VERBATIM from `untitiled0.ipynb`.
Do NOT modify this file.  All preprocessing decisions are locked to the
notebook's exact implementation.
"""
import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    """Two 3x3 conv layers, each followed by BatchNorm + ReLU."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class AttentionGate(nn.Module):
    """
    Takes:
      - g: gating signal from the decoder (coarser, deeper features)
      - x: skip connection from the encoder (finer, shallower features)
    Outputs: x reweighted by a learned attention map (same shape as x)
    """

    def __init__(
        self, g_channels: int, x_channels: int, inter_channels: int
    ) -> None:
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(g_channels, inter_channels, kernel_size=1),
            nn.BatchNorm2d(inter_channels),
        )
        self.W_x = nn.Sequential(
            # stride=2 to match g's spatial size
            nn.Conv2d(x_channels, inter_channels, kernel_size=1, stride=2),
            nn.BatchNorm2d(inter_channels),
        )
        self.psi = nn.Sequential(
            nn.Conv2d(inter_channels, 1, kernel_size=1),
            nn.BatchNorm2d(1),
            nn.Sigmoid(),
        )
        self.relu = nn.ReLU(inplace=True)
        self.upsample = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)

    def forward(self, g: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        g1 = self.W_g(g)
        x1 = self.W_x(x)
        psi = self.relu(g1 + x1)
        psi = self.psi(psi)
        psi = self.upsample(psi)   # back to x's spatial resolution
        return x * psi


class DownBlock(nn.Module):
    """ConvBlock followed by 2×2 max pooling.
    Returns (skip, down): pre-pool features and pooled output."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.conv = ConvBlock(in_channels, out_channels)
        self.pool = nn.MaxPool2d(kernel_size=2)

    def forward(self, x: torch.Tensor):
        skip = self.conv(x)
        down = self.pool(skip)
        return skip, down


class UpBlock(nn.Module):
    """Upsample decoder features, apply attention gate, concatenate, refine."""

    def __init__(
        self, in_channels: int, skip_channels: int, out_channels: int
    ) -> None:
        super().__init__()
        self.upsample = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
        self.attn = AttentionGate(
            g_channels=in_channels,
            x_channels=skip_channels,
            inter_channels=skip_channels // 2,
        )
        self.conv = ConvBlock(in_channels + skip_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        attn_skip = self.attn(g=x, x=skip)
        x = self.upsample(x)
        x = torch.cat([x, attn_skip], dim=1)
        return self.conv(x)


class AttentionUNet(nn.Module):
    """
    Attention U-Net — exactly as defined in `untitiled0.ipynb`.

    Default args match the trained checkpoint:
        in_channels=1, out_channels=1, base_channels=32
    """

    def __init__(
        self,
        in_channels: int = 1,
        out_channels: int = 1,
        base_channels: int = 32,
    ) -> None:
        super().__init__()
        c = base_channels

        # Encoder
        self.down1 = DownBlock(in_channels, c)       # 256 -> 128, c
        self.down2 = DownBlock(c, c * 2)              # 128 -> 64, 2c
        self.down3 = DownBlock(c * 2, c * 4)          # 64  -> 32, 4c
        self.down4 = DownBlock(c * 4, c * 8)          # 32  -> 16, 8c

        # Bottleneck
        self.bottleneck = ConvBlock(c * 8, c * 16)    # 16×16, 16c

        # Decoder (attention gates inside UpBlock)
        self.up4 = UpBlock(c * 16, c * 8, c * 8)     # -> 32×32
        self.up3 = UpBlock(c * 8,  c * 4, c * 4)     # -> 64×64
        self.up2 = UpBlock(c * 4,  c * 2, c * 2)     # -> 128×128
        self.up1 = UpBlock(c * 2,  c,     c)          # -> 256×256

        # Output head
        self.out_conv = nn.Conv2d(c, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skip1, x = self.down1(x)   # skip1: c,   256×256 | x: c,   128×128
        skip2, x = self.down2(x)   # skip2: 2c,  128×128 | x: 2c,  64×64
        skip3, x = self.down3(x)   # skip3: 4c,  64×64   | x: 4c,  32×32
        skip4, x = self.down4(x)   # skip4: 8c,  32×32   | x: 8c,  16×16

        x = self.bottleneck(x)     # 16c, 16×16

        x = self.up4(x, skip4)     # 8c,  32×32
        x = self.up3(x, skip3)     # 4c,  64×64
        x = self.up2(x, skip2)     # 2c,  128×128
        x = self.up1(x, skip1)     # c,   256×256

        return self.out_conv(x)    # out_channels, 256×256
