import numpy as np
import pytest

from app.pipeline.extractor import SlideFeatureExtractor, SlideFeatureVector
from app.pipeline.parser import ImageElement, SlideRaw, TextElement

EXTRACTOR = SlideFeatureExtractor()

_EXPECTED_DIM = 59


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_slide(
    slide_index: int = 0,
    texts: list[TextElement] | None = None,
    images: list[ImageElement] | None = None,
    bg: tuple[int, int, int] = (255, 255, 255),
    w_emu: int = 9144000,
    h_emu: int = 5143500,
) -> SlideRaw:
    return SlideRaw(
        slide_index=slide_index,
        text_elements=texts or [],
        image_elements=images or [],
        background_color_rgb=bg,
        slide_width_emu=w_emu,
        slide_height_emu=h_emu,
    )


def _make_text(
    text: str = "Hello",
    font: str = "Arial",
    size: float = 24.0,
    bold: bool = False,
    italic: bool = False,
    color: tuple[int, int, int] = (0, 0, 0),
    x: float = 0.1,
    y: float = 0.1,
    w: float = 0.5,
    h: float = 0.1,
    alignment: str = "left",
) -> TextElement:
    return TextElement(
        text=text,
        font_family=font,
        font_size=size,
        is_bold=bold,
        is_italic=italic,
        color_rgb=color,
        x=x,
        y=y,
        width=w,
        height=h,
        alignment=alignment,
    )


def _make_image(x: float = 0.6, y: float = 0.1, w: float = 0.3, h: float = 0.5) -> ImageElement:
    return ImageElement(x=x, y=y, width=w, height=h)


# ---------------------------------------------------------------------------
# Core invariants
# ---------------------------------------------------------------------------


class TestToNumpy:
    def test_empty_slide_is_59d(self):
        vec = EXTRACTOR.extract(_make_slide())
        arr = vec.to_numpy()
        assert arr.shape == (_EXPECTED_DIM,), f"Expected {_EXPECTED_DIM}, got {arr.shape[0]}"

    def test_text_only_slide_is_59d(self):
        slide = _make_slide(texts=[_make_text("Hello World", "Arial", 24.0)])
        arr = EXTRACTOR.extract(slide).to_numpy()
        assert arr.shape == (_EXPECTED_DIM,)

    def test_image_only_slide_is_59d(self):
        slide = _make_slide(images=[_make_image()])
        arr = EXTRACTOR.extract(slide).to_numpy()
        assert arr.shape == (_EXPECTED_DIM,)

    def test_mixed_slide_is_59d(self):
        slide = _make_slide(
            texts=[_make_text("Title"), _make_text("Body text here", "Calibri", 18.0)],
            images=[_make_image()],
        )
        arr = EXTRACTOR.extract(slide).to_numpy()
        assert arr.shape == (_EXPECTED_DIM,)

    def test_no_nan_empty_slide(self):
        arr = EXTRACTOR.extract(_make_slide()).to_numpy()
        assert np.all(np.isfinite(arr)), "NaN or Inf in empty slide vector"

    def test_no_nan_text_slide(self):
        slide = _make_slide(texts=[_make_text("Some text", "Pretendard", 20.0)])
        arr = EXTRACTOR.extract(slide).to_numpy()
        assert np.all(np.isfinite(arr)), "NaN or Inf in text slide vector"

    def test_no_nan_image_slide(self):
        arr = EXTRACTOR.extract(_make_slide(images=[_make_image()])).to_numpy()
        assert np.all(np.isfinite(arr))

    def test_values_are_float64(self):
        arr = EXTRACTOR.extract(_make_slide()).to_numpy()
        assert arr.dtype == np.float64


# ---------------------------------------------------------------------------
# Typography features
# ---------------------------------------------------------------------------


