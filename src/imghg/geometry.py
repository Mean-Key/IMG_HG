import numpy as np


def compute_head_points(g1, g2, height, up=(0.0, 0.0, 1.0)):
    g1 = np.asarray(g1, dtype=float)
    g2 = np.asarray(g2, dtype=float)
    up = np.asarray(up, dtype=float)

    up_norm = np.linalg.norm(up)
    if np.isclose(up_norm, 0.0):
        raise ValueError("Up vector must be non-zero.")
    if height <= 0.0:
        raise ValueError("Object height must be positive.")

    up = up / up_norm
    offset = height * up
    return g1 + offset, g2 + offset


def project_point_to_ground(camera_center, point, ground_z=0.0):
    camera_center = np.asarray(camera_center, dtype=float)
    point = np.asarray(point, dtype=float)
    direction = point - camera_center

    if np.isclose(direction[2], 0.0):
        raise ValueError("Camera ray is parallel to the ground plane.")

    lam = (ground_z - camera_center[2]) / direction[2]
    projected = camera_center + lam * direction
    projected[2] = ground_z
    return projected


def ground_quad_from_view(g1, g2, camera_center, height, ground_z=0.0):
    g1 = np.asarray(g1, dtype=float)
    g2 = np.asarray(g2, dtype=float)
    h1, h2 = compute_head_points(g1, g2, height)
    p1 = project_point_to_ground(camera_center, h1, ground_z)
    p2 = project_point_to_ground(camera_center, h2, ground_z)
    quad = np.stack([g1, g2, p2, p1])
    return quad, (h1, h2), (p1, p2)


def camera_center_from_rt(r, t):
    """Return world-space camera center for X_cam = R X_world + t."""
    r = np.asarray(r, dtype=float).reshape(3, 3)
    t = np.asarray(t, dtype=float).reshape(3)
    return -r.T @ t


def project_world_point(point, k, r, t):
    """Project one world-space 3D point to a pixel using a pinhole camera."""
    point = np.asarray(point, dtype=float).reshape(3)
    k = np.asarray(k, dtype=float).reshape(3, 3)
    r = np.asarray(r, dtype=float).reshape(3, 3)
    t = np.asarray(t, dtype=float).reshape(3)

    point_cam = r @ point + t
    if point_cam[2] <= 0.0:
        raise ValueError("Point lies on or behind the camera plane.")

    uvw = k @ point_cam
    return uvw[:2] / uvw[2]


def reprojection_error(point_a, point_b, k, r, t):
    """Pixel distance between the projections of two world-space points."""
    uv_a = project_world_point(point_a, k, r, t)
    uv_b = project_world_point(point_b, k, r, t)
    return float(np.linalg.norm(uv_a - uv_b))
