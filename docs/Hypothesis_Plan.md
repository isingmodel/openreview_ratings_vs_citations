# 심층 분석 가설 및 계획 (Hypothesis Plan)

기존의 단순 상관관계(Correlation) 분석을 넘어, 리뷰 데이터와 인용 수 간의 더 깊은 관계를 파헤치기 위한 5가지 창의적 가설과 검증 계획입니다.

---

## 1. 양극화 가설 (The Polarization Hypothesis)
> *"천재적인 아이디어는 초기에는 호불호가 극명하게 갈린다."*

*   **가설 내용**: 리뷰 점수의 **평균(Mean)**보다 **분산(Variance)**이 높은 논문이 추후 인용 수가 더 높을 것이다. 즉, 모든 리뷰어가 '6점'을 준 논문(안전한 논문)보다, '3점, 9점, 10점'을 받은 논문(논쟁적 논문)이 학계에 더 큰 충격을 준다.
*   **분석 방법**:
    *   리뷰 점수의 표준편차(Standard Deviation) 계산.
    *   `Rating Variance` vs `Log Citations` 상관관계 분석.
    *   특정 그룹(High Variance)의 인용 수 분포 비교.
*   **필요 데이터**: `preprocessed.parquet`의 `rating` (리스트) 또는 `var_rating` 필드 사용 가능.

## 2. 비전문가 통찰 가설 extension (The Outsider Insight Hypothesis)
> *"전문가는 틀에 갇혀 있지만, 제너럴리스트는 직관을 본다."*

*   **가설 내용**: 기존 분석에서 'Low Confidence' 리뷰어의 예측력이 높음을 확인했습니다. 이를 확장하여, **(Low Confidence 평점 - High Confidence 평점)**의 격차(Gap)가 클수록 인용이 높을 것이다.
    *   **Gap > 0**: 전문가는 비판했지만 일반 리뷰어는 열광함 (→ 대중적/혁신적일 가능성).
    *   **Gap < 0**: 전문가는 좋아했지만 일반 리뷰어는 이해 못함 (→ 너무 기술적이거나 틈새 분야).
*   **분석 방법**:
    *   각 논문별 `Trend Gap = Avg(Low Conf) - Avg(High Conf)` 계산.
    *   `Trend Gap`과 인용 수의 상관관계 분석.
*   **필요 데이터**: `preprocessed.parquet`의 `rating` 내 `confidence` 정보 파싱 필요.

## 3. 주제별 거품 가설 (The Topic Hype Hypothesis)
> *"점수 때문이 아니라, 그냥 요새 뜨는 주제라서 인용되는 것이다."*

*   **가설 내용**: 전체 상관관계(r ≈ 0.17)가 낮은 이유는 "인기 분야(Hype Topic)"의 노이즈 때문이다. **LLM, Diffusion** 같은 인기 분야는 리뷰 점수와 무관하게 인용이 높고, **Theory, Optimization** 같은 비주류 분야는 리뷰 점수가 인용을 잘 예측할 것이다.
*   **분석 방법**:
    *   논문 제목/키워드 기반 토픽 클러스터링 (LLM, RL, CV, Theory 등).
    *   각 클러스터 별 `Rating vs Citation` 상관관계(Pearson r) 비교.
*   **필요 데이터**: `preprocessed.parquet`의 `title` 필드.

## 4. 라벨 효과 가설 (The Label Effect Hypothesis)
> *"Oral이라서 인용되는가, 좋아서 Oral인가?"*

*   **가설 내용**: 비슷한 점수대(예: 평균 7.0)에서도 최종 결정(Decision)이 **Oral/Spotlight**냐 **Poster**냐에 따라 인용 수가 급격히 갈린다. 즉, 리뷰 점수 자체보다 학회가 붙여준 "라벨"이 인용을 견인한다.
*   **분석 방법**:
    *   점수 구간을 통제(Control)한 상태에서 `Decision Type`에 따른 인용 수 평균 비교 (ANOVA).
    *   회귀 분석: `Citation ~ Rating + Decision_Type` (Decision_Type의 회귀 계수 확인).
*   **필요 데이터**: `preprocessed.parquet`의 `decision` 필드.

## 5. 숨겨진 보석 가설 (The False Negatives)
> *"리뷰어가 거절한 논문 중 진짜 혁심은 어디에 있는가?"*

*   **가설 내용**: 현재 분석은 채택된(Accepted) 논문만 보고 있어 "생존자 편향(Survivorship Bias)"이 존재함. **거절(Reject)되었지만 훗날 최고 인용 수(Top 1%)를 기록한 논문**들은 어떤 리뷰 패턴을 보였는가?
    *   예: 점수는 낮았으나 Confidence가 매우 낮았거나, 리뷰 길이가 매우 길었거나(논쟁적).
*   **분석 방법**:
    *   `openreview_raw.json`(Reject 포함)에서 데이터 로드.
    *   Reject된 논문들의 인용 수 추적 (OpenAlex/Google Scholar 매칭 필요).
    *   High Impact Rejects vs Low Impact Rejects 리뷰 특성 비교.
*   **필요 데이터**: `openreview_raw.json` 및 추가적인 Reject 논문 인용 수 수집 필요.

---

## 실행 계획 (Action Plan)

1.  **우선 순위 1**: 데이터가 이미 준비된 **가설 1(양극화)** 및 **가설 4(라벨 효과)** 즉시 분석.
2.  **우선 순위 2**: 텍스트 처리가 필요한 **가설 3(주제 분석)** 스크립트 작성.
3.  **우선 순위 3**: 추가 데이터 수집이 필요한 **가설 5(Reject 논문 분석)** 파이프라인 구축.
