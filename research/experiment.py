"""Reproducible synthetic planar anamorphosis pilot. No real-world claims."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

W, L = 2.0, 3.0  # plane dimensions in metres
CW, CH, FOCAL = 1024, 768, 800.0
TW, TH = 600, 900  # floor texture: approximately 300 pixels/metre
SOURCE_N = 512
K = np.array([[FOCAL, 0, CW/2], [0, FOCAL, CH/2], [0, 0, 1.]])
PLANE = np.array([[-W/2, L], [W/2, L], [W/2, 0], [-W/2, 0]])
UV_CORNERS = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])
UV_GRID = np.stack(np.meshgrid(np.linspace(0, 1, 21), np.linspace(0, 1, 21)), -1).reshape(-1, 2)


def transform(H, points):
    p = np.column_stack([points, np.ones(len(points))]) @ H.T
    assert np.all(np.abs(p[:, 2]) > 1e-10), 'Projection through infinity'
    return p[:, :2] / p[:, 2:]


def camera(distance, height, lateral=0.):
    C = np.array([lateral, -distance, height])
    target = np.array([0., L/2, 0.])
    forward = target-C
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0., 0., 1.])
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    R = np.vstack([right, down, forward])
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-12)
    assert np.linalg.det(R) > .999999
    t = -R @ C
    G = K @ np.column_stack([R[:, 0], R[:, 1], t])
    return G, R, C


def project_3d(points, R, C):
    # Independent 3-D camera route used to validate the planar homography.
    xyz = np.column_stack([points, np.zeros(len(points))])
    xyz_camera = (xyz-C) @ R.T
    assert np.all(xyz_camera[:, 2] > 0), 'Points behind observer'
    pixels = xyz_camera @ K.T
    return pixels[:, :2] / pixels[:, 2:]


def inside(points, eps=1e-8):
    return ((np.abs(points[:, 0]) <= W/2+eps) &
            (points[:, 1] >= -eps) & (points[:, 1] <= L+eps))


def target_map(G):
    # Largest image-centred square contained in the projected floor, with 10% margin.
    low, high = 0., float(min(CW, CH))/2-1
    for _ in range(60):
        half = (low+high)/2
        target = (UV_CORNERS-.5)*2*half + [CW/2, CH/2]
        if inside(transform(np.linalg.inv(G), target)).all():
            low = half
        else:
            high = half
    side = 2*low*.9
    assert side > 1
    return np.array([[side, 0, CW/2-side/2], [0, side, CH/2-side/2], [0, 0, 1.]])


def placements(G, target):
    exact = np.linalg.inv(G) @ target
    # Least-squares affine fit to the four exact physical corner locations.
    A = np.column_stack([UV_CORNERS, np.ones(4)])
    coeff = np.linalg.lstsq(A, transform(exact, UV_CORNERS), rcond=None)[0]
    affine = np.vstack([coeff.T, [0, 0, 1.]])
    naive_side = .9*min(W, L)
    naive = np.array([[naive_side, 0, -naive_side/2],
                      [0, -naive_side, L/2+naive_side/2], [0, 0, 1.]])
    return {'uncorrected': naive, 'affine_corner_fit': affine, 'projective': exact}


def errors(observed, expected):
    raw = np.sqrt(np.mean(np.sum((observed-expected)**2, axis=1)))
    # Similarity-aligned error isolates shape from translation, rotation and scale.
    x, y = observed-observed.mean(0), expected-expected.mean(0)
    u, s, vt = np.linalg.svd(x.T@y)
    correction = np.eye(2)
    correction[-1, -1] = np.linalg.det(u@vt)
    Q = u@correction@vt
    scale = np.trace(np.diag(s)@correction)/np.sum(x*x)
    aligned = scale*x@Q
    shape = np.sqrt(np.mean(np.sum((aligned-y)**2, axis=1)))
    return float(raw), float(shape)


def image_pattern():
    im = np.full((SOURCE_N, SOURCE_N, 3), 245, np.uint8)
    for p in range(0, SOURCE_N, 32):
        cv2.line(im, (p, 0), (p, SOURCE_N-1), (100, 100, 100), 1)
        cv2.line(im, (0, p), (SOURCE_N-1, p), (100, 100, 100), 1)
    cv2.circle(im, (256, 256), 150, (30, 170, 245), -1)
    cv2.putText(im, 'VIEW', (155, 273), cv2.FONT_HERSHEY_SIMPLEX, 1.7, (20, 20, 20), 4)
    cv2.rectangle(im, (5, 5), (506, 506), (40, 40, 210), 4)
    return im


def main(output):
    start = perf_counter()
    output.mkdir(parents=True, exist_ok=True)
    cv2.setNumThreads(2)
    cv2.setRNGSeed(20261008)
    rng = np.random.default_rng(20261008)
    records = []
    for distance in [1., 2., 3., 5.]:
        for height in [1.2, 1.6, 1.8]:
            G, R, C = camera(distance, height)
            target = target_map(G)
            expected = transform(target, UV_GRID)
            for name, mapping in placements(G, target).items():
                physical = transform(mapping, UV_GRID)
                observed = project_3d(physical, R, C)
                assert np.allclose(observed, transform(G, physical), atol=1e-9)
                raw, shape = errors(observed, expected)
                if name == 'projective':
                    assert raw < 1e-8
                    assert inside(physical).all()
                records.append(dict(distance_m=distance, height_m=height, method=name,
                                    target_side_px=target[0, 0], rmse_px=raw,
                                    shape_rmse_px=shape, normalized_rmse=raw/(np.sqrt(2)*target[0, 0]),
                                    out_of_region_fraction=float((~inside(physical)).mean())))
    baseline = pd.DataFrame(records)
    baseline.to_csv(output/'baseline.csv', index=False)

    nominal_G, R0, C0 = camera(3., 1.6)
    target = target_map(nominal_G)
    mapping = placements(nominal_G, target)['projective']
    expected = transform(target, UV_GRID)
    physical = transform(mapping, UV_GRID)
    rays = np.column_stack([expected, np.ones(len(expected))]) @ np.linalg.inv(K).T @ R0
    intersections = C0 + (-C0[2]/rays[:, 2])[:, None]*rays
    ray_plane_error = float(np.max(np.linalg.norm(intersections[:, :2]-physical, axis=1)))
    assert ray_plane_error < 1e-10
    assert np.max(np.abs(intersections[:, 2])) < 1e-10
    rows = []
    for dd in [-.5, -.25, -.1, 0., .1, .25, .5]:
        for dh in [-.2, -.1, -.05, 0., .05, .1, .2]:
            for dx in [-.3, -.15, 0., .15, .3]:
                _, R, C = camera(3+dd, 1.6+dh, dx)
                raw, shape = errors(project_3d(physical, R, C), expected)
                rows.append(dict(delta_distance_m=dd, delta_height_m=dh, delta_lateral_m=dx,
                                 rmse_px=raw, shape_rmse_px=shape,
                                 normalized_rmse=raw/(np.sqrt(2)*target[0, 0])))
    sensitivity = pd.DataFrame(rows)
    sensitivity.to_csv(output/'viewpoint_sensitivity.csv', index=False)

    # Hypothetical independent measurement error, NOT an empirically fitted distribution.
    rows = []
    for index, (ed, eh, ex) in enumerate(rng.normal(size=(1000, 3))*[.05, .03, .02]):
        estimated_G, _, _ = camera(3+ed, 1.6+eh, ex)
        perturbed_mapping = np.linalg.inv(estimated_G) @ target
        physical_points = transform(perturbed_mapping, UV_GRID)
        raw, shape = errors(project_3d(physical_points, R0, C0), expected)
        rows.append(dict(sample=index, distance_error_m=ed, height_error_m=eh,
                         lateral_error_m=ex, rmse_px=raw, shape_rmse_px=shape,
                         out_of_region_fraction=float((~inside(physical_points)).mean())))
    monte_carlo = pd.DataFrame(rows)
    monte_carlo.to_csv(output/'measurement_error_monte_carlo.csv', index=False)

    pattern = image_pattern()
    cv2.imwrite(str(output/'desired.png'), pattern)
    source_to_unit = np.diag([1/(SOURCE_N-1), 1/(SOURCE_N-1), 1.])
    plane_to_texture = np.array([[(TW-1)/W, 0, (TW-1)/2],
                                 [0, -(TH-1)/L, TH-1], [0, 0, 1.]])
    ideal = cv2.warpPerspective(pattern, target@source_to_unit, (CW, CH))
    target_mask = cv2.warpPerspective(np.full((SOURCE_N, SOURCE_N),255,np.uint8),
                                     target@source_to_unit, (CW,CH), flags=cv2.INTER_NEAREST)
    mask = cv2.erode(target_mask, np.ones((5,5),np.uint8)) > 0
    fig, axes = plt.subplots(3, 2, figsize=(10, 13), layout='constrained')
    render_rows = []
    for row, (name, m) in enumerate(placements(nominal_G, target).items()):
        texture = cv2.warpPerspective(pattern, plane_to_texture@m@source_to_unit, (TW,TH))
        observed = cv2.warpPerspective(texture, nominal_G@np.linalg.inv(plane_to_texture), (CW,CH))
        mse = float(np.mean((observed[mask].astype(float)-ideal[mask].astype(float))**2))
        render_rows.append(dict(method=name, mse=mse, psnr_db=float(10*np.log10(255**2/mse)),
                                roi_pixels=int(mask.sum())))
        cv2.imwrite(str(output/f'{name}_topview.png'), texture)
        cv2.imwrite(str(output/f'{name}_observer.png'), observed)
        axes[row,0].imshow(cv2.cvtColor(texture,cv2.COLOR_BGR2RGB), extent=[-W/2,W/2,0,L])
        axes[row,0].set_title(name+' / top view'); axes[row,0].set_xlabel('X (m)'); axes[row,0].set_ylabel('Y (m)')
        axes[row,1].imshow(cv2.cvtColor(observed,cv2.COLOR_BGR2RGB)); axes[row,1].set_title(name+' / observer view')
        axes[row,1].axis('off')
    fig.savefig(output/'baseline_views.png', dpi=150); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(11, 5), layout='constrained')
    for ax, name, title in zip(axes, ['desired', 'projective_topview', 'projective_observer'],
                              ['Desired image', 'Printed plane: top view', 'Observer: 3 m distance, 1.6 m eye height']):
        image = cv2.cvtColor(cv2.imread(str(output/(name+'.png'))), cv2.COLOR_BGR2RGB)
        ax.imshow(image); ax.set_title(title); ax.axis('off')
        if name.endswith('observer'):
            ax.set_xlim(430, 594); ax.set_ylim(466, 302)
    fig.savefig(output/'anamorphic_overview.png', dpi=150); plt.close(fig)
    pd.DataFrame(render_rows).to_csv(output/'render_quality.csv',index=False)
    fig, axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,metric in zip(axes,['rmse_px','shape_rmse_px']):
        table=sensitivity[sensitivity.delta_lateral_m==0].pivot(index='delta_height_m',columns='delta_distance_m',values=metric)
        im=ax.imshow(table.values,origin='lower',aspect='auto',cmap='magma')
        ax.set_xticks(range(len(table.columns)),[f'{v:+.2f}' for v in table.columns])
        ax.set_yticks(range(len(table.index)),[f'{v:+.2f}' for v in table.index])
        ax.set_xlabel('Distance offset (m)'); ax.set_ylabel('Eye-height offset (m)')
        ax.set_title(metric); fig.colorbar(im,ax=ax,label='px')
    fig.savefig(output/'sensitivity.png',dpi=150);plt.close(fig)

    # Directional sensitivity at nominal pose, using fixed print and re-aimed gaze.
    local=[]
    for name,axis in [('distance',0),('height',1),('lateral',2)]:
        delta=np.zeros(3);delta[axis]=.01
        _,Rp,Cp=camera(3+delta[0],1.6+delta[1],delta[2])
        _,Rm,Cm=camera(3-delta[0],1.6-delta[1],-delta[2])
        jac=(project_3d(physical,Rp,Cp)-project_3d(physical,Rm,Cm))/.02
        local.append(dict(parameter=name,rms_pixels_per_m=float(np.sqrt(np.mean(np.sum(jac*jac,axis=1))))))

    summary=dict(
        status='synthetic pilot; not a physical experiment or novelty demonstration',
        created_utc=datetime.now(timezone.utc).isoformat(), seed=20261008,
        model=dict(plane_width_m=W,plane_depth_m=L,image_width_px=CW,image_height_px=CH,
                   focal_length_px=FOCAL,look_at=[0,L/2,0],floor_texture_px=[TW,TH],
                   nominal_distance_m=3,nominal_height_m=1.6,nominal_target_side_px=float(target[0,0])),
        counts=dict(baseline_configurations=12,baseline_method_rows=len(baseline),
                    points_per_configuration=len(UV_GRID),viewpoint_conditions=len(sensitivity),
                    monte_carlo_samples=len(monte_carlo)),
        baseline_mean_rmse_px=baseline.groupby('method').rmse_px.mean().to_dict(),
        baseline_mean_shape_rmse_px=baseline.groupby('method').shape_rmse_px.mean().to_dict(),
        baseline_max_outside_fraction=baseline.groupby('method').out_of_region_fraction.max().to_dict(),
        monte_carlo_assumed_sigma_m=dict(distance=.05,height=.03,lateral=.02),
        monte_carlo_rmse_px=monte_carlo.rmse_px.quantile([.5,.95]).to_dict(),
        monte_carlo_shape_rmse_px=monte_carlo.shape_rmse_px.quantile([.5,.95]).to_dict(),
        local_sensitivity=local,render_quality=render_rows,
        independent_ray_plane_max_error_m=ray_plane_error,
        software={name:importlib.metadata.version(name) for name in ['numpy','opencv-python-headless','pandas','matplotlib']},
        python=platform.python_version(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        elapsed_seconds=perf_counter()-start)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True,help='Use a new directory for each preserved research run.')
    args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('Output directory is not empty; choose a new run directory to preserve prior results.')
    main(args.output)
