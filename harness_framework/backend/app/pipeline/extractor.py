from __future__ import annotations

import colorsys
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np

from app.pipeline.parser import SlideRaw

_ε = 1e-8

_BULLET_STARTERS = ("-", "•", "·", "*")
_SENTENCE_PATTERN = re.compile(r"[.!?]")


@dataclass
class SlideFeatureVector:
    slide_index: int

    # Typography (29차원, index 0~28)
    dominant_font_one_hot: list[float]  # 길이 20 (KNOWN_FONTS 19개 + Other 1개)
    font_size_mean: float               # pt / 72
    font_size_std: float                # pt / 72
    font_size_min: float                # pt / 72
    font_size_max: float                # pt / 72
    font_size_median: float             # pt / 72
    bold_ratio: float
    italic_ratio: float
    font_variety_count: float           # 사용 폰트 수 / 5, clip 1.0
    line_spacing_normalized: float      # 줄간격 평균 / 2.0, clip at 1.0. 텍스트 없으면 0.

    # Color (15차원, index 29~43)
    dominant_color_1: tuple[float, float, float]
    dominant_color_2: tuple[float, float, float]
    dominant_color_3: tuple[float, float, float]
    background_color: tuple[float, float, float]
    color_variance: float
    saturation_mean: float
    brightness_mean: float

    # Layout (11차원, index 44~54)
    text_area_ratio: float
    image_area_ratio: float
    whitespace_ratio: float
    alignment_left_ratio: float
    alignment_center_ratio: float
    alignment_right_ratio: float
    margin_top: float
    margin_bottom: float
    margin_left: float
    margin_right: float
    element_count: float                # 요소 수 / 20, clip 1.0

    # Content Density (4차원, index 55~58)
    word_count_normalized: float        # 단어 수 / 100, clip 1.0
    bullet_count_normalized: float      # 불릿 수 / 20, clip 1.0
    text_image_ratio: float             # 텍스트 면적 / (텍스트+이미지 면적)
    sentence_count_normalized: float    # 문장 수 / 30, clip 1.0

    def to_numpy(self) -> np.ndarray:
        """모든 수치 feature를 59차원 1D numpy 배열로 직렬화한다."""
        values: list[float] = (
            self.dominant_font_one_hot  # 0~19 (20)
            + [
                self.font_size_mean,           # 20
                self.font_size_std,            # 21
                self.font_size_min,            # 22
                self.font_size_max,            # 23
                self.font_size_median,         # 24
                self.bold_ratio,               # 25
                self.italic_ratio,             # 26
                self.font_variety_count,       # 27
                self.line_spacing_normalized,  # 28
            ]
            + list(self.dominant_color_1)   # 29~31
            + list(self.dominant_color_2)   # 32~34
            + list(self.dominant_color_3)   # 35~37
            + list(self.background_color)   # 38~40
            + [
                self.color_variance,           # 41
                self.saturation_mean,          # 42
                self.brightness_mean,          # 43
                self.text_area_ratio,          # 44
                self.image_area_ratio,         # 45
                self.whitespace_ratio,         # 46
                self.alignment_left_ratio,     # 47
                self.alignment_center_ratio,   # 48
                self.alignment_right_ratio,    # 49
                self.margin_top,               # 50
                self.margin_bottom,            # 51
                self.margin_left,              # 52
                self.margin_right,             # 53
                self.element_count,            # 54
                self.word_count_normalized,    # 55
                self.bullet_count_normalized,  # 56
                self.text_image_ratio,         # 57
                self.sentence_count_normalized,  # 58
            ]
        )
        return np.array(values, dtype=np.float64)


