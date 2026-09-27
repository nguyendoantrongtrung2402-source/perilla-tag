from __future__ import annotations

import colorsys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from PIL import Image, ImageOps

# ROI trung tâm dùng giống nhau cho ảnh camera và ảnh tải lên.
ROI_NORMALIZED = (0.35, 0.35, 0.65, 0.65)

# Hai ngưỡng Hue thử nghiệm V1 từ dữ liệu thực nghiệm.
FRESH_HUE_MIN = 50.53
SPOILAGE_HUE_MAX = 43.41

# Chỉ để cảnh báo khi Hue sát ranh giới.
# KHÔNG phải ngưỡng khoa học về độ tươi/hư hỏng.
BOUNDARY_WARNING_DEG = 0.75

# Bộ lọc pixel, giữ gần với Color Stability Tool.
MAX_SAMPLED_PIXELS = 250_000
PIXEL_MAX_LIMIT = 250.0
PIXEL_MIN_LIMIT = 5.0
LUMINANCE_MIN = 12.0
LUMINANCE_MAX = 246.0
ROBUST_KEEP_RATIO = 0.95
MIN_FILTERED_PIXELS = 20

# Chỉ dùng để cảnh báo chất lượng ảnh.
QUALITY_MIN_SATURATION = 5.0
QUALITY_MIN_VALUE = 15.0
QUALITY_MAX_VALUE = 95.0
QUALITY_MAX_EXTREME_REJECT_RATIO = 0.20
QUALITY_MIN_USED_RATIO = 0.50

# Giữ để sau này có thể dùng model.
FEATURE_SCHEMA = ("R", "G", "B", "Hue", "Saturation", "Value")


@dataclass(frozen=True)
class ColorResult:
    r: float
    g: float
    b: float
    hue: float
    saturation: float
    value: float
    hex_code: str
    used_pixels: int
    sampled_pixels: int
    valid_ratio: float
    extreme_reject_ratio: float
    filter_fallback: bool

    @property
    def features(self) -> np.ndarray:
        return np.array(
            [self.r, self.g, self.b, self.hue, self.saturation, self.value],
            dtype=np.float64,
        )


@dataclass(frozen=True)
class ImageQuality:
    low_confidence: bool
    reasons: tuple[str, ...]

    @property
    def summary(self) -> str:
        if not self.reasons:
            return "Ổn"
        return "; ".join(self.reasons)


@dataclass(frozen=True)
class _RobustRGB:
    r: float
    g: float
    b: float
    used_pixels: int
    sampled_pixels: int
    valid_ratio: float
    extreme_reject_ratio: float
    filter_fallback: bool


def normalize_image(image: Image.Image) -> Image.Image:
    """Sửa hướng ảnh theo EXIF và chuyển về RGB."""
    return ImageOps.exif_transpose(image).convert("RGB")


