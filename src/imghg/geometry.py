import numpy as np


def compute_head_points(g1, g2, height, up=(0.0, 0.0, 1.0)):
    g1 = np.asarray(g1, dtype=float)
    g2 = np.asarray(g2, dtype=float)
    up = np.asarray(up, dtype=float)
    up = up / np.linalg.norm(up)
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
