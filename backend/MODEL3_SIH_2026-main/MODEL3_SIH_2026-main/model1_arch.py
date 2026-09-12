import torch.nn as nn
class DownBlock(nn.Module):
    """ConvBlock followed by 2x2 max pooling. Returns both the pre-pool feature map
    (needed later for skip connections) and the pooled output (goes deeper into encoder)."""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = ConvBlock(in_channels, out_channels)
        self.pool = nn.MaxPool2d(kernel_size=2)

    def forward(self, x):
        skip = self.conv(x)      # full-resolution features, saved for skip connection
        down = self.pool(skip)   # downsampled, passed to next encoder stage
        return skip, down
class AttentionGate(nn.Module):
    """
    Takes:
      - g: gating signal from the decoder (coarser, deeper features)
      - x: skip connection from the encoder (finer, shallower features)
    Outputs: x reweighted by a learned attention map (same shape as x)
    """
    def __init__(self, g_channels, x_channels, inter_channels):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(g_channels, inter_channels, kernel_size=1),
            nn.BatchNorm2d(inter_channels)
        )
        self.W_x = nn.Sequential(
            nn.Conv2d(x_channels, inter_channels, kernel_size=1, stride=2),  # stride=2 to match g's spatial size
            nn.BatchNorm2d(inter_channels)
        )
        self.psi = nn.Sequential(
            nn.Conv2d(inter_channels, 1, kernel_size=1),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )
        self.relu = nn.ReLU(inplace=True)
        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

    def forward(self, g, x):
        g1 = self.W_g(g)
        x1 = self.W_x(x)
        psi = self.relu(g1 + x1)
        psi = self.psi(psi)
        psi = self.upsample(psi)   # back to x's spatial resolution
        return x * psi
class UpBlock(nn.Module):
    """
    Upsamples decoder features, applies attention gate to the skip connection,
    concatenates both, then refines with a ConvBlock.
    """
    def __init__(self, in_channels, skip_channels, out_channels):
        super().__init__()
        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.attn = AttentionGate(g_channels=in_channels, x_channels=skip_channels, inter_channels=skip_channels // 2)
        self.conv = ConvBlock(in_channels + skip_channels, out_channels)

    def forward(self, x, skip):
        # x: deeper decoder features (before upsampling)
        # skip: corresponding encoder skip connection (finer resolution)
        attn_skip = self.attn(g=x, x=skip)   # reweight skip using attention (uses x at its original resolution)
        x = self.upsample(x)                 # upsample decoder features to match skip's resolution
        x = torch.cat([x, attn_skip], dim=1) # concatenate along channel dim
        x = self.conv(x)
        return x
class AttentionUNet(nn.Module):
    def __init__(self, in_channels=1, out_channels=1, base_channels=32):
        super().__init__()
        c = base_channels

        # Encoder
        self.down1 = DownBlock(in_channels, c)       # 256 -> 128, c
        self.down2 = DownBlock(c, c * 2)              # 128 -> 64, 2c
        self.down3 = DownBlock(c * 2, c * 4)          # 64 -> 32, 4c
        self.down4 = DownBlock(c * 4, c * 8)          # 32 -> 16, 8c

        # Bottleneck
        self.bottleneck = ConvBlock(c * 8, c * 16)     # 16x16, 16c

        # Decoder (with attention gates inside UpBlock)
        self.up4 = UpBlock(in_channels=c * 16, skip_channels=c * 8, out_channels=c * 8)   # -> 32x32
        self.up3 = UpBlock(in_channels=c * 8,  skip_channels=c * 4, out_channels=c * 4)   # -> 64x64
        self.up2 = UpBlock(in_channels=c * 4,  skip_channels=c * 2, out_channels=c * 2)   # -> 128x128
        self.up1 = UpBlock(in_channels=c * 2,  skip_channels=c,     out_channels=c)       # -> 256x256

        # Output head
        self.out_conv = nn.Conv2d(c, out_channels, kernel_size=1)

    def forward(self, x):
        skip1, x = self.down1(x)   # skip1: c, 256x256   | x: c, 128x128
        skip2, x = self.down2(x)   # skip2: 2c, 128x128  | x: 2c, 64x64
        skip3, x = self.down3(x)   # skip3: 4c, 64x64    | x: 4c, 32x32
        skip4, x = self.down4(x)   # skip4: 8c, 32x32    | x: 8c, 16x16

        x = self.bottleneck(x)     # 16c, 16x16

        x = self.up4(x, skip4)     # 8c, 32x32
        x = self.up3(x, skip3)     # 4c, 64x64
        x = self.up2(x, skip2)     # 2c, 128x128
        x = self.up1(x, skip1)     # c, 256x256

        return self.out_conv(x)    # out_channels, 256x256
class ConvBlock(nn.Module):
    """Two 3x3 conv layers, each followed by BatchNorm + ReLU."""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)
