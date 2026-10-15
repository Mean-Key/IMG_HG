from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from imghg.geometry import ground_quad_from_view, project_world_point
from imghg.warp import warp_target_to_ground

IMAGE_PATH = ROOT / "inputs" / "cone.png"
OUTPUT_DIR = ROOT / "outputs"

G1 = np.array([-0.30, 4.00, 0.00])
G2 = np.array([0.30, 4.00, 0.00])
CAMERA_CENTER = np.array([0.00, 0.00, 1.60])
OBJECT_HEIGHT = 0.70
PIXELS_PER_METER = 500.0

IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080

K = np.array(
    [
        [1000.0, 0.0, 960.0],
        [0.0, 1000.0, 540.0],
        [0.0, 0.0, 1.0],
    ],
    dtype=float,
)


def look_at_rt(camera_center, target, world_up=(0.0, 0.0, 1.0)):
    c = np.asarray(camera_center, dtype=float)
    target = np.asarray(target, dtype=float)
    world_up = np.asarray(world_up, dtype=float)

    z_axis = target - c
    z_axis /= np.linalg.norm(z_axis)

    x_axis = np.cross(z_axis, world_up)
    x_axis /= np.linalg.norm(x_axis)

    y_axis = np.cross(z_axis, x_axis)
    y_axis /= np.linalg.norm(y_axis)

    r = np.stack([x_axis, y_axis, z_axis])
    t = -r @ c
    return r, t


def ensure_rgba(image):
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    elif image.shape[2] == 3:
        alpha = np.full(image.shape[:2] + (1,), 255, dtype=np.uint8)
        image = np.concatenate([image, alpha], axis=2)
    return image


def render_rgba_to_quad(image_rgba, dst_quad, output_size):
    h, w = image_rgba.shape[:2]
    src = np.array(
        [
            [0.0, h - 1.0],
            [w - 1.0, h - 1.0],
            [w - 1.0, 0.0],
            [0.0, 0.0],
        ],
        dtype=np.float32,
    )
    dst = np.asarray(dst_quad, dtype=np.float32)
    homography = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(
        image_rgba,
        homography,
        output_size,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )


def render_ground_texture(ground_rgba, ground_dst_px, projected_quad, output_size):
    homography = cv2.getPerspectiveTransform(
        np.asarray(ground_dst_px, dtype=np.float32),
        np.asarray(projected_quad, dtype=np.float32),
    )
    return cv2.warpPerspective(
        ground_rgba,
        homography,
        output_size,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )


def composite_on_white(rgba):
    rgb = rgba[:, :, :3].astype(np.float32)
    alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
    white = np.full_like(rgb, 255.0)
    return np.clip(rgb * alpha + white * (1.0 - alpha), 0, 255).astype(np.uint8)


def crop_to_alpha_union(reference_rgba, illusion_rgba, pad=20):
    mask = (reference_rgba[:, :, 3] > 0) | (illusion_rgba[:, :, 3] > 0)
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise RuntimeError("Rendered object is outside the image.")

    x0 = max(int(xs.min()) - pad, 0)
    x1 = min(int(xs.max()) + pad + 1, reference_rgba.shape[1])
    y0 = max(int(ys.min()) - pad, 0)
    y1 = min(int(ys.max()) + pad + 1, reference_rgba.shape[0])
    return x0, y0, x1, y1


def compute_rmse(a, b):
    diff = a.astype(np.float64) - b.astype(np.float64)
    return float(np.sqrt(np.mean(diff * diff)))


def compute_psnr(a, b):
    rmse = compute_rmse(a, b)
    if rmse == 0.0:
        return float("inf")
    return float(20.0 * np.log10(255.0 / rmse))


def compute_ssim(a, b):
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2
    scores = []

    for channel in range(3):
        x = a[:, :, channel]
        y = b[:, :, channel]

        mu_x = cv2.GaussianBlur(x, (11, 11), 1.5)
        mu_y = cv2.GaussianBlur(y, (11, 11), 1.5)
        mu_x2 = mu_x * mu_x
        mu_y2 = mu_y * mu_y
        mu_xy = mu_x * mu_y

        sigma_x2 = cv2.GaussianBlur(x * x, (11, 11), 1.5) - mu_x2
        sigma_y2 = cv2.GaussianBlur(y * y, (11, 11), 1.5) - mu_y2
        sigma_xy = cv2.GaussianBlur(x * y, (11, 11), 1.5) - mu_xy

        numerator = (2.0 * mu_xy + c1) * (2.0 * sigma_xy + c2)
        denominator = (mu_x2 + mu_y2 + c1) * (sigma_x2 + sigma_y2 + c2)
        scores.append(float(np.mean(numerator / denominator)))

    return float(np.mean(scores))