def crop_indicator_roi(
    image: Image.Image,
    roi_normalized: tuple[float, float, float, float] = ROI_NORMALIZED,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Cắt ROI trung tâm từ ảnh thật."""

    image = normalize_image(image)
    width, height = image.size

    x1n, y1n, x2n, y2n = roi_normalized

    if width < 2 or height < 2:
        raise ValueError("Ảnh quá nhỏ để phân tích.")

    if not (0 <= x1n < x2n <= 1 and 0 <= y1n < y2n <= 1):
        raise ValueError("Tỷ lệ ROI không hợp lệ.")

    x1 = int(round(x1n * width))
    y1 = int(round(y1n * height))
    x2 = int(round(x2n * width))
    y2 = int(round(y2n * height))

    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(x1 + 1, min(x2, width))
    y2 = max(y1 + 1, min(y2, height))

    if (x2 - x1) < 2 or (y2 - y1) < 2:
        raise ValueError("ROI quá nhỏ để phân tích.")

    return image.crop((x1, y1, x2, y2)), (x1, y1, x2, y2)


def _robust_mean_rgb(roi: Image.Image) -> _RobustRGB:
    """
    Cách lấy màu đại diện:

    ROI
    → loại pixel quá sáng/tối
    → tìm median RGB
    → loại 5% pixel lệch xa màu trung tâm nhất
    → lấy Mean RGB.
    """

    arr = np.asarray(roi.convert("RGB"), dtype=np.float64)

    if arr.size == 0:
        raise ValueError("ROI không có dữ liệu pixel.")

    flat = arr.reshape(-1, 3)

    pixel_count = int(flat.shape[0])

    stride = max(1, pixel_count // MAX_SAMPLED_PIXELS)

    sampled = flat[::stride]

    sampled_count = int(sampled.shape[0])

    if sampled_count == 0:
        raise ValueError("ROI không có đủ dữ liệu pixel.")

    max_channel = sampled.max(axis=1)
    min_channel = sampled.min(axis=1)

    luminance = (
        0.2126 * sampled[:, 0]
        + 0.7152 * sampled[:, 1]
        + 0.0722 * sampled[:, 2]
    )

    initial_mask = (
        (max_channel < PIXEL_MAX_LIMIT)
        & (min_channel > PIXEL_MIN_LIMIT)
        & (luminance >= LUMINANCE_MIN)
        & (luminance <= LUMINANCE_MAX)
    )

    initial_valid = sampled[initial_mask]

    initial_valid_count = int(initial_valid.shape[0])

    extreme_reject_ratio = 1.0 - (
        initial_valid_count / sampled_count
    )

    # Nếu bộ lọc làm còn quá ít pixel thì dùng phương án dự phòng.
    filter_fallback = (
        initial_valid_count < MIN_FILTERED_PIXELS
    )

    candidates = (
        sampled
        if filter_fallback
        else initial_valid
    )

    if candidates.shape[0] == 0:
        raise ValueError(
            "ROI không có đủ pixel hợp lệ để phân tích."
        )

    # Median RGB làm tâm màu.
    median_rgb = np.median(
        candidates,
        axis=0,
    )

    # Khoảng cách từng pixel tới màu trung tâm.
    distances = np.linalg.norm(
        candidates - median_rgb,
        axis=1,
    )

    order = np.argsort(distances)

    # Giữ 95% pixel gần màu trung tâm nhất.
    keep_count = max(
        1,
        int(
            np.floor(
                candidates.shape[0]
                * ROBUST_KEEP_RATIO
            )
        ),
    )

    kept = candidates[
        order[:keep_count]
    ]

    mean = kept.mean(axis=0)

    used_pixels = int(
        kept.shape[0]
    )

    valid_ratio = (
        used_pixels
        / sampled_count
    )

    return _RobustRGB(
        r=float(mean[0]),
        g=float(mean[1]),
        b=float(mean[2]),
        used_pixels=used_pixels,
        sampled_pixels=sampled_count,
        valid_ratio=float(valid_ratio),
        extreme_reject_ratio=float(
            extreme_reject_ratio
        ),
        filter_fallback=filter_fallback,
    )


def mean_rgb(
    roi: Image.Image,
) -> tuple[float, float, float]:
    """Mean RGB sau bộ lọc pixel."""

    result = _robust_mean_rgb(roi)

    return (
        result.r,
        result.g,
        result.b,
    )


def rgb_to_hsv(
    r: float,
    g: float,
    b: float,
) -> tuple[float, float, float]:
    """
    Mean RGB
    → Hue 0–360°
    → Saturation 0–100%
    → Value 0–100%.
    """

    rn = np.clip(
        r / 255.0,
        0.0,
        1.0,
    )

    gn = np.clip(
        g / 255.0,
        0.0,
        1.0,
    )

    bn = np.clip(
        b / 255.0,
        0.0,
        1.0,
    )

    h, s, v = colorsys.rgb_to_hsv(
        float(rn),
        float(gn),
        float(bn),
    )

    return (
        h * 360.0,
        s * 100.0,
        v * 100.0,
    )


def rgb_to_hex(
    r: float,
    g: float,
    b: float,
) -> str:

    values = [
        int(
            round(
                np.clip(
                    value,
                    0,
                    255,
                )
            )
        )
        for value in (r, g, b)
    ]

    return "#{:02X}{:02X}{:02X}".format(
        *values
    )


def analyze_color(
    roi: Image.Image,
) -> ColorResult:
    """
    ROI
    → lọc pixel
    → Mean RGB
    → HSV
    → Hue.
    """

    robust = _robust_mean_rgb(
        roi
    )

    h, s, v = rgb_to_hsv(
        robust.r,
        robust.g,
        robust.b,
    )

    return ColorResult(
        r=robust.r,
        g=robust.g,
        b=robust.b,
        hue=h,
        saturation=s,
        value=v,
        hex_code=rgb_to_hex(
            robust.r,
            robust.g,
            robust.b,
        ),
        used_pixels=robust.used_pixels,
        sampled_pixels=robust.sampled_pixels,
        valid_ratio=robust.valid_ratio,
        extreme_reject_ratio=(
            robust.extreme_reject_ratio
        ),
        filter_fallback=(
            robust.filter_fallback
        ),
    )


def classify_hue(
    hue: float,
) -> str:
    """
    Phân loại V1 bằng Hue.

    >= 50.53
        → Còn tươi

    > 43.41 và < 50.53
        → Đang thay đổi

    <= 43.41
        → Có dấu hiệu hư hỏng
    """

    if not np.isfinite(hue):
        raise ValueError(
            "Hue không hợp lệ."
        )

    if hue >= FRESH_HUE_MIN:
        return "fresh"

    if hue <= SPOILAGE_HUE_MAX:
        return "spoilage_sign"

    return "transition"


def is_near_hue_boundary(
    hue: float,
) -> bool:
    """
    Chỉ dùng để cảnh báo khi
    Hue nằm sát ranh giới.
    """

    return (
        abs(
            hue - FRESH_HUE_MIN
        )
        <= BOUNDARY_WARNING_DEG
        or
        abs(
            hue - SPOILAGE_HUE_MAX
        )
        <= BOUNDARY_WARNING_DEG
    )


def assess_image_quality(
    color: ColorResult,
) -> ImageQuality:
    """
    Kiểm tra chất lượng ảnh.

    Không dùng kết quả này để
    quyết định tươi/hư.
    """

    reasons: list[str] = []

    if color.filter_fallback:
        reasons.append(
            "bộ lọc phải dùng phương án dự phòng"
        )

    if (
        color.extreme_reject_ratio
        > QUALITY_MAX_EXTREME_REJECT_RATIO
    ):
        reasons.append(
            "ROI có nhiều vùng quá sáng/tối"
        )

    if (
        color.valid_ratio
        < QUALITY_MIN_USED_RATIO
    ):
        reasons.append(
            "tỷ lệ pixel dùng để tính màu thấp"
        )

    if (
        color.saturation
        < QUALITY_MIN_SATURATION
    ):
        reasons.append(
            "màu có độ bão hòa quá thấp"
        )

    if (
        color.value
        < QUALITY_MIN_VALUE
    ):
        reasons.append(
            "ROI quá tối"
        )

    elif (
        color.value
        > QUALITY_MAX_VALUE
    ):
        reasons.append(
            "ROI quá sáng"
        )

    return ImageQuality(
        low_confidence=bool(
            reasons
        ),
        reasons=tuple(
            reasons
        ),
    )


# ==================================================
# MODEL — GIỮ CHO PHÁT TRIỂN SAU
# Perilla Tag V1 KHÔNG cần model.joblib.
# ==================================================

def load_model(
    model_path: str | Path,
) -> tuple[
    Any | None,
    str,
    str | None,
]:

    path = Path(
        model_path
    )

    if not path.exists():
        return (
            None,
            "missing",
            None,
        )

    try:
        model = joblib.load(
            path
        )

    except Exception as exc:
        return (
            None,
            "error",
            (
                "Không thể đọc model.joblib: "
                f"{exc.__class__.__name__}"
            ),
        )

    n_features = getattr(
        model,
        "n_features_in_",
        None,
    )

    if (
        n_features is not None
        and int(n_features)
        != len(FEATURE_SCHEMA)
    ):

        return (
            None,
            "error",
            (
                f"Model đang cần "
                f"{int(n_features)} feature, "
                f"nhưng Perilla Tag gửi "
                f"{len(FEATURE_SCHEMA)} feature."
            ),
        )

    if not hasattr(
        model,
        "predict",
    ):
        return (
            None,
            "error",
            "model.joblib không có hàm predict().",
        )

    return (
        model,
        "loaded",
        None,
    )


def normalize_label(
    raw_label: Any,
) -> str | None:

    if isinstance(
        raw_label,
        np.generic,
    ):
        raw_label = (
            raw_label.item()
        )

    if isinstance(
        raw_label,
        str,
    ):

        key = (
            raw_label
            .strip()
            .lower()
        )

        mapping = {
            "fresh":
                "fresh",
            "transition":
                "transition",
            "spoiled":
                "spoilage_sign",
            "spoilage_sign":
                "spoilage_sign",
        }

        return mapping.get(
            key
        )

    if (
        isinstance(
            raw_label,
            (int, np.integer),
        )
        and not isinstance(
            raw_label,
            bool,
        )
    ):

        return {
            0: "fresh",
            1: "transition",
            2: "spoilage_sign",
        }.get(
            int(raw_label)
        )

    return None


def predict_state(
    model: Any,
    color: ColorResult,
) -> tuple[
    str | None,
    str | None,
]:

    x = (
        color.features
        .reshape(1, -1)
    )

    try:
        prediction = (
            model.predict(x)
        )

    except Exception as exc:
        return (
            None,
            (
                "Mô hình không thể dự đoán: "
                f"{exc.__class__.__name__}"
            ),
        )

    if (
        prediction is None
        or len(prediction) == 0
    ):

        return (
            None,
            "Mô hình không trả về kết quả.",
        )

    label = normalize_label(
        prediction[0]
    )

    if label is None:
        return (
            None,
            "Đầu ra của mô hình không đúng định dạng.",
        )

    return (
        label,
        None,
    )