class TestTypography:
    def test_known_font_one_hot(self):
        slide = _make_slide(texts=[_make_text(font="Arial")])
        vec = EXTRACTOR.extract(slide)
        # Arial is index 4 in KNOWN_FONTS
        arial_idx = SlideFeatureExtractor.KNOWN_FONTS.index("Arial")
        assert vec.dominant_font_one_hot[arial_idx] == pytest.approx(1.0)
        assert vec.dominant_font_one_hot[19] == pytest.approx(0.0)  # Other

    def test_unknown_font_goes_to_other(self):
        slide = _make_slide(texts=[_make_text(font="Comic Sans MS")])
        vec = EXTRACTOR.extract(slide)
        assert vec.dominant_font_one_hot[19] == pytest.approx(1.0)

    def test_font_one_hot_sums_to_one(self):
        slide = _make_slide(
            texts=[
                _make_text(font="Arial"),
                _make_text(font="Calibri"),
                _make_text(font="UnknownFont"),
            ]
        )
        vec = EXTRACTOR.extract(slide)
        total = sum(vec.dominant_font_one_hot)
        assert total == pytest.approx(1.0)

    def test_font_one_hot_empty_slide(self):
        vec = EXTRACTOR.extract(_make_slide())
        assert all(v == 0.0 for v in vec.dominant_font_one_hot)

    def test_font_size_normalized_by_72(self):
        slide = _make_slide(texts=[_make_text(size=72.0)])
        vec = EXTRACTOR.extract(slide)
        assert vec.font_size_mean == pytest.approx(1.0)

    def test_font_size_zeros_for_empty(self):
        vec = EXTRACTOR.extract(_make_slide())
        assert vec.font_size_mean == 0.0
        assert vec.font_size_std == 0.0

    def test_bold_ratio(self):
        slide = _make_slide(
            texts=[_make_text(bold=True), _make_text(bold=True), _make_text(bold=False)]
        )
        vec = EXTRACTOR.extract(slide)
        assert vec.bold_ratio == pytest.approx(2 / 3)

    def test_italic_ratio(self):
        slide = _make_slide(texts=[_make_text(italic=True), _make_text(italic=False)])
        vec = EXTRACTOR.extract(slide)
        assert vec.italic_ratio == pytest.approx(0.5)

    def test_font_variety_count_clipped_at_1(self):
        # 6종 이상의 폰트 → clip at 1.0
        slide = _make_slide(
            texts=[_make_text(font=f"Font{i}") for i in range(10)]
        )
        vec = EXTRACTOR.extract(slide)
        assert vec.font_variety_count == pytest.approx(1.0)

    def test_line_spacing_default_when_text_exists(self):
        slide = _make_slide(texts=[_make_text()])
        vec = EXTRACTOR.extract(slide)
        assert vec.line_spacing_normalized == pytest.approx(0.5)

    def test_line_spacing_zero_for_empty(self):
        vec = EXTRACTOR.extract(_make_slide())
        assert vec.line_spacing_normalized == 0.0


# ---------------------------------------------------------------------------
# Color features
# ---------------------------------------------------------------------------


class TestColor:
    def test_dominant_color_normalized(self):
        slide = _make_slide(texts=[_make_text(color=(255, 128, 0))])
        vec = EXTRACTOR.extract(slide)
        assert vec.dominant_color_1 == pytest.approx((1.0, 128 / 255, 0.0))

    def test_fewer_than_3_colors_fills_black(self):
        slide = _make_slide(texts=[_make_text(color=(100, 100, 100))])
        vec = EXTRACTOR.extract(slide)
        assert vec.dominant_color_2 == (0.0, 0.0, 0.0)
        assert vec.dominant_color_3 == (0.0, 0.0, 0.0)

    def test_background_color_normalized(self):
        slide = _make_slide(bg=(0, 128, 255))
        vec = EXTRACTOR.extract(slide)
        assert vec.background_color == pytest.approx((0.0, 128 / 255, 1.0))

    def test_color_variance_all_black(self):
        slide = _make_slide(texts=[_make_text(color=(0, 0, 0))])
        vec = EXTRACTOR.extract(slide)
        # all 9 values are 0 → variance = 0
        assert vec.color_variance == pytest.approx(0.0)

    def test_color_variance_finite(self):
        slide = _make_slide(
            texts=[
                _make_text(color=(255, 0, 0)),
                _make_text(color=(0, 255, 0)),
                _make_text(color=(0, 0, 255)),
            ]
        )
        arr = EXTRACTOR.extract(slide).to_numpy()
        assert np.isfinite(arr[41])  # color_variance is index 41

    def test_saturation_brightness_in_range(self):
        slide = _make_slide(texts=[_make_text(color=(255, 0, 0))])
        vec = EXTRACTOR.extract(slide)
        assert 0.0 <= vec.saturation_mean <= 1.0
        assert 0.0 <= vec.brightness_mean <= 1.0

    def test_empty_slide_color_no_nan(self):
        arr = EXTRACTOR.extract(_make_slide()).to_numpy()
        assert np.all(np.isfinite(arr[29:44]))


# ---------------------------------------------------------------------------
# Layout features
# ---------------------------------------------------------------------------


