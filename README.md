# IMG_HG — 평면 아나모픽 이미지 생성 연구

관찰자의 **거리와 눈높이**를 입력받아, 지정된 평면 위의 그림이 해당 위치에서 원하는 비율로 보이도록 원근을 보정하는 연구입니다. 탑뷰에서는 늘어나거나 왜곡된 그림이 관찰 시점에서는 원래 형태로 보입니다.

![원본, 평면 탑뷰, 관찰 시점 비교](research/docs/assets/anamorphic_overview.png)

그림은 거리 3 m·눈높이 1.6 m의 **합성 시뮬레이션**입니다. 실제 인쇄·촬영 결과가 아니며, 관찰 영상은 확대해서 표시했습니다.

## 연구 문서

- [연구 대시보드](research/docs/00_연구_대시보드.md)
- [선행연구 조사와 인용 검증 상태](research/docs/01_선행연구.md)
- [수학 모델·실험 설계](research/docs/02_방법과_실험설계.md)
- [실험 결과](research/docs/03_실험결과.md)
- [논문 초안 v0.1](research/docs/04_논문초안.md)
- [후속 실험 계획](research/docs/05_후속실험.md)

## 코드와 데이터

[설치·재현 방법](research/README.md) · [실험 코드](research/experiment.py) · [원시 결과](research/results/pilot-002) · [참고문헌](research/references.bib)

현재 거리·높이 12조합, 관찰 위치 변화 245조건, 가정된 측정 오차 1,000표본의 초기 실험을 기록했습니다. 기본 호모그래피 변환 자체는 알려진 방법이며, 신규성·실물 정확도·사람의 착시 경험은 아직 검증하지 않았습니다.

## Notion

[Image Homography 연구 페이지](https://app.notion.com/p/Image-Homography-3f3e5ab1122c8048a7afc1ed2a74b266)를 참고 문서 공간으로 지정했습니다. **Notion 게시 완료는 확인되지 않았습니다.** GitHub의 문서·코드·결과를 연구 기록으로 관리합니다.

Notion으로 옮길 Markdown·그림 묶음은 다음 명령으로 만들 수 있습니다.

```bash
python research/package_notion.py
```

생성 위치: `research/exports/IMG_HG_Notion_import.zip`. ZIP 생성에는 Python 표준 라이브러리만 필요합니다.
