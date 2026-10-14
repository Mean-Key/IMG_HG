# IMG_HG — View-Dependent Ground Image

Ground points 두 점과 기준 카메라 시점을 이용해, 세워진 평면 이미지가 바닥에 놓였을 때 기준 시점에서 원래 형태로 보이도록 ground texture를 생성하는 프로젝트입니다.

## Current pipeline

```text
G1, G2 (fixed ground points)
        +
object height
        ↓
H1, H2 (upright head points)
        +
reference camera center C
        ↓
ray-ground intersection
        ↓
P1, P2
        ↓
Ground quad = [G1, G2, P2, P1]
        ↓
Homography warp
        ↓
ground image
```

핵심 조건은 아래 두 ray가 각각 동일한 image ray를 공유하는 것입니다.

```text
C -> H1 -> P1
C -> H2 -> P2
```

따라서 기준 카메라에서는 바닥의 `P1`, `P2`가 세워진 평면의 `H1`, `H2`와 같은 방향에 보입니다.

## Repository structure

```text
IMG_HG/
├─ src/
│  └─ imghg/
│     ├─ __init__.py
│     ├─ geometry.py      # G/H/P geometry
│     └─ warp.py          # target image -> ground texture
├─ scripts/
│  └─ make_ground_image.py
├─ tests/
│  └─ test_geometry.py
├─ inputs/                # target images and future calibration inputs
├─ outputs/               # generated ground images
├─ experiments/           # viewpoint/depth/robot experiments
└─ research/              # legacy pilot documents and previous experiments
```

`research/`는 이전 pilot 자료 보존용입니다. 새 구현은 `src/`, `scripts/`, `tests/`, `experiments/`를 기준으로 진행합니다.

## Phase 1

현재 목표는 하나입니다.

> `G1, G2 + camera center + target image + object height`로 기준 시점에서 세워진 평면처럼 보이는 ground image를 생성한다.

현재 구현은 ground plane을 `z=0`으로 가정합니다.

### Example

```bash
python scripts/make_ground_image.py \
  --image inputs/cone.png \
  --g1=-0.30,4.0,0.0 \
  --g2=0.30,4.0,0.0 \
  --camera=0.0,0.0,1.6 \
  --height=0.70 \
  --output outputs/ground_cone.png
```

출력 시 `H1`, `H2`, `P1`, `P2`, homography와 ground texture 위치 정보가 함께 표시됩니다.

## Next phases

```text
Phase 1  Ground image generation
Phase 2  Viewpoint sweep / valid-view region
Phase 3  Monocular depth
Phase 4  Stereo depth
Phase 5  Multi-view reconstruction
Phase 6  Robot obstacle avoidance
```

SRWarp는 Phase 1 geometry가 검증된 뒤 `cv2.warpPerspective` baseline과 교체/비교합니다.