class TestLayout:
    def test_text_area_ratio(self):
        # single text element occupying 0.5 × 0.2 = 0.10
        slide = _make_slide(texts=[_make_text(w=0.5, h=0.2)])
        vec = EXTRACTOR.extract(slide)
        assert vec.text_area_ratio == pytest.approx(0.10)

    def test_image_area_ratio(self):
        slide = _make_slide(images=[_make_image(w=0.4, h=0.5)])
        vec = EXTRACTOR.extract(slide)
        assert vec.image_area_ratio == pytest.approx(0.20)

    def test_whitespace_ratio_complement(self):
        slide = _make_slide(
            texts=[_make_text(w=0.3, h=0.2)],
            images=[_make_image(w=0.2, h=0.2)],
        )
        vec = EXTRACTOR.extract(slide)
        assert vec.whitespace_ratio == pytest.approx(1.0 - 0.06 - 0.04, abs=1e-6)

    def test_whitespace_clip_at_zero(self):
        # area sums > 1 should not make whitespace negative
        slide = _make_slide(
            texts=[_make_text(w=0.9, h=0.9)],
            images=[_make_image(w=0.9, h=0.9)],
        )
        vec = EXTRACTOR.extract(slide)
        assert vec.whitespace_ratio >= 0.0

    def test_alignment_ratios(self):
        slide = _make_slide(
            texts=[
                _make_text(alignment="left"),
                _make_text(alignment="left"),
                _make_text(alignment="center"),
            ]
        )
        vec = EXTRACTOR.extract(slide)
        assert vec.alignment_left_ratio == pytest.approx(2 / 3)
        assert vec.alignment_center_ratio == pytest.approx(1 / 3)
        assert vec.alignment_right_ratio == pytest.approx(0.0)

    def test_margins_empty_slide_default(self):
        vec = EXTRACTOR.extract(_make_slide())
        assert vec.margin_top == pytest.approx(0.5)
        assert vec.margin_bottom == pytest.approx(0.5)
        assert vec.margin_left == pytest.approx(0.5)
        assert vec.margin_right == pytest.approx(0.5)

    def test_element_count_clipped(self):
        slide = _make_slide(texts=[_make_text() for _ in range(25)])
        vec = EXTRACTOR.extract(slide)
        assert vec.element_count == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Content Density features
# ---------------------------------------------------------------------------


class TestContentDensity:
    def test_word_count_normalized(self):
        slide = _make_slide(texts=[_make_text("one two three four five")])
        vec = EXTRACTOR.extract(slide)
        assert vec.word_count_normalized == pytest.approx(5 / 100)

    def test_word_count_clipped_at_1(self):
        slide = _make_slide(texts=[_make_text(" ".join(["word"] * 200))])
        vec = EXTRACTOR.extract(slide)
        assert vec.word_count_normalized == pytest.approx(1.0)

    def test_bullet_count(self):
        slide = _make_slide(
            texts=[
                _make_text("- item one"),
                _make_text("• item two"),
                _make_text("normal text"),
            ]
        )
        vec = EXTRACTOR.extract(slide)
        assert vec.bullet_count_normalized == pytest.approx(2 / 20)

    def test_sentence_count(self):
        slide = _make_slide(texts=[_make_text("Hello. World! How are you?")])
        vec = EXTRACTOR.extract(slide)
        assert vec.sentence_count_normalized == pytest.approx(3 / 30)

    def test_text_image_ratio_text_only(self):
        slide = _make_slide(texts=[_make_text(w=0.5, h=0.2)])
        vec = EXTRACTOR.extract(slide)
        assert vec.text_image_ratio == pytest.approx(1.0)

    def test_text_image_ratio_image_only(self):
        slide = _make_slide(images=[_make_image()])
        vec = EXTRACTOR.extract(slide)
        assert vec.text_image_ratio == pytest.approx(0.0)

    def test_text_image_ratio_empty_is_zero(self):
        vec = EXTRACTOR.extract(_make_slide())
        assert vec.text_image_ratio == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# extract_all
# ---------------------------------------------------------------------------


class TestExtractAll:
    def test_returns_same_count(self):
        slides = [_make_slide(slide_index=i) for i in range(5)]
        vecs = EXTRACTOR.extract_all(slides)
        assert len(vecs) == 5

    def test_slide_index_preserved(self):
        slides = [_make_slide(slide_index=i) for i in range(3)]
        vecs = EXTRACTOR.extract_all(slides)
        for i, vec in enumerate(vecs):
            assert vec.slide_index == i

    def test_all_59d(self):
        slides = [_make_slide(slide_index=i, texts=[_make_text(f"Slide {i}")]) for i in range(4)]
        for vec in EXTRACTOR.extract_all(slides):
            assert vec.to_numpy().shape == (_EXPECTED_DIM,)
