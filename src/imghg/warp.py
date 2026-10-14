import cv2
import numpy as np


def ground_xy_to_raster(quad_xy, pixels_per_meter):
    quad_xy = np.asarray(quad_xy, dtype=np.float32)
    min_xy = quad_xy.min(axis=0)
    max_xy = quad_xy.max(axis=0)

    width = int(np.ceil((max_xy[0] - min_xy[0]) * pixels_per_meter)) + 1
    height = int(np.ceil((max_xy[1] - min_xy[1]) * pixels_per_meter)) + 1

    dst = (quad_xy - min_xy) * pixels_per_meter
    dst[:, 1] = height - 1 - dst[:, 1]
    return dst.astype(np.float32), (width, height), min_xy


def warp_target_to_ground(image, ground_quad, pixels_per_meter=500.0):
    if image is None:
        raise ValueError("Input image is empty.")

    ground_quad = np.asarray(ground_quad, dtype=float)
    if ground_quad.shape != (4, 3):
        raise ValueError("ground_quad must have shape (4, 3).")

    h, w = image.shape[:2]
    src = np.array(
        [
            [0, h - 1],
            [w - 1, h - 1],
            [w - 1, 0],
            [0, 0],
        ],
        dtype=np.float32,
    )

    dst, output_size, origin_xy = ground_xy_to_raster(
        ground_quad[:, :2], pixels_per_meter
    )
    homography = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(image, homography, output_size)

    metadata = {
        "origin_xy": origin_xy,
        "pixels_per_meter": float(pixels_per_meter),
        "dst_quad_px": dst,
    }
    return warped, homography, metadata