class SlideFeatureExtractor:
    KNOWN_FONTS = [
        "Pretendard", "Noto Sans KR", "Malgun Gothic", "나눔고딕",
        "Arial", "Helvetica", "Times New Roman", "Georgia",
        "Calibri", "Cambria", "Verdana", "Tahoma",
        "Apple SD Gothic Neo", "Spoqa Han Sans", "Source Han Sans",
        "Roboto", "Open Sans", "Lato", "Montserrat",
    ]  # 길이 19 고정 (index 0~18). 목록에 없는 폰트는 index 19 = "Other"에 집계.

    def extract(self, slide: SlideRaw) -> SlideFeatureVector:
        """단일 SlideRaw → SlideFeatureVector 변환."""
        typo = self._typography(slide)
        color = self._color(slide)
        layout = self._layout(slide)
        content = self._content(slide)

        return SlideFeatureVector(
            slide_index=slide.slide_index,
            # Typography
            dominant_font_one_hot=typo["dominant_font_one_hot"],
            font_size_mean=typo["font_size_mean"],
            font_size_std=typo["font_size_std"],
            font_size_min=typo["font_size_min"],
            font_size_max=typo["font_size_max"],
            font_size_median=typo["font_size_median"],
            bold_ratio=typo["bold_ratio"],
            italic_ratio=typo["italic_ratio"],
            font_variety_count=typo["font_variety_count"],
            line_spacing_normalized=typo["line_spacing_normalized"],
            # Color
            dominant_color_1=color["dominant_color_1"],
            dominant_color_2=color["dominant_color_2"],
            dominant_color_3=color["dominant_color_3"],
            background_color=color["background_color"],
            color_variance=color["color_variance"],
            saturation_mean=color["saturation_mean"],
            brightness_mean=color["brightness_mean"],
            # Layout
            text_area_ratio=layout["text_area_ratio"],
            image_area_ratio=layout["image_area_ratio"],
            whitespace_ratio=layout["whitespace_ratio"],
            alignment_left_ratio=layout["alignment_left_ratio"],
            alignment_center_ratio=layout["alignment_center_ratio"],
            alignment_right_ratio=layout["alignment_right_ratio"],
            margin_top=layout["margin_top"],
            margin_bottom=layout["margin_bottom"],
            margin_left=layout["margin_left"],
            margin_right=layout["margin_right"],
            element_count=layout["element_count"],
            # Content
            word_count_normalized=content["word_count_normalized"],
            bullet_count_normalized=content["bullet_count_normalized"],
            text_image_ratio=content["text_image_ratio"],
            sentence_count_normalized=content["sentence_count_normalized"],
        )

    def extract_all(self, slides: list[SlideRaw]) -> list[SlideFeatureVector]:
        """슬라이드 목록 전체 변환."""
        return [self.extract(s) for s in slides]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _typography(self, slide: SlideRaw) -> dict:
        texts = slide.text_elements
        n = len(texts)

        # dominant_font_one_hot (20차원)
        one_hot = [0.0] * 20
        if n > 0:
            font_counter: Counter[str] = Counter(t.font_family for t in texts)
            known_count = 0
            for i, font in enumerate(self.KNOWN_FONTS):
                cnt = font_counter.get(font, 0)
                one_hot[i] = cnt / n
                known_count += cnt
            one_hot[19] = max(0.0, (n - known_count)) / n  # Other

        # font_size statistics (정규화: pt / 72)
        if n > 0:
            sizes = np.array([t.font_size for t in texts], dtype=np.float64)
            font_size_mean = float(np.mean(sizes)) / 72
            font_size_std = float(np.std(sizes)) / 72
            font_size_min = float(np.min(sizes)) / 72
            font_size_max = float(np.max(sizes)) / 72
            font_size_median = float(np.median(sizes)) / 72
        else:
            font_size_mean = font_size_std = font_size_min = font_size_max = font_size_median = 0.0

        # bold / italic ratios
        if n > 0:
            bold_ratio = sum(1 for t in texts if t.is_bold) / n
            italic_ratio = sum(1 for t in texts if t.is_italic) / n
        else:
            bold_ratio = italic_ratio = 0.0

        # font variety
        variety = len(set(t.font_family for t in texts))
        font_variety_count = min(variety / 5, 1.0)

        # line spacing — TextElement does not carry line_spacing from parser.
        # Treat absent data as default (1.0), normalized to 1.0/2.0 = 0.5.
        # Empty slide → 0 per dataclass spec.
        line_spacing_normalized = 0.5 if n > 0 else 0.0

        return {
            "dominant_font_one_hot": one_hot,
            "font_size_mean": font_size_mean,
            "font_size_std": font_size_std,
            "font_size_min": font_size_min,
            "font_size_max": font_size_max,
            "font_size_median": font_size_median,
            "bold_ratio": bold_ratio,
            "italic_ratio": italic_ratio,
            "font_variety_count": font_variety_count,
            "line_spacing_normalized": line_spacing_normalized,
        }

    def _color(self, slide: SlideRaw) -> dict:
        texts = slide.text_elements

        # 가장 빈도 높은 3개 텍스트 색상
        color_counter: Counter[tuple[int, int, int]] = Counter(
            t.color_rgb for t in texts
        )
        top3 = [c for c, _ in color_counter.most_common(3)]
        while len(top3) < 3:
            top3.append((0, 0, 0))

        def norm_rgb(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
            return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)

        dc1 = norm_rgb(top3[0])
        dc2 = norm_rgb(top3[1])
        dc3 = norm_rgb(top3[2])
        bg = norm_rgb(slide.background_color_rgb)

        # color_variance: dominant_color 3개의 9개 RGB 값 전체 분산
        all_vals = list(dc1) + list(dc2) + list(dc3)
        color_variance = float(np.var(all_vals))

        # saturation / brightness via HSV
        def s_v(rgb_norm: tuple[float, float, float]) -> tuple[float, float]:
            _, s, v = colorsys.rgb_to_hsv(*rgb_norm)
            return s, v

        sv1 = s_v(dc1)
        sv2 = s_v(dc2)
        sv3 = s_v(dc3)
        saturation_mean = (sv1[0] + sv2[0] + sv3[0]) / 3.0
        brightness_mean = (sv1[1] + sv2[1] + sv3[1]) / 3.0

        return {
            "dominant_color_1": dc1,
            "dominant_color_2": dc2,
            "dominant_color_3": dc3,
            "background_color": bg,
            "color_variance": color_variance,
            "saturation_mean": saturation_mean,
            "brightness_mean": brightness_mean,
        }

    def _layout(self, slide: SlideRaw) -> dict:
        texts = slide.text_elements
        images = slide.image_elements
        all_elems = [*texts, *images]

        # area ratios
        text_area = sum(t.width * t.height for t in texts)
        image_area = sum(img.width * img.height for img in images)
        text_area_ratio = min(text_area, 1.0)
        image_area_ratio = min(image_area, 1.0)
        whitespace_ratio = max(0.0, 1.0 - text_area_ratio - image_area_ratio)

        # alignment ratios (unknown alignment은 제외)
        if texts:
            nt = len(texts)
            alignment_left_ratio = sum(1 for t in texts if t.alignment == "left") / nt
            alignment_center_ratio = sum(1 for t in texts if t.alignment == "center") / nt
            alignment_right_ratio = sum(1 for t in texts if t.alignment == "right") / nt
        else:
            alignment_left_ratio = alignment_center_ratio = alignment_right_ratio = 0.0

        # margins
        if all_elems:
            margin_top = max(0.0, min(1.0, min(e.y for e in all_elems)))
            margin_bottom = max(0.0, min(1.0, min(1.0 - e.y - e.height for e in all_elems)))
            margin_left = max(0.0, min(1.0, min(e.x for e in all_elems)))
            margin_right = max(0.0, min(1.0, min(1.0 - e.x - e.width for e in all_elems)))
        else:
            margin_top = margin_bottom = margin_left = margin_right = 0.5

        element_count = min(len(all_elems) / 20.0, 1.0)

        return {
            "text_area_ratio": text_area_ratio,
            "image_area_ratio": image_area_ratio,
            "whitespace_ratio": whitespace_ratio,
            "alignment_left_ratio": alignment_left_ratio,
            "alignment_center_ratio": alignment_center_ratio,
            "alignment_right_ratio": alignment_right_ratio,
            "margin_top": margin_top,
            "margin_bottom": margin_bottom,
            "margin_left": margin_left,
            "margin_right": margin_right,
            "element_count": element_count,
        }

    def _content(self, slide: SlideRaw) -> dict:
        texts = slide.text_elements

        all_text = " ".join(t.text for t in texts)
        word_count_normalized = min(len(all_text.split()) / 100.0, 1.0)

        bullet_count = sum(
            1 for t in texts if t.text.strip().startswith(_BULLET_STARTERS)
        )
        bullet_count_normalized = min(bullet_count / 20.0, 1.0)

        sentence_count = len(_SENTENCE_PATTERN.findall(all_text))
        sentence_count_normalized = min(sentence_count / 30.0, 1.0)

        text_area = sum(t.width * t.height for t in texts)
        image_area = sum(img.width * img.height for img in slide.image_elements)
        denom = text_area + image_area
        text_image_ratio = text_area / denom if denom > _ε else 0.0

        return {
            "word_count_normalized": word_count_normalized,
            "bullet_count_normalized": bullet_count_normalized,
            "text_image_ratio": text_image_ratio,
            "sentence_count_normalized": sentence_count_normalized,
        }
