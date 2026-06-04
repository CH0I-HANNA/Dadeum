import pytest

from app.pipeline.hmm_scorer import HMMScorer, _rule_based_score


# ── _rule_based_score 단위 테스트 ─────────────────────────────────────────────

class TestRuleBasedScore:
    def test_short_sequence_returns_zero(self):
        assert _rule_based_score([]) == 0.0
        assert _rule_based_score([0]) == 0.0
        assert _rule_based_score([0, 2]) == 0.0

    def test_normal_sequence_returns_zero(self):
        # 표지 → 섹션 → 본문 → 본문 → 마무리
        assert _rule_based_score([0, 1, 2, 2, 4]) == 0.0

    def test_cover_after_first_slide(self):
        # 표지가 중간에 등장 (+0.25)
        score = _rule_based_score([0, 1, 0, 2, 4])
        assert score == pytest.approx(0.25)

    def test_cover_appears_twice_after_first(self):
        # 표지가 두 번 중간에 등장 (+0.50)
        score = _rule_based_score([0, 0, 1, 2, 4])
        assert score == pytest.approx(0.25)

    def test_closing_before_last_slide(self):
        # 마무리가 마지막 전에 등장 (+0.20)
        score = _rule_based_score([0, 1, 4, 2, 4])
        assert score == pytest.approx(0.20 + 0.20)  # 마무리 중간 + 마무리 후 본문

    def test_closing_followed_by_body(self):
        # 마무리 다음에 본문 등장 (+0.20 for closing before last, +0.20 for body after closing)
        score = _rule_based_score([0, 1, 2, 4, 2, 4])
        assert score == pytest.approx(0.20 + 0.20)

    def test_four_consecutive_same_role(self):
        # 동일 역할 4번 연속 (+0.15)
        score = _rule_based_score([0, 2, 2, 2, 2, 4])
        assert score == pytest.approx(0.15)

    def test_five_consecutive_adds_only_once(self):
        # 5번 연속이어도 4번째 진입할 때만 +0.15 (run_len==4 조건)
        score = _rule_based_score([0, 2, 2, 2, 2, 2, 4])
        assert score == pytest.approx(0.15)

    def test_penalty_clipped_at_one(self):
        # 다수의 위반이 누적되어도 최대 1.0
        # 표지 반복 4번 → 4 * 0.25 = 1.0 → clipped
        score = _rule_based_score([0, 0, 0, 0, 0, 4])
        assert score == 1.0

    def test_abnormal_screenshot_sequence(self):
        # 마무리 표지 역순 패턴
        score = _rule_based_score([4, 0, 2, 2, 1, 0, 2, 4, 0])
        assert score == 1.0

    def test_score_in_range(self):
        for seq in [
            [0, 1, 2, 3, 4],
            [0, 0, 1, 2, 4],
            [4, 2, 0, 1, 2],
            [0, 1, 2, 2, 2, 2, 4],
        ]:
            s = _rule_based_score(seq)
            assert 0.0 <= s <= 1.0, f"seq={seq}, score={s}"


# ── HMMScorer 클래스 테스트 ────────────────────────────────────────────────────

class TestHMMScorer:
    def test_load_returns_instance(self):
        scorer = HMMScorer.load()
        assert isinstance(scorer, HMMScorer)

    def test_score_sequence_normal(self):
        scorer = HMMScorer.load()
        assert scorer.score_sequence([0, 1, 2, 2, 4]) == 0.0

    def test_score_sequence_abnormal(self):
        scorer = HMMScorer.load()
        assert scorer.score_sequence([4, 0, 2, 2, 1, 0, 2, 4, 0]) == 1.0

    def test_score_sequence_short(self):
        scorer = HMMScorer.load()
        assert scorer.score_sequence([0, 1]) == 0.0

    def test_score_always_in_range(self):
        scorer = HMMScorer.load()
        for seq in [[0, 1, 2, 4], [0, 0, 0, 0, 4], [4, 2, 1, 0]]:
            s = scorer.score_sequence(seq)
            assert 0.0 <= s <= 1.0
