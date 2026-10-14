from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from imghg.geometry import ground_quad_from_view
from imghg.warp import warp_target_to_ground


# -----------------------------------------------------------------------------
# Phase 1 configuration
# -----------------------------------------------------------------------------
IMAGE_PATH = ROOT / "inputs" / "cone.png"
OUTPUT_PATH = ROOT / "outputs" / "ground_cone.png"

G1 = np.array([-0.30, 4.00, 0.00], dtype=float)
G2 = np.array([0.30, 4.00, 0.00], dtype=float)
CAMERA_CENTER = np.array([0.00, 0.00, 1.60], dtype=float)
OBJECT_HEIGHT = 0.70
PIXELS_PER_METER = 500.0
PADDING_PX = 20


def main():
    image = cv2.imread(str(IMAGE_PATH), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(
            f"Target image not found: {IMAGE_PATH}\n"
            "Place a PNG image at inputs/cone.png."
        )

    quad, (h1, h2), (p1, p2) = ground_quad_from_view(
        G1,
        G2,
        CAMERA_CENTER,
        OBJECT_HEIGHT,
    )

    ground_image, homography, metadata = warp_target_to_ground(
        image,
        quad,
        pixels_per_meter=PIXELS_PER_METER,
        padding_px=PADDING_PX,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not cv2.imwrite(str(OUTPUT_PATH), ground_image):
        raise RuntimeError(f"Failed to save: {OUTPUT_PATH}")

    print("\n=== Phase 1: Ground Image Generation ===")
    print(f"G1 = {G1}")
    print(f"G2 = {G2}")
    print(f"H1 = {h1}")
    print(f"H2 = {h2}")
    print(f"P1 = {p1}")
    print(f"P2 = {p2}")

    print("\nGround quad order:")
    print("[G1, G2, P2, P1]")
    print(quad)

    print("\nDestination quad [px]:")
    print(metadata["dst_quad_px"])

    print("\nHomography:")
    print(homography)

    print("\nOutput size:")
    print(metadata["output_size"])

    print("\nSaved:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
