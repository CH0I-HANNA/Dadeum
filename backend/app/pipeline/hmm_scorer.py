from __future__ import annotations

from typing import Optional

# 역할 인덱스 상수
ROLE_COVER = 0    # 표지
ROLE_SECTION = 1  # 섹션헤더
ROLE_BODY = 2     # 본문
ROLE_VISUAL = 3   # 도표/시각자료
ROLE_CLOSING = 4  # 마무리


def _rule_based_score(role_sequence: list[int]) -> float:
    """규칙 기반 구조 이상 점수 (0~1, 높을수록 이상).

    규칙:
    1. 표지(0)가 첫 슬라이드 이후에 등장 — 각 등장마다 +0.25
    2. 마무리(4)가 마지막 슬라이드 이전에 등장 — 각 등장마다 +0.20
    3. 같은 역할이 4번 이상 연속 — +0.15
    4. 마무리 다음에 표지/섹션/본문이 오는 경우 — 각 위반마다 +0.20
    """
    n = len(role_sequence)
    if n < 3:
        return 0.0

    penalty = 0.0

    for i, role in enumerate(role_sequence):
        # 규칙 1: 표지가 첫 슬라이드 이후 등장
        if role == ROLE_COVER and i > 0:
            penalty += 0.25

        # 규칙 2: 마무리가 마지막 슬라이드 이전 등장
        if role == ROLE_CLOSING and i < n - 1:
            penalty += 0.20

        # 규칙 4: 마무리 다음에 내용 슬라이드 등장
        if i > 0 and role_sequence[i - 1] == ROLE_CLOSING:
            if role in (ROLE_COVER, ROLE_SECTION, ROLE_BODY, ROLE_VISUAL):
                penalty += 0.20

    # 규칙 3: 동일 역할 4번 이상 연속
    run_len = 1
    for i in range(1, n):
        if role_sequence[i] == role_sequence[i - 1]:
            run_len += 1
            if run_len == 4:
                penalty += 0.15
        else:
            run_len = 1

    return min(1.0, penalty)


class HMMScorer:
    def score_sequence(self, role_sequence: list[int]) -> float:
        return _rule_based_score(role_sequence)

    @classmethod
    def load(cls) -> "HMMScorer":
        return cls()
