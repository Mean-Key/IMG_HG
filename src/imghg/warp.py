import cv2
import numpy as np


def ground_xy_to_raster(quad_xy, pixels_per_meter=500.0, padding_px=20):
    quad_xy = np.asarray(quad_xy, dtype=np.float32)

    if quad_xy.shape != (4, 2):
        raise ValueError("quad_xy must have shape (4, 2).")
    if pixels_per_meter <= 0:
        raise ValueError("pixels_per_meter must be positive.")

    min_xy = quad_xy.min(axis=0)
    max_xy = quad_xy.max(axis=0)

    span_xy = max_xy - min_xy
    width = int(np.ceil(span_xy[0] * pixels_per_meter)) + 2 * padding_px + 1
    height = int(np.ceil(span_xy[1] * pixels_per_meter)) + 2 * padding_px + 1

    dst = (quad_xy - min_xy) * pixels_per_meter
    dst[:, 0] += padding_px
    dst[:, 1] += padding_px

    # World +Y is up in the ground map, image +Y is down.
    dst[:, 1] = height - 1 - dst[:, 1]

    return dst.astype(np.float32), (width, height), min_xy


def warp_target_to_ground(
    image,
    ground_quad,
    pixels_per_meter=500.0,
    padding_px=20,
):
    if image is None:
        raise ValueError("Input image is empty.")

    ground_quad = np.asarray(ground_quad, dtype=float)
    if ground_quad.shape != (4, 3):
        raise ValueError("ground_quad must have shape (4, 3).")

    h, w = image.shape[:2]

    # Source order: BL, BR, TR, TL
    src = np.array(
        [
            [0.0, h - 1.0],
            [w - 1.0, h - 1.0],
            [w - 1.0, 0.0],
            [0.0, 0.0],
        ],
        dtype=np.float32,
    )

    # Destination order: G1, G2, P2, P1
    dst, output_size, origin_xy = ground_xy_to_raster(
        ground_quad[:, :2],
        pixels_per_meter=pixels_per_meter,
        padding_px=padding_px,
    )

    homography = cv2.getPerspectiveTransform(src, dst)

    if image.ndim == 3 and image.shape[2] == 4:
        border_value = (0, 0, 0, 0)
    else:
        border_value = 0

    warped = cv2.warpPerspective(
        image,
        homography,
        output_size,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_value,
    )

    metadata = {
        "origin_xy": origin_xy,
        "pixels_per_meter": float(pixels_per_meter),
        "dst_quad_px": dst,
        "output_size": output_size,
    }

    return warped, homography, metadata
