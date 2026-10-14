import numpy as np

from imghg.geometry import ground_quad_from_view


def test_projected_head_points_are_collinear_with_camera():
    g1 = np.array([-0.3, 4.0, 0.0])
    g2 = np.array([0.3, 4.0, 0.0])
    camera = np.array([0.0, 0.0, 1.6])

    quad, (h1, h2), (p1, p2) = ground_quad_from_view(
        g1, g2, camera, height=0.7
    )

    assert np.allclose(quad[0], g1)
    assert np.allclose(quad[1], g2)
    assert np.isclose(p1[2], 0.0)
    assert np.isclose(p2[2], 0.0)

    cross1 = np.cross(h1 - camera, p1 - camera)
    cross2 = np.cross(h2 - camera, p2 - camera)
    assert np.linalg.norm(cross1) < 1e-10
    assert np.linalg.norm(cross2) < 1e-10
