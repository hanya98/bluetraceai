import torch
from PIL import Image
import numpy as np

from model1_arch import AttentionUNet


CHECKPOINT_PATH = r"attention_unet_best.pth"
IMAGE_PATH = r"PUT_YOUR_256x256_SAR_PNG_HERE"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Device:", device)

# Create exactly the architecture used during training
model = AttentionUNet(
    in_channels=1,
    out_channels=1,
    base_channels=32
).to(device)

# Load trained weights
model.load_state_dict(
    torch.load(CHECKPOINT_PATH, map_location=device)
)

model.eval()

# Same preprocessing used during Model 1 training
img = Image.open(IMAGE_PATH).convert("L")

if img.size != (256, 256):
    raise ValueError(f"Expected 256x256 image, got {img.size}")

arr = np.array(img, dtype=np.float32) / 255.0

x = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).to(device)

with torch.no_grad():
    logits = model(x)
    probs = torch.sigmoid(logits)
    mask = (probs > 0.5).float()

print("Input shape:", x.shape)
print("Output shape:", logits.shape)
print("Positive pixels:", int(mask.sum().item()))
print("Mean probability:", float(probs.mean().item()))

print("\nModel 1 inference successful.")