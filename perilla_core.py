from __future__ import annotations

import colorsys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from PIL import Image, ImageOps

# ROI trung tâm dùng giống nhau cho ảnh camera và ảnh tải lên.
# (x1, y1, x2, y2) theo tỉ lệ 0..1 của ảnh thật.
ROI_NORMALIZED = (0.35, 0.35, 0.65, 0.65)

# Thứ tự feature phải giống hệt lúc huấn luyện model.joblib.
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

    @property
    def features(self) -> np.ndarray:
        """Vector [R, G, B, Hue, Saturation, Value] để đưa vào model."""
        return np.array(
            [self.r, self.g, self.b, self.hue, self.saturation, self.value],
            dtype=np.float64,
        )


def normalize_image(image: Image.Image) -> Image.Image:
    """Sửa hướng ảnh theo EXIF và chuyển về RGB."""
    return ImageOps.exif_transpose(image).convert("RGB")


def crop_indicator_roi(
    image: Image.Image,
    roi_normalized: tuple[float, float, float, float] = ROI_NORMALIZED,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Cắt ROI từ ảnh thật bằng tọa độ tương đối."""
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


def mean_rgb(roi: Image.Image) -> tuple[float, float, float]:
    """Tính Mean RGB trên toàn bộ pixel trong ROI."""
    arr = np.asarray(roi.convert("RGB"), dtype=np.float64)
    if arr.size == 0:
        raise ValueError("ROI không có dữ liệu pixel.")
    mean = arr.reshape(-1, 3).mean(axis=0)
    return float(mean[0]), float(mean[1]), float(mean[2])


def rgb_to_hsv(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Đổi Mean RGB sang Hue 0..360°, Saturation/Value 0..100%."""
    rn = np.clip(r / 255.0, 0.0, 1.0)
    gn = np.clip(g / 255.0, 0.0, 1.0)
    bn = np.clip(b / 255.0, 0.0, 1.0)
    h, s, v = colorsys.rgb_to_hsv(float(rn), float(gn), float(bn))
    return h * 360.0, s * 100.0, v * 100.0


def rgb_to_hex(r: float, g: float, b: float) -> str:
    values = [int(round(np.clip(v, 0, 255))) for v in (r, g, b)]
    return "#{:02X}{:02X}{:02X}".format(*values)


def analyze_color(roi: Image.Image) -> ColorResult:
    r, g, b = mean_rgb(roi)
    h, s, v = rgb_to_hsv(r, g, b)
    return ColorResult(
        r=r,
        g=g,
        b=b,
        hue=h,
        saturation=s,
        value=v,
        hex_code=rgb_to_hex(r, g, b),
    )


def load_model(model_path: str | Path) -> tuple[Any | None, str, str | None]:
    """
    Trả về (model, status, message).
    status: 'loaded', 'missing', hoặc 'error'.
    """
    path = Path(model_path)
    if not path.exists():
        return None, "missing", None

    try:
        model = joblib.load(path)
    except Exception as exc:  # lỗi model phải được báo thân thiện ở giao diện
        return None, "error", f"Không thể đọc model.joblib: {exc.__class__.__name__}"

    n_features = getattr(model, "n_features_in_", None)
    if n_features is not None and int(n_features) != len(FEATURE_SCHEMA):
        return (
            None,
            "error",
            f"Model đang cần {int(n_features)} feature, nhưng Perilla Tag gửi {len(FEATURE_SCHEMA)} feature.",
        )

    if not hasattr(model, "predict"):
        return None, "error", "model.joblib không có hàm predict()."

    return model, "loaded", None


def normalize_label(raw_label: Any) -> str | None:
    """Đổi nhãn model thành 1 trong 3 mã nội bộ. Không tự đoán nhãn lạ."""
    if isinstance(raw_label, np.generic):
        raw_label = raw_label.item()

    if isinstance(raw_label, str):
        key = raw_label.strip().lower()
        mapping = {
            "fresh": "fresh",
            "transition": "transition",
            "spoiled": "spoiled",
        }
        return mapping.get(key)

    if isinstance(raw_label, (int, np.integer)) and not isinstance(raw_label, bool):
        return {0: "fresh", 1: "transition", 2: "spoiled"}.get(int(raw_label))

    return None


def predict_state(model: Any, color: ColorResult) -> tuple[str | None, str | None]:
    """Dự đoán 1 nhãn. Không tính hoặc hiển thị phần trăm 'độ tươi'."""
    x = color.features.reshape(1, -1)
    try:
        prediction = model.predict(x)
    except Exception as exc:
        return None, f"Mô hình không thể dự đoán: {exc.__class__.__name__}"

    if prediction is None or len(prediction) == 0:
        return None, "Mô hình không trả về kết quả."

    label = normalize_label(prediction[0])
    if label is None:
        return None, "Đầu ra của mô hình không đúng định dạng."
    return label, None
