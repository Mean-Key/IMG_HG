import argparse
from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from imghg.geometry import ground_quad_from_view
from imghg.warp import warp_target_to_ground


def parse_vec3(text):
    values = [float(v) for v in text.split(",")]
    if len(values) != 3:
        raise argparse.ArgumentTypeError("Expected x,y,z")
    return np.array(values, dtype=float)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--g1", type=parse_vec3, required=True)
    parser.add_argument("--g2", type=parse_vec3, required=True)
    parser.add_argument("--camera", type=parse_vec3, required=True)
    parser.add_argument("--height", type=float, required=True)
    parser.add_argument("--ppm", type=float, default=500.0)
    parser.add_argument("--output", default="outputs/ground_image.png")
    args = parser.parse_args()

    image = cv2.imread(args.image, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(args.image)

    quad, (h1, h2), (p1, p2) = ground_quad_from_view(
        args.g1, args.g2, args.camera, args.height
    )
    warped, homography, metadata = warp_target_to_ground(image, quad, args.ppm)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), warped)

    print(f"G1: {args.g1}")
    print(f"G2: {args.g2}")
    print(f"H1: {h1}")
    print(f"H2: {h2}")
    print(f"P1: {p1}")
    print(f"P2: {p2}")
    print("Ground quad order: G1, G2, P2, P1")
    print(f"Output: {output}")
    print(f"Origin XY: {metadata['origin_xy']}")
    print(f"Homography:\n{homography}")


if __name__ == "__main__":
    main()