def make_comparison(reference, illusion):
    diff = cv2.absdiff(reference, illusion)
    scale = reference.shape[0] / diff.shape[0]
    if not np.isclose(scale, 1.0):
        diff = cv2.resize(diff, None, fx=scale, fy=scale)

    return np.concatenate([reference, illusion, diff], axis=1)


def main():
    target = cv2.imread(str(IMAGE_PATH), cv2.IMREAD_UNCHANGED)
    if target is None:
        raise FileNotFoundError(f"Input image not found: {IMAGE_PATH}")
    target = ensure_rgba(target)

    quad, (h1, h2), (p1, p2) = ground_quad_from_view(
        G1,
        G2,
        CAMERA_CENTER,
        OBJECT_HEIGHT,
    )

    ground_rgba, _, metadata = warp_target_to_ground(
        target,
        quad,
        PIXELS_PER_METER,
    )
    ground_rgba = ensure_rgba(ground_rgba)

    target_center = (G1 + G2 + h1 + h2) / 4.0
    r, t = look_at_rt(CAMERA_CENTER, target_center)

    upright_quad_px = np.array(
        [
            project_world_point(G1, K, r, t),
            project_world_point(G2, K, r, t),
            project_world_point(h2, K, r, t),
            project_world_point(h1, K, r, t),
        ],
        dtype=np.float32,
    )

    ground_quad_px = np.array(
        [
            project_world_point(G1, K, r, t),
            project_world_point(G2, K, r, t),
            project_world_point(p2, K, r, t),
            project_world_point(p1, K, r, t),
        ],
        dtype=np.float32,
    )

    output_size = (IMAGE_WIDTH, IMAGE_HEIGHT)
    reference_rgba = render_rgba_to_quad(target, upright_quad_px, output_size)
    illusion_rgba = render_ground_texture(
        ground_rgba,
        metadata["dst_quad_px"],
        ground_quad_px,
        output_size,
    )

    reference = composite_on_white(reference_rgba)
    illusion = composite_on_white(illusion_rgba)

    x0, y0, x1, y1 = crop_to_alpha_union(reference_rgba, illusion_rgba)
    reference_crop = reference[y0:y1, x0:x1]
    illusion_crop = illusion[y0:y1, x0:x1]

    rmse = compute_rmse(reference_crop, illusion_crop)
    psnr = compute_psnr(reference_crop, illusion_crop)
    ssim = compute_ssim(reference_crop, illusion_crop)

    corner_error = np.linalg.norm(upright_quad_px - ground_quad_px, axis=1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTPUT_DIR / "ground_cone.png"), ground_rgba)
    cv2.imwrite(str(OUTPUT_DIR / "reference_upright.png"), reference)
    cv2.imwrite(str(OUTPUT_DIR / "preview_from_camera.png"), illusion)
    cv2.imwrite(
        str(OUTPUT_DIR / "comparison.png"),
        make_comparison(reference_crop, illusion_crop),
    )

    metrics_text = (
        f"RMSE: {rmse:.6f}\n"
        f"PSNR: {psnr:.6f} dB\n"
        f"SSIM: {ssim:.9f}\n"
        f"Corner errors [px]: {corner_error.tolist()}\n"
        f"Max corner error [px]: {float(corner_error.max()):.12f}\n"
        f"Crop: x={x0}:{x1}, y={y0}:{y1}\n"
    )
    (OUTPUT_DIR / "metrics.txt").write_text(metrics_text, encoding="utf-8")

    print()
    print("Phase 1 reference comparison")
    print("----------------------------")
    print(f"RMSE : {rmse:.6f}")
    print(f"PSNR : {psnr:.6f} dB")
    print(f"SSIM : {ssim:.9f}")
    print(f"Corner errors [px] : {corner_error}")
    print(f"Max corner error   : {corner_error.max():.12f} px")
    print()
    print("Saved:")
    print(OUTPUT_DIR / "reference_upright.png")
    print(OUTPUT_DIR / "preview_from_camera.png")
    print(OUTPUT_DIR / "comparison.png")
    print(OUTPUT_DIR / "metrics.txt")


if __name__ == "__main__":
    main()
