# 평면 아나모픽 연구 실험 재현

[연구 대시보드](docs/00_연구_대시보드.md)에서 선행연구·방법·결과·논문 초안을 확인할 수 있습니다. 본 폴더는 초기 연구 자료이며 완성된 서비스나 최종 논문 결과가 아닙니다.

## 설치

저장소 루트에서 Python 3.12와 uv를 사용합니다. Linux CPU 환경에서 검증했으며 GPU는 필요하지 않습니다.

```bash
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python --only-binary :all: research/requirements.lock
source .venv/bin/activate
export MPLBACKEND=Agg
```

`requirements.lock`에는 검증에 사용한 의존성 전체 버전이 고정되어 있습니다. GUI 창 대신 PNG·CSV·JSON 결과를 저장합니다. 다른 운영체제나 별도 머신에서의 설치는 검증하지 않았습니다.

## 실험 실행

```bash
python research/experiment.py --output research/results/local-reproduction
```

출력 디렉터리가 비어 있지 않으면 기존 실험을 덮어쓰지 않고 실패합니다. 다른 run은 새로운 디렉터리로 실행하세요. `local-*` 결과는 Git에서 제외되어 있으며, 보존할 실험은 검토 후 별도 run 이름으로 관리합니다.

코드는 이상적 평면과 핀홀 카메라를 사용해 다음을 실행합니다.

- 거리 4종 × 눈높이 3종에서 무보정·아핀·투영 보정 비교: 36행, 조건마다 441점.
- 고정 출력물의 관찰 위치 변화: 245조건.
- 생성기 입력의 측정 오차: 가정된 분포 1,000표본, seed=20261008.
- 호모그래피와 별도 3차원 투영, 광선-평면 교차의 일관성 검사.
- 탑뷰·관찰 시점 그림과 유한 해상도 영상 오차 생성.

## 보존된 결과

[results/pilot-002](results/pilot-002)는 문서에서 보고한 run입니다.

| 파일 | 내용 |
|---|---|
| `summary.json` | 설정, 코드 SHA-256, 패키지 버전, seed, 요약 |
| `baseline.csv` | 거리·높이·방법별 기하 오차 |
| `viewpoint_sensitivity.csv` | 고정 출력물의 관찰 위치 변화 |
| `measurement_error_monte_carlo.csv` | 가정된 입력 측정 오차 1,000표본 |
| `render_quality.csv` | 한 합성 그림의 MSE·PSNR |
| `*.png` | 기준 그림, 보정 출력물, 관찰 영상 및 도표 |

PILOT-001은 초기 클라우드 작업의 이전 run이며 이 저장소에는 PILOT-002만 포함했습니다. 두 run의 네 수치 CSV는 바이트 단위로 동일했습니다. 정확한 투영 보정의 0에 가까운 오차는 참 기하를 사용한 수치 검증이며, 실제 측정 정확도나 학술적 신규성을 입증하지 않습니다.

## 문헌과 출처

[references.bib](references.bib)와 [source_manifest.json](source_manifest.json)에 참고문헌과 열람한 파일의 URL·해시를 보관했습니다. 원문 열람과 서지 정보만 확인한 문헌은 [선행연구표](docs/01_선행연구.md)에서 구분합니다. 원문 PDF 사본은 저장소에 포함하지 않습니다.

## Notion 가져오기

저장소 루트에서 다음 명령을 실행합니다.

```bash
python research/package_notion.py
```

`research/exports/IMG_HG_Notion_import.zip`에 Markdown 6개와 설명 그림 3개를 묶습니다. 이 작업은 Notion에 자동 게시하지 않습니다. Notion 가져오기 후 링크·그림 표시 여부는 별도로 확인해야 합니다. 원격 게시 성공은 아직 확인되지 않았습니다.
