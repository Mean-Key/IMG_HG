import numpy as np

from imghg.geometry import (
    camera_center_from_rt,
    ground_quad_from_view,
    reprojection_error,
)


def look_at_rt(camera_center, target, world_up=(0.0, 0.0, 1.0)):
    camera_center = np.asarray(camera_center, dtype=float)
    target = np.asarray(target, dtype=float)
    world_up = np.asarray(world_up, dtype=float)

    z_axis = target - camera_center
    z_axis /= np.linalg.norm(z_axis)

    x_axis = np.cross(z_axis, world_up)
    x_axis /= np.linalg.norm(x_axis)

    y_axis = np.cross(z_axis, x_axis)
    y_axis /= np.linalg.norm(y_axis)

    r = np.stack([x_axis, y_axis, z_axis])
    t = -r @ camera_center
    return r, t


def test_projected_head_points_are_collinear_with_camera():
    g1 = np.array([-0.3, 4.0, 0.0])
    g2 = np.array([0.3, 4.0, 0.0])
    camera = np.array([0.0, 0.0, 1.6])

    quad, (h1, h2), (p1, p2) = ground_quad_from_view(
        g1, g2, camera, height=0.7
    )

    assert np.allclose(quad[0], g1)
    assert np.allclose(quad[1], g2)
    assert np.allclose(quad[2], p2)
    assert np.allclose(quad[3], p1)
    assert np.isclose(p1[2], 0.0)
    assert np.isclose(p2[2], 0.0)

    cross1 = np.cross(h1 - camera, p1 - camera)
    cross2 = np.cross(h2 - camera, p2 - camera)
    assert np.linalg.norm(cross1) < 1e-10
    assert np.linalg.norm(cross2) < 1e-10


def test_head_and_ground_projection_have_same_pixel_coordinates():
    g1 = np.array([-0.3, 4.0, 0.0])
    g2 = np.array([0.3, 4.0, 0.0])
    camera = np.array([0.0, 0.0, 1.6])
    height = 0.7

    k = np.array(
        [
            [1000.0, 0.0, 960.0],
            [0.0, 1000.0, 540.0],
            [0.0, 0.0, 1.0],
        ]
    )

    r, t = look_at_rt(camera, target=np.array([0.0, 4.0, 0.35]))
    recovered_camera = camera_center_from_rt(r, t)
    assert np.allclose(recovered_camera, camera, atol=1e-12)

    _, (h1, h2), (p1, p2) = ground_quad_from_view(
        g1, g2, recovered_camera, height
    )

    err1 = reprojection_error(h1, p1, k, r, t)
    err2 = reprojection_error(h2, p2, k, r, t)

    assert err1 < 1e-9
    assert err2 < 1e-9


def test_invalid_height_is_rejected():
    g1 = np.array([-0.3, 4.0, 0.0])
    g2 = np.array([0.3, 4.0, 0.0])
    camera = np.array([0.0, 0.0, 1.6])

    try:
        ground_quad_from_view(g1, g2, camera, height=0.0)
    except ValueError as exc:
        assert "height" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for non-positive object height.")
